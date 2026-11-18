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


def _get_update_resolver():
    try:
        import plugin_update_resolver
        return plugin_update_resolver
    except ImportError:
        try:
            from core import plugin_update_resolver
            return plugin_update_resolver
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
                "trajectory_recorder.py", "tree_sitter_daemon.py", "workflow_orchestrator.py", "nbpack_envelope.py",
                "commercial_packager_provisioner.py", "handoff_validator.py", "pii_sanitizer.py",
                "prompt_injection_guard.py", "output_guardrail_validator.py", "dynamic_dag_orchestrator.py", "self_reflection_engine.py", "consensus_quorum_engine.py", "agent_capability_guard.py", "fleet_manager.py", "fleet_agent.py", "agent_memory_engine.py", "tool_contract_validator.py", "few_shot_retriever.py", "hitl_checkpoint_manager.py", "container_plan_executor.py", "git_bundle_transport.py", "plugin_update_resolver.py"
            },
            "allow_nbpack_compilation": False,
            "allow_custom_agent_creation": False,
            "allow_private_vpc": False,
            "allow_worm_egress": False,
            "allow_multi_tenant_gateway": False,
            "expose_basic_platform_tools": False,
            # Autonomous delivery workflows bundled per tier (mirrors allowed_engines gating)
            "allowed_workflows": {
                "basic_autonomous_cicd.yaml",
                "intellij_pycharm_plugin_delivery_flow.yaml",
                "derivation_pipeline.yaml",
                "pr_gatekeeper.yaml"
            }
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
                "worktree_engine.py", "prompt_drift_sentinel.py", "doc_drift_synchronizer.py",
                "swarm_governor.py", "commercial_packager_provisioner.py", "handoff_validator.py",
                "pii_sanitizer.py", "prompt_injection_guard.py", "output_guardrail_validator.py", "dynamic_dag_orchestrator.py", "self_reflection_engine.py", "consensus_quorum_engine.py", "agent_capability_guard.py", "fleet_manager.py", "fleet_agent.py", "agent_memory_engine.py", "tool_contract_validator.py", "few_shot_retriever.py", "hitl_checkpoint_manager.py", "container_plan_executor.py", "git_bundle_transport.py", "plugin_update_resolver.py"
            },
            "allow_nbpack_compilation": False,
            "allow_custom_agent_creation": True,
            "allow_private_vpc": False,
            "allow_worm_egress": False,
            "allow_multi_tenant_gateway": False,
            "expose_basic_platform_tools": False,
            "allowed_workflows": {
                "basic_autonomous_cicd.yaml",
                "intellij_pycharm_plugin_delivery_flow.yaml",
                "vscode_plugin_delivery_flow.yaml",
                "derivation_pipeline.yaml",
                "pr_gatekeeper.yaml"
            }
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
                "cognitive_router.py", "adversarial_fuzzer.py", "diagnostic_reprompt.py",
                "swarm_governor.py", "commercial_packager_provisioner.py", "handoff_validator.py",
                "pii_sanitizer.py", "prompt_injection_guard.py", "output_guardrail_validator.py", "dynamic_dag_orchestrator.py", "self_reflection_engine.py", "consensus_quorum_engine.py", "agent_capability_guard.py", "fleet_manager.py", "fleet_agent.py", "agent_memory_engine.py", "tool_contract_validator.py", "few_shot_retriever.py", "hitl_checkpoint_manager.py", "container_plan_executor.py", "git_bundle_transport.py", "plugin_update_resolver.py",
                "otel_exporter.py", "context_gateway.py", "swarm_fleet_dispatcher.py", "consolidation_synthesizer.py",
                "plan_module_orchestrator.py", "agent_registry_synchronizer.py"
            },
            "allow_nbpack_compilation": True,
            "allow_custom_agent_creation": True,
            "allow_private_vpc": False,
            "allow_worm_egress": False,
            "allow_multi_tenant_gateway": True,
            "expose_basic_platform_tools": True,
            "allowed_workflows": {
                "basic_autonomous_cicd.yaml",
                "intellij_pycharm_plugin_delivery_flow.yaml",
                "vscode_plugin_delivery_flow.yaml",
                "commercial_packaging_provisioning_flow.yaml",
                "saas_portal_delivery_flow.yaml",
                "iot_mobile_delivery_flow.yaml",
                "derivation_pipeline.yaml",
                "pr_gatekeeper.yaml"
            }
        },
        "plan_enterprise": {
            "allowed_engines": "ALL", # All engines permitted
            "allow_nbpack_compilation": True,
            "allow_custom_agent_creation": True,
            "allow_private_vpc": True,
            "allow_worm_egress": True,
            "allow_multi_tenant_gateway": True,
            "expose_basic_platform_tools": True,
            "allowed_workflows": "ALL"
        }
    }

    @classmethod
    def load_billing_plans(cls, workspace_root: Path) -> Dict[str, Any]:
        """Loads billing plans and pricing models from config."""
        config_path = workspace_root / ".nb" / "config" / "billing_plans.yaml"
        if not config_path.exists():
            config_path = workspace_root / "workplace" / "modules" / "mod_intellij_plugin" / "src" / "main" / "resources" / "percipience" / "config" / "billing_plans.yaml"
        if not config_path.exists():
            repo_candidate = Path(__file__).resolve().parents[2] / ".nb" / "config" / "billing_plans.yaml"
            if repo_candidate.exists():
                config_path = repo_candidate
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
        if isinstance(tier_rules.get("allowed_workflows"), set):
            tier_rules["allowed_workflows"] = sorted(list(tier_rules["allowed_workflows"]))

        canonical_name = tier_data.get("name", norm_tier)
        return {
            "tier_id": norm_tier,
            "canonical_name": canonical_name,
            "tier_name": canonical_name,
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
        allowed_workflows = rules.get("allowed_workflows", [])
        is_all_workflows = allowed_workflows == "ALL"
        allowed_workflow_set = set(allowed_workflows) if isinstance(allowed_workflows, list) else set()

        if output_dir is None:
            output_dir = workspace_root / ".nb" / "bundles" / f"package_{tier_id}"
        else:
            output_dir = Path(output_dir).resolve()

        if output_dir.exists():
            shutil.rmtree(output_dir)
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
            for f in scripts_src.glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    dst_file = scripts_dst / f.name
                    shutil.copy2(f, dst_file)
                    dst_file.chmod(0o755)
                    rel_path = f"scripts/{f.name}"
                    bundled_files.append(rel_path)
                    file_hashes[rel_path] = hashlib.sha256(dst_file.read_bytes()).hexdigest()

        # 3b. Package .nb/git_hooks/ (pre-commit guardrail hooks) for plugin & IDE bootstrapping
        git_hooks_src = workspace_root / ".nb" / "git_hooks"
        hooks_dst = output_dir / "hooks"
        hooks_dst.mkdir(parents=True, exist_ok=True)
        if git_hooks_src.exists():
            for f in sorted(git_hooks_src.glob("*")):
                if f.is_file() and not f.name.startswith("."):
                    dst_file = hooks_dst / f.name
                    shutil.copy2(f, dst_file)
                    dst_file.chmod(0o755)
                    rel_path = f"hooks/{f.name}"
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
            for f in sorted(core_src.glob("*.py")):
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
                    for f in sorted(sub_src.glob("*")):
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
                    for f in sorted(sub_src.glob("*.yaml")):
                        # Tier-gate autonomous delivery workflows (mirrors CORE_TIER_RULES gating)
                        if sub == "custom/workflows":
                            if not is_all_workflows and f.name not in allowed_workflow_set:
                                continue
                        elif sub == "custom/agents" and tier_id == "plan_free":
                            # Free Tier retains only baseline agents (no enterprise / portal / iot agents)
                            if "enterprise" in f.name or "saas_portal" in f.name or "iot_mobile" in f.name:
                                continue
                        dst_file = sub_dst / f.name
                        shutil.copy2(f, dst_file)
                        rel_path = f"agentic/{sub}/{f.name}"
                        bundled_files.append(rel_path)
                        file_hashes[rel_path] = hashlib.sha256(dst_file.read_bytes()).hexdigest()

        # 6b. Package tier-appropriate autonomous delivery workflows (workflows/)
        workflows_dst = output_dir / "workflows"
        workflows_dst.mkdir(parents=True, exist_ok=True)
        delivery_workflows_src = workspace_root / ".nb" / "agentic" / "custom" / "workflows"
        if not delivery_workflows_src.exists():
            delivery_workflows_src = workspace_root / "workplace" / "modules" / "mod_intellij_plugin" / "src" / "main" / "resources" / "percipience" / "agentic" / "custom" / "workflows"
        if delivery_workflows_src.exists():
            for f in sorted(delivery_workflows_src.glob("*.yaml")):
                if not is_all_workflows and f.name not in allowed_workflow_set:
                    continue
                dst_cicd = workflows_dst / f.name
                shutil.copy2(f, dst_cicd)
                rel_path = f"workflows/{f.name}"
                bundled_files.append(rel_path)
                file_hashes[rel_path] = hashlib.sha256(dst_cicd.read_bytes()).hexdigest()

        # 6c. Package canonical .nb/agentic/workflows/ (gatekeeper & plan derivation workflows)
        canonical_workflows_src = workspace_root / ".nb" / "agentic" / "workflows"
        if canonical_workflows_src.exists():
            canonical_workflows_dst = agentic_dst / "workflows"
            canonical_workflows_dst.mkdir(parents=True, exist_ok=True)
            for f in sorted(canonical_workflows_src.glob("*.yaml")):
                if not is_all_workflows and f.name not in allowed_workflow_set:
                    continue
                dst_file = canonical_workflows_dst / f.name
                shutil.copy2(f, dst_file)
                rel_path = f"agentic/workflows/{f.name}"
                bundled_files.append(rel_path)
                file_hashes[rel_path] = hashlib.sha256(dst_file.read_bytes()).hexdigest()

        # 7. Package Master Plan template
        plan_dst = output_dir / "plan"
        plan_dst.mkdir(parents=True, exist_ok=True)
        if tier_id == "plan_free":
            free_plan = workspace_root / ".nb" / "plan" / "master" / "parent-master-free-plan" / "detailed.md"
            if not free_plan.exists():
                free_plan = workspace_root / ".nb" / "plan" / "claude-context-engineering-parent-master-free_plan.md"
            if free_plan.exists():
                dst_plan = plan_dst / "claude-context-engineering-parent-master-free_plan.md"
                shutil.copy2(free_plan, dst_plan)
                bundled_files.append("plan/claude-context-engineering-parent-master-free_plan.md")
                file_hashes["plan/claude-context-engineering-parent-master-free_plan.md"] = hashlib.sha256(dst_plan.read_bytes()).hexdigest()
        else:
            master_plan = workspace_root / ".nb" / "plan" / "master" / "parent-master-plan" / "detailed.md"
            if not master_plan.exists():
                master_plan = workspace_root / ".nb" / "plan" / "claude-context-engineering-parent-master-plan.md"
            if master_plan.exists():
                dst_plan = plan_dst / "claude-context-engineering-parent-master-plan.md"
                shutil.copy2(master_plan, dst_plan)
                bundled_files.append("plan/claude-context-engineering-parent-master-plan.md")
                file_hashes["plan/claude-context-engineering-parent-master-plan.md"] = hashlib.sha256(dst_plan.read_bytes()).hexdigest()

            # Also provide free plan template for offline fallback
            free_plan = workspace_root / ".nb" / "plan" / "master" / "parent-master-free-plan" / "detailed.md"
            if not free_plan.exists():
                free_plan = workspace_root / ".nb" / "plan" / "claude-context-engineering-parent-master-free_plan.md"
            if free_plan.exists():
                dst_free = plan_dst / "claude-context-engineering-parent-master-free_plan.md"
                shutil.copy2(free_plan, dst_free)
                bundled_files.append("plan/claude-context-engineering-parent-master-free_plan.md")
                file_hashes["plan/claude-context-engineering-parent-master-free_plan.md"] = hashlib.sha256(dst_free.read_bytes()).hexdigest()

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

        # 8b. Emit the offline auto-upgrade version manifest (percipience/version.json)
        resolver = _get_update_resolver()
        if resolver is not None:
            version_manifest = resolver.emit_version_manifest(
                output_dir,
                plugin_version=resolver.CURRENT_PLUGIN_VERSION,
                platform_version=resolver.CURRENT_PLATFORM_VERSION,
                tier=tier_id,
                channel="stable",
            )
            rel_manifest = version_manifest.relative_to(output_dir).as_posix()
            bundled_files.append(rel_manifest)
            file_hashes[rel_manifest] = hashlib.sha256(version_manifest.read_bytes()).hexdigest()

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
            "canonical_name": spec["canonical_name"],
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
            for item in ["bin", "config", "core", "agentic", "plan", "workflows", "scripts", "hooks"]:
                src_item = src_pkg_dir / item
                dst_item = ij_resources / item
                if src_item.exists():
                    if dst_item.exists():
                        shutil.rmtree(dst_item)
                    shutil.copytree(src_item, dst_item)

            # Emit the embedded offline auto-upgrade version manifest (jar: percipience/version.json)
            resolver = _get_update_resolver()
            if resolver is not None:
                resolver.emit_version_manifest(
                    ij_resources,
                    plugin_version=resolver.CURRENT_PLUGIN_VERSION,
                    platform_version=resolver.CURRENT_PLATFORM_VERSION,
                    tier=tier_id,
                    channel="stable",
                )

            # Ensure both canonical plan templates are present in IDE resources
            free_plan_src = workspace_root / ".nb" / "plan" / "master" / "parent-master-free-plan" / "detailed.md"
            if not free_plan_src.exists():
                free_plan_src = workspace_root / ".nb" / "plan" / "claude-context-engineering-parent-master-free_plan.md"
            if free_plan_src.exists():
                (ij_resources / "plan").mkdir(parents=True, exist_ok=True)
                shutil.copy2(free_plan_src, ij_resources / "plan" / "claude-context-engineering-parent-master-free_plan.md")

            master_plan_src = workspace_root / ".nb" / "plan" / "master" / "parent-master-plan" / "detailed.md"
            if not master_plan_src.exists():
                master_plan_src = workspace_root / ".nb" / "plan" / "claude-context-engineering-parent-master-plan.md"
            if master_plan_src.exists():
                (ij_resources / "plan").mkdir(parents=True, exist_ok=True)
                shutil.copy2(master_plan_src, ij_resources / "plan" / "claude-context-engineering-parent-master-plan.md")

            # Copy license
            shutil.copy2(src_pkg_dir / "PERCIPIENCE_LICENSE.json", ij_resources / "tenant_license.json")
            provisioned_targets.append("mod_intellij_plugin")

        # 3. Provision VSCode Extension
        if target in ["all", "vscode", "mod_vscode_extension"]:
            vscode_dir = workspace_root / "workplace" / "modules" / "mod_vscode_extension"
            if vscode_dir.exists():
                vscode_runtime = vscode_dir / "percipience_runtime"
                vscode_runtime.mkdir(parents=True, exist_ok=True)
                for item in ["bin", "config", "core", "agentic", "plan", "workflows", "scripts", "hooks"]:
                    src_item = src_pkg_dir / item
                    dst_item = vscode_runtime / item
                    if src_item.exists():
                        if dst_item.exists():
                            shutil.rmtree(dst_item)
                        shutil.copytree(src_item, dst_item)
                resolver = _get_update_resolver()
                if resolver is not None:
                    resolver.emit_version_manifest(
                        vscode_runtime,
                        plugin_version=resolver.CURRENT_PLUGIN_VERSION,
                        platform_version=resolver.CURRENT_PLATFORM_VERSION,
                        tier=tier_id,
                        channel="stable",
                    )
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
        tenant_id_or_tier: Optional[str] = None,
        feature: Optional[str] = None,
        tier_or_tenant: Optional[str] = None,
        feature_name: Optional[str] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Enforces and checks RBAC permission gates against the active license.
        Supports both positional and keyword invocation signatures.
        """
        workspace_root = Path(workspace_root).resolve()
        target = tenant_id_or_tier or tier_or_tenant or kwargs.get("tier") or kwargs.get("tenant") or kwargs.get("tenant_id") or "plan_free"
        feat = feature or feature_name or kwargs.get("action") or kwargs.get("feature_name") or ""
        if not feat and len(args) > 0:
            feat = args[0]

        spec = cls.audit_billing_entitlements(workspace_root, target)
        entitlements = spec.get("features", {})
        rules = spec.get("rules", {})
        allowed = bool(entitlements.get(feat, False) or rules.get(feat, False))
        tier_label = spec.get("canonical_name") or spec.get("tier_name") or "Plan"
        reason = f"Feature '{feat}' is {'granted' if allowed else 'not granted'} under {tier_label} entitlements."

        return {
            "feature": feat,
            "action": feat,
            "allowed": allowed,
            "permitted": allowed,
            "tier": spec["tier"],
            "tier_name": tier_label,
            "canonical_name": tier_label,
            "reason": reason,
            "enforcement": "STRICT_RBAC"
        }

    @classmethod
    def generate_license(
        cls,
        workspace_root: Path,
        tier: str,
        tenant_id: str = "tenant_community_default",
        tenant_name: Optional[str] = None,
        seats: Optional[int] = None,
        worktrees: Optional[int] = None,
        audits: Optional[int] = None,
        custom_features: Optional[Dict[str, bool]] = None,
        payment_reference: Optional[str] = None,
        expires_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Mints and cryptographically signs a tenant license file for any tier.
        """
        workspace_root = Path(workspace_root).resolve()
        spec = cls.get_tier_spec(tier, workspace_root)
        tier_id = spec["tier_id"]
        canonical_name = spec["canonical_name"]

        now = datetime.now(timezone.utc)
        issued_at = now.isoformat()
        expires_at = None
        if expires_days:
            from datetime import timedelta
            expires_at = (now + timedelta(days=expires_days)).isoformat()

        t_name = tenant_name or tenant_id.replace("_", " ").title()
        eff_seats = seats if seats is not None else spec["included_seats"]
        eff_worktrees = worktrees if worktrees is not None else spec["included_concurrent_worktrees"]
        eff_audits = audits if audits is not None else spec["included_pr_audits_monthly"]

        features = dict(spec["features"])
        if custom_features:
            features.update(custom_features)

        raw_id_seed = f"{tier_id}_{tenant_id}_{issued_at}"
        lic_suffix = hashlib.sha256(raw_id_seed.encode("utf-8")).hexdigest()[:12]
        license_id = f"lic_{tier_id}_{lic_suffix}"

        payload = {
            "license_id": license_id,
            "tenant_id": tenant_id,
            "tenant_name": t_name,
            "tier": tier_id,
            "tier_name": canonical_name,
            "base_price_monthly_usd": spec["base_price_monthly_usd"],
            "included_seats": eff_seats,
            "included_concurrent_worktrees": eff_worktrees,
            "included_pr_audits_monthly": eff_audits,
            "entitled_features": features,
            "payment_reference": payment_reference,
            "issued_at": issued_at,
            "expires_at": expires_at
        }

        serialized = json.dumps(payload, sort_keys=True)
        sig = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        payload["signature_sha256"] = sig

        merkle_block_id = None
        MerkleEngineClass = _get_merkle_engine()
        if MerkleEngineClass:
            try:
                seal = MerkleEngineClass.record_state(
                    workspace_root=workspace_root,
                    agent_id="agent_commercial_packager_provisioner",
                    action=f"MINT_LICENSE_{tier_id.upper()}",
                    step_id="step_license_minting",
                    changed_files=[license_id]
                )
                merkle_block_id = seal.get("block_id")
            except Exception:
                pass
        payload["merkle_block_id"] = merkle_block_id

        return payload

    @classmethod
    def install_license(
        cls,
        workspace_root: Path,
        license_data: Dict[str, Any],
        target_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Installs a minted license into active workspace .nb/context/tenant_license.json
        and updates context_ledger.yaml project tier accordingly.
        """
        workspace_root = Path(workspace_root).resolve()
        ctx_dir = workspace_root / ".nb" / "context"
        ctx_dir.mkdir(parents=True, exist_ok=True)

        dest_file = target_path or (ctx_dir / "tenant_license.json")
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        content = json.dumps(license_data, indent=2)
        dest_file.write_text(content, encoding="utf-8")

        alias_file = workspace_root / ".nb" / "tenant_license.json"
        try:
            alias_file.write_text(content, encoding="utf-8")
        except Exception:
            pass

        tier = license_data.get("tier", "plan_free")
        for ledger_name in ["context_ledger.yaml", "context_ledger.public.yaml"]:
            ledger_path = ctx_dir / "ledger" / ledger_name
            if ledger_path.exists():
                try:
                    lines = ledger_path.read_text(encoding="utf-8").splitlines()
                    new_lines = []
                    project_seen = False
                    tier_updated = False
                    for line in lines:
                        if line.strip().startswith("project:"):
                            project_seen = True
                            new_lines.append(line)
                            continue
                        if project_seen and line.strip().startswith("tier:"):
                            new_lines.append(f"  tier: \"{tier}\"")
                            tier_updated = True
                            project_seen = False
                            continue
                        if project_seen and not line.startswith("  "):
                            new_lines.append(f"  tier: \"{tier}\"")
                            tier_updated = True
                            project_seen = False
                        new_lines.append(line)
                    if not tier_updated:
                        new_lines.append(f"tier: \"{tier}\"")
                    ledger_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                except Exception:
                    pass

        return {
            "status": "INSTALLED",
            "installed_path": str(dest_file),
            "tier": tier,
            "tenant_id": license_data.get("tenant_id"),
            "license_id": license_data.get("license_id"),
            "signature_sha256": license_data.get("signature_sha256")
        }

    @classmethod
    def get_active_license(cls, workspace_root: Path) -> Dict[str, Any]:
        """
        Retrieves the active workspace license, checking .nb/context/tenant_license.json
        and fallback candidates.
        """
        workspace_root = Path(workspace_root).resolve()
        candidates = [
            workspace_root / ".nb" / "context" / "tenant_license.json",
            workspace_root / ".nb" / "tenant_license.json",
            workspace_root / "tenant_license.json",
            workspace_root / ".percipience_license.json",
            workspace_root / ".nb" / "context" / "PERCIPIENCE_LICENSE.json",
            workspace_root / ".nb" / "PERCIPIENCE_LICENSE.json"
        ]
        for c in candidates:
            if c.exists() and c.is_file():
                try:
                    data = json.loads(c.read_text(encoding="utf-8"))
                    data["source_path"] = str(c)
                    data["is_installed"] = True
                    return data
                except Exception:
                    pass

        spec = cls.get_tier_spec("plan_free", workspace_root)
        return {
            "license_id": "lic_default_free",
            "tenant_id": "tenant_community_default",
            "tenant_name": "Free Community Tier (Unlicensed)",
            "tier": "plan_free",
            "tier_name": spec["canonical_name"],
            "base_price_monthly_usd": 0,
            "included_seats": 1,
            "included_concurrent_worktrees": 1,
            "included_pr_audits_monthly": 500,
            "entitled_features": spec["features"],
            "source_path": None,
            "is_installed": False
        }

    @classmethod
    def self_generate_license_after_payment(
        cls,
        workspace_root: Path,
        payment_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Autonomous post-payment hook (Stripe / checkout webhook integration).
        Receives payment confirmation, mints the paid tier license with payment reference,
        installs it into the active workspace, and logs cryptographic Merkle proof.
        """
        workspace_root = Path(workspace_root).resolve()
        payment_id = payment_payload.get("payment_id") or payment_payload.get("payment_intent_id") or payment_payload.get("id") or f"pay_{hashlib.sha256(str(datetime.now(timezone.utc)).encode()).hexdigest()[:10]}"
        tenant_id = payment_payload.get("tenant_id") or payment_payload.get("customer_id") or "tenant_paid_customer"
        tenant_name = payment_payload.get("tenant_name") or payment_payload.get("customer_name")
        raw_tier = payment_payload.get("tier") or payment_payload.get("plan") or "plan_team"
        custom_seats = payment_payload.get("seats")
        custom_worktrees = payment_payload.get("worktrees")
        custom_audits = payment_payload.get("audits")

        license_data = cls.generate_license(
            workspace_root=workspace_root,
            tier=raw_tier,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            seats=custom_seats,
            worktrees=custom_worktrees,
            audits=custom_audits,
            payment_reference=payment_id
        )

        install_res = cls.install_license(workspace_root, license_data)

        audit_file = workspace_root / ".nb" / "context" / "ledger" / "payment_license_audit.jsonl"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "POST_PAYMENT_LICENSE_SELF_GENERATED",
            "payment_id": payment_id,
            "tenant_id": tenant_id,
            "tier": license_data["tier"],
            "license_id": license_data["license_id"],
            "signature": license_data["signature_sha256"]
        }
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry) + "\n")

        return {
            "status": "SUCCESS",
            "action": "PAYMENT_FULFILLED_LICENSE_MINTED",
            "license": license_data,
            "installation": install_res,
            "audit_entry": audit_entry
        }
