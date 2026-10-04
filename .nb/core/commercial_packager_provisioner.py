#!/usr/bin/env python3
"""
Percipience Commercial Packager, Provisioner & Permissioning Engine
Packages appropriate config, executables, scripts, core engines, contracts,
and agentic workflows based on Commercial Pricing and Revenue models
(Free Community, Team, Business, and Enterprise Dedicated).
Provisions and permissions packages across IntelliJ, VSCode, and SaaS Portal.
"""

import os
import sys
import json
import yaml
import zlib
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

def _get_merkle_engine():
    try:
        from core.merkle_engine import MerkleEngine
        return MerkleEngine
    except ImportError:
        try:
            from workplace.core.merkle_engine import MerkleEngine
            return MerkleEngine
        except ImportError:
            return None


class CommercialPackagerProvisioner:
    """
    Manages tier-based packaging, artifact filtering, license generation,
    cryptographic sealing, multi-IDE provisioning, and RBAC permissioning.
    """

    # Mapping of tiers to inclusion rules and feature matrices
    TIER_NORMALIZATION = {
        "free": "plan_free",
        "plan_free": "plan_free",
        "community": "plan_free",
        "team": "plan_team",
        "plan_team": "plan_team",
        "business": "plan_business",
        "plan_business": "plan_business",
        "enterprise": "plan_enterprise",
        "plan_enterprise": "plan_enterprise"
    }

    # Core engine file classifications per tier
    CORE_TIER_RULES = {
        "plan_free": {
            "allowed_engines": {
                "__init__.py", "merkle_engine.py", "ast_optimizer.py", "token_tracker.py",
                "token_optimizer_suite.py", "autonomous_cicd.py", "layered_context_validator.py",
                "error_recovery_orchestrator.py", "flaky_test_detector.py", "contract_compatibility_checker.py",
                "dependency_cve_sentinel.py", "eval_scoring_engine.py", "living_doc_engine.py",
                "terminal_agent_ast_proxy.py", "attention_budgeter.py", "ambiguity_resolver.py",
                "maturity_evaluator.py", "poisoning_sentinel.py", "prompt_benchmark_engine.py",
                "reconciliation_engine.py", "request_formalizer.py", "semantic_prompt_cache.py",
                "trajectory_recorder.py", "tree_sitter_daemon.py", "workflow_orchestrator.py", "nbpack_envelope.py"
            },
            "allow_nbpack_compilation": False,
            "allow_custom_agent_creation": False,
            "allow_private_vpc": False,
            "allow_worm_egress": False,
            "allow_multi_tenant_gateway": False,
            "expose_basic_platform_tools": False
        },
        "plan_team": {
            "allowed_engines": {
                "__init__.py", "merkle_engine.py", "ast_optimizer.py", "token_tracker.py",
                "token_optimizer_suite.py", "autonomous_cicd.py", "layered_context_validator.py",
                "error_recovery_orchestrator.py", "flaky_test_detector.py", "contract_compatibility_checker.py",
                "dependency_cve_sentinel.py", "eval_scoring_engine.py", "living_doc_engine.py",
                "terminal_agent_ast_proxy.py", "attention_budgeter.py", "ambiguity_resolver.py",
                "maturity_evaluator.py", "poisoning_sentinel.py", "prompt_benchmark_engine.py",
                "reconciliation_engine.py", "request_formalizer.py", "semantic_prompt_cache.py",
                "trajectory_recorder.py", "tree_sitter_daemon.py", "workflow_orchestrator.py",
                "worktree_engine.py", "prompt_drift_sentinel.py", "doc_drift_synchronizer.py"
            },
            "allow_nbpack_compilation": False,
            "allow_custom_agent_creation": True,
            "allow_private_vpc": False,
            "allow_worm_egress": False,
            "allow_multi_tenant_gateway": False,
            "expose_basic_platform_tools": False
        },
        "plan_business": {
            "allowed_engines": {
                "__init__.py", "merkle_engine.py", "ast_optimizer.py", "token_tracker.py",
                "token_optimizer_suite.py", "autonomous_cicd.py", "layered_context_validator.py",
                "error_recovery_orchestrator.py", "flaky_test_detector.py", "contract_compatibility_checker.py",
                "dependency_cve_sentinel.py", "eval_scoring_engine.py", "living_doc_engine.py",
                "terminal_agent_ast_proxy.py", "attention_budgeter.py", "ambiguity_resolver.py",
                "maturity_evaluator.py", "poisoning_sentinel.py", "prompt_benchmark_engine.py",
                "reconciliation_engine.py", "request_formalizer.py", "semantic_prompt_cache.py",
                "trajectory_recorder.py", "tree_sitter_daemon.py", "workflow_orchestrator.py",
                "worktree_engine.py", "prompt_drift_sentinel.py", "doc_drift_synchronizer.py",
                "nbpack_envelope.py", "agent_plugin_engine.py", "semantic_parity_engine.py",
                "cognitive_router.py", "adversarial_fuzzer.py", "diagnostic_reprompt.py"
            },
            "allow_nbpack_compilation": True,
            "allow_custom_agent_creation": True,
            "allow_private_vpc": False,
            "allow_worm_egress": False,
            "allow_multi_tenant_gateway": True,
            "expose_basic_platform_tools": True
        },
        "plan_enterprise": {
            "allowed_engines": "ALL", # All engines permitted
            "allow_nbpack_compilation": True,
            "allow_custom_agent_creation": True,
            "allow_private_vpc": True,
            "allow_worm_egress": True,
            "allow_multi_tenant_gateway": True,
            "expose_basic_platform_tools": True
        }
    }

    @classmethod
    def load_billing_plans(cls, workspace_root: Path) -> Dict[str, Any]:
        """Loads billing plans and pricing models from config."""
        config_path = workspace_root / ".nb" / "config" / "billing_plans.yaml"
        if not config_path.exists():
            config_path = workspace_root / "workplace" / "modules" / "mod_intellij_plugin" / "src" / "main" / "resources" / "percipience" / "config" / "billing_plans.yaml"
        if config_path.exists():
            try:
                return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            except Exception:
                pass
        return {}

    @classmethod
    def get_tier_spec(cls, tier: str, workspace_root: Path) -> Dict[str, Any]:
        """Returns the normalized tier specification and feature entitlements."""
        norm_tier = cls.TIER_NORMALIZATION.get(tier.lower().strip(), "plan_free")
        plans_data = cls.load_billing_plans(workspace_root)
        plans = plans_data.get("plans", {})
        
        tier_data = plans.get(norm_tier, {
            "id": norm_tier,
            "name": norm_tier.replace("_", " ").title(),
            "base_price_monthly_usd": 0 if norm_tier == "plan_free" else 1499,
            "included_seats": 1 if norm_tier == "plan_free" else 15,
            "included_concurrent_worktrees": 1 if norm_tier == "plan_free" else 5,
            "included_pr_audits_monthly": 500 if norm_tier == "plan_free" else 5000,
            "features": {}
        })
        
        raw_rules = cls.CORE_TIER_RULES.get(norm_tier, cls.CORE_TIER_RULES["plan_free"])
        tier_rules = dict(raw_rules)
        if isinstance(tier_rules.get("allowed_engines"), set):
            tier_rules["allowed_engines"] = sorted(list(tier_rules["allowed_engines"]))

        return {
            "tier_id": norm_tier,
            "canonical_name": tier_data.get("name", norm_tier),
            "base_price_monthly_usd": tier_data.get("base_price_monthly_usd", 0),
            "included_seats": tier_data.get("included_seats", 1),
            "included_concurrent_worktrees": tier_data.get("included_concurrent_worktrees", 1),
            "included_pr_audits_monthly": tier_data.get("included_pr_audits_monthly", 500),
            "features": tier_data.get("features", {}),
            "rules": tier_rules
        }

    @classmethod
    def package_tier(
        cls,
        workspace_root: Path,
        tier: str,
        output_dir: Optional[Path] = None,
        tenant_id: str = "tenant_community_default"
    ) -> Dict[str, Any]:
        """
        Assembles, filters, seals, and packages the exact runtime assets
        for the given tier according to Commercial Pricing rules.
        """
        workspace_root = Path(workspace_root).resolve()
        spec = cls.get_tier_spec(tier, workspace_root)
        tier_id = spec["tier_id"]
        rules = spec["rules"]

        if output_dir is None:
            output_dir = workspace_root / ".nb" / "bundles" / f"package_{tier_id}"
        else:
            output_dir = Path(output_dir).resolve()

        output_dir.mkdir(parents=True, exist_ok=True)

        bundled_files: List[str] = []
        file_hashes: Dict[str, str] = {}

        # 1. Package .nb/bin/percipience
        bin_src = workspace_root / ".nb" / "bin" / "percipience"
        bin_dst_dir = output_dir / "bin"
        bin_dst_dir.mkdir(parents=True, exist_ok=True)
        if bin_src.exists():
            bin_dst = bin_dst_dir / "percipience"
            shutil.copy2(bin_src, bin_dst)
            bin_dst.chmod(0o755)
            rel_path = "bin/percipience"
            bundled_files.append(rel_path)
            file_hashes[rel_path] = hashlib.sha256(bin_dst.read_bytes()).hexdigest()

        # 2. Package .nb/config/
        config_src = workspace_root / ".nb" / "config"
        config_dst = output_dir / "config"
        config_dst.mkdir(parents=True, exist_ok=True)
        if config_src.exists():
            for f in config_src.glob("*.yaml"):
                dst_file = config_dst / f.name
                shutil.copy2(f, dst_file)
                rel_path = f"config/{f.name}"
                bundled_files.append(rel_path)
                file_hashes[rel_path] = hashlib.sha256(dst_file.read_bytes()).hexdigest()

        # 3. Package .nb/scripts/
        scripts_src = workspace_root / ".nb" / "scripts"
        scripts_dst = output_dir / "scripts"
        scripts_dst.mkdir(parents=True, exist_ok=True)
        if scripts_src.exists():
            for f in scripts_src.glob("*.sh"):
                dst_file = scripts_dst / f.name
                shutil.copy2(f, dst_file)
                dst_file.chmod(0o755)
                rel_path = f"scripts/{f.name}"
                bundled_files.append(rel_path)
                file_hashes[rel_path] = hashlib.sha256(dst_file.read_bytes()).hexdigest()

        # 4. Package .nb/core/ based on tier filtering
        core_src = workspace_root / ".nb" / "core"
        if not core_src.exists():
            core_src = workspace_root / "workplace" / "core"

        core_dst = output_dir / "core"
        core_dst.mkdir(parents=True, exist_ok=True)

        allowed_engines = set(rules.get("allowed_engines", [])) if isinstance(rules.get("allowed_engines"), list) else rules.get("allowed_engines", set())
        if core_src.exists():
            for f in core_src.glob("*.py"):
                if f.name.startswith("."):
                    continue
                if allowed_engines == "ALL" or f.name in allowed_engines:
                    dst_file = core_dst / f.name
                    shutil.copy2(f, dst_file)
                    rel_path = f"core/{f.name}"
                    bundled_files.append(rel_path)
                    file_hashes[rel_path] = hashlib.sha256(dst_file.read_bytes()).hexdigest()

        # 5. Package .nb/context/ (contracts & rules)
        context_src = workspace_root / ".nb" / "context"
        context_dst = output_dir / "context"
        context_dst.mkdir(parents=True, exist_ok=True)
        if context_src.exists():
            for sub in ["contracts", "rules"]:
                sub_src = context_src / sub
                if sub_src.exists():
                    sub_dst = context_dst / sub
                    sub_dst.mkdir(parents=True, exist_ok=True)
                    for f in sub_src.glob("*"):
                        if f.is_file() and not f.name.startswith("."):
                            dst_file = sub_dst / f.name
                            shutil.copy2(f, dst_file)
                            rel_path = f"context/{sub}/{f.name}"
                            bundled_files.append(rel_path)
                            file_hashes[rel_path] = hashlib.sha256(dst_file.read_bytes()).hexdigest()

        # 6. Package .nb/agentic/ (custom agents & workflows)
        agentic_src = workspace_root / ".nb" / "agentic"
        agentic_dst = output_dir / "agentic"
        agentic_dst.mkdir(parents=True, exist_ok=True)
        if agentic_src.exists():
            for sub in ["custom/agents", "custom/workflows"]:
                sub_src = agentic_src / sub
                if sub_src.exists():
                    sub_dst = agentic_dst / sub
                    sub_dst.mkdir(parents=True, exist_ok=True)
                    for f in sub_src.glob("*.yaml"):
                        # In Free Tier, only package basic free agents & basic CI/CD workflow
                        if tier_id == "plan_free":
                            if "enterprise" in f.name or "saas_portal" in f.name or "iot_mobile" in f.name:
                                continue
                        dst_file = sub_dst / f.name
                        shutil.copy2(f, dst_file)
                        rel_path = f"agentic/{sub}/{f.name}"
                        bundled_files.append(rel_path)
                        file_hashes[rel_path] = hashlib.sha256(dst_file.read_bytes()).hexdigest()

        # 7. Package Master Plan template
        plan_dst = output_dir / "plan"
        plan_dst.mkdir(parents=True, exist_ok=True)
        if tier_id == "plan_free":
            free_plan = workspace_root / ".nb" / "plan" / "master" / "parent-master-free-plan" / "detailed.md"
            if free_plan.exists():
                dst_plan = plan_dst / "claude-context-engineering-parent-master-free_plan.md"
                shutil.copy2(free_plan, dst_plan)
                bundled_files.append("plan/claude-context-engineering-parent-master-free_plan.md")
        else:
            master_plan = workspace_root / ".nb" / "plan" / "master" / "parent-master-plan" / "detailed.md"
            if master_plan.exists():
                dst_plan = plan_dst / "claude-context-engineering-parent-master-plan.md"
                shutil.copy2(master_plan, dst_plan)
                bundled_files.append("plan/claude-context-engineering-parent-master-plan.md")

        # 8. Generate PERCIPIENCE_LICENSE.json
        manifest_payload = {
            "license_id": f"lic_{tier_id}_{hashlib.sha256(datetime.now(timezone.utc).isoformat().encode()).hexdigest()[:12]}",
            "tenant_id": tenant_id,
            "tier": tier_id,
            "tier_name": spec["canonical_name"],
            "base_price_monthly_usd": spec["base_price_monthly_usd"],
            "included_seats": spec["included_seats"],
            "included_concurrent_worktrees": spec["included_concurrent_worktrees"],
            "included_pr_audits_monthly": spec["included_pr_audits_monthly"],
            "entitled_features": spec["features"],
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "total_files": len(bundled_files),
            "file_manifest": file_hashes
        }

        # Calculate license signature
        license_json = json.dumps(manifest_payload, indent=2)
        license_sig = hashlib.sha256(license_json.encode("utf-8")).hexdigest()
        manifest_payload["signature_sha256"] = license_sig

        license_file = output_dir / "PERCIPIENCE_LICENSE.json"
        license_file.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
        bundled_files.append("PERCIPIENCE_LICENSE.json")

        # 9. Seal Merkle Block
        merkle_block_id = None
        MerkleEngineClass = _get_merkle_engine()
        if MerkleEngineClass:
            try:
                seal = MerkleEngineClass.record_state(
                    workspace_root=workspace_root,
                    agent_id="agent_commercial_packager_provisioner",
                    action=f"PACKAGE_TIER_{tier_id.upper()}",
                    step_id="step_commercial_packaging",
                    changed_files=[str(output_dir)]
                )
                merkle_block_id = seal.get("block_id")
            except Exception:
                pass

        return {
            "status": "PACKAGED",
            "tier": tier_id,
            "tier_name": spec["canonical_name"],
            "canonical_name": spec["canonical_name"],
            "package_dir": str(output_dir),
            "output_directory": str(output_dir),
            "total_files": len(bundled_files),
            "bundled_files_count": len(bundled_files),
            "bundled_files": bundled_files,
            "merkle_root": license_sig,
            "license_id": manifest_payload.get("license_id"),
            "license_signature": license_sig,
            "sealed_at": manifest_payload.get("issued_at"),
            "merkle_block_id": merkle_block_id
        }

    @classmethod
    def audit_billing_entitlements(
        cls,
        workspace_root: Path,
        tenant_id_or_tier: str = "tenant_community_default",
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Audits billing entitlements and current limits for a tenant.
        """
        workspace_root = Path(workspace_root).resolve()
        t_id = tenant_id or tenant_id_or_tier
        tenant_tier = t_id
        tenant_hierarchy_file = workspace_root / ".nb" / "context" / "tenant_hierarchy.json"
        if tenant_hierarchy_file.exists():
            try:
                data = json.loads(tenant_hierarchy_file.read_text(encoding="utf-8"))
                tenants = data.get("tenants", {})
                if t_id in tenants:
                    tenant_tier = tenants[t_id].get("tier", "plan_free")
            except Exception:
                pass

        spec = cls.get_tier_spec(tenant_tier, workspace_root)
        return {
            "tenant_id": t_id,
            "tier": spec["tier_id"],
            "tier_name": spec["canonical_name"],
            "base_price_monthly_usd": spec["base_price_monthly_usd"],
            "included_seats": spec["included_seats"],
            "included_concurrent_worktrees": spec["included_concurrent_worktrees"],
            "included_pr_audits_monthly": spec["included_pr_audits_monthly"],
            "features": spec["features"],
            "rules": spec["rules"]
        }

    @classmethod
    def provision_target(
        cls,
        workspace_root: Path,
        tenant_id: str,
        tier: str,
        target: str = "all",
        license_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Provisions and permissions packaged artifacts across IntelliJ, VSCode, and SaaS Portal.
        """
        workspace_root = Path(workspace_root).resolve()
        spec = cls.get_tier_spec(tier, workspace_root)
        tier_id = spec["tier_id"]

        # 1. Package the tier
        pkg_res = cls.package_tier(
            workspace_root=workspace_root,
            tier=tier_id,
            tenant_id=tenant_id
        )
        src_pkg_dir = Path(pkg_res["package_dir"])

        provisioned_targets: List[str] = []

        # 2. Provision IntelliJ / PyCharm Plugin
        if target in ["all", "intellij", "pycharm", "ide", "mod_intellij_plugin"]:
            ij_resources = workspace_root / "workplace" / "modules" / "mod_intellij_plugin" / "src" / "main" / "resources" / "percipience"
            ij_resources.mkdir(parents=True, exist_ok=True)
            for item in ["bin", "config", "core", "agentic", "plan"]:
                src_item = src_pkg_dir / item
                dst_item = ij_resources / item
                if src_item.exists():
                    if dst_item.exists():
                        shutil.rmtree(dst_item)
                    shutil.copytree(src_item, dst_item)
            # Copy license
            shutil.copy2(src_pkg_dir / "PERCIPIENCE_LICENSE.json", ij_resources / "tenant_license.json")
            provisioned_targets.append("mod_intellij_plugin")

        # 3. Provision VSCode Extension
        if target in ["all", "vscode", "mod_vscode_extension"]:
            vscode_dir = workspace_root / "workplace" / "modules" / "mod_vscode_extension"
            if vscode_dir.exists():
                vscode_runtime = vscode_dir / "percipience_runtime"
                vscode_runtime.mkdir(parents=True, exist_ok=True)
                for item in ["bin", "config", "core"]:
                    src_item = src_pkg_dir / item
                    dst_item = vscode_runtime / item
                    if src_item.exists():
                        if dst_item.exists():
                            shutil.rmtree(dst_item)
                        shutil.copytree(src_item, dst_item)
                shutil.copy2(src_pkg_dir / "PERCIPIENCE_LICENSE.json", vscode_dir / ".percipience_license.json")
                provisioned_targets.append("mod_vscode_extension")

        # 4. Provision SaaS Portal & Gateway Hierarchy
        if target in ["all", "portal", "saas", "saas_portal_gateway"]:
            tenant_hierarchy_file = workspace_root / ".nb" / "context" / "tenant_hierarchy.json"
            hierarchy = {"tenants": {}, "projects": {}, "repositories": {}}
            if tenant_hierarchy_file.exists():
                try:
                    hierarchy = json.loads(tenant_hierarchy_file.read_text(encoding="utf-8"))
                except Exception:
                    pass

            tenants = hierarchy.setdefault("tenants", {})
            tenants[tenant_id] = {
                "tenant_id": tenant_id,
                "name": tenant_id.replace("_", " ").title(),
                "slug": tenant_id.replace("_", "-"),
                "tier": tier_id,
                "status": "ACTIVE",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "settings": {
                    "max_concurrent_worktrees": spec["included_concurrent_worktrees"],
                    "monthly_pr_audits_quota": spec["included_pr_audits_monthly"]
                },
                "metadata": {
                    "entitlements": spec["features"],
                    "provisioned_at": datetime.now(timezone.utc).isoformat()
                }
            }
            tenant_hierarchy_file.write_text(json.dumps(hierarchy, indent=2), encoding="utf-8")
            provisioned_targets.append("saas_portal_gateway")

        # 5. Record Merkle Seal
        merkle_block_id = None
        MerkleEngineClass = _get_merkle_engine()
        if MerkleEngineClass:
            try:
                seal = MerkleEngineClass.record_state(
                    workspace_root=workspace_root,
                    agent_id="agent_commercial_packager_provisioner",
                    action=f"PROVISION_{tenant_id.upper()}_{tier_id.upper()}",
                    step_id="step_commercial_provisioning",
                    changed_files=provisioned_targets
                )
                merkle_block_id = seal.get("block_id")
            except Exception:
                pass

        license_token = pkg_res.get("license_token") or pkg_res.get("license_id")
        return {
            "status": "PROVISIONED",
            "tenant_id": tenant_id,
            "tier": tier_id,
            "targets": provisioned_targets,
            "provisioned_targets": provisioned_targets,
            "license_token": license_token,
            "package_info": pkg_res,
            "package_result": pkg_res,
            "merkle_block_id": merkle_block_id
        }

    @classmethod
    def verify_permissions(
        cls,
        workspace_root: Path,
        tenant_id: str = "tenant_community_default",
        action: str = "",
        target_file: Optional[str] = None,
        feature: str = "",
        tenant_id_or_tier: Optional[str] = None
    ) -> Dict[str, Any]:
        t_id = tenant_id_or_tier or tenant_id
        """
        Verifies whether a tenant or tier is permitted to perform an action or use a feature.
        """
        workspace_root = Path(workspace_root).resolve()
        evaluated_action = action or feature

        tenant_tier = t_id
        tenant_hierarchy_file = workspace_root / ".nb" / "context" / "tenant_hierarchy.json"
        if tenant_hierarchy_file.exists():
            try:
                data = json.loads(tenant_hierarchy_file.read_text(encoding="utf-8"))
                tenants = data.get("tenants", {})
                if t_id in tenants:
                    tenant_tier = tenants[t_id].get("tier", "plan_free")
            except Exception:
                pass

        spec = cls.get_tier_spec(tenant_tier, workspace_root)
        features = spec.get("features", {})
        rules = spec.get("rules", {})

        allowed = bool(features.get(evaluated_action, False))

        # Check rule overrides
        if evaluated_action in rules:
            allowed = bool(rules[evaluated_action])
        elif evaluated_action == "allow_worm_egress":
            allowed = bool(rules.get("allow_worm_egress", False))
        elif evaluated_action == "allow_nbpack_compilation":
            allowed = bool(rules.get("allow_nbpack_compilation", False))
        elif evaluated_action == "allow_custom_agent_creation":
            allowed = bool(rules.get("allow_custom_agent_creation", False))
        elif evaluated_action == "allow_private_vpc":
            allowed = bool(rules.get("allow_private_vpc", False))
        elif evaluated_action == "allow_multi_tenant_gateway":
            allowed = bool(rules.get("allow_multi_tenant_gateway", False))
        elif evaluated_action == "basic_platform_tools_exposure":
            allowed = bool(rules.get("expose_basic_platform_tools", False))

        return {
            "tenant_id": t_id,
            "tenant_or_tier": t_id,
            "tier": spec["tier_id"],
            "resolved_tier": spec["tier_id"],
            "tier_name": spec["canonical_name"],
            "action": evaluated_action,
            "feature": evaluated_action,
            "permitted": allowed,
            "allowed": allowed,
            "reason": "Permitted under tier entitlements" if allowed else f"Action/Feature '{evaluated_action}' requires tier upgrade from {spec['canonical_name']}"
        }
