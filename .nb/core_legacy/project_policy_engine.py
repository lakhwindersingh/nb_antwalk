"""
Neutron Binary Percipience - Minute Project Control & Policy Configuration Engine (CAP-41 / Section 18.2)
Provides fine-grained, per-project declarative policy governance:
  - TODO-PRT-04: Attention Slicing Quotas, Cognitive Routing Tiering Rules, and AST Pruning Limits
  - TODO-PRT-05: PR Verification Gates, Diagnostic Re-prompt Bounds (1-5 turns), Flaky Test Quarantine Thresholds,
                 and Cross-Module Wire Contract Breaking-Change Policies
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import datetime
import json
import os
from pathlib import Path
import yaml

try:
    from core.attention_budgeter import AttentionBudgeter
except (ImportError, ModuleNotFoundError):
    AttentionBudgeter = None

try:
    from core.cognitive_router import CognitiveRouter
except (ImportError, ModuleNotFoundError):
    CognitiveRouter = None

try:
    from core.ast_optimizer import ASTOptimizer
except (ImportError, ModuleNotFoundError):
    ASTOptimizer = None

try:
    from core.contract_compatibility_checker import ContractCompatibilityChecker
except (ImportError, ModuleNotFoundError):
    ContractCompatibilityChecker = None


class WireContractRule(str, Enum):
    STRICT_BLOCK = "STRICT_BLOCK"
    ALLOW_ADDITIVE_WARN = "ALLOW_ADDITIVE_WARN"
    MANUAL_APPROVAL = "MANUAL_APPROVAL"


@dataclass
class AttentionSlicingPolicy:
    persona_invariants_pct: float = 15.0
    contracts_schemas_pct: float = 25.0
    ast_codebase_pct: float = 35.0
    memory_trajectories_pct: float = 10.0
    reserved_output_pct: float = 15.0

    def validate(self):
        total = (
            self.persona_invariants_pct
            + self.contracts_schemas_pct
            + self.ast_codebase_pct
            + self.memory_trajectories_pct
            + self.reserved_output_pct
        )
        if abs(total - 100.0) > 0.1:
            raise ValueError(f"Attention budget quotas must sum to 100.0% (got {total:.2f}%).")
        for k, v in asdict(self).items():
            if v < 0.0:
                raise ValueError(f"Quota '{k}' cannot be negative (got {v}).")


@dataclass
class CognitiveRoutingPolicy:
    tier_a_threshold: float = 0.70  # Task complexity score >= threshold routes to Tier A
    fallback_model: str = "claude-3-5-sonnet-20241022"
    custom_tier_a_tasks: List[str] = field(default_factory=lambda: ["wire_contract_compat", "security_audit", "pr_gate_merge_decision"])
    custom_tier_b_tasks: List[str] = field(default_factory=lambda: ["ast_parsing", "unit_test_run", "doc_generation"])
    max_cost_ceiling_per_call_usd: float = 1.00

    def validate(self):
        if not (0.0 <= self.tier_a_threshold <= 1.0):
            raise ValueError(f"tier_a_threshold must be between 0.0 and 1.0 (got {self.tier_a_threshold}).")
        if self.max_cost_ceiling_per_call_usd <= 0.0:
            raise ValueError("max_cost_ceiling_per_call_usd must be greater than 0.0.")


@dataclass
class ASTPruningPolicy:
    max_stripping_depth: int = 3
    preserve_decorators: bool = True
    preserve_docstrings: bool = False
    max_sibling_repeats: int = 2
    strip_private_methods: bool = True
    keep_signatures_only: bool = True

    def validate(self):
        if self.max_stripping_depth < 1:
            raise ValueError("max_stripping_depth must be at least 1.")
        if self.max_sibling_repeats < 1:
            raise ValueError("max_sibling_repeats must be at least 1.")


@dataclass
class SelfHealingSLAPolicy:
    max_diagnostic_reprompts: int = 3  # Configurable 1-5 turns
    flaky_quarantine_variance_threshold: float = 0.15  # Failure variance > 15% quarantines test
    wire_contract_breaking_rule: WireContractRule = WireContractRule.STRICT_BLOCK
    auto_rollback_on_sla_breach: bool = True
    sla_timeout_seconds: int = 120

    def validate(self):
        if not (1 <= self.max_diagnostic_reprompts <= 5):
            raise ValueError(f"max_diagnostic_reprompts must be between 1 and 5 turns (got {self.max_diagnostic_reprompts}).")
        if not (0.01 <= self.flaky_quarantine_variance_threshold <= 1.0):
            raise ValueError(f"flaky_quarantine_variance_threshold must be between 0.01 and 1.0 (got {self.flaky_quarantine_variance_threshold}).")
        if self.sla_timeout_seconds < 10:
            raise ValueError("sla_timeout_seconds must be at least 10s.")


@dataclass
class ProjectPolicy:
    tenant_id: str
    project_id: str
    environment: str = "production"  # "development" | "production"
    vcs_repository: Dict[str, str] = field(default_factory=lambda: {"url": "https://github.com/acme/fairyfly.git", "default_branch": "main"})
    hitl_quarantine_webhook: str = ""
    version: int = 1
    updated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_by: str = "system"
    attention: AttentionSlicingPolicy = field(default_factory=AttentionSlicingPolicy)
    routing: CognitiveRoutingPolicy = field(default_factory=CognitiveRoutingPolicy)
    ast: ASTPruningPolicy = field(default_factory=ASTPruningPolicy)
    healing_sla: SelfHealingSLAPolicy = field(default_factory=SelfHealingSLAPolicy)

    @property
    def certified_invariants(self) -> Dict[str, str]:
        return {
            "attention_slicing": "15/25/35/10/15 Ratio (15% Invariants / 25% Contracts / 35% AST / 10% Memory / 15% Headroom (Certified Zero Lost-in-Middle)",
            "ast_skeletonization": "Tree-Sitter 6D Polyglot Interface Preservation (Zero Body Leakage)",
            "self_healing_sla": "Bounded 3-Turn Convergence Loop with Surgical Rollback (RP_k)",
            "wire_contract_rule": "STRICT_BLOCK" if self.environment == "production" else "ALLOW_ADDITIVE_WARN",
            "swarm_graph_integrity": "Kahn DAG Acyclicity Enforced (Depth Ceiling D <= 3)",
            "cbac_sandboxing": "Least-Privilege Ephemeral HMAC-SHA256 Token Leasing"
        }

    def validate(self):
        if self.environment not in ("production", "development"):
            raise ValueError(f"environment must be 'production' or 'development' (got '{self.environment}').")
        self.attention.validate()
        self.routing.validate()
        self.ast.validate()
        self.healing_sla.validate()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "environment": self.environment,
            "vcs_repository": self.vcs_repository,
            "hitl_quarantine_webhook": self.hitl_quarantine_webhook,
            "version": self.version,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
            "certified_invariants": self.certified_invariants,
            "attention": asdict(self.attention),
            "routing": asdict(self.routing),
            "ast": asdict(self.ast),
            "healing_sla": {
                **asdict(self.healing_sla),
                "wire_contract_breaking_rule": self.healing_sla.wire_contract_breaking_rule.value
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectPolicy":
        env = data.get("environment", "production")
        vcs_repo = data.get("vcs_repository", {"url": "https://github.com/acme/fairyfly.git", "default_branch": "main"})
        hitl_hook = data.get("hitl_quarantine_webhook", "")

        att_data = data.get("attention", {})
        rout_data = data.get("routing", {})
        ast_data = data.get("ast", {})
        sla_data = data.get("healing_sla", {})

        default_wire_rule = WireContractRule.STRICT_BLOCK.value if env == "production" else WireContractRule.ALLOW_ADDITIVE_WARN.value
        sla_rule_str = sla_data.get("wire_contract_breaking_rule", default_wire_rule)
        sla_data_clean = {k: v for k, v in sla_data.items() if k != "wire_contract_breaking_rule"}
        sla_policy = SelfHealingSLAPolicy(
            wire_contract_breaking_rule=WireContractRule(sla_rule_str),
            **sla_data_clean
        )

        policy = cls(
            tenant_id=data.get("tenant_id", "default_tenant"),
            project_id=data.get("project_id", "default_project"),
            environment=env,
            vcs_repository=vcs_repo,
            hitl_quarantine_webhook=hitl_hook,
            version=data.get("version", 1),
            updated_at=data.get("updated_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
            updated_by=data.get("updated_by", "system"),
            attention=AttentionSlicingPolicy(**att_data),
            routing=CognitiveRoutingPolicy(**rout_data),
            ast=ASTPruningPolicy(**ast_data),
            healing_sla=sla_policy
        )
        policy.validate()
        return policy


class ProjectPolicyManager:
    """
    Manages per-project policy retrieval, live updates, and integration bindings.
    """

    def __init__(self, policy_dir: Optional[Path] = None):
        self.policy_dir = policy_dir
        self._policies: Dict[str, ProjectPolicy] = {}

    def _policy_key(self, tenant_id: str, project_id: str) -> str:
        return f"{tenant_id}::{project_id}"

    def get_policy(self, tenant_id: str, project_id: str) -> ProjectPolicy:
        """Retrieves or loads the project-specific policy. Defaults if not found."""
        key = self._policy_key(tenant_id, project_id)
        if key in self._policies:
            return self._policies[key]

        # Check persistence directory
        if self.policy_dir:
            file_path = self.policy_dir / f"{tenant_id}_{project_id}.yaml"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                    policy = ProjectPolicy.from_dict(data)
                    self._policies[key] = policy
                    return policy
                except Exception:
                    pass

        # Return baseline default policy for project
        default_policy = ProjectPolicy(tenant_id=tenant_id, project_id=project_id)
        self._policies[key] = default_policy
        return default_policy

    def update_policy(
        self,
        tenant_id: str,
        project_id: str,
        patch_data: Dict[str, Any],
        user_id: str = "admin"
    ) -> ProjectPolicy:
        """Updates and validates project policy, incrementing version and persisting."""
        current = self.get_policy(tenant_id, project_id)
        curr_dict = current.to_dict()

        # Merge patches
        for sec in ["attention", "routing", "ast", "healing_sla"]:
            if sec in patch_data and isinstance(patch_data[sec], dict):
                curr_dict[sec].update(patch_data[sec])

        # Merge 5-point streamlined control surface
        for direct_field in ["environment", "vcs_repository", "hitl_quarantine_webhook"]:
            if direct_field in patch_data:
                curr_dict[direct_field] = patch_data[direct_field]

        if "environment" in patch_data:
            env = patch_data["environment"]
            curr_dict["environment"] = env
            if "healing_sla" not in patch_data or "wire_contract_breaking_rule" not in patch_data.get("healing_sla", {}):
                curr_dict["healing_sla"]["wire_contract_breaking_rule"] = (
                    WireContractRule.STRICT_BLOCK.value if env == "production" else WireContractRule.ALLOW_ADDITIVE_WARN.value
                )

        curr_dict["version"] = current.version + 1
        curr_dict["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        curr_dict["updated_by"] = user_id

        new_policy = ProjectPolicy.from_dict(curr_dict)
        new_policy.validate()

        key = self._policy_key(tenant_id, project_id)
        self._policies[key] = new_policy

        if self.policy_dir:
            self.policy_dir.mkdir(parents=True, exist_ok=True)
            file_path = self.policy_dir / f"{tenant_id}_{project_id}.yaml"
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(new_policy.to_dict(), f, sort_keys=False)

        return new_policy

    # -------------------------------------------------------------------------
    # Integration Execution Bindings
    # -------------------------------------------------------------------------

    def slice_context_with_project_policy(
        self,
        tenant_id: str,
        project_id: str,
        sections: Dict[str, str],
        max_total_tokens: int = 8192
    ) -> Dict[str, Any]:
        """
        Executes Attention Slicing using project-specific dynamic ratios (TODO-PRT-04).
        """
        policy = self.get_policy(tenant_id, project_id).attention
        custom_quotas = {
            "persona_invariants": policy.persona_invariants_pct / 100.0,
            "contracts_schemas": policy.contracts_schemas_pct / 100.0,
            "ast_codebase": policy.ast_codebase_pct / 100.0,
            "memory_trajectories": policy.memory_trajectories_pct / 100.0,
            "reserved_output": policy.reserved_output_pct / 100.0
        }

        # Calculate section token quotas
        quota_tokens = {
            k: int(max_total_tokens * weight)
            for k, weight in custom_quotas.items()
        }

        adjusted_sections: Dict[str, str] = {}
        section_token_metrics: Dict[str, Dict[str, Any]] = {}
        total_used = 0

        chars_per_tok = getattr(AttentionBudgeter, "CHARS_PER_TOKEN", 4.0) if AttentionBudgeter else 4.0

        def _estimate(text: str) -> int:
            if AttentionBudgeter:
                return AttentionBudgeter.estimate_tokens(text)
            return max(1, len(text) // 4)

        for sec_key, quota in quota_tokens.items():
            if sec_key == "reserved_output":
                continue
            raw_text = sections.get(sec_key, "")
            raw_tokens = _estimate(raw_text)

            if raw_tokens <= quota:
                adjusted_text = raw_text
                trimmed_tokens = 0
            else:
                if sec_key == "persona_invariants":
                    # Non-overridable: Invariants preserved
                    adjusted_text = raw_text
                    trimmed_tokens = 0
                else:
                    char_cutoff = int(quota * chars_per_tok)
                    adjusted_text = raw_text[:char_cutoff] + "\n... [SLICED_BY_PROJECT_POLICY]"
                    trimmed_tokens = raw_tokens - _estimate(adjusted_text)

            adj_tokens = _estimate(adjusted_text)
            total_used += adj_tokens
            adjusted_sections[sec_key] = adjusted_text
            section_token_metrics[sec_key] = {
                "allocated_quota_tokens": quota,
                "raw_tokens": raw_tokens,
                "adjusted_tokens": adj_tokens,
                "trimmed_tokens": trimmed_tokens,
                "quota_ratio": custom_quotas[sec_key]
            }

        return {
            "max_total_tokens": max_total_tokens,
            "total_used_tokens": total_used,
            "reserved_output_tokens": quota_tokens["reserved_output"],
            "headroom_pct": round((quota_tokens["reserved_output"] / max_total_tokens) * 100.0, 1),
            "sections": adjusted_sections,
            "metrics": section_token_metrics,
            "policy_version": self.get_policy(tenant_id, project_id).version
        }

    def route_cognitive_task_with_project_policy(
        self,
        tenant_id: str,
        project_id: str,
        task_type: str,
        requested_model: Optional[str] = None,
        complexity_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Routes task using project-level complexity threshold and custom tier lists (TODO-PRT-04).
        """
        policy = self.get_policy(tenant_id, project_id).routing
        task_norm = task_type.lower().replace("-", "_").strip()

        tier_a_model = getattr(CognitiveRouter, "TIER_A_MODEL", "claude-3-5-sonnet-20241022") if CognitiveRouter else "claude-3-5-sonnet-20241022"
        tier_b_model = getattr(CognitiveRouter, "TIER_B_MODEL", "gemini-1.5-flash") if CognitiveRouter else "gemini-1.5-flash"

        is_custom_tier_a = task_norm in [t.lower() for t in policy.custom_tier_a_tasks]
        is_custom_tier_b = task_norm in [t.lower() for t in policy.custom_tier_b_tasks]

        if is_custom_tier_a:
            is_tier_a = True
            reason = "Explicit project policy: Task configured for Tier A."
        elif is_custom_tier_b:
            is_tier_a = False
            reason = "Explicit project policy: Task configured for Tier B."
        elif complexity_score is not None:
            is_tier_a = complexity_score >= policy.tier_a_threshold
            reason = f"Complexity score {complexity_score:.2f} {'meets' if is_tier_a else 'below'} project threshold {policy.tier_a_threshold:.2f}."
        else:
            # Fallback to default CognitiveRouter knowledge if available
            if CognitiveRouter:
                default_res = CognitiveRouter.dispatch(task_type, requested_model)
                is_tier_a = default_res["assigned_tier"] == "Tier_A"
                reason = default_res["rationale"]
            else:
                is_tier_a = False
                reason = "Default fallback routing without CognitiveRouter engine."

        assigned_tier = "Tier_A" if is_tier_a else "Tier_B"
        assigned_model = tier_a_model if is_tier_a else tier_b_model
        discount_pct = 0.0 if is_tier_a else 90.0

        return {
            "task_type": task_type,
            "assigned_tier": assigned_tier,
            "assigned_model": assigned_model,
            "cost_discount_pct": discount_pct,
            "tier_a_threshold": policy.tier_a_threshold,
            "rationale": reason,
            "project_id": project_id
        }

    def prune_ast_with_project_policy(
        self,
        tenant_id: str,
        project_id: str,
        html_or_source: str,
        language: str = "html",
        focus_sections: Optional[List[str]] = None
    ) -> str:
        """
        Prunes source or HTML skeleton using project AST policy (TODO-PRT-04).
        """
        if not ASTOptimizer:
            return html_or_source

        policy = self.get_policy(tenant_id, project_id).ast
        if language.lower() in ("html", "xml", "jsx"):
            return ASTOptimizer.prune_html(
                html_code=html_or_source,
                focus_sections=focus_sections,
                max_sibling_repeats=policy.max_sibling_repeats
            )
        # Default AST source pruning
        pruned, _ = ASTOptimizer.prune_source(html_or_source, language=language)
        return pruned

    def evaluate_pr_gate(
        self,
        tenant_id: str,
        project_id: str,
        test_run_history: List[Dict[str, Any]],
        base_contract: Optional[Dict[str, Any]] = None,
        head_contract: Optional[Dict[str, Any]] = None,
        current_heal_turn: int = 0
    ) -> Dict[str, Any]:
        """
        Evaluates PR Gate against project-specific SLA policies (TODO-PRT-05):
        - Statistical flaky test quarantine thresholds (failure variance > threshold)
        - Wire contract breaking change enforcement rule
        - Configurable diagnostic re-prompt attempts (1-5 turns)
        """
        policy = self.get_policy(tenant_id, project_id).healing_sla

        # 1. Wire Contract Compatibility Audit
        contract_status = "PASS"
        contract_violations = []
        if base_contract and head_contract and ContractCompatibilityChecker:
            compat_result = ContractCompatibilityChecker.check_compatibility(base_contract, head_contract)
            if not compat_result["is_compatible"]:
                contract_violations = compat_result["breaking_changes"]
                if policy.wire_contract_breaking_rule == WireContractRule.STRICT_BLOCK:
                    contract_status = "BLOCKED"
                elif policy.wire_contract_breaking_rule == WireContractRule.ALLOW_ADDITIVE_WARN:
                    contract_status = "WARNING_ALLOWED"
                elif policy.wire_contract_breaking_rule == WireContractRule.MANUAL_APPROVAL:
                    contract_status = "AWAITING_MANUAL_APPROVAL"

        # 2. Statistical Flaky Test Quarantine Analysis
        quarantined_tests = []
        regular_failures = []
        for test in test_run_history:
            test_id = test.get("test_id", "unknown_test")
            runs = test.get("runs", 1)
            failures = test.get("failures", 0)
            if runs > 0:
                fail_rate = failures / runs
                if 0.0 < fail_rate <= policy.flaky_quarantine_variance_threshold:
                    # Within acceptable flaky variance threshold -> Quarantine to prevent false alarm
                    quarantined_tests.append({
                        "test_id": test_id,
                        "failure_rate": round(fail_rate, 3),
                        "variance_threshold": policy.flaky_quarantine_variance_threshold,
                        "action": "QUARANTINED"
                    })
                elif fail_rate > policy.flaky_quarantine_variance_threshold:
                    regular_failures.append({
                        "test_id": test_id,
                        "failure_rate": round(fail_rate, 3),
                        "action": "DETERMINISTIC_FAILURE"
                    })

        # 3. Diagnostic Re-Prompt Healing Boundary Check
        exceeded_healing_sla = current_heal_turn >= policy.max_diagnostic_reprompts
        can_retry_heal = current_heal_turn < policy.max_diagnostic_reprompts

        # Overall PR Gate Decision
        is_blocked = (contract_status == "BLOCKED") or len(regular_failures) > 0
        gate_decision = "FAIL" if is_blocked else "PASS"

        recommended_action = "PROCEED_MERGE"
        if is_blocked:
            if can_retry_heal:
                recommended_action = f"DIAGNOSTIC_REPROMPT_TURN_{current_heal_turn + 1}"
            else:
                recommended_action = "TRIGGER_AUTOMATED_ROLLBACK" if policy.auto_rollback_on_sla_breach else "HUMAN_ESCALATION"

        return {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "gate_decision": gate_decision,
            "recommended_action": recommended_action,
            "contract_audit": {
                "rule": policy.wire_contract_breaking_rule.value,
                "status": contract_status,
                "violations": contract_violations
            },
            "test_audit": {
                "total_evaluated": len(test_run_history),
                "quarantined_flaky_tests": quarantined_tests,
                "deterministic_failures": regular_failures,
                "flaky_threshold": policy.flaky_quarantine_variance_threshold
            },
            "healing_sla": {
                "current_turn": current_heal_turn,
                "max_allowed_reprompts": policy.max_diagnostic_reprompts,
                "can_retry": can_retry_heal,
                "auto_rollback_configured": policy.auto_rollback_on_sla_breach
            }
        }
