#!/usr/bin/env python3
"""
Synchronizes active plan MANIFEST.yaml files with autonomous execution specifications,
re-entrant lifecycle hooks, and specification contracts from templates.
"""

from pathlib import Path
import yaml
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
PLAN_ROOT = Path(__file__).resolve().parents[1]

ACTIVE_PLAN_SPECS = {
    "l1/vscode-plugin": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_vscode_lsp_architect",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module l1_vscode_extension",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_ide_plugins_space.py -v",
            "handover": "percipience handoff issue --from agent_vscode_lsp_architect --to agent_qa_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/lsp_percipience_bridge.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/vscode_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/ide_boundary_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/zero_trust_sandbox_rules.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "l1/intellij-pycharm-plugin": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_jetbrains_psi_architect",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module l1_jetbrains_plugin",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_ide_plugins_space.py -v",
            "handover": "percipience handoff issue --from agent_jetbrains_psi_architect --to agent_qa_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/jetbrains_air_ide_bridge.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/psi_ast_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/psi_threading_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/zero_trust_sandbox_rules.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "l1/npx-installer": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_npx_distribution_engineer",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module l1_npx_bootstrap",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_play3_suite.py -v",
            "handover": "percipience handoff issue --from agent_npx_distribution_engineer --to agent_qa_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/npx_manifest_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/cli_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/npx_zero_dependency_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/reproducible_tarball_attestations.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "l1/saas-portal-domain": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_saas_portal_architect",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module l1_saas_portal",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_portal_commercial_provisioning.py workplace/tests/test_portal_observability_auth.py workplace/tests/test_portal_swarm_governance.py -v",
            "handover": "percipience handoff issue --from agent_saas_portal_architect --to agent_qa_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/saas_portal_rpc_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/portal_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/multitenant_isolation_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/portal_rbac_security_rules.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "l1/tiered-wheel-packaging": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_packaging_release_engineer",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module l1_wheel_packaging",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_commercial_license_management.py workplace/tests/test_tier3_enterprise_launch.py -v",
            "handover": "percipience handoff issue --from agent_packaging_release_engineer --to agent_qa_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/wheel_tier_spec_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/wheel_attestation_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/licensing_boundary_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/wheel_signing_attestations.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "master/cloud-agnostic-infrastructure-substrate": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_infrastructure_mesh_architect",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module master_infrastructure",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_enterprise_cicd_sandboxing.py workplace/tests/test_container_plan_executor.py -v",
            "handover": "percipience handoff issue --from agent_infrastructure_mesh_architect --to agent_security_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/cloud_mesh_substrate_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/infra_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/cloud_agnostic_substrate_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/zero_trust_mesh_network_rules.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "master/enterprise-ui-design-system": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_ui_design_system_architect",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module master_ui_design_system",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_ui_design_system.py -v",
            "handover": "percipience handoff issue --from agent_ui_design_system_architect --to agent_qa_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/ui_token_design_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/component_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/wcag_aa_accessibility_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/design_token_immutability.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "master/parent-master-free-plan": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_community_framework_architect",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module master_parent_free",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_project_policy_engine.py workplace/tests/test_solution_simplification.py -v",
            "handover": "percipience handoff issue --from agent_community_framework_architect --to agent_governance_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/free_tier_capability_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/community_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/community_tier_isolation_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/open_source_governance_rules.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "master/parent-master-plan": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_parent_framework_architect",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module master_parent_framework",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_agent_memory_engine.py workplace/tests/test_few_shot_retriever.py workplace/tests/test_self_reflection_engine.py -v",
            "handover": "percipience handoff issue --from agent_parent_framework_architect --to agent_governance_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/master_parent_framework_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/framework_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/parent_framework_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/zero_trust_mesh_security_rules.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "master/plan-assessment": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_plan_assessment_evaluator",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module master_plan_assessment",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_plan_bundle_imports.py workplace/tests/test_runtime_guardrails.py workplace/tests/test_agent_capability_guard.py -v",
            "handover": "percipience handoff issue --from agent_plan_assessment_evaluator --to agent_governance_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/plan_assessment_rubric_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/assessment_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/plan_assessment_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/deterministic_scoring_rules.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "master/security-mesh": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_zero_trust_security_architect",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module master_security_mesh",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_security_mesh.py workplace/tests/test_tenant_provisioning.py -v",
            "handover": "percipience handoff issue --from agent_zero_trust_security_architect --to agent_red_team_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/security_mesh_wire_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/auth_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/zero_trust_mesh_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/cryptographic_token_invariants.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "master/sequential-plan-orchestrator": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_orchestrator_core_engineer",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module master_orchestrator",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_dynamic_dag_orchestrator.py workplace/tests/test_plan_module_orchestrator.py workplace/tests/test_hitl_checkpoint_manager.py -v",
            "handover": "percipience handoff issue --from agent_orchestrator_core_engineer --to agent_qa_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/plan_orchestrator_wire_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/dag_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/acyclic_dag_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/state_transition_invariants.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
    "test": {
        "autonomous_execution": {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "specialist_agent": "agent_test_governance_architect",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
            "finops_metering": True,
        },
        "lifecycle_hooks": {
            "pre_spawn": "percipience worktree lease --module test_governance",
            "pre_execution": "percipience check --ast-prune --schema-lint",
            "post_execution": "pytest workplace/tests/test_master_test_plan.py workplace/tests/test_vulnerability_suite.py -v",
            "handover": "percipience handoff issue --from agent_test_governance_architect --to agent_red_team_sentinel",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal --worm-egress",
        },
        "specification_contracts": {
            "wire_contracts": [
                {
                    "path": ".nb/context/contracts/master_test_runner_contract.yaml",
                    "type": "RPC_OR_EVENT_STREAM",
                    "strict_mode": True,
                },
                {
                    "path": ".nb/context/contracts/test_telemetry_schema.json",
                    "type": "STATE_TELEMETRY",
                    "strict_mode": True,
                },
            ],
            "invariant_rules": [
                {
                    "path": ".nb/context/rules/test_pyramid_invariants.md",
                    "type": "ARCHITECTURAL_BOUNDARIES",
                },
                {
                    "path": ".nb/context/rules/zero_regression_security_rules.md",
                    "type": "PERFORMANCE_AND_SECURITY",
                },
            ],
        },
    },
}


