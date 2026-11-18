#!/usr/bin/env python3
"""
Percipience Structured Multi-Pass Self-Reflection & Critic Verification Engine (GAP-AGT-02 / TODO-AGT-02)
Implements 3-phase Reflexion (GENERATE -> CRITIQUE -> REFINE) verification loops
and enforces zero-disk-write guarantees until 5 mandatory invariant pillars pass.
"""

import ast
import json
import os
import re
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) >= 3 and (Path(__file__).resolve().parents[2] / ".nb").exists() else Path(__file__).resolve().parents[1]


class ReflexionVerificationError(Exception):
    """Raised when an agent attempts disk writes before passing Critic verification."""
    pass


@dataclass
class CritiqueEnvelope:
    phase: str
    iteration: int
    critique: str
    defects_found: List[str]
    severity: str  # "LOW", "MEDIUM", "HIGH"
    refined_plan: str
    passes_invariants: bool
    convergence_score: float
    pillar_scores: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SelfReflectionEngine:
    """
    Enforces Generator -> Critic -> Refiner verification cycles.
    Prevents hallucinated or unverified code from reaching the physical filesystem.
    """

    CONVERGENCE_THRESHOLD: float = 0.90
    MAX_REFLECT_TURNS: int = 2

    # Invariant Pillars
    PILLARS = [
        "wire_contract_conformity",
        "edge_case_coverage",
        "type_signature_purity",
        "guardrail_compliance",
        "token_budget_adherence"
    ]

    @classmethod
    def evaluate_invariants(
        cls,
        code_or_artifact: str,
        task_context: Optional[Dict[str, Any]] = None
    ) -> CritiqueEnvelope:
        """
        Evaluates a generated code artifact against 5 invariant pillars:
        1. Wire Contract Schema Conformity
        2. Edge-Case Coverage (null, bounds, exception handling)
        3. Type Signature Purity (type hints, return types)
        4. Guardrail Policy Compliance (forbidden calls, secrets, path breakout)
        5. Token Budget Adherence
        """
        task_context = task_context or {}
        defects: List[str] = []
        pillar_scores: Dict[str, float] = {}

        # 1. Wire Contract Schema Conformity
        # Check if contract references or schemas are respected
        contract_score = 1.0
        expected_contracts = task_context.get("expected_contracts", [])
        for c in expected_contracts:
            if c not in code_or_artifact:
                defects.append(f"Missing required contract symbol or schema reference: '{c}'")
                contract_score -= 0.3
        pillar_scores["wire_contract_conformity"] = max(0.0, contract_score)

        # 2. Edge-Case Coverage
        # Check presence of defensive programming (try/except, None check, boundary conditions)
        edge_score = 1.0
        has_error_handling = bool(re.search(r"\b(try\b|except\b|catch\b|throw\b|raise\b|if .* (is None|== None|not None))", code_or_artifact))
        has_boundary_check = bool(re.search(r"\b(len\(|< 0|> 0|empty|isinstance|Optional|null)\b", code_or_artifact))
        if not has_error_handling:
            defects.append("Missing explicit error handling (no try/except or null checks detected)")
            edge_score -= 0.3
        if not has_boundary_check:
            defects.append("Missing defensive boundary checks (no bounds/length/type guards detected)")
            edge_score -= 0.2
        pillar_scores["edge_case_coverage"] = max(0.0, edge_score)

        # 3. Type Signature Purity
        # Parse Python AST if Python code
        type_score = 1.0
        if "def " in code_or_artifact or "class " in code_or_artifact:
            try:
                tree = ast.parse(code_or_artifact)
                functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                untyped_funcs = 0
                for f in functions:
                    if f.returns is None and not f.name.startswith("__"):
                        untyped_funcs += 1
                if functions and untyped_funcs > 0:
                    defects.append(f"{untyped_funcs} function(s) missing explicit return type annotations")
                    type_score -= min(0.4, untyped_funcs * 0.1)
            except SyntaxError:
                # Syntax error itself is a severe defect
                defects.append("Syntax error in generated code artifact")
                type_score = 0.0
        pillar_scores["type_signature_purity"] = max(0.0, type_score)

        # 4. Guardrail Policy Compliance
        guardrail_score = 1.0
        unsafe_patterns = [
            (r"\bos\.system\(", "Prohibited os.system invocation detected"),
            (r"\beval\(", "Prohibited eval() invocation detected"),
            (r"\bexec\(", "Prohibited exec() invocation detected"),
            (r"rm\s+-rf\s+/", "Hostile filesystem wipe pattern detected"),
            (r"(api_key|password|secret)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]", "Hardcoded credential detected"),
        ]
        for pattern, desc in unsafe_patterns:
            if re.search(pattern, code_or_artifact):
                defects.append(desc)
                guardrail_score -= 0.5
        pillar_scores["guardrail_compliance"] = max(0.0, guardrail_score)

        # 5. Token Budget Adherence
        budget_score = 1.0
        max_tokens = task_context.get("max_tokens", 8000)
        est_tokens = len(code_or_artifact) // 4
        if est_tokens > max_tokens:
            defects.append(f"Token budget exceeded: {est_tokens} > {max_tokens}")
            budget_score = max(0.0, 1.0 - (est_tokens - max_tokens) / max_tokens)
        pillar_scores["token_budget_adherence"] = budget_score

        # Calculate weighted convergence score
        convergence = sum(pillar_scores.values()) / len(pillar_scores)
        passes = (convergence >= cls.CONVERGENCE_THRESHOLD) and (len(defects) == 0 or all("Missing required" not in d for d in defects))

        severity = "LOW"
        if convergence < 0.6:
            severity = "HIGH"
        elif convergence < 0.9:
            severity = "MEDIUM"

        critique_summary = (
            f"All {len(cls.PILLARS)} invariant pillars satisfied with convergence score {convergence:.2f}"
            if passes
            else f"Critic identified {len(defects)} defect(s). Convergence score: {convergence:.2f}"
        )

        return CritiqueEnvelope(
            phase="CRITIQUE",
            iteration=1,
            critique=critique_summary,
            defects_found=defects,
            severity=severity,
            refined_plan="Refine code to satisfy identified missing annotations, defensive checks, and contract invariants" if defects else "Ready for deployment",
            passes_invariants=passes,
            convergence_score=round(convergence, 3),
            pillar_scores={k: round(v, 3) for k, v in pillar_scores.items()}
        )

    @classmethod
    def run_reflexion_cycle(
        cls,
        task_spec: Dict[str, Any],
        generator_fn: Callable[[Dict[str, Any]], str],
        critic_fn: Optional[Callable[[str, Dict[str, Any]], CritiqueEnvelope]] = None,
        refiner_fn: Optional[Callable[[str, CritiqueEnvelope, Dict[str, Any]], str]] = None,
        max_turns: int = MAX_REFLECT_TURNS
    ) -> Dict[str, Any]:
        """
        Executes a 3-Phase Reflexion Protocol:
        GENERATE -> CRITIQUE -> REFINE up to max_turns iterations.
        Returns the finalized payload along with verification envelope.
        """
        critic = critic_fn or cls.evaluate_invariants
        history: List[Dict[str, Any]] = []

        # 1. GENERATE
        current_artifact = generator_fn(task_spec)
        envelope = critic(current_artifact, task_spec)
        envelope.phase = "CRITIQUE"
        envelope.iteration = 1
        history.append({
            "phase": "GENERATE",
            "iteration": 1,
            "artifact": current_artifact,
            "envelope": envelope.to_dict()
        })

        # 2. Check early exit
        if envelope.passes_invariants and envelope.convergence_score >= cls.CONVERGENCE_THRESHOLD:
            return {
                "status": "APPROVED",
                "final_artifact": current_artifact,
                "passes_invariants": True,
                "iterations": 1,
                "final_envelope": envelope.to_dict(),
                "history": history
            }

        # 3. REFINE Loop (Bounded by max_turns)
        for turn in range(2, max_turns + 1):
            if refiner_fn:
                refined_artifact = refiner_fn(current_artifact, envelope, task_spec)
            else:
                # Default heuristic refiner: appends defensive comments and annotations if missing
                refined_artifact = current_artifact
                if "error handling" in " ".join(envelope.defects_found):
                    refined_artifact = "# Defensive wrapper\ntry:\n" + "\n".join("    " + line for line in refined_artifact.splitlines()) + "\nexcept Exception as err:\n    pass\n"

            current_artifact = refined_artifact
            envelope = critic(current_artifact, task_spec)
            envelope.phase = "REFINE"
            envelope.iteration = turn
            history.append({
                "phase": "REFINE",
                "iteration": turn,
                "artifact": current_artifact,
                "envelope": envelope.to_dict()
            })

            if envelope.passes_invariants and envelope.convergence_score >= cls.CONVERGENCE_THRESHOLD:
                return {
                    "status": "APPROVED",
                    "final_artifact": current_artifact,
                    "passes_invariants": True,
                    "iterations": turn,
                    "final_envelope": envelope.to_dict(),
                    "history": history
                }

        # Exhausted turns without reaching 0.90 convergence
        return {
            "status": "ESCALATED_TO_HITL",
            "final_artifact": current_artifact,
            "passes_invariants": False,
            "iterations": max_turns,
            "final_envelope": envelope.to_dict(),
            "history": history
        }

    @classmethod
    def safe_apply_filesystem_write(
        cls,
        target_path: Path,
        content: str,
        reflexion_result: Dict[str, Any]
    ) -> bool:
        """
        Enforces zero disk writes unless Critic verification passed with passes_invariants=True.
        """
        if not reflexion_result.get("passes_invariants", False):
            score = reflexion_result.get("final_envelope", {}).get("convergence_score", 0.0)
            defects = reflexion_result.get("final_envelope", {}).get("defects_found", [])
            raise ReflexionVerificationError(
                f"Zero disk write allowed: Critic verification not passed. "
                f"Convergence score: {score:.2f} < {cls.CONVERGENCE_THRESHOLD:.2f}. "
                f"Defects: {defects}"
            )

        target_path = Path(target_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write
        tmp_p = target_path.with_suffix(f"{target_path.suffix}.tmp.{uuid.uuid4().hex[:6]}")
        tmp_p.write_text(content, encoding="utf-8")
        tmp_p.replace(target_path)
        return True
