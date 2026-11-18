#!/usr/bin/env python3
"""
Neutron Binary Percipience - Plan Module Orchestrator

Projects a canonical plan directory (its root ``concise.md`` / ``detailed.md`` and
any discovered submodules under ``modules/``) into the agentic runtime so the plan
can be derived autonomously, sequentially, and reproducibly.

For a given plan directory the orchestrator:

    1. Reads ``MANIFEST.yaml`` to resolve ``plan_id``, ``plan_name``, and the
       declared ``modules:`` list.
    2. Discoveres every submodule that is actually present on disk
       (``modules/**/*.md``), so plans whose submodules have not yet been authored
       still process cleanly, and plans that gain submodules later are picked up
       automatically.
    3. Generates, for every discovered submodule:
         * a derivation agent  -> .nb/agentic/custom/agents/agent_<module_id>.yaml
         * a governing rule    -> .nb/context/rules/<module_id>_rules.md
    4. Generates a sequential derivation workflow that runs the root plan and then
       each submodule in dependency order, sealing a Merkle block at the end:
         * .nb/agentic/workflows/wf_<plan_id>_derivation.yaml
    5. Reconciles the settings.json registries via AgentRegistrySynchronizer so the
       new agents and rules become first-class platform citizens.
    6. Optionally bundles the freshly generated artifacts into the appropriate
       commercial release package (IntelliJ plugin / VSCode / SaaS) through the
       CommercialPackagerProvisioner.

Every write is idempotent: unchanged artifacts are left byte-identical, so the
orchestrator can run on every gatekeeper pass without churn.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is a hard platform dependency
    yaml = None


class _LiteralStr(str):
    """Marker type so multi-line strings are emitted as YAML literal blocks."""


def _dump_yaml(data: Dict[str, Any]) -> str:
    """Serializes a mapping to YAML preserving key order and literal blocks."""

    class _Dumper(yaml.SafeDumper):
        pass

    def _literal(dumper, value):
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|")

    _Dumper.add_representer(_LiteralStr, _literal)
    return yaml.dump(
        data,
        Dumper=_Dumper,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=100,
    )


class PlanModuleOrchestrator:
    """Generates per-submodule agents, rules, and a derivation workflow for a plan."""

    AGENTS_DIR = ".nb/agentic/custom/agents"
    RULES_DIR = ".nb/context/rules"
    WORKFLOWS_DIR = ".nb/agentic/workflows"

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
    # Discovery
    # ------------------------------------------------------------------
    def _read_manifest(self, plan_dir: Path) -> Dict[str, Any]:
        manifest_path = plan_dir / "MANIFEST.yaml"
        if manifest_path.exists() and yaml is not None:
            try:
                data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return {}

    @staticmethod
    def _title_from_text(text: str, fallback: str) -> str:
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                title = re.sub(r"^Module\s+\d+\s*:\s*", "", title, flags=re.IGNORECASE)
                return title or fallback
        return fallback

    @staticmethod
    def _slug_from_stem(stem: str) -> str:
        slug = re.sub(r"^\d+[_\-.\s]*", "", stem).strip()
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", slug).strip("_").lower()
        return slug or "module"

    def discover_modules(self, plan_dir: Path) -> List[Dict[str, Any]]:
        """
        Returns the ordered list of submodules actually present on disk.

        The manifest ``modules:`` list is authoritative for id/title/file, but a
        submodule only materializes when its source file exists (so a plan may
        declare future submodules without breaking derivation). Any extra
        markdown file found under ``modules/`` (recursively) that the manifest
        does not declare is also picked up, so newly authored submodules are
        processed without editing the manifest.
        """
        manifest = self._read_manifest(plan_dir)
        modules: List[Dict[str, Any]] = []
        seen: set = set()

        declared = manifest.get("modules", [])
        if isinstance(declared, list):
            for entry in declared:
                if not isinstance(entry, dict):
                    continue
                rel_file = str(entry.get("file") or entry.get("path") or "").strip()
                if not rel_file:
                    continue
                src = plan_dir / rel_file
                if not src.exists():
                    continue
                module_id = str(entry.get("id") or "").strip()
                if not module_id:
                    module_id = self._slug_from_stem(Path(rel_file).stem)
                title = str(entry.get("title") or "").strip()
                if not title:
                    title = self._title_from_text(src.read_text(encoding="utf-8"), module_id)
                record = self._module_record(plan_dir, module_id, rel_file, title, src)
                modules.append(record)
                seen.add(module_id)

        modules_dir = plan_dir / "modules"
        if modules_dir.exists():
            for src in sorted(modules_dir.rglob("*.md")):
                if src.name.lower() == "readme.md":
                    continue
                rel_file = src.relative_to(plan_dir).as_posix()
                if rel_file in {m["file"] for m in modules}:
                    continue
                module_id = self._slug_from_stem(src.stem)
                base = module_id
                i = 2
                while module_id in seen:
                    module_id = f"{base}_{i}"
                    i += 1
                title = self._title_from_text(src.read_text(encoding="utf-8"), module_id)
                modules.append(self._module_record(plan_dir, module_id, rel_file, title, src))
                seen.add(module_id)

        return modules

    def _module_record(
        self, plan_dir: Path, module_id: str, rel_file: str, title: str, src: Path
    ) -> Dict[str, Any]:
        return {
            "id": module_id,
            "file": rel_file,
            "title": title or module_id,
            "source_path": src,
            "present": src.exists(),
            "agent_id": f"agent_{module_id}",
            "step_id": f"step_{module_id}",
            "rule_rel": f"{self.RULES_DIR}/{module_id}_rules.md",
        }

    def declared_but_missing(self, plan_dir: Path) -> List[Dict[str, str]]:
        """Returns manifest-declared modules whose source file is not yet authored."""
        plan_dir = Path(plan_dir).resolve()
        manifest = self._read_manifest(plan_dir)
        missing: List[Dict[str, str]] = []
        declared = manifest.get("modules", [])
        if isinstance(declared, list):
            for entry in declared:
                if not isinstance(entry, dict):
                    continue
                rel_file = str(entry.get("file") or entry.get("path") or "").strip()
                if rel_file and not (plan_dir / rel_file).exists():
                    module_id = str(entry.get("id") or "").strip() or self._slug_from_stem(
                        Path(rel_file).stem
                    )
                    missing.append({"id": module_id, "file": rel_file})
        return missing

    def discover_plan(self, plan_dir: Path) -> Optional[Dict[str, Any]]:
        plan_dir = Path(plan_dir).resolve()
        if not plan_dir.exists() or not plan_dir.is_dir():
            return None
        manifest = self._read_manifest(plan_dir)
        slug = plan_dir.name
        plan_id = str(manifest.get("plan_id") or f"plan_{slug}").strip()
        plan_name = str(manifest.get("plan_name") or slug.replace("-", " ").title()).strip()
        try:
            plan_rel = plan_dir.relative_to(self.workspace_root).as_posix()
        except ValueError:
            plan_rel = plan_dir.as_posix()
        return {
            "plan_id": plan_id,
            "plan_name": plan_name,
            "slug": slug,
            "dir": plan_dir,
            "rel": plan_rel,
            "manifest": manifest,
            "concise": "concise.md" if (plan_dir / "concise.md").exists() else None,
            "detailed": "detailed.md" if (plan_dir / "detailed.md").exists() else None,
            "agent_id": f"agent_{plan_id}",
            "workflow_id": f"wf_{plan_id}_derivation",
            "workflow_file": f"{self.WORKFLOWS_DIR}/wf_{plan_id}_derivation.yaml",
        }

    # ------------------------------------------------------------------
    # Content generation
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_mission(text: str) -> str:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if re.match(r"^##\s*1\.\s+(Architectural Mission|Mission|Overview)", line, re.IGNORECASE):
                para: List[str] = []
                for nxt in lines[i + 1:]:
                    if nxt.strip() == "":
                        if para:
                            break
                        continue
                    if nxt.startswith("#"):
                        break
                    para.append(nxt.strip())
                if para:
                    return " ".join(para)
        for line in lines:
            s = line.strip()
            if s and not s.startswith(("#", "-", "*", "|", "```", "**", ">")):
                return s
        return ""

    @staticmethod
    def _extract_invariants(text: str, limit: int = 16) -> List[str]:
        bullets: List[str] = []
        for line in text.splitlines():
            m = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.+)$", line)
            if not m:
                continue
            item = m.group(1).strip()
            if not item or item.startswith("`") and item.endswith("`") and len(item) < 4:
                continue
            if "mermaid" in item.lower() or item.startswith("graph "):
                continue
            item = re.sub(r"\s+", " ", item)
            if item not in bullets:
                bullets.append(item)
            if len(bullets) >= limit:
                break
        return bullets

    @staticmethod
    def _extract_headings(text: str, limit: int = 12) -> List[str]:
        headings: List[str] = []
        for line in text.splitlines():
            m = re.match(r"^(#{2,3})\s+(.+)$", line)
            if m:
                headings.append(m.group(2).strip())
            if len(headings) >= limit:
                break
        return headings

    def _rule_content(self, plan: Dict[str, Any], module: Dict[str, Any]) -> str:
        text = ""
        if module["present"]:
            text = module["source_path"].read_text(encoding="utf-8")
        mission = self._extract_mission(text) or (
            f"Derive the {module['title']} submodule of {plan['plan_name']} per its "
            "governing specification."
        )
        invariants = self._extract_invariants(text)
        if not invariants:
            invariants = [
                f"Implement {module['title']} exactly to the governing module specification.",
                f"Source of truth: {plan['rel']}/{module['file']}",
                "Operate under sandboxed worktree isolation with zero cross-module leakage.",
                "Seal a Merkle block upon successful derivation.",
            ]
        headings = self._extract_headings(text)
        section_map = "\n".join(f"- {h}" for h in headings) or "- (no sections declared)"

        return (
            f"# {module['title']} - Module Derivation & Invariant Rules\n\n"
            f"**Rule ID**: `{module['id']}_rules`  \n"
            f"**Governing Plan**: `{plan['rel']}`  \n"
            f"**Source Module**: `{module['file']}`  \n"
            f"**Classification**: Plan Module Invariants (Strict Enforcement)  \n"
            f"**Auto-Generated By**: `agent_plan_module_orchestrator`\n\n"
            f"> This rule governs the autonomous derivation of the `{module['id']}` "
            f"submodule of the `{plan['plan_id']}` master plan. It is projected into "
            f"`settings.json` under `context_rules`.\n\n"
            f"---\n\n"
            f"## 1. Architectural Mission\n"
            f"{mission}\n\n"
            f"## 2. Invariant Checklist\n"
            + "".join(f"- {item}\n" for item in invariants)
            + f"\n## 3. Section Map\n{section_map}\n\n"
            f"## 4. Enforcement\n"
            f"- Tier: Plan Module Invariant\n"
            f"- Enforcement Point: `{plan['workflow_file']}#{module['step_id']}`\n"
            f"- Fail Action: `AUTO_HEAL_OR_ROLLBACK`\n"
            f"- Verification: `venv/bin/python -m pytest workplace/tests/` and `percipience gate`\n"
        )

    def _agent_manifest(self, plan: Dict[str, Any], module: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "agent_id": module["agent_id"],
            "name": module["title"],
            "version": "1.0.0",
            "category": "plan_module_derivation",
            "model": "claude-3-5-sonnet",
            "model_tier": "tier_b",
            "temperature": 0.1,
            "role": f"{module['title']} Derivation Specialist",
            "description": _LiteralStr(
                f"Autonomous derivation specialist for plan module {module['id']} of the "
                f"{plan['plan_id']} master plan. Implements, verifies, and seals "
                f"{module['title']} under sandboxed worktree isolation.\n"
            ),
            "source_plan": plan["rel"],
            "source_module": module["file"],
            "governing_rules": [module["rule_rel"]],
            "sandboxed_worktree": f".nb/workspaces/wt_{module['id']}",
            "module_scope": {
                "allowed_modules": ["workplace/"],
                "denied_paths": [".git", ".nb/context/invariants"],
            },
            "tools_and_capabilities": [
                {
                    "name": "derive_module",
                    "description": "Executes the bounded derivation of the module under worktree isolation",
                    "handler": "workplace/core/container_plan_executor.py",
                },
                {
                    "name": "enforce_module_invariants",
                    "description": "Validates layered context and module invariants",
                    "handler": "workplace/core/layered_context_validator.py",
                },
            ],
            "workflow_bindings": [
                {
                    "workflow_id": plan["workflow_id"],
                    "stage": module["step_id"],
                    "fail_action": "AUTO_HEAL_OR_ROLLBACK",
                }
            ],
            "autonomous_cicd_hooks": {
                "auto_trigger_in_cicd": True,
                "target_workflows": [
                    {
                        "workflow_id": plan["workflow_id"],
                        "step_id": module["step_id"],
                        "step_name": f"Derive module {module['id']}",
                        "fail_action": "AUTO_HEAL_OR_ROLLBACK",
                    }
                ],
            },
            "system_prompt": _LiteralStr(
                f"You are the {module['title']} derivation specialist for the "
                f"{plan['plan_id']} master plan.\n"
                f"Derive the {module['id']} submodule exactly to its governing "
                f"specification in {plan['rel']}/{module['file']}, honoring "
                f"{module['rule_rel']}.\n"
                f"Operate inside the sandboxed worktree, never touch denied paths, and "
                f"seal a Merkle block on success.\n"
            ),
        }

    def _root_agent_manifest(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        docs = [d for d in (plan["concise"], plan["detailed"]) if d]
        manifest = plan.get("manifest", {})
        manifest_data = manifest.get("plan") if isinstance(manifest.get("plan"), dict) else manifest
        version = str(manifest.get("version") or manifest_data.get("version") or "1.0.0")
        agent_manifest = {
            "agent_id": plan["agent_id"],
            "name": f"{plan['plan_name']} - Root Plan Orchestrator",
            "version": version,
            "category": "plan_derivation",
            "model": "claude-3-5-sonnet",
            "model_tier": "tier_a",
            "temperature": 0.1,
            "role": f"{plan['plan_name']} Root Derivation Orchestrator",
            "description": _LiteralStr(
                f"Root derivation orchestrator for the {plan['plan_id']} master plan. "
                f"Executes the concise/detailed root specification and coordinates the "
                f"sequential derivation of every discovered submodule.\n"
            ),
            "source_plan": plan["rel"],
            "source_documents": docs,
            "workflow_bindings": [
                {
                    "workflow_id": plan["workflow_id"],
                    "stage": "step_plan_root",
                    "fail_action": "AUTO_HEAL_OR_ROLLBACK",
                }
            ],
            "module_scope": {
                "allowed_modules": ["workplace/"],
                "denied_paths": [".git", ".nb/context/invariants"],
            },
            "system_prompt": _LiteralStr(
                f"You are the root derivation orchestrator for the {plan['plan_id']} "
                f"master plan ({plan['plan_name']}).\n"
                f"Execute the root specification in {plan['rel']} and coordinate the "
                f"sequential derivation of each discovered submodule.\n"
            ),
        }
        if "autonomous_execution" in manifest:
            agent_manifest["autonomous_execution"] = manifest["autonomous_execution"]
        if "lifecycle_hooks" in manifest:
            agent_manifest["lifecycle_hooks"] = manifest["lifecycle_hooks"]
        if "specification_contracts" in manifest:
            agent_manifest["specification_contracts"] = manifest["specification_contracts"]
        return agent_manifest

    def _workflow_doc(self, plan: Dict[str, Any], modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        manifest = plan.get("manifest", {})
        steps: List[Dict[str, Any]] = [
            {
                "id": "step_plan_root",
                "name": f"Derive {plan['plan_id']} root artifacts (concise.md + detailed.md)",
                "executor": plan["agent_id"],
                "tier": "Tier_A",
                "fail_action": "AUTO_HEAL_OR_ROLLBACK",
            }
        ]
        previous = "step_plan_root"
        for module in modules:
            steps.append(
                {
                    "id": module["step_id"],
                    "name": f"Derive module {module['id']} ({module['title']})",
                    "executor": module["agent_id"],
                    "tier": "Tier_B",
                    "depends_on": [previous],
                    "source_module": module["file"],
                    "governing_rules": module["rule_rel"],
                    "fail_action": "AUTO_HEAL_OR_ROLLBACK",
                }
            )
            previous = module["step_id"]
        steps.append(
            {
                "id": "step_module_merkle_seal",
                "name": "Merkle State Ledger Sealing (plan module derivation)",
                "executor": "platform.merkle_ledger",
                "tier": "Tier_A",
                "depends_on": [previous],
                "action": "SEAL_BLOCK",
            }
        )
        wf_doc = {
            "workflow_id": plan["workflow_id"],
            "description": _LiteralStr(
                f"Autonomous sequential derivation workflow for the {plan['plan_id']} "
                f"master plan ({plan['plan_name']}). Executes the root plan and then "
                f"derives each discovered submodule ({len(modules)}) in dependency order. "
                f"Auto-generated by agent_plan_module_orchestrator; idempotent and safe to "
                f"regenerate.\n"
            ),
            "source_plan": plan["rel"],
            "generated_by": "agent_plan_module_orchestrator",
            "steps": steps,
        }
        if "autonomous_execution" in manifest:
            wf_doc["autonomous_execution"] = manifest["autonomous_execution"]
        if "lifecycle_hooks" in manifest:
            wf_doc["lifecycle_hooks"] = manifest["lifecycle_hooks"]
        if "specification_contracts" in manifest:
            wf_doc["specification_contracts"] = manifest["specification_contracts"]
        return wf_doc

    # ------------------------------------------------------------------
    # Filesystem writes
    # ------------------------------------------------------------------
    def _write_if_changed(self, path: Path, content: str) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                return "unchanged"
            path.write_text(content, encoding="utf-8")
            return "updated"
        path.write_text(content, encoding="utf-8")
        return "created"

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def synchronize_dependencies(self, target: str, **kwargs) -> List[Dict[str, Any]]:
        """Synchronize a target and its manifest prerequisites in dependency order."""
        plan_root = self.workspace_root / ".nb/plan"
        aliases: Dict[str, List[Path]] = {}
        manifests: Dict[Path, Dict[str, Any]] = {}

        def normalize(value: str) -> str:
            value = value.strip().replace("\\", "/")
            if ".nb/plan/" in value:
                value = value.split(".nb/plan/", 1)[1]
            value = value.removeprefix("./").strip("/")
            for suffix in ("/MANIFEST.yaml", "/concise.md", "/detailed.md"):
                if value.endswith(suffix):
                    value = value[:-len(suffix)]
                    break
            return value.lower().replace("-", "_").replace("/", "_")

        for path in sorted(plan_root.rglob("MANIFEST.yaml")):
            relative = path.parent.relative_to(plan_root)
            if relative.parts and relative.parts[0] in ("archive", "templates"):
                continue
            manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError(f"Invalid plan manifest: {path}")
            metadata = manifest.get("plan") if isinstance(manifest.get("plan"), dict) else manifest
            identity = metadata.get("id") or manifest.get("plan_id") or relative.as_posix()
            if not isinstance(identity, str) or not identity.strip():
                raise ValueError(f"Invalid plan identity: {path}")
            manifests[path] = manifest
            for alias in {normalize(identity), normalize(relative.as_posix())}:
                aliases.setdefault(alias, []).append(path)

        def resolve(reference: str) -> Path:
            matches = aliases.get(normalize(reference), [])
            if len(matches) != 1:
                raise ValueError(f"{'Ambiguous' if matches else 'Unknown'} plan dependency: {reference}")
            return matches[0]

        ordered: List[Path] = []
        visiting: List[Path] = []
        visited = set()

        def visit(path: Path) -> None:
            if path in visiting:
                raise ValueError(f"Plan dependency cycle: {' -> '.join(str(p.parent.name) for p in visiting + [path])}")
            if path in visited:
                return
            visiting.append(path)
            manifest = manifests[path]
            metadata = manifest.get("plan") if isinstance(manifest.get("plan"), dict) else manifest
            dependencies = manifest.get("dependencies", metadata.get("dependencies", []))
            if isinstance(dependencies, dict):
                dependencies = dependencies.get("requires", [])
            if isinstance(dependencies, str):
                dependencies = [dependencies]
            if not isinstance(dependencies, list) or any(not isinstance(d, str) or not d.strip() for d in dependencies):
                raise ValueError(f"Invalid plan dependencies: {path}")
            for dependency in dependencies:
                visit(resolve(dependency))
            visiting.pop()
            visited.add(path)
            ordered.append(path)

        visit(resolve(target))
        return [self.synchronize(path.parent, **kwargs) for path in ordered]

    def synchronize(
        self,
        plan_dir: Path,
        apply: bool = True,
        sync_registries: bool = True,
        bundle_tier: Optional[str] = None,
        bundle_target: str = "intellij",
        provision: bool = False,
        tenant_id: str = "tenant_community_default",
    ) -> Dict[str, Any]:
        plan = self.discover_plan(plan_dir)
        if not plan:
            return {"status": "NO_PLAN", "plan_dir": str(plan_dir)}

        modules = self.discover_modules(plan["dir"])
        missing = self.declared_but_missing(plan["dir"])
        report: Dict[str, Any] = {
            "status": "SYNCHRONIZED" if apply else "CHECKED",
            "plan_id": plan["plan_id"],
            "plan_dir": plan["rel"],
            "modules_discovered": len(modules),
            "modules": [
                {"id": m["id"], "file": m["file"], "present": m["present"]} for m in modules
            ],
            "modules_skipped_missing": missing,
            "artifacts": {"agents": [], "rules": [], "workflows": []},
        }

        agent_specs: List[Tuple[str, Dict[str, Any]]] = [
            ("agents", self._root_agent_manifest(plan)),
        ]
        for module in modules:
            agent_specs.append(("agents", self._agent_manifest(plan, module)))

        rule_specs: List[Tuple[str, str]] = [
            (f"{self.RULES_DIR}/{m['id']}_rules.md", self._rule_content(plan, m))
            for m in modules
        ]
        workflow_specs: List[Tuple[str, str]] = [
            (plan["workflow_file"], _dump_yaml(self._workflow_doc(plan, modules))),
        ]

        for category, manifest in agent_specs:
            rel = f"{self.AGENTS_DIR}/{manifest['agent_id']}.yaml"
            content = _dump_yaml(manifest)
            if apply:
                state = self._write_if_changed(self.workspace_root / rel, content)
            else:
                state = "unchanged" if (self.workspace_root / rel).exists() else "created"
            report["artifacts"][category].append({"path": rel, "state": state})

        for rel, content in rule_specs:
            if apply:
                state = self._write_if_changed(self.workspace_root / rel, content)
            else:
                state = "unchanged" if (self.workspace_root / rel).exists() else "created"
            report["artifacts"]["rules"].append({"path": rel, "state": state})

        for rel, content in workflow_specs:
            if apply:
                state = self._write_if_changed(self.workspace_root / rel, content)
            else:
                state = "unchanged" if (self.workspace_root / rel).exists() else "created"
            report["artifacts"]["workflows"].append({"path": rel, "state": state})

        if apply and sync_registries:
            try:
                from core.agent_registry_synchronizer import AgentRegistrySynchronizer

                report["registries"] = AgentRegistrySynchronizer(self.workspace_root).sync()
            except Exception as exc:  # pragma: no cover - registry sync is best effort
                report["registries"] = {"status": "SKIPPED", "error": str(exc)}

        if apply and bundle_tier:
            report["bundle"] = self.bundle(
                tier=bundle_tier,
                target=bundle_target,
                provision=provision,
                tenant_id=tenant_id,
            )

        return report

    def bundle(
        self,
        tier: str = "plan_business",
        target: str = "intellij",
        provision: bool = False,
        tenant_id: str = "tenant_community_default",
    ) -> Dict[str, Any]:
        """
        Bundles generated artifacts into the commercial release package.

        ``provision=False`` performs a lightweight tier packaging into
        ``.nb/bundles/package_<tier>``. ``provision=True`` additionally resolves the
        artifacts onto a concrete target (IntelliJ/PyCharm plugin, VSCode, or SaaS).
        """
        try:
            from core.commercial_packager_provisioner import CommercialPackagerProvisioner
        except Exception as exc:  # pragma: no cover
            return {"status": "UNAVAILABLE", "error": str(exc)}

        if provision:
            return CommercialPackagerProvisioner.provision_target(
                workspace_root=self.workspace_root,
                tenant_id=tenant_id,
                tier=tier,
                target=target,
            )
        return CommercialPackagerProvisioner.package_tier(
            workspace_root=self.workspace_root,
            tier=tier,
            tenant_id=tenant_id,
        )

    # ------------------------------------------------------------------
    # CLI
    # ------------------------------------------------------------------
    @classmethod
    def cli(cls, argv: Optional[List[str]] = None) -> int:
        parser = argparse.ArgumentParser(
            prog="plan_module_orchestrator",
            description="Generate per-submodule agents, rules, and a derivation workflow for a plan.",
        )
        parser.add_argument("--plan", required=True, help="Path to the plan directory")
        parser.add_argument("--check", action="store_true", help="Report drift without writing")
        parser.add_argument("--no-sync-registries", action="store_true", help="Skip settings.json reconciliation")
        parser.add_argument("--bundle-tier", default=None, help="Tier to package after generation (e.g. plan_business)")
        parser.add_argument("--bundle-target", default="intellij", help="Provisioning target when --provision is set")
        parser.add_argument("--provision", action="store_true", help="Provision artifacts onto a concrete target")
        parser.add_argument("--tenant-id", default="tenant_community_default")
        args = parser.parse_args(argv)

        result = cls().synchronize(
            plan_dir=Path(args.plan),
            apply=not args.check,
            sync_registries=not args.no_sync_registries,
            bundle_tier=args.bundle_tier,
            bundle_target=args.bundle_target,
            provision=args.provision,
            tenant_id=args.tenant_id,
        )
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") in ("SYNCHRONIZED", "CHECKED") else 1


if __name__ == "__main__":
    raise SystemExit(PlanModuleOrchestrator.cli())
