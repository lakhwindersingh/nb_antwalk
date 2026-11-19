"""
Percipience Semantic Prompt & LLM Response Caching Engine (CAP-39)
Provides vector cosine similarity caching for LLM requests, dropping token cost to zero
for semantically equivalent diagnostic, evaluation, and query turns.
"""

import math
import re
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class SemanticPromptCache:
    """
    In-memory and persistent semantic cache using stemmed term-frequency cosine vector similarity.
    """

    CACHE_PERSIST_PATH = (REPO_ROOT / ".nb" / "context" / "ledger" / "semantic_cache.json" if (REPO_ROOT / ".nb" / "context").exists() else REPO_ROOT / "context" / "ledger" / "semantic_cache.json")

    STOPWORDS = {"how", "do", "i", "can", "the", "a", "an", "is", "for", "to", "in", "of", "and"}

    def __init__(self, default_threshold: float = 0.80, max_entries: int = 1000):
        self.default_threshold = default_threshold
        self.max_entries = max_entries
        self.cache_entries: List[Dict[str, Any]] = []
        self.hits = 0
        self.misses = 0
        self.tokens_saved_total = 0

    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        """Normalizes, stems simple plurals, and filters stopwords."""
        raw_words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
        tokens = []
        for w in raw_words:
            if w in cls.STOPWORDS:
                continue
            if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
                w = w[:-1]
            tokens.append(w)
        return tokens

    @classmethod
    def _compute_vector(cls, tokens: List[str]) -> Dict[str, float]:
        """Builds term-frequency unit vector."""
        counts: Dict[str, float] = {}
        for t in tokens:
            counts[t] = counts.get(t, 0.0) + 1.0
        norm = math.sqrt(sum(v * v for v in counts.values()))
        if norm == 0:
            return counts
        return {k: v / norm for k, v in counts.items()}

    @classmethod
    def cosine_similarity(cls, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculates cosine similarity between two term-frequency unit vectors."""
        dot_product = sum(val * vec2.get(term, 0.0) for term, val in vec1.items())
        return max(0.0, min(1.0, dot_product))

    def get(self, prompt: str, threshold: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached response if a semantically similar prompt exists above threshold.
        """
        thresh = threshold or self.default_threshold
        tokens = self._tokenize(prompt)
        query_vec = self._compute_vector(tokens)
        now = time.time()

        best_match: Optional[Dict[str, Any]] = None
        best_sim = 0.0

        for entry in self.cache_entries:
            if entry.get("expires_at", 0) < now:
                continue

            sim = self.cosine_similarity(query_vec, entry["vector"])
            if sim > best_sim:
                best_sim = sim
                best_match = entry

        if best_match and best_sim >= thresh:
            self.hits += 1
            saved = best_match.get("tokens_saved", 0)
            self.tokens_saved_total += saved
            return {
                "cache_hit": True,
                "similarity_score": round(best_sim, 4),
                "cached_response": best_match["response"],
                "tokens_saved": saved,
                "entry_id": best_match["id"]
            }

        self.misses += 1
        return None

    def set(
        self,
        prompt: str,
        response: str,
        tokens_saved: int = 0,
        ttl_seconds: int = 86400
    ) -> str:
        """Stores a prompt and response pair in the semantic cache."""
        if len(self.cache_entries) >= self.max_entries:
            self.cache_entries.pop(0)

        entry_id = f"cache_{int(time.time() * 1000)}"
        tokens = self._tokenize(prompt)
        vec = self._compute_vector(tokens)

        entry = {
            "id": entry_id,
            "prompt_preview": prompt[:80],
            "response": response,
            "vector": vec,
            "tokens_saved": tokens_saved,
            "created_at": time.time(),
            "expires_at": time.time() + ttl_seconds
        }

        self.cache_entries.append(entry)
        return entry_id

    def get_metrics(self) -> Dict[str, Any]:
        """Returns cache telemetry and savings accounting."""
        total_requests = self.hits + self.misses
        hit_rate = round((self.hits / max(total_requests, 1)) * 100, 2)
        cost_saved_usd = round((self.tokens_saved_total / 1e6) * 3.00, 4)

        return {
            "total_requests": total_requests,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": hit_rate,
            "tokens_saved_total": self.tokens_saved_total,
            "estimated_cost_saved_usd": cost_saved_usd,
            "active_cache_entries": len(self.cache_entries)
        }
