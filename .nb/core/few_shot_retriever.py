#!/usr/bin/env python3
"""
Dynamic Few-Shot Exemplar Selection & Context-Aware RAG Injection Engine (TODO-AGT-16)
Scores, ranks, and injects golden code patterns and counter-factual negative exemplars
into agent derivation contexts while respecting mathematical attention budgets.
"""

from dataclasses import dataclass, field, asdict
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class Exemplar:
    """Represents a curated code pattern exemplar."""
    exemplar_id: str
    title: str
    language: str
    ast_pattern: str
    domain_tags: List[str]
    code_snippet: str
    explanation: str
    is_negative: bool = False
    score: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Exemplar":
        return cls(
            exemplar_id=data.get("exemplar_id", ""),
            title=data.get("title", ""),
            language=data.get("language", ""),
            ast_pattern=data.get("ast_pattern", ""),
            domain_tags=data.get("domain_tags", []),
            code_snippet=data.get("code_snippet", ""),
            explanation=data.get("explanation", ""),
            is_negative=data.get("is_negative", False),
            score=data.get("score", 0.0)
        )


class FewShotRetriever:
    """
    Retrieves and ranks dynamic few-shot exemplars using multi-factor scoring:
    S_exemplar = 0.40 * S_lang + 0.35 * S_ast_pattern + 0.25 * S_domain_tag
    """

    def __init__(self, exemplar_library_path: Optional[Path] = None):
        self.library_path = exemplar_library_path or (
            Path(__file__).resolve().parent.parent.parent / ".nb" / "context" / "exemplars" / "exemplar_library.json"
        )
        self.exemplars: List[Exemplar] = []
        self.load_library()

    def load_library(self, path: Optional[Path] = None) -> None:
        """Loads exemplar entries from the JSON library."""
        target_path = Path(path or self.library_path).resolve()
        if not target_path.exists():
            self.exemplars = []
            return

        try:
            data = json.loads(target_path.read_text(encoding="utf-8"))
            raw_list = data.get("exemplars", [])
            self.exemplars = [Exemplar.from_dict(item) for item in raw_list]
        except Exception:
            self.exemplars = []

    def compute_similarity_score(
        self,
        exemplar: Exemplar,
        query_lang: str,
        query_pattern: str,
        domain_tags: List[str]
    ) -> float:
        """
        Computes 3-factor composite matching score:
        S = 0.40 * S_lang + 0.35 * S_pattern + 0.25 * S_tags
        """
        # 1. Language matching (0.40 weight)
        q_lang = query_lang.lower().strip()
        e_lang = exemplar.language.lower().strip()
        if q_lang == e_lang:
            s_lang = 1.0
        elif (q_lang in ["javascript", "typescript"] and e_lang in ["javascript", "typescript"]):
            s_lang = 0.75
        elif q_lang == "polyglot" or e_lang == "polyglot":
            s_lang = 0.50
        else:
            s_lang = 0.0

        # 2. AST Pattern matching (0.35 weight)
        q_pat = query_pattern.lower().strip()
        e_pat = exemplar.ast_pattern.lower().strip()
        if q_pat == e_pat:
            s_pattern = 1.0
        elif q_pat in e_pat or e_pat in q_pat:
            s_pattern = 0.70
        else:
            # Word token overlap
            q_words = set(q_pat.replace("_", " ").split())
            e_words = set(e_pat.replace("_", " ").split())
            union = q_words | e_words
            s_pattern = (len(q_words & e_words) / len(union)) if union else 0.0

        # 3. Domain Tags Jaccard similarity (0.25 weight)
        q_tags = set(t.lower().strip() for t in domain_tags)
        e_tags = set(t.lower().strip() for t in exemplar.domain_tags)
        if not q_tags or not e_tags:
            s_tags = 0.0
        else:
            intersection = q_tags & e_tags
            union = q_tags | e_tags
            s_tags = len(intersection) / len(union)

        composite_score = (0.40 * s_lang) + (0.35 * s_pattern) + (0.25 * s_tags)
        return round(composite_score, 4)

    def estimate_tokens(self, text: str) -> int:
        """Approximate token count (1 token ~= 4 characters)."""
        return max(1, len(text) // 4)

    def retrieve(
        self,
        query_lang: str,
        query_pattern: str,
        domain_tags: Optional[List[str]] = None,
        top_k: int = 3,
        min_score_threshold: float = 0.20,
        max_token_budget: int = 1000,
        include_negative: bool = True
    ) -> List[Exemplar]:
        """
        Retrieves top-k ranked exemplars respecting the maximum token budget.
        """
        tags = domain_tags or []
        scored_positives: List[Tuple[float, Exemplar]] = []
        scored_negatives: List[Tuple[float, Exemplar]] = []

        for ex in self.exemplars:
            score = self.compute_similarity_score(ex, query_lang, query_pattern, tags)
            if score >= min_score_threshold:
                # Clone with score
                ex_copy = Exemplar.from_dict(ex.to_dict())
                ex_copy.score = score
                if ex.is_negative:
                    scored_negatives.append((score, ex_copy))
                else:
                    scored_positives.append((score, ex_copy))

        scored_positives.sort(key=lambda x: x[0], reverse=True)
        scored_negatives.sort(key=lambda x: x[0], reverse=True)

        selected: List[Exemplar] = []
        consumed_tokens = 0

        # Prioritize positive exemplars up to top_k
        for score, ex in scored_positives[:top_k]:
            est = self.estimate_tokens(ex.code_snippet + ex.explanation)
            if consumed_tokens + est <= max_token_budget:
                selected.append(ex)
                consumed_tokens += est

        # Append top 1 counter-factual negative exemplar if budget permits and requested
        if include_negative and scored_negatives:
            top_neg = scored_negatives[0][1]
            est_neg = self.estimate_tokens(top_neg.code_snippet + top_neg.explanation)
            if consumed_tokens + est_neg <= max_token_budget:
                selected.append(top_neg)

        return selected

    def format_prompt_injection(self, exemplars: List[Exemplar]) -> str:
        """
        Formats retrieved exemplars into Markdown prompt context.
        Returns empty string if zero exemplars retrieved (graceful zero-shot fallback).
        """
        if not exemplars:
            return ""

        lines = [
            "### Reference Implementation Exemplars (Few-Shot Context)",
            "> Invariants: Follow the architectural conventions demonstrated below. Do NOT reproduce anti-patterns.\n"
        ]

        for idx, ex in enumerate(exemplars, 1):
            category = "⚠️ [ANTI-PATTERN COUNTER-FACTUAL]" if ex.is_negative else "✅ [GOLDEN PATTERN]"
            lines.append(f"#### Exemplar {idx}: {ex.title} ({category})")
            lines.append(f"- **Language**: `{ex.language}` | **Pattern**: `{ex.ast_pattern}` | **Match Score**: `{ex.score:.2f}`")
            lines.append(f"- **Guidance**: {ex.explanation}")
            lines.append(f"```{ex.language}")
            lines.append(ex.code_snippet.strip())
            lines.append("```\n")

        return "\n".join(lines)
