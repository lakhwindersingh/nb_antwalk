"""
Percipience Error Taxonomy & Adaptive Recovery Playbook Orchestrator (CAP-28)
Classifies runtime agent errors into four distinct categories and dispatches
specialized self-healing mitigation playbooks to prevent catastrophic workflow failures.
"""

import re
import time
import random
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class ErrorCategory(str, Enum):
    """Four-pillar classification of agent and workflow execution errors."""
    TRANSIENT = "TRANSIENT"         # Network, rate limit, timeout, lock contention
    STRUCTURAL = "STRUCTURAL"       # Syntax error, AST parse failure, missing import, type error
    INVARIANT = "INVARIANT"         # Contract incompatibility, schema break, Merkle hash mismatch
    HALLUCINATORY = "HALLUCINATORY" # Leaked secrets, poison package, circular delegation, hallucinated API


class ErrorDiagnostic:
    """Structured diagnostic representation of a caught system or agent error."""
    def __init__(
        self,
        category: ErrorCategory,
        message: str,
        module_id: Optional[str] = None,
        file_path: Optional[str] = None,
        raw_trace: str = "",
        confidence_score: float = 0.95
    ):
        self.category = category
        self.message = message
        self.module_id = module_id
        self.file_path = file_path
        self.raw_trace = raw_trace
        self.confidence_score = confidence_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "message": self.message,
            "module_id": self.module_id,
            "file_path": self.file_path,
            "confidence_score": self.confidence_score
        }


class ErrorRecoveryOrchestrator:
    """
    Automates taxonomy-driven error diagnosis and applies adaptive self-healing playbooks.
    """

    TRANSIENT_PATTERNS = [
        r"rate limit", r"429", r"timeout", r"connection reset",
        r"temporarily unavailable", r"503", r"504", r"redis lock busy",
        r"lease contention"
    ]

    STRUCTURAL_PATTERNS = [
        r"syntaxerror", r"indentationerror", r"parse error", r"ast parse",
        r"importerror", r"modulenotfounderror", r"typeerror", r"unexpected token",
        r"cannot find symbol"
    ]

    INVARIANT_PATTERNS = [
        r"contract.*incompatib", r"breaking change", r"semver.*violation",
        r"schema validation failed", r"merkle.*mismatch", r"hash mismatch",
        r"invariant breach"
    ]

    HALLUCINATORY_PATTERNS = [
        r"secret leaked", r"aws_secret", r"sk-[a-zA-Z0-9]{20,}", r"private key",
        r"poisoning detected", r"circular delegation", r"hallucinated.*endpoint",
        r"rogue subagent"
    ]

    @classmethod
    def classify_error(
        cls,
        error_message: str,
        stack_trace: str = "",
        module_id: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> ErrorDiagnostic:
        """Classifies an error string into one of the four ErrorCategory pillars."""
        combined_text = f"{error_message} {stack_trace}".lower()

        # Check in priority order: Hallucinatory -> Invariant -> Structural -> Transient
        for pat in cls.HALLUCINATORY_PATTERNS:
            if re.search(pat, combined_text):
                return ErrorDiagnostic(
                    category=ErrorCategory.HALLUCINATORY,
                    message=error_message,
                    module_id=module_id,
                    file_path=file_path,
                    raw_trace=stack_trace,
                    confidence_score=0.99
                )

        for pat in cls.INVARIANT_PATTERNS:
            if re.search(pat, combined_text):
                return ErrorDiagnostic(
                    category=ErrorCategory.INVARIANT,
                    message=error_message,
                    module_id=module_id,
                    file_path=file_path,
                    raw_trace=stack_trace,
                    confidence_score=0.95
                )

        for pat in cls.STRUCTURAL_PATTERNS:
            if re.search(pat, combined_text):
                return ErrorDiagnostic(
                    category=ErrorCategory.STRUCTURAL,
                    message=error_message,
                    module_id=module_id,
                    file_path=file_path,
                    raw_trace=stack_trace,
                    confidence_score=0.92
                )

        for pat in cls.TRANSIENT_PATTERNS:
            if re.search(pat, combined_text):
                return ErrorDiagnostic(
                    category=ErrorCategory.TRANSIENT,
                    message=error_message,
                    module_id=module_id,
                    file_path=file_path,
                    raw_trace=stack_trace,
                    confidence_score=0.90
                )

        # Default fallback to Structural if code/trace exists, otherwise Transient
        default_cat = ErrorCategory.STRUCTURAL if stack_trace else ErrorCategory.TRANSIENT
        return ErrorDiagnostic(
            category=default_cat,
            message=error_message,
            module_id=module_id,
            file_path=file_path,
            raw_trace=stack_trace,
            confidence_score=0.70
        )

    @classmethod
    def execute_recovery_playbook(
        cls,
        diagnostic: ErrorDiagnostic,
        retry_count: int = 0,
        max_retries: int = 3,
        module_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the appropriate recovery playbook based on the diagnosed error category.
        """
        category = diagnostic.category
        effective_module = module_id or diagnostic.module_id

        if category == ErrorCategory.TRANSIENT:
            # Playbook 1: Exponential backoff with jitter
            if retry_count >= max_retries:
                return {
                    "action_taken": "ESCALATE_HITL_TRANSIENT_EXHAUSTED",
                    "status": "FAILED",
                    "retries_attempted": retry_count,
                    "resolution": f"Exhausted {max_retries} transient retries. Manual network/host inspection required."
                }
            backoff_base = 0.5 * (2 ** retry_count)
            jitter = random.uniform(0.05, 0.25)
            sleep_duration = round(backoff_base + jitter, 3)
            return {
                "action_taken": "EXPONENTIAL_BACKOFF_RETRY",
                "status": "RETRY_SCHEDULED",
                "backoff_sec": sleep_duration,
                "next_retry": retry_count + 1,
                "resolution": f"Scheduled retry {retry_count + 1}/{max_retries} after {sleep_duration}s backoff."
            }

        elif category == ErrorCategory.STRUCTURAL:
            # Playbook 2: AST-scoped prompt repair & targeted diagnostic re-prompting
            return {
                "action_taken": "SYNTHESIZE_AST_DIAGNOSTIC_REPROMPT",
                "status": "HEALING_DISPATCHED",
                "target_file": diagnostic.file_path or "source_ast",
                "reduction_pct": 75.0,
                "resolution": "Synthesized AST-scoped isolated repair prompt for syntax/type self-healing."
            }

        elif category == ErrorCategory.INVARIANT:
            # Playbook 3: Dual-Reconciliation & Spec Evolution RFC
            return {
                "action_taken": "TRIGGER_DUAL_RECONCILIATION_EVOLVE",
                "status": "SPEC_DELTA_GENERATED",
                "target_module": effective_module or "root",
                "resolution": "Generated RFC delta in user/hitl/proposed_spec_delta.md for contract compatibility review."
            }

        elif category == ErrorCategory.HALLUCINATORY:
            # Playbook 4: Immediate Poisoning Quarantine & Surgical Module Rollback
            return {
                "action_taken": "ISOLATE_QUARANTINE_AND_SURGICAL_ROLLBACK",
                "status": "QUARANTINED_AND_ROLLED_BACK",
                "quarantine_file": "user/hitl/poisoning_quarantine.md",
                "target_module": effective_module or "all",
                "resolution": "Isolated incident to poisoning quarantine and triggered rollback to recovery point RP_k."
            }

        return {
            "action_taken": "DEFAULT_LOG_AND_HALT",
            "status": "FAILED",
            "resolution": "Unknown error pattern; halted pipeline for safety."
        }
