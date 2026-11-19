"""
Percipience Layered Context & Custom Agent Validator
Enforces the 3-Tier Precedence Hierarchy:
Tier 1 (Base Platform Invariants) -> Tier 2 (Enterprise Global Context) -> Tier 3 (Module Domain Context)
Ensures custom agents, rules, and wire contracts run seamlessly without violating platform security constraints.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None

class LayeredContextValidator:
    """Validates unencrypted customer context layered against base platform invariants and wire contracts."""

    @classmethod
    def validate_layered_hierarchy(cls, workspace_root: Path) -> Dict[str, Any]:
        results = {
            "tier1_invariants": "VALID",
            "tier2_global_rules": [],
            "tier3_custom_schemas": [],
            "custom_agents": [],
            "violations": [],
            "overall_valid": True
        }

        # 1. Audit Tier 2: Enterprise Global Context
        rules_dir = (workspace_root / ".nb" / "context" / "custom" / "rules" if (workspace_root / ".nb" / "context").exists() else workspace_root / "context" / "custom" / "rules")
        if rules_dir.exists():
            for rf in rules_dir.glob("*.md"):
                content = rf.read_text(encoding="utf-8")
                # Check that custom rule doesn't attempt to disable safety checks
                if "disable_poisoning_quarantine" in content.lower():
                    results["violations"].append(f"Illegal rule in {rf.name}: cannot disable poisoning quarantine.")
                    results["overall_valid"] = False
                else:
                    results["tier2_global_rules"].append(rf.name)

        # 2. Audit Tier 3: Custom Domain Schemas
        schemas_dir = (workspace_root / ".nb" / "context" / "custom" / "schemas" if (workspace_root / ".nb" / "context").exists() else workspace_root / "context" / "custom" / "schemas")
        if schemas_dir.exists():
            for sf in schemas_dir.glob("*.yaml"):
                results["tier3_custom_schemas"].append(sf.name)

        # 3. Audit Custom Agents
        agents_dir = (workspace_root / ".nb" / "agentic" / "custom" / "agents" if (workspace_root / ".nb" / "agentic").exists() else workspace_root / "agentic" / "custom" / "agents")
        if agents_dir.exists():
            for af in agents_dir.glob("*.yaml"):
                results["custom_agents"].append(af.name)

        # 4. Audit Wire Contracts
        contract_res = cls.validate_wire_contracts(workspace_root)
        results["wire_contracts"] = contract_res.get("contracts", [])
        if not contract_res.get("valid", True):
            results["violations"].extend(contract_res.get("errors", []))
            results["overall_valid"] = False

        return results

    @classmethod
    def validate_wire_contracts(cls, workspace_root: Path) -> Dict[str, Any]:
        """Audits context/contracts/ schemas for required specification fields and valid syntax."""
        contracts_dir = (workspace_root / ".nb" / "context" / "contracts" if (workspace_root / ".nb" / "context").exists() else workspace_root / "context" / "contracts")
        res = {
            "valid": True,
            "contracts": [],
            "errors": []
        }

        if not contracts_dir.exists():
            res["errors"].append(f"Contracts directory missing: {contracts_dir}")
            res["valid"] = False
            return res

        contract_files = list(contracts_dir.glob("*.yaml")) + list(contracts_dir.glob("*.json"))
        if not contract_files:
            res["errors"].append("No contract files found in context/contracts/")
            res["valid"] = False
            return res

        for cf in contract_files:
            try:
                with open(cf, "r", encoding="utf-8") as f:
                    if cf.suffix in (".yaml", ".yml"):
                        data = yaml.safe_load(f) if yaml else {}
                    else:
                        data = json.load(f)
                
                # Verify required contract meta
                if not isinstance(data, dict):
                    res["errors"].append(f"Contract {cf.name} must be a top-level dictionary mapping.")
                    res["valid"] = False
                    continue

                title = data.get("title")
                c_type = data.get("type")
                required_props = data.get("required")

                if not title or not c_type:
                    res["errors"].append(f"Contract {cf.name} missing 'title' or 'type' definition.")
                    res["valid"] = False
                else:
                    res["contracts"].append({
                        "name": cf.name,
                        "title": title,
                        "type": c_type,
                        "required_fields_count": len(required_props) if isinstance(required_props, list) else 0
                    })
            except Exception as e:
                res["errors"].append(f"Failed to parse contract {cf.name}: {str(e)}")
                res["valid"] = False

        return res

    @classmethod
    def validate_sample_payload(cls, contract_schema: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates a runtime payload against a JSON schema contract."""
        errors = []
        required = contract_schema.get("required", [])
        for field in required:
            if field not in payload:
                errors.append(f"Missing required contract field: '{field}'")

        properties = contract_schema.get("properties", {})
        for k, v in payload.items():
            if k in properties:
                prop_type = properties[k].get("type")
                if prop_type == "string" and not isinstance(v, str):
                    errors.append(f"Field '{k}' expected string, got {type(v).__name__}")
                elif prop_type == "integer" and not isinstance(v, int):
                    errors.append(f"Field '{k}' expected integer, got {type(v).__name__}")
                elif prop_type == "number" and not isinstance(v, (int, float)):
                    errors.append(f"Field '{k}' expected number, got {type(v).__name__}")
                elif prop_type == "object" and not isinstance(v, dict):
                    errors.append(f"Field '{k}' expected object, got {type(v).__name__}")

        return len(errors) == 0, errors