def sync_manifest(plan_rel: str, spec: dict):
    manifest_file = PLAN_ROOT / plan_rel / "MANIFEST.yaml"
    if not manifest_file.exists():
        print(f"❌ Manifest not found: {manifest_file}")
        return False

    with open(manifest_file, "r", encoding="utf-8") as f:
        content = f.read()

    # If autonomous_execution is already present, don't double inject
    if "autonomous_execution:" in content:
        print(f"⏩ {plan_rel} already contains autonomous_execution, skipping injection.")
        return True

    # Build YAML snippet
    snippet_dict = {
        "autonomous_execution": spec["autonomous_execution"],
        "lifecycle_hooks": spec["lifecycle_hooks"],
        "specification_contracts": spec["specification_contracts"],
    }
    yaml_snippet = yaml.dump(snippet_dict, default_flow_style=False, sort_keys=False, allow_unicode=True, width=1000)

    # Insert right before 'file_versions:'
    target = "file_versions:"
    idx = content.find(target)
    if idx == -1:
        print(f"❌ Could not find '{target}' in {manifest_file}")
        return False

    new_content = content[:idx] + yaml_snippet + content[idx:]

    with open(manifest_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Injected autonomous capabilities into {plan_rel}/MANIFEST.yaml")
    return True


def main():
    print(f"🚀 Injecting autonomous execution specs into {len(ACTIVE_PLAN_SPECS)} active plans...")
    success = True
    for plan_rel, spec in ACTIVE_PLAN_SPECS.items():
        if not sync_manifest(plan_rel, spec):
            success = False
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
