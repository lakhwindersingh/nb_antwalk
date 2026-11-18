"""Resolve plan manifests into a validated, target-specific dependency order."""

from pathlib import Path
from typing import Any, Dict, List

import yaml


class PlanDependencyResolver:
    """Indexes plan manifests and resolves aliases to a transitive DAG closure."""

    def __init__(self, plan_root: Path):
        self.plan_root = Path(plan_root).resolve()
        if not self.plan_root.is_dir():
            raise FileNotFoundError(f"Plan directory not found: {self.plan_root}")
        self.workspace_root = self.plan_root.parent.parent
        self._plans: Dict[str, Dict[str, Any]] = {}
        self._aliases: Dict[str, str] = {}
        self._ambiguous_aliases = set()
        self._load_manifests()

    @staticmethod
    def _normalize(value: str) -> str:
        value = value.strip().replace("\\", "/")
        if ".nb/plan/" in value:
            value = value.split(".nb/plan/", 1)[1]
        value = value.removeprefix("./").strip("/")
        for suffix in ("/MANIFEST.yaml", "/manifest.yaml", "/concise.md", "/detailed.md", ".md"):
            if value.endswith(suffix):
                value = value[:-len(suffix)]
                break
        return value.lower().replace("-", "_").replace("/", "_")

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @classmethod
    def _spec_files(cls, manifest: Dict[str, Any], manifest_path: Path) -> List[Path]:
        files = []
        for section_name in ("versions", "file_versions"):
            versions = cls._as_dict(manifest.get(section_name))
            for version in versions.values():
                entry = cls._as_dict(version)
                if entry.get("exists") is False:
                    continue
                relative = entry.get("file") or entry.get("path")
                if isinstance(relative, str) and relative:
                    files.append((manifest_path.parent / relative).resolve())
        if not files:
            files = [
                (manifest_path.parent / filename).resolve()
                for filename in ("concise.md", "detailed.md", "README.md")
                if (manifest_path.parent / filename).is_file()
            ]
        return sorted(set(files))

    def _add_alias(self, alias: str, plan_id: str) -> None:
        if not isinstance(alias, str):
            return
        normalized = self._normalize(alias)
        if not normalized:
            return
        existing = self._aliases.get(normalized)
        if existing and existing != plan_id:
            self._ambiguous_aliases.add(normalized)
        else:
            self._aliases[normalized] = plan_id

    def _load_manifests(self) -> None:
        manifests = sorted(self.plan_root.glob("**/MANIFEST.yaml"))
        if not manifests:
            raise ValueError(f"No plan manifests found under {self.plan_root}")

        for manifest_path in manifests:
            try:
                document = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError) as exc:
                raise ValueError(f"Could not load plan manifest {manifest_path}: {exc}") from exc
            if not isinstance(document, dict) or not document:
                raise ValueError(f"Invalid plan manifest: {manifest_path}")
            manifest = document
            plan_metadata = self._as_dict(manifest.get("plan")) or manifest
            relative_dir = manifest_path.parent.relative_to(self.plan_root).as_posix()
            inferred_id = relative_dir.replace("/", "_").replace("-", "_")
            plan_id = plan_metadata.get("id") or manifest.get("plan_id") or inferred_id
            if not isinstance(plan_id, str) or not plan_id.strip():
                raise ValueError(f"Plan manifest has no usable identity: {manifest_path}")
            plan_id = plan_id.strip()
            if plan_id in self._plans:
                raise ValueError(f"Duplicate canonical plan ID {plan_id!r}")

            dependency_metadata = manifest.get("dependencies", plan_metadata.get("dependencies", {}))
            if isinstance(dependency_metadata, list):
                requires = dependency_metadata
            elif isinstance(dependency_metadata, dict):
                requires = dependency_metadata.get("requires", [])
            else:
                raise ValueError(f"Invalid dependencies in {manifest_path}: expected a mapping or list")
            if isinstance(requires, str):
                requires = [requires]
            if (
                not isinstance(requires, list)
                or any(not isinstance(item, str) or not item.strip() for item in requires)
            ):
                raise ValueError(f"Invalid dependencies.requires in {manifest_path}")

            parent = manifest.get("parent_plan", plan_metadata.get("parent_plan"))
            self._plans[plan_id] = {
                "plan_id": plan_id,
                "name": plan_metadata.get("name", plan_id),
                "manifest_path": manifest_path,
                "relative_path": relative_dir,
                "spec_files": self._spec_files(manifest, manifest_path),
                "requires": [item.strip() for item in requires],
                "parent_plan": str(parent) if parent else None,
                "dependency_ids": [],
            }
            self._add_alias(plan_id, plan_id)
            self._add_alias(relative_dir, plan_id)
            self._add_alias(relative_dir.replace("/", "_"), plan_id)
            self._add_alias(f"{relative_dir}/MANIFEST.yaml", plan_id)
            self._add_alias(manifest.get("plan_id", ""), plan_id)

        if self._ambiguous_aliases:
            aliases = ", ".join(sorted(self._ambiguous_aliases))
            raise ValueError(f"Ambiguous plan aliases: {aliases}")

    def _resolve_dependencies(self, plan: Dict[str, Any]) -> List[str]:
        resolved = []
        for reference in plan["requires"]:
            dependency_id = self._resolve_id(reference)
            if dependency_id not in resolved:
                resolved.append(dependency_id)
        if plan["parent_plan"]:
            try:
                parent_id = self._resolve_id(plan["parent_plan"])
            except ValueError:
                parent_document = self._parent_document_path(plan["parent_plan"])
                if not parent_document.is_relative_to(self.plan_root) or not parent_document.is_file():
                    raise
            else:
                if parent_id not in resolved:
                    resolved.append(parent_id)
        return resolved

    def _parent_document_path(self, reference: str) -> Path:
        normalized = reference.replace("\\", "/")
        if ".nb/plan/" in normalized:
            normalized = normalized.split(".nb/plan/", 1)[1]
        normalized = normalized.removeprefix("./").strip("/")
        path = Path(normalized)
        if path.is_absolute():
            return path
        return (self.plan_root / path).resolve()

    def _resolve_id(self, target: str) -> str:
        normalized = self._normalize(target)
        if normalized in self._ambiguous_aliases:
            raise ValueError(f"Ambiguous plan dependency: {target}")
        plan_id = self._aliases.get(normalized)
        if not plan_id:
            raise ValueError(f"Unknown plan dependency: {target}")
        return plan_id

    def resolve(self, target_plan: str) -> List[Dict[str, Any]]:
        """Return the transitive dependency closure in prerequisite-first order."""
        target_id = self._resolve_id(target_plan)
        ordered: List[Dict[str, Any]] = []
        visiting = []
        visited = set()

        def visit(plan_id: str) -> None:
            if plan_id in visiting:
                cycle = visiting[visiting.index(plan_id):] + [plan_id]
                raise ValueError(f"Dependency cycle: {' -> '.join(cycle)}")
            if plan_id in visited:
                return
            visiting.append(plan_id)
            plan = self._plans[plan_id]
            plan["dependency_ids"] = self._resolve_dependencies(plan)
            for dependency_id in plan["dependency_ids"]:
                visit(dependency_id)
            visiting.pop()
            visited.add(plan_id)
            ordered.append(dict(plan))

        visit(target_id)
        return ordered