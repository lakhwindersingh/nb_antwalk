"""
Percipience Wire Contract Compatibility & Breaking Change Checker
Enforces Semantic Versioning (SemVer) and backward-compatibility rules on API & Event contracts.
Flags breaking field removals or payload type alterations.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple

class ContractCompatibilityChecker:
    """Audits contract evolution between base and proposed revisions."""

    @classmethod
    def check_compatibility(
        cls,
        base_contract: Dict[str, Any],
        head_contract: Dict[str, Any]
    ) -> Dict[str, Any]:
        breaking_changes = []
        compatible_additions = []

        base_props = base_contract.get("properties", {})
        head_props = head_contract.get("properties", {})
        base_req = set(base_contract.get("required", []))
        head_req = set(head_contract.get("required", []))

        # 1. Check for removed fields
        for field, spec in base_props.items():
            if field not in head_props:
                if field in base_req:
                    breaking_changes.append(f"REMOVED_REQUIRED_FIELD: '{field}' was deleted from contract.")
                else:
                    breaking_changes.append(f"REMOVED_OPTIONAL_FIELD: '{field}' was deleted from contract.")

        # 2. Check for type mutations
        for field, base_spec in base_props.items():
            if field in head_props:
                head_spec = head_props[field]
                b_type = base_spec.get("type")
                h_type = head_spec.get("type")
                if b_type != h_type:
                    breaking_changes.append(
                        f"TYPE_MUTATION: Field '{field}' changed type from '{b_type}' to '{h_type}'."
                    )

        # 3. Check for newly introduced required fields without defaults (breaking)
        for field in head_req:
            if field not in base_req and field not in base_props:
                breaking_changes.append(
                    f"NEW_REQUIRED_FIELD_WITHOUT_DEFAULT: '{field}' added as required in head contract."
                )

        # 4. Check for compatible additions (new optional fields)
        for field in head_props:
            if field not in base_props and field not in head_req:
                compatible_additions.append(f"ADDED_OPTIONAL_FIELD: '{field}' added cleanly.")

        is_compatible = len(breaking_changes) == 0

        return {
            "is_compatible": is_compatible,
            "status": "COMPATIBLE" if is_compatible else "BREAKING_CHANGES_DETECTED",
            "breaking_changes": breaking_changes,
            "compatible_additions": compatible_additions,
            "recommendation": "SAFE_TO_MERGE" if is_compatible else "REVERT_OR_BUMP_MAJOR_VERSION"
        }

    @classmethod
    def check_all_contracts(cls, workspace_root) -> Dict[str, Any]:
        """Audits all contracts for backward compatibility against recorded baseline evidence."""
        from pathlib import Path
        root = Path(workspace_root)
        evidence_path = root / ".nb" / "context" / "ledger" / "contract_compatibility_results.json"
        if evidence_path.is_file():
            try:
                evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                checks = evidence.get("checks", [])
                if isinstance(checks, list) and checks:
                    all_compatible = True
                    violations = []
                    for check in checks:
                        if not isinstance(check, dict):
                            all_compatible = False
                            violations.append("Malformed check record")
                            break
                        base_rel = check.get("baseline_path", "")
                        head_rel = check.get("candidate_path", "")
                        base_path = (root / base_rel).resolve()
                        head_path = (root / head_rel).resolve()
                        if not base_path.is_file() or not head_path.is_file():
                            all_compatible = False
                            violations.append(f"Missing schema files: {base_rel} -> {head_rel}")
                            break
                        base_sha = hashlib.sha256(base_path.read_bytes()).hexdigest()
                        head_sha = hashlib.sha256(head_path.read_bytes()).hexdigest()
                        if base_sha != check.get("baseline_sha256") or head_sha != check.get("candidate_sha256"):
                            all_compatible = False
                            violations.append(f"Hash mismatch for {base_rel}")
                            break
                        try:
                            import yaml
                            base_obj = yaml.safe_load(base_path.read_text(encoding="utf-8")) or {}
                            head_obj = yaml.safe_load(head_path.read_text(encoding="utf-8")) or {}
                        except Exception:
                            base_obj = json.loads(base_path.read_text(encoding="utf-8"))
                            head_obj = json.loads(head_path.read_text(encoding="utf-8"))
                        res = cls.check_compatibility(base_obj, head_obj)
                        if not res.get("is_compatible"):
                            all_compatible = False
                            violations.extend(res.get("violations", []))
                    if all_compatible:
                        return {
                            "all_compatible": True,
                            "contracts_checked": len(checks),
                            "violations": []
                        }
                    else:
                        return {
                            "all_compatible": False,
                            "contracts_checked": len(checks),
                            "violations": violations
                        }
            except Exception as e:
                return {
                    "all_compatible": False,
                    "contracts_checked": 0,
                    "violations": [str(e)]
                }
        return {
            'all_compatible': False,
            'contracts_checked': 0,
            'violations': ['Baseline contract revisions are required for compatibility checks.']
        }
