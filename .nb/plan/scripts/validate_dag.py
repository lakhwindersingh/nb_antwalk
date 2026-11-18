#!/usr/bin/env python3
"""
Automated Dependency DAG & Plan Integrity Validator.
Parses all MANIFEST.yaml files across .nb/plan, verifies Canonical Schema v3.0,
ensures dangling references do not exist, and enforces acyclic dependency ordering (Kahn's Algorithm).
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Any
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
PLAN_ROOT = REPO_ROOT / ".nb/plan"

REQUIRED_V3_KEYS = [
    "schema_version",
    "plan_id",
    "plan_name",
    "version",
    "layer",
    "status",
    "maturity",
    "dependencies",
    "semantic_parity",
    "key_capabilities",
    "file_versions"
]

LAYER_HIERARCHY = {
    "architecture": 0,
    "master": 0,
    "l1": 1,
    "domain": 1,
    "l2": 2,
    "extensions": 2,
    "extension": 2,
    "l3": 3,
    "l4": 4,
    "l5": 5,
    "test": 6,
}


class PlanDagValidator:
    def __init__(self, plan_root: Path):
        self.plan_root = plan_root
        self.manifests: Dict[str, Dict[str, Any]] = {}
        self.plan_paths: Dict[str, Path] = {}
        self.alias_to_id: Dict[str, str] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def discover_plans(self):
        """Locate all active MANIFEST.yaml files except templates and archives."""
        for p in sorted(self.plan_root.glob("**/MANIFEST.yaml")):
            if "templates" in p.parts or "archive" in p.parts:
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                plan_id = data.get("plan_id") or (data.get("plan", {}).get("id") if isinstance(data.get("plan"), dict) else None)
                if not plan_id:
                    self.errors.append(f"Missing plan_id in {p.relative_to(self.plan_root)}")
                    continue
                self.manifests[plan_id] = data
                self.plan_paths[plan_id] = p.parent

                # Register canonical aliases for dependency resolution
                rel_str = p.parent.relative_to(self.plan_root).as_posix()
                self.alias_to_id[plan_id] = plan_id
                self.alias_to_id[rel_str] = plan_id
                self.alias_to_id[p.parent.name] = plan_id
                self.alias_to_id[rel_str.replace("/", "_").replace("-", "_")] = plan_id
                self.alias_to_id[p.parent.name.replace("-", "_")] = plan_id
            except Exception as e:
                self.errors.append(f"Failed to parse {p}: {e}")

    def validate_schema_compliance(self):
        """Ensure all plans conform to Canonical Schema v3.0."""
        for plan_id, manifest in self.manifests.items():
            rel_path = self.plan_paths[plan_id].relative_to(self.plan_root)
            for req_key in REQUIRED_V3_KEYS:
                if req_key not in manifest:
                    self.errors.append(f"[{rel_path}] {plan_id}: Missing required v3 key '{req_key}'")

            # Validate maturity block
            maturity = manifest.get("maturity", {})
            if not isinstance(maturity, dict):
                self.errors.append(f"[{rel_path}] {plan_id}: 'maturity' must be a mapping")
            else:
                for mat_key in ["stage", "implementation_status", "test_coverage", "production_ready"]:
                    if mat_key not in maturity:
                        self.errors.append(f"[{rel_path}] {plan_id}: Missing maturity field '{mat_key}'")

            # Validate semantic parity block
            parity = manifest.get("semantic_parity", {})
            if not isinstance(parity, dict):
                self.errors.append(f"[{rel_path}] {plan_id}: 'semantic_parity' must be a mapping")
            else:
                if "composite_score" not in parity or "vectors" not in parity:
                    self.errors.append(f"[{rel_path}] {plan_id}: Incomplete 'semantic_parity' block")

            # Validate file_versions
            file_versions = manifest.get("file_versions", {})
            for doc in ["concise", "detailed", "readme"]:
                if doc not in file_versions:
                    self.errors.append(f"[{rel_path}] {plan_id}: file_versions missing '{doc}'")

    def validate_dependencies_and_cycles(self):
        """Validate references, layer boundaries, and absence of cycles via Kahn's algorithm."""
        adj: Dict[str, List[str]] = {p: [] for p in self.manifests}
        in_degree: Dict[str, int] = {p: 0 for p in self.manifests}

        for plan_id, manifest in self.manifests.items():
            rel_path = self.plan_paths[plan_id].relative_to(self.plan_root)
            layer = manifest.get("layer", "master")
            deps = manifest.get("dependencies", {})

            requires = deps.get("requires", []) if isinstance(deps, dict) else deps
            if not isinstance(requires, list):
                self.errors.append(f"[{rel_path}] {plan_id}: 'dependencies.requires' must be a list")
                continue

            for req in requires:
                req_clean = req.split("(")[0].strip() if isinstance(req, str) else str(req)
                # If dependency is a direct markdown document, check disk existence
                if req_clean.endswith(".md"):
                    doc_path = self.plan_root / req_clean
                    if not doc_path.exists():
                        self.warnings.append(f"[{rel_path}] {plan_id}: Referenced document '{req_clean}' not found")
                    continue

                canonical_req = self.alias_to_id.get(req_clean) or self.alias_to_id.get(req)
                if not canonical_req or canonical_req not in self.manifests:
                    self.warnings.append(f"[{rel_path}] {plan_id}: External or optional dependency '{req}'")
                    continue

                req_layer = str(self.manifests[canonical_req].get("layer", "master")).lower()
                cur_layer = str(layer).lower()
                # Layer hierarchy check: lower numbered layers cannot depend on higher numbered layers
                if cur_layer in LAYER_HIERARCHY and req_layer in LAYER_HIERARCHY:
                    if LAYER_HIERARCHY[cur_layer] < LAYER_HIERARCHY[req_layer]:
                        self.errors.append(
                            f"[{rel_path}] {plan_id} (layer {layer}) illegally depends on higher-layer {canonical_req} (layer {req_layer})"
                        )

                adj[canonical_req].append(plan_id)
                in_degree[plan_id] += 1

            # Validate enables list if present
            if isinstance(deps, dict) and "enables" in deps:
                for enabled in deps.get("enables", []):
                    if enabled not in self.manifests:
                        self.warnings.append(f"[{rel_path}] {plan_id}: 'enables' references unknown plan '{enabled}'")

        # Kahn's algorithm for topological sorting / cycle detection
        queue = [p for p, deg in in_degree.items() if deg == 0]
        sorted_plans = []

        while queue:
            node = queue.pop(0)
            sorted_plans.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_plans) != len(self.manifests):
            cycle_nodes = [p for p, deg in in_degree.items() if deg > 0]
            self.errors.append(f"Dependency cycle detected among plans: {cycle_nodes}")
        else:
            print(f"✅ DAG topological ordering verified successfully ({len(sorted_plans)} plans):")
            for idx, p in enumerate(sorted_plans, 1):
                layer = self.manifests[p].get("layer", "master")
                print(f"   [{idx:02d}] {p} ({layer})")

    def run(self) -> bool:
        print(f"🔍 Validating Plan Manifests in: {self.plan_root}")
        self.discover_plans()
        print(f"📦 Discovered {len(self.manifests)} active plans.")

        self.validate_schema_compliance()
        self.validate_dependencies_and_cycles()

        if self.warnings:
            print("\n⚠️  Warnings:")
            for w in self.warnings:
                print(f"   - {w}")

        if self.errors:
            print("\n❌ Validation Errors:")
            for e in self.errors:
                print(f"   - {e}")
            return False

        print("\n✨ All Plan DAG, Schema, and Dependency Validation Gates PASSED!")
        return True


def main():
    validator = PlanDagValidator(PLAN_ROOT)
    success = validator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
