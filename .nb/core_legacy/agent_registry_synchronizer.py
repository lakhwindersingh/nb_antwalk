#!/usr/bin/env python3
"""
Neutron Binary Percipience - Registry & Context Synchronizer

Reconciles the curated registry sections embedded in the AI agent settings files
with the canonical filesystem sources of truth:

    agent_registry     <- .nb/agentic/custom/agents/*.yaml      (list, agent_id)
    context_rules      <- .nb/context/rules/**                  (map, key -> path)
    context_contracts  <- .nb/context/contracts/**              (map, key -> path)
    workflow_registry  <- .nb/agentic/workflows/**              (map, key -> path)
                          .nb/agentic/custom/workflows/**
    workflow_hooks     <- agent autonomous_cicd_hooks /         (map, key -> path)
                          workflow_bindings + workflow triggers

Multi-LLM Targets
-----------------
The same registry projection is materialized for every supported coding agent
(mirroring terminal_agent_ast_proxy.SUPPORTED_AGENTS):

    claude   -> settings.json, .claude/settings.json   (top-level sections)
    gemini   -> .gemini/settings.json                  (namespaced: percipience)
    aider    -> .aider.conf.yml                        (namespaced: percipience)
    cursor   -> .cursor/settings.json                  (namespaced: percipience)

For the Claude targets the registry sections are projected at the document root
(backward compatible). For the other providers the platform block is namespaced
under ``percipience`` so provider-native keys are never clobbered, and a pointer
to that provider's canonical AST context file is recorded.

Semantics
---------
* agent_registry is projected as a sorted, de-duplicated list of declared agent_ids.
* context_rules / context_contracts / workflow_registry are reconciled as maps.
  Existing symbolic keys are preserved when they already point at a discovered
  file (so friendly aliases survive). Newly discovered files receive a
  deterministic key derived from their filename. Entries that point outside the
  managed directory (e.g. the ledger) are retained untouched.
* workflow_hooks reconciles the workflow hook bindings declared by agent
  manifests (autonomous_cicd_hooks.target_workflows, workflow_bindings) and the
  event triggers declared inside workflow files across both workflow
  directories.

The synchronizer is deterministic and idempotent so it can be wired as a mandatory
preflight step of the CI/CD gatekeeper workflow. It never mutates the underlying
rule, contract, agent, or workflow artifacts.
"""

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import yaml

    try:
        from yaml import CSafeLoader as SafeLoader
    except ImportError:
        from yaml import SafeLoader
except ImportError:
    yaml = None
    SafeLoader = None


class AgentRegistrySynchronizer:
    """Projects canonical agents, rules, contracts & workflows into AI agent settings."""

    AGENTS_DIR = ".nb/agentic/custom/agents"
    RULES_DIR = ".nb/context/rules"
    CONTRACTS_DIR = ".nb/context/contracts"
    WORKFLOWS_DIR = ".nb/agentic/workflows"
    CUSTOM_WORKFLOWS_DIR = ".nb/agentic/custom/workflows"
    SETTINGS_FILES = ("settings.json", ".claude/settings.json")
    PROVIDER_NAMESPACE = "percipience"

    # (settings_key, kind, source_dirs)
    SPECS: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
        ("agent_registry", "list", (AGENTS_DIR,)),
        ("context_rules", "map", (RULES_DIR,)),
        ("context_contracts", "map", (CONTRACTS_DIR,)),
        ("workflow_registry", "map", (WORKFLOWS_DIR, CUSTOM_WORKFLOWS_DIR)),
        ("workflow_hooks", "hooks", (WORKFLOWS_DIR, CUSTOM_WORKFLOWS_DIR)),
    )

    # Supported multi-LLM settings targets. ``namespace=None`` projects the
    # registry sections at the document root (Claude layout); otherwise the
    # platform block is nested under the ``percipience`` key.
    LLM_TARGETS: Tuple[Dict[str, Any], ...] = (
        {
            "id": "claude",
            "name": "Claude Code",
            "format": "json",
            "files": ("settings.json", ".claude/settings.json"),
            "namespace": None,
            "create": False,
            "context_file": ".nb/context/percipience_claude_context.md",
            "defaults": {},
        },
        {
            "id": "gemini",
            "name": "Gemini CLI",
            "format": "json",
            "files": (".gemini/settings.json",),
            "namespace": PROVIDER_NAMESPACE,
            "create": True,
            "context_file": ".nb/context/percipience_gemini_context.md",
            "defaults": {},
        },
        {
            "id": "aider",
            "name": "Aider",
            "format": "yaml",
            "files": (".aider.conf.yml",),
            "namespace": PROVIDER_NAMESPACE,
            "create": True,
            "context_file": ".nb/context/percipience_aider_context.md",
            "defaults": {"read": [".nb/context/percipience_aider_context.md"]},
        },
        {
            "id": "cursor",
            "name": "Cursor CLI",
            "format": "json",
            "files": (".cursor/settings.json",),
            "namespace": PROVIDER_NAMESPACE,
            "create": True,
            "context_file": None,
            "defaults": {},
        },
    )

    def __init__(self, workspace_root: Optional[Path] = None):
        if workspace_root:
            self.workspace_root = Path(workspace_root).resolve()
        else:
            cur = Path(__file__).resolve()
            if len(cur.parents) >= 3 and cur.parents[1].name in (".nb", "workplace"):
                self.workspace_root = cur.parents[2]
            else:
                self.workspace_root = cur.parents[1]

    # ------------------------------------------------------------------
    # Canonical sources
    # ------------------------------------------------------------------
    def scan_agent_ids(self) -> List[str]:
        """
        Returns the sorted, de-duplicated set of agent_ids declared by every
        YAML manifest under the canonical custom agents directory.
        """
        agent_ids: List[str] = []
        agents_dir = self.workspace_root / self.AGENTS_DIR
        if not agents_dir.exists():
            return agent_ids

        for manifest in sorted(agents_dir.glob("*.yaml")) + sorted(agents_dir.glob("*.yml")):
            agent_id = self._read_agent_id(manifest)
            if agent_id:
                agent_ids.append(agent_id)

        return sorted(set(agent_ids))

    def _read_agent_id(self, manifest: Path) -> Optional[str]:
        data = self._load_yaml(manifest)
        stem = manifest.stem
        fallback = stem if stem.startswith("agent_") else f"agent_{stem}"
        if not isinstance(data, dict):
            return fallback
        meta = data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {}
        return meta.get("agent_id") or data.get("agent_id") or fallback

    def _load_yaml(self, path: Path) -> Any:
        if yaml is None:
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                if SafeLoader is not None:
                    return yaml.load(f, Loader=SafeLoader) or {}
                return yaml.safe_load(f) or {}
        except Exception:
            return None

    def scan_files(self, rel_dir: str) -> List[str]:
        """Returns sorted, repo-relative POSIX paths for every file under rel_dir."""
        base = self.workspace_root / rel_dir
        if not base.exists():
            return []
        files = [
            p.relative_to(self.workspace_root).as_posix()
            for p in base.rglob("*")
            if p.is_file() and not p.name.startswith(".")
        ]
        return sorted(files)

    def scan_files_multi(self, rel_dirs: Tuple[str, ...]) -> List[str]:
        """Returns the sorted union of files across several canonical directories."""
        found: Set[str] = set()
        for rel_dir in rel_dirs:
            found.update(self.scan_files(rel_dir))
        return sorted(found)

    # ------------------------------------------------------------------
    # Workflow indexing & hook extraction
    # ------------------------------------------------------------------
    def _iter_workflows(self, rel_dirs: Tuple[str, ...]):
        for rel in self.scan_files_multi(rel_dirs):
            if not rel.endswith((".yaml", ".yml")):
                continue
            data = self._load_yaml(self.workspace_root / rel)
            if isinstance(data, dict):
                yield rel, data

    @staticmethod
    def _slug(value: Any) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
        return slug or "item"

    def _workflow_index(self, rel_dirs: Tuple[str, ...]) -> Tuple[Dict[str, str], Set[str]]:
        """Maps each workflow_id/id/stem alias to its artifact path."""
        id_to_path: Dict[str, str] = {}
        for rel, data in self._iter_workflows(rel_dirs):
            aliases: Set[str] = set()
            for key in ("workflow_id", "id"):
                val = data.get(key)
                if isinstance(val, str) and val:
                    aliases.add(val)
            stem = Path(rel).stem
            aliases.add(stem)
            if stem.startswith("wf_"):
                aliases.add(stem[3:])
            else:
                aliases.add(f"wf_{stem}")
            for alias in aliases:
                id_to_path.setdefault(alias, rel)
        return id_to_path, set(id_to_path.keys())

    @staticmethod
    def _hook_ids(raw: Any) -> List[str]:
        if isinstance(raw, dict):
            return [str(k) for k in raw.keys()]
        if isinstance(raw, list):
            ids: List[str] = []
            for item in raw:
                if isinstance(item, str):
                    ids.append(item)
                elif isinstance(item, dict):
                    val = item.get("id") or item.get("name") or item.get("event")
                    if val:
                        ids.append(str(val))
            return ids
        return []

    @staticmethod
    def _trigger_events(trigger: Any) -> List[str]:
        if isinstance(trigger, dict):
            events = trigger.get("events")
            if isinstance(events, list) and events:
                return [str(e) for e in events]
            ttype = trigger.get("type")
            if isinstance(ttype, str) and ttype:
                return [ttype]
            return []
        if isinstance(trigger, str) and trigger:
            return [trigger]
        if isinstance(trigger, list):
            return [str(e) for e in trigger if isinstance(e, str)]
        return []

    def _collect_hooks(self, rel_dirs: Tuple[str, ...]) -> Dict[str, str]:
        id_to_path, _ = self._workflow_index(rel_dirs)
        hooks: Dict[str, str] = {}

        for rel, data in self._iter_workflows(rel_dirs):
            wf_key = self._slug(data.get("workflow_id") or data.get("id") or Path(rel).stem)
            for hid in self._hook_ids(data.get("hooks")):
                hooks[f"{wf_key}__{self._slug(hid)}"] = rel
            for event in self._trigger_events(data.get("trigger")):
                hooks[f"{wf_key}__{self._slug(event)}"] = rel

        agents_dir = self.workspace_root / self.AGENTS_DIR
        if agents_dir.exists():
            for manifest in sorted(agents_dir.glob("*.yaml")) + sorted(agents_dir.glob("*.yml")):
                data = self._load_yaml(manifest)
                if not isinstance(data, dict):
                    continue
                meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
                agent_id = meta.get("agent_id") or data.get("agent_id") or self._read_agent_id(manifest)

                bindings: List[Tuple[Any, Any]] = []
                cicd = data.get("autonomous_cicd_hooks")
                if isinstance(cicd, dict):
                    for tw in cicd.get("target_workflows", []) or []:
                        if isinstance(tw, dict):
                            bindings.append((tw.get("workflow_id"), tw.get("step_id") or tw.get("insertion_point")))
                for wb in data.get("workflow_bindings", []) or []:
                    if isinstance(wb, dict):
                        bindings.append((wb.get("workflow_id"), wb.get("stage") or wb.get("step_id")))

                for workflow_id, step in bindings:
                    if not workflow_id:
                        continue
                    target = id_to_path.get(str(workflow_id), str(workflow_id))
                    key = f"{agent_id}__{self._slug(workflow_id)}__{self._slug(step or 'default')}"
                    hooks[key] = target

        return dict(sorted(hooks.items()))

    # ------------------------------------------------------------------
    # Targets
    # ------------------------------------------------------------------
    def settings_paths(self) -> List[Path]:
        """Returns the Claude settings file paths (backward-compatible helper)."""
        return [self.workspace_root / rel for rel in self.SETTINGS_FILES]

    def _read_any(self, path: Path, fmt: str) -> Dict[str, Any]:
        if not path.exists():
            return {}
        if fmt == "yaml":
            data = self._load_yaml(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        return data if isinstance(data, dict) else {}

    def _read_settings(self, path: Path) -> Dict[str, Any]:
        """Backward-compatible helper for the Claude JSON settings files."""
        return self._read_any(path, "json")

    def _write_settings(self, path: Path, data: Dict[str, Any]) -> None:
        """Backward-compatible helper for the Claude JSON settings files."""
        self._write_any(path, data, "json")

    def _write_any(self, path: Path, data: Dict[str, Any], fmt: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "yaml":
            if yaml is None:
                raise RuntimeError("PyYAML is required to serialize YAML targets")
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

    # ------------------------------------------------------------------
    # Reconciliation primitives
    # ------------------------------------------------------------------
    @staticmethod
    def _derive_key(rel_path: str, used: set) -> str:
        stem = Path(rel_path).stem
        key = re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_") or "item"
        if key not in used:
            return key
        ext = Path(rel_path).suffix.lstrip(".")
        base = f"{key}_{ext}" if ext else key
        candidate, i = base, 2
        while candidate in used:
            candidate = f"{base}_{i}"
            i += 1
        return candidate

    @staticmethod
    def _prefixes(rel_dirs: Tuple[str, ...]) -> Tuple[str, ...]:
        return tuple(rel.rstrip("/") + "/" for rel in rel_dirs)

    def _build_map(self, current: Any, rel_dirs: Tuple[str, ...]) -> Dict[str, str]:
        """Projects discovered files into a symbolic-key -> path map."""
        current = current if isinstance(current, dict) else {}
        prefixes = self._prefixes(rel_dirs)

        existing_key_by_path: Dict[str, str] = {}
        retained: Dict[str, str] = {}
        for key, value in current.items():
            if isinstance(value, str) and value.startswith(prefixes):
                existing_key_by_path[value] = key
            else:
                retained[key] = value

        result: Dict[str, str] = dict(retained)
        used = set(result.keys())
        for rel in self.scan_files_multi(rel_dirs):
            key = existing_key_by_path.get(rel)
            if not key or key in used:
                key = self._derive_key(rel, used)
            result[key] = rel
            used.add(key)
        return result

    def _build_hooks(self, current: Any, rel_dirs: Tuple[str, ...]) -> Dict[str, str]:
        """Reconciles workflow hook bindings into a symbolic-key -> workflow map."""
        current = current if isinstance(current, dict) else {}
        prefixes = self._prefixes(rel_dirs)
        _, workflow_ids = self._workflow_index(rel_dirs)
        desired = self._collect_hooks(rel_dirs)

        retained = {
            key: value
            for key, value in current.items()
            if key not in desired
            and not (isinstance(value, str) and (value.startswith(prefixes) or value in workflow_ids))
        }
        result: Dict[str, str] = dict(retained)
        result.update(desired)
        return result

    def _project_sections(self, current: Dict[str, Any]) -> Dict[str, Any]:
        """Builds the reconciled registry sections from the canonical sources."""
        sections: Dict[str, Any] = {}
        for settings_key, kind, sources in self.SPECS:
            if kind == "list":
                sections[settings_key] = self.scan_agent_ids()
            elif kind == "hooks":
                sections[settings_key] = self._build_hooks(current.get(settings_key), sources)
            else:
                sections[settings_key] = self._build_map(current.get(settings_key), sources)
        return sections

    def _project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Returns the fully synchronized Claude-style settings document (root sections)."""
        projected = copy.deepcopy(data)
        projected.update(self._project_sections(data))
        return projected

    def _project_target(self, target: Dict[str, Any], existing: Dict[str, Any]) -> Dict[str, Any]:
        """Returns the synchronized settings document for one LLM target."""
        namespace = target.get("namespace")
        if namespace is None:
            return self._project(existing)

        projected = copy.deepcopy(existing)
        for key, value in (target.get("defaults") or {}).items():
            projected.setdefault(key, copy.deepcopy(value))

        old_block = projected.get(namespace)
        old_block = dict(old_block) if isinstance(old_block, dict) else {}

        block: Dict[str, Any] = {
            "provider": target["id"],
            "display_name": target["name"],
            "format": target["format"],
        }
        if target.get("context_file"):
            block["context_file"] = target["context_file"]
        block.update(self._project_sections(old_block))
        projected[namespace] = block
        return projected

    @staticmethod
    def _section_keys() -> Set[str]:
        return {spec[0] for spec in AgentRegistrySynchronizer.SPECS}

    def _section_drift(self, current: Any, desired: Any, sources: Tuple[str, ...], kind: str) -> Dict[str, Any]:
        if kind == "list":
            current_list = [x for x in current if isinstance(x, str)] if isinstance(current, list) else []
            desired_list = list(desired)
            return {
                "in_sync": current_list == desired_list,
                "count": len(desired_list),
                "missing": sorted(set(desired_list) - set(current_list)),
                "extra": sorted(set(current_list) - set(desired_list)),
            }

        current_map = current if isinstance(current, dict) else {}
        desired_map = desired if isinstance(desired, dict) else {}
        prefixes = self._prefixes(sources)
        if kind == "hooks":
            _, workflow_ids = self._workflow_index(sources)
        else:
            workflow_ids = set()
        managed_current = {
            k: v
            for k, v in current_map.items()
            if k in desired_map
            or (isinstance(v, str) and (v.startswith(prefixes) or v in workflow_ids))
        }
        return {
            "in_sync": current_map == desired_map,
            "count": len(desired_map),
            "missing": sorted(set(desired_map.values()) - set(managed_current.values())),
            "extra": sorted(set(managed_current.values()) - set(desired_map.values())),
        }

    def _diff_target(self, target: Dict[str, Any], current: Dict[str, Any], desired: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        namespace = target.get("namespace")
        sections: Dict[str, Any] = {}
        in_sync = True

        if namespace is None:
            for key, kind, sources in self.SPECS:
                drift = self._section_drift(current.get(key), desired.get(key), sources, kind)
                sections[key] = drift
                in_sync = in_sync and drift["in_sync"]
            return sections, in_sync

        cur_block = current.get(namespace) if isinstance(current.get(namespace), dict) else {}
        des_block = desired.get(namespace) if isinstance(desired.get(namespace), dict) else {}
        for key, kind, sources in self.SPECS:
            drift = self._section_drift(cur_block.get(key), des_block.get(key), sources, kind)
            sections[key] = drift
            in_sync = in_sync and drift["in_sync"]

        keys = self._section_keys()
        cur_meta = {k: v for k, v in cur_block.items() if k not in keys}
        des_meta = {k: v for k, v in des_block.items() if k not in keys}
        meta_sync = cur_meta == des_meta
        sections["_metadata"] = {
            "in_sync": meta_sync,
            "count": len(des_meta),
            "missing": sorted(set(des_meta) - set(cur_meta)),
            "extra": sorted(set(cur_meta) - set(des_meta)),
        }
        return sections, (in_sync and meta_sync and cur_block == des_block)

    def _changed_sections(self, target: Dict[str, Any], current: Dict[str, Any], desired: Dict[str, Any]) -> List[str]:
        namespace = target.get("namespace")
        if namespace is None:
            return [key for key, _, _ in self.SPECS if current.get(key) != desired.get(key)]

        keys = self._section_keys()
        cur_block = current.get(namespace) if isinstance(current.get(namespace), dict) else {}
        des_block = desired.get(namespace) if isinstance(desired.get(namespace), dict) else {}
        changed = [key for key, _, _ in self.SPECS if cur_block.get(key) != des_block.get(key)]
        cur_meta = {k: v for k, v in cur_block.items() if k not in keys}
        des_meta = {k: v for k, v in des_block.items() if k not in keys}
        if cur_meta != des_meta:
            changed.append("_metadata")
        return changed

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def check(self) -> Dict[str, Any]:
        """Non-mutating drift report for every managed section of every LLM settings file."""
        report: Dict[str, Any] = {"files": {}, "missing": [], "drift": False}
        for target in self.LLM_TARGETS:
            fmt = target["format"]
            for rel in target["files"]:
                path = self.workspace_root / rel
                if not path.exists():
                    if target.get("create", False):
                        report["missing"].append(rel)
                        report["drift"] = True
                    continue
                current = self._read_any(path, fmt)
                desired = self._project_target(target, current)
                sections, in_sync = self._diff_target(target, current, desired)
                report["files"][rel] = sections
                if not in_sync:
                    report["drift"] = True
        return report

    def sync(self) -> Dict[str, Any]:
        """
        Writes the synchronized registry sections into every LLM settings file.
        Idempotent: files already in sync are left byte-identical.
        """
        result: Dict[str, Any] = {
            "status": "IN_SYNC",
            "updated": [],
            "created": [],
            "unchanged": [],
            "missing": [],
            "sections": {},
        }
        for target in self.LLM_TARGETS:
            fmt = target["format"]
            for rel in target["files"]:
                path = self.workspace_root / rel
                exists = path.exists()
                if not exists and not target.get("create", False):
                    result["missing"].append(rel)
                    continue

                current = self._read_any(path, fmt) if exists else {}
                desired = self._project_target(target, current)

                if not exists:
                    self._write_any(path, desired, fmt)
                    result["created"].append(rel)
                    result["sections"][rel] = ["*created*"]
                    continue

                if current == desired:
                    result["unchanged"].append(rel)
                    continue

                self._write_any(path, desired, fmt)
                result["updated"].append(rel)
                result["sections"][rel] = self._changed_sections(target, current, desired)

        if result["updated"] or result["created"]:
            result["status"] = "SYNCHRONIZED"
        return result

    def run(self, apply: bool = True) -> Dict[str, Any]:
        """Entrypoint used by the workflow executor."""
        return self.sync() if apply else self.check()

    @classmethod
    def cli(cls, argv: Optional[List[str]] = None) -> int:
        argv = list(sys.argv[1:] if argv is None else argv)
        apply = "--check" not in argv
        result = cls().run(apply=apply)
        print(json.dumps(result, indent=2))
        return 0 if not (apply is False and result.get("drift")) else 1


if __name__ == "__main__":
    raise SystemExit(AgentRegistrySynchronizer.cli())
