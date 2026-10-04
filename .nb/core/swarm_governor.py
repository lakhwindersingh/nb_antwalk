"""
Percipience Swarm Governor & Hierarchical Authority Tree Engine (CAP-30)
Enforces a 4-level organizational hierarchy across autonomous agents to prevent
rogue subagent spawning, unauthorized privilege escalation, and role usurpation.
"""

from enum import IntEnum
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class AuthorityLevel(IntEnum):
    """Hierarchical authority tiers for agents and human operators."""
    GATEKEEPER_SENTINEL = 1   # Can veto/quarantine/halt; cannot author application code
    SPECIALIST_WORKER = 2     # Can edit module code/tests; cannot merge PRs or mutate wire contracts
    DOMAIN_ARCHITECT = 3      # Can edit wire contracts/schemas and living docs; cannot seal Merkle genesis
    ORCHESTRATOR = 4          # Full platform authority: workflow execution, PR gate merge, Merkle genesis


class SwarmGovernor:
    """
    Supervises agent swarms, intercepts unauthorized child spawning,
    and enforces strict role-based capability boundaries.
    """

    MAX_SWARM_DEPTH = 2
    MAX_CONCURRENT_SUBAGENTS = 4

    # Registry mapping known agent roles to their base authority tier
    AGENT_TIER_REGISTRY: Dict[str, AuthorityLevel] = {
        # Level 4: Orchestrators
        "lead_architect": AuthorityLevel.ORCHESTRATOR,
        "pipeline_orchestrator": AuthorityLevel.ORCHESTRATOR,
        "platform_admin": AuthorityLevel.ORCHESTRATOR,
        "root": AuthorityLevel.ORCHESTRATOR,

        # Level 3: Domain Architects
        "agent_living_doc_architect": AuthorityLevel.DOMAIN_ARCHITECT,
        "contract_compatibility_checker": AuthorityLevel.DOMAIN_ARCHITECT,
        "agent_contract_compatibility_checker": AuthorityLevel.DOMAIN_ARCHITECT,

        # Level 2: Specialist Workers
        "agent_tester": AuthorityLevel.SPECIALIST_WORKER,
        "agent_request_formalizer": AuthorityLevel.SPECIALIST_WORKER,
        "ast_pruner": AuthorityLevel.SPECIALIST_WORKER,
        "platform.ast_pruner": AuthorityLevel.SPECIALIST_WORKER,
        "agent_quality_guard": AuthorityLevel.SPECIALIST_WORKER,
        "doc_drift_synchronizer": AuthorityLevel.SPECIALIST_WORKER,
        "agent_doc_drift_synchronizer": AuthorityLevel.SPECIALIST_WORKER,

        # Level 1: Gatekeepers & Sentinels
        "security_auditor": AuthorityLevel.GATEKEEPER_SENTINEL,
        "agent_dependency_cve_sentinel": AuthorityLevel.GATEKEEPER_SENTINEL,
        "dependency_cve_sentinel": AuthorityLevel.GATEKEEPER_SENTINEL,
        "flaky_test_detector": AuthorityLevel.GATEKEEPER_SENTINEL,
        "agent_flaky_test_detector": AuthorityLevel.GATEKEEPER_SENTINEL,
        "poisoning_sentinel": AuthorityLevel.GATEKEEPER_SENTINEL,
    }

    # Minimum authority required for critical actions
    ACTION_PERMISSION_MATRIX: Dict[str, AuthorityLevel] = {
        "SEAL_MERKLE_GENESIS": AuthorityLevel.ORCHESTRATOR,
        "MERGE_PR_GATE": AuthorityLevel.ORCHESTRATOR,
        "SEAL_BLOCK": AuthorityLevel.DOMAIN_ARCHITECT,
        "MODIFY_WIRE_CONTRACT": AuthorityLevel.DOMAIN_ARCHITECT,
        "SYNCHRONIZE_LIVING_DOCS": AuthorityLevel.DOMAIN_ARCHITECT,
        "EDIT_MODULE_CODE": AuthorityLevel.SPECIALIST_WORKER,
        "GENERATE_DIFF": AuthorityLevel.SPECIALIST_WORKER,
        "RUN_UNIT_TESTS": AuthorityLevel.SPECIALIST_WORKER,
        "VETO_QUARANTINE_PR": AuthorityLevel.GATEKEEPER_SENTINEL,
        "TRIGGER_SURGICAL_ROLLBACK": AuthorityLevel.GATEKEEPER_SENTINEL,
    }

    @classmethod
    def get_agent_authority(cls, agent_id: str) -> Dict[str, Any]:
        """Resolves the authority level for a given agent ID."""
        normalized = agent_id.lower().strip()
        level = cls.AGENT_TIER_REGISTRY.get(normalized, AuthorityLevel.SPECIALIST_WORKER)
        return {
            "agent_id": agent_id,
            "authority_level": int(level),
            "tier_name": level.name,
            "can_merge_pr": level >= AuthorityLevel.ORCHESTRATOR,
            "can_modify_contracts": level >= AuthorityLevel.DOMAIN_ARCHITECT,
            "can_edit_code": level >= AuthorityLevel.SPECIALIST_WORKER,
            "can_veto": level >= AuthorityLevel.GATEKEEPER_SENTINEL
        }

    @classmethod
    def authorize_action(
        cls,
        agent_id: str,
        action: str,
        module_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates whether the requesting agent has sufficient authority to execute the action.
        """
        agent_meta = cls.get_agent_authority(agent_id)
        agent_level = agent_meta["authority_level"]

        action_normalized = action.upper().strip()
        required_level = cls.ACTION_PERMISSION_MATRIX.get(action_normalized, AuthorityLevel.SPECIALIST_WORKER)

        # Gatekeepers have veto rights but cannot author code
        if agent_level == AuthorityLevel.GATEKEEPER_SENTINEL and action_normalized in ["EDIT_MODULE_CODE", "GENERATE_DIFF"]:
            return {
                "authorized": False,
                "status": "DENIED_ROLE_CONFLICT",
                "agent_id": agent_id,
                "action": action,
                "reason": "Gatekeeper sentinels are strictly read-only auditors and cannot author code."
            }

        authorized = agent_level >= int(required_level)
        return {
            "authorized": authorized,
            "status": "AUTHORIZED" if authorized else "DENIED_INSUFFICIENT_AUTHORITY",
            "agent_id": agent_id,
            "action": action,
            "agent_tier": agent_meta["tier_name"],
            "required_tier": required_level.name,
            "module_id": module_id
        }

    @classmethod
    def intercept_spawn(
        cls,
        parent_id: str,
        child_id: str,
        current_depth: int = 0,
        active_subagent_count: int = 0
    ) -> Dict[str, Any]:
        """
        Intercepts subagent spawning requests to enforce recursion limits and hierarchy trees.
        A parent cannot spawn a child with higher authority, nor exceed max swarm depth.
        """
        if current_depth >= cls.MAX_SWARM_DEPTH:
            return {
                "allowed": False,
                "status": "RECURSION_DEPTH_EXCEEDED",
                "parent_id": parent_id,
                "child_id": child_id,
                "reason": f"Swarm recursion depth limit ({cls.MAX_SWARM_DEPTH}) exceeded."
            }

        if active_subagent_count >= cls.MAX_CONCURRENT_SUBAGENTS:
            return {
                "allowed": False,
                "status": "SWARM_CAPACITY_EXCEEDED",
                "parent_id": parent_id,
                "child_id": child_id,
                "reason": f"Active concurrent subagent limit ({cls.MAX_CONCURRENT_SUBAGENTS}) reached."
            }

        parent_meta = cls.get_agent_authority(parent_id)
        child_meta = cls.get_agent_authority(child_id)

        # Hierarchy invariant: Child authority cannot exceed parent authority
        if child_meta["authority_level"] > parent_meta["authority_level"]:
            return {
                "allowed": False,
                "status": "ROLE_USURPATION_BLOCKED",
                "parent_id": parent_id,
                "child_id": child_id,
                "reason": f"Parent tier ({parent_meta['tier_name']}) cannot spawn higher-tier child ({child_meta['tier_name']})."
            }

        return {
            "allowed": True,
            "status": "SPAWN_PERMITTED",
            "parent_id": parent_id,
            "child_id": child_id,
            "parent_tier": parent_meta["tier_name"],
            "child_tier": child_meta["tier_name"],
            "depth": current_depth + 1
        }
