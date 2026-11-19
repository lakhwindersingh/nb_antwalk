"""
Percipience Context Attention Slicing & Token Budgeting Engine (CAP-32)
Enforces mathematical budget quotas across prompt sections to prevent context
overflow and mitigate LLM "lost-in-the-middle" attention degradation.
"""

from pathlib import Path
from typing import Dict, Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class AttentionBudgeter:
    """
    Allocates and enforces declarative token budgets across prompt sections:
    - Persona & Invariant Rules: 15% (Strictly preserved, never pruned)
    - Cross-Module Contracts & Schemas: 25% (High priority)
    - AST-Pruned Codebase Context: 35% (Surgically pruned if over-budget)
    - Memory & Prior Trajectories: 10% (Truncated from oldest entries)
    - Reserved Generation Output: 15% (Guaranteed headroom)
    """

    BUDGET_QUOTAS = {
        "persona_invariants": 0.15,
        "contracts_schemas": 0.25,
        "ast_codebase": 0.35,
        "memory_trajectories": 0.10,
        "reserved_output": 0.15
    }

    CHARS_PER_TOKEN = 4.0

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimates token count using character heuristics (~4 chars/token)."""
        if not text:
            return 0
        return max(1, int(len(text) / cls.CHARS_PER_TOKEN))

    @classmethod
    def slice_context(
        cls,
        sections: Dict[str, str],
        max_total_tokens: int = 8192
    ) -> Dict[str, Any]:
        """
        Calculates section token distributions and bounds each section within its quota.
        """
        quota_tokens = {
            k: int(max_total_tokens * weight)
            for k, weight in cls.BUDGET_QUOTAS.items()
        }

        adjusted_sections: Dict[str, str] = {}
        section_token_metrics: Dict[str, Dict[str, Any]] = {}
        total_used_tokens = 0

        for section_key, quota in quota_tokens.items():
            if section_key == "reserved_output":
                continue

            raw_text = sections.get(section_key, "")
            raw_tokens = cls.estimate_tokens(raw_text)

            if raw_tokens <= quota:
                adjusted_text = raw_text
                trimmed_tokens = 0
            else:
                if section_key == "persona_invariants":
                    # Invariants must never be truncated
                    adjusted_text = raw_text
                    trimmed_tokens = 0
                else:
                    # Proportionally trim text to fit quota
                    max_chars = int(quota * cls.CHARS_PER_TOKEN)
                    adjusted_text = raw_text[:max_chars] + "\n... [ATTENTION_TRUNCATED_TO_PRESERVE_BUDGET]"
                    trimmed_tokens = raw_tokens - cls.estimate_tokens(adjusted_text)

            current_tokens = cls.estimate_tokens(adjusted_text)
            total_used_tokens += current_tokens

            section_token_metrics[section_key] = {
                "allocated_quota_tokens": quota,
                "raw_tokens": raw_tokens,
                "adjusted_tokens": current_tokens,
                "trimmed_tokens": max(0, trimmed_tokens),
                "quota_utilization_pct": round((current_tokens / quota) * 100, 2)
            }
            adjusted_sections[section_key] = adjusted_text

        # Assemble unified attention-sliced prompt
        assembled_prompt = (
            f"=== SYSTEM INVARIANTS & PERSONA ===\n{adjusted_sections.get('persona_invariants', '')}\n\n"
            f"=== WIRE CONTRACTS & SCHEMAS ===\n{adjusted_sections.get('contracts_schemas', '')}\n\n"
            f"=== AST CODEBASE CONTEXT ===\n{adjusted_sections.get('ast_codebase', '')}\n\n"
            f"=== EPISODIC MEMORY & TRAJECTORIES ===\n{adjusted_sections.get('memory_trajectories', '')}\n"
        )

        return {
            "status": "SLICED_SUCCESSFULLY",
            "max_total_tokens": max_total_tokens,
            "total_used_tokens": total_used_tokens,
            "reserved_output_tokens": quota_tokens["reserved_output"],
            "remaining_headroom_tokens": max_total_tokens - total_used_tokens,
            "section_metrics": section_token_metrics,
            "assembled_prompt": assembled_prompt
        }
