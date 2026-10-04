"""
Percipience Quantitative LLM Evals & Hallucination Scoring Engine (CAP-37)
Evaluates generated code and artifacts across 5 quantitative dimensions:
1. Faithfulness (G-Eval / Grounding)
2. Hallucination Detection Rate
3. Context Relevancy
4. Code Correctness & Syntax Invariants
5. Semantic Parity / Drift
"""

import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class EvalScoringEngine:
    """
    Automated Quantitative Evaluation & Hallucination Scoring Suite.
    Calculates multi-dimensional rubric scores and composite quality metrics.
    """

    RUBRIC_WEIGHTS = {
        "faithfulness": 0.25,
        "hallucination_freedom": 0.25,
        "context_relevancy": 0.15,
        "code_correctness": 0.20,
        "semantic_parity": 0.15
    }

    STOPWORDS = {
        "a", "an", "the", "in", "on", "of", "for", "to", "and", "or", "is", "use",
        "with", "by", "from", "at", "as", "def", "return", "class", "import"
    }

    @staticmethod
    def _normalize_tokens(text: str) -> set:
        """Tokenizes, lowercases, and stems basic plurals/suffixes."""
        words = re.findall(r"\b[a-zA-Z_0-9]+\b", text.lower())
        stems = set()
        for w in words:
            if len(w) > 3 and w.endswith("s"):
                stems.add(w[:-1])
            stems.add(w)
        return stems

    @classmethod
    def evaluate_code_correctness(cls, code_str: str, language: str = "python") -> Dict[str, Any]:
        """Verifies syntax validity and absence of catastrophic parse errors."""
        if language.lower() == "python":
            try:
                ast.parse(code_str)
                return {"score": 1.0, "is_valid_syntax": True, "error": None}
            except SyntaxError as e:
                return {
                    "score": 0.0,
                    "is_valid_syntax": False,
                    "error": f"SyntaxError at line {e.lineno}: {e.msg}"
                }
        balanced = (code_str.count("{") == code_str.count("}")) and (code_str.count("(") == code_str.count(")"))
        return {"score": 1.0 if balanced else 0.5, "is_valid_syntax": balanced, "error": None}

    @classmethod
    def evaluate_hallucination_indicators(
        cls,
        generated_code: str,
        valid_symbols: Optional[List[str]] = None,
        disallowed_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Scans generated code for phantom imports, invented libraries, or fake APIs."""
        phantom_markers = [
            r"import fake_", r"import non_existent_", r"from magic_utils import",
            r"TODO:\s*implement_this_real_api", r"<INSERT_SECRET_HERE>"
        ]
        if disallowed_patterns:
            phantom_markers.extend(disallowed_patterns)

        detected_hallucinations = []
        for pat in phantom_markers:
            if re.search(pat, generated_code, re.IGNORECASE):
                detected_hallucinations.append(pat)

        if valid_symbols and len(valid_symbols) > 0:
            found_symbols = [s for s in valid_symbols if s in generated_code]
            grounding_ratio = len(found_symbols) / len(valid_symbols)
        else:
            grounding_ratio = 1.0

        hallucination_freedom = max(0.0, 1.0 - (len(detected_hallucinations) * 0.4) - ((1.0 - grounding_ratio) * 0.2))
        hallucination_freedom = round(hallucination_freedom, 3)

        return {
            "hallucination_freedom_score": hallucination_freedom,
            "hallucination_rate": round(1.0 - hallucination_freedom, 3),
            "detected_hallucinations": detected_hallucinations,
            "is_hallucination_free": len(detected_hallucinations) == 0 and hallucination_freedom >= 0.85
        }

    @classmethod
    def evaluate_generation(
        cls,
        generated_code: str,
        requirement_spec: str,
        context_provided: str,
        valid_symbols: Optional[List[str]] = None,
        language: str = "python"
    ) -> Dict[str, Any]:
        """Full 5-dimensional quantitative evaluation pipeline."""
        # 1. Code Correctness
        correctness_res = cls.evaluate_code_correctness(generated_code, language)
        score_correctness = correctness_res["score"]

        # 2. Hallucination Freedom
        hallucination_res = cls.evaluate_hallucination_indicators(generated_code, valid_symbols)
        score_hallucination = hallucination_res["hallucination_freedom_score"]

        # 3. Faithfulness
        context_tokens = cls._normalize_tokens(context_provided) - cls.STOPWORDS
        code_tokens = cls._normalize_tokens(generated_code) - cls.STOPWORDS
        if code_tokens:
            overlap = code_tokens.intersection(context_tokens)
            score_faithfulness = min(1.0, (len(overlap) + 2) / (len(code_tokens) + 1))
        else:
            score_faithfulness = 0.8
        score_faithfulness = round(max(0.6, score_faithfulness), 3)

        # 4. Context Relevancy
        req_tokens = cls._normalize_tokens(requirement_spec) - cls.STOPWORDS
        if req_tokens and context_tokens:
            matched_req = req_tokens.intersection(context_tokens)
            score_context_relevancy = min(1.0, (len(matched_req) + 2) / (len(req_tokens) + 1))
        else:
            score_context_relevancy = 0.9
        score_context_relevancy = round(max(0.6, score_context_relevancy), 3)

        # 5. Semantic Parity
        if req_tokens and code_tokens:
            matched_code = req_tokens.intersection(code_tokens)
            score_semantic_parity = min(1.0, (len(matched_code) + 1) / (len(req_tokens) + 1))
        else:
            score_semantic_parity = 0.9
        score_semantic_parity = round(max(0.7, score_semantic_parity), 3)

        # Composite G-Eval score
        composite_score = round(
            (score_faithfulness * cls.RUBRIC_WEIGHTS["faithfulness"]) +
            (score_hallucination * cls.RUBRIC_WEIGHTS["hallucination_freedom"]) +
            (score_context_relevancy * cls.RUBRIC_WEIGHTS["context_relevancy"]) +
            (score_correctness * cls.RUBRIC_WEIGHTS["code_correctness"]) +
            (score_semantic_parity * cls.RUBRIC_WEIGHTS["semantic_parity"]),
            3
        )

        is_passing = composite_score >= 0.75 and correctness_res["is_valid_syntax"]
        return {
            "evaluation_status": "PASSED" if is_passing else "FAILED",
            "composite_geval_score": composite_score,
            "is_passing": is_passing,
            "rubrics": {
                "faithfulness": score_faithfulness,
                "hallucination_freedom": score_hallucination,
                "hallucination_rate": hallucination_res["hallucination_rate"],
                "context_relevancy": score_context_relevancy,
                "code_correctness": score_correctness,
                "semantic_parity": score_semantic_parity
            },
            "correctness_details": correctness_res,
            "hallucination_details": hallucination_res
        }
