"""
Percipience Requirement Clarification & Ambiguity Resolution Engine (CAP-34)
Quantifies specification entropy and drafts structured clarification RFCs with interactive
multiple-choice questions before autonomous implementation starts.
"""

import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class AmbiguityResolver:
    """
    Evaluates input engineering specifications for ambiguity, unstated constraints,
    and vague terminology, generating interactive clarification RFCs for human operators.
    """

    VAGUE_TERMS = [
        r"\bfast\b", r"\brobust\b", r"\bsimple\b", r"\bbetter\b", r"\bmodern\b",
        r"\bscalable\b", r"\buser friendly\b", r"\bstandard\b", r"\beasy\b",
        r"\bclean\b", r"\bquickly\b", r"\bnice\b", r"\bintuitive\b"
    ]

    TECHNICAL_INDICATORS = [
        r"\b(http|rest|grpc|graphql)\b", r"\b(get|post|put|delete|patch)\b",
        r"\b(json|yaml|protobuf)\b", r"\b(schema|table|column|field|type)\b",
        r"\b(status code|200|201|400|401|403|404|500)\b", r"\b(jwt|oauth|cmek|tls)\b",
        r"\b(latency|sla|p99|rps|qps)\b"
    ]

    CLARIFICATION_DIR = REPO_ROOT / "user" / "hitl" / "clarification_requests"

    @classmethod
    def _ensure_dir(cls) -> Path:
        cls.CLARIFICATION_DIR.mkdir(parents=True, exist_ok=True)
        return cls.CLARIFICATION_DIR

    @classmethod
    def evaluate_ambiguity(cls, requirement_text: str) -> Dict[str, Any]:
        """
        Calculates an ambiguity score (0.0 = completely precise, 1.0 = highly ambiguous).
        """
        if not requirement_text or len(requirement_text.strip()) < 15:
            return {
                "ambiguity_score": 1.0,
                "status": "CRITICAL_AMBIGUITY",
                "is_ambiguous": True,
                "vague_terms_found": ["extremely_short_text"],
                "missing_technical_anchors": ["data_models", "api_endpoints", "error_conditions"],
                "clarification_questions": [
                    "What specific business domain does this requirement apply to?",
                    "What are the precise input and output schema types?",
                    "What error conditions and status codes should be handled?"
                ]
            }

        text_lower = requirement_text.lower()

        # Count vague buzzwords
        vague_found = [term.strip(r"\b") for term in cls.VAGUE_TERMS if re.search(term, text_lower)]
        vague_penalty = min(0.5, len(vague_found) * 0.12)

        # Count presence of technical anchors
        tech_found = [ind.strip(r"\b") for ind in cls.TECHNICAL_INDICATORS if re.search(ind, text_lower)]
        tech_reward = min(0.6, len(tech_found) * 0.15)

        # Length / detail factor
        word_count = len(requirement_text.split())
        length_penalty = 0.3 if word_count < 25 else (0.15 if word_count < 50 else 0.0)

        # Composite ambiguity score
        ambiguity_score = max(0.0, min(1.0, 0.4 + vague_penalty + length_penalty - tech_reward))
        ambiguity_score = round(ambiguity_score, 3)

        is_ambiguous = ambiguity_score >= 0.35

        # Formulate clarification questions
        questions: List[str] = []
        if vague_found:
            questions.append(f"Could you specify concrete numerical metrics for vague terms: {', '.join(vague_found)}?")
        if not re.search(r"(error|fail|exception|status|40|50)", text_lower):
            questions.append("What specific error responses, exception types, or HTTP error status codes should be returned on failure?")
        if not re.search(r"(type|int|str|bool|array|object|schema)", text_lower):
            questions.append("What are the strict field types, constraints (e.g. min/max lengths), and default values for the payload?")

        if not questions and is_ambiguous:
            questions.append("Please provide sample request/response payloads or concrete acceptance criteria.")

        return {
            "ambiguity_score": ambiguity_score,
            "status": "AMBIGUOUS_REQUIRES_CLARIFICATION" if is_ambiguous else "PRECISE_SPECIFICATION",
            "is_ambiguous": is_ambiguous,
            "vague_terms_found": vague_found,
            "technical_anchors_count": len(tech_found),
            "word_count": word_count,
            "clarification_questions": questions
        }

    @classmethod
    def generate_clarification_rfc(
        cls,
        requirement_id: str,
        requirement_text: str,
        eval_report: Optional[Dict[str, Any]] = None,
        out_dir: Optional[Path] = None
    ) -> Path:
        """
        Generates an interactive Markdown Clarification RFC in `user/hitl/clarification_requests/`.
        """
        dest_dir = out_dir or cls._ensure_dir()
        dest_dir.mkdir(parents=True, exist_ok=True)
        report = eval_report or cls.evaluate_ambiguity(requirement_text)

        rfc_content = f"""# Percipience Requirement Clarification RFC: {requirement_id}

> **Status**: PENDING_HUMAN_IN_THE_LOOP_CLARIFICATION  
> **Ambiguity Score**: {report.get('ambiguity_score')} ({report.get('status')})  
> **Generated Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

---

## 1. Raw Engineering Request
```text
{requirement_text.strip()}
```

## 2. Detected Ambiguity Factors
- **Vague / Subjective Terms**: {', '.join(report.get('vague_terms_found', [])) or 'None'}
- **Technical Anchors Identified**: {report.get('technical_anchors_count', 0)}
- **Word Count**: {report.get('word_count', 0)}

## 3. Required Clarification Questions
"""
        for idx, q in enumerate(report.get("clarification_questions", []), 1):
            rfc_content += f"{idx}. **{q}**\n   - [ ] Option A / Precise Spec: \n   - [ ] Option B / Alternative: \n\n"

        rfc_content += """---
*Please populate clarification answers above or refine the formal request template in `user/inputs/formal_requests/` before unblocking the autonomous derivation pipeline.*
"""
        out_file = dest_dir / f"CR_{requirement_id}.md"
        out_file.write_text(rfc_content, encoding="utf-8")
        return out_file
