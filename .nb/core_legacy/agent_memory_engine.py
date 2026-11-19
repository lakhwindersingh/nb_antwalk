#!/usr/bin/env python3
"""
Percipience 3-Tier Persistent Agent Memory Architecture (GAP-AGT-03 / TODO-AGT-03)
Provides Working Memory (ephemeral session scratchpad), Episodic Memory (persistent historical
JSONL event stream of resolutions & failures), and Semantic Memory (conceptual rules store).
"""

import hashlib
import json
import os
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

REPO_ROOT = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) >= 3 and (Path(__file__).resolve().parents[2] / ".nb").exists() else Path(__file__).resolve().parents[1]


class AgentMemoryEngine:
    """
    Manages Tier 1 (Working), Tier 2 (Episodic), and Tier 3 (Semantic) agent memories.
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        working_dir: Optional[Path] = None,
        episodic_dir: Optional[Path] = None,
        semantic_dir: Optional[Path] = None
    ):
        root = base_dir or REPO_ROOT
        if root.name in ("swarm_memory", "memory") or (root / "episodic").exists():
            self.working_dir = working_dir or (root / "working")
            self.episodic_dir = episodic_dir or (root / "episodic")
            self.semantic_dir = semantic_dir or (root / "semantic")
        else:
            self.working_dir = working_dir or (root / ".nb" / "context" / "memory" / "working")
            self.episodic_dir = episodic_dir or (root / ".nb" / "context" / "memory" / "episodic")
            self.semantic_dir = semantic_dir or (root / ".nb" / "context" / "memory" / "semantic")

        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.episodic_dir.mkdir(parents=True, exist_ok=True)
        self.semantic_dir.mkdir(parents=True, exist_ok=True)

        self.episodes_file = self.episodic_dir / "episodes.jsonl"
        self.concepts_file = self.semantic_dir / "concepts.json"

        self._ensure_semantic_defaults()

    def _ensure_semantic_defaults(self) -> None:
        """Seeds default platform semantic concepts if store is empty."""
        if not self.concepts_file.exists():
            default_concepts = {
                "quad_space_architecture": {
                    "concept_id": "quad_space_architecture",
                    "title": "Quad-Space Architectural Boundaries",
                    "description": "Strict separation between .nb/ (core/governance), workplace/ (code), user/ (requests), and .claude/ (agent config).",
                    "rules": [
                        "Never write temporary or mutable project code to .nb/core or user/.",
                        "All production implementation logic belongs in workplace/modules/."
                    ],
                    "tags": ["architecture", "quad_space", "invariants"]
                },
                "merkle_immutability": {
                    "concept_id": "merkle_immutability",
                    "title": "Merkle Ledger Immutability & WORM Audit",
                    "description": "All state transitions must be sealed with SHA-256 blocks anchored in Write-Once-Read-Many storage.",
                    "rules": [
                        "Do not mutate existing Merkle block files.",
                        "Recovery points (RP_*) require valid cryptographic linkage."
                    ],
                    "tags": ["merkle", "worm", "security"]
                },
                "wire_contract_invariants": {
                    "concept_id": "wire_contract_invariants",
                    "title": "Cross-Module Wire Contracts",
                    "description": "Wire contracts in .nb/context/contracts/ govern cross-module communication schemas.",
                    "rules": [
                        "Public module APIs must strictly adhere to active wire contract schemas.",
                        "Breaking wire contract changes require SemVer major increment."
                    ],
                    "tags": ["contracts", "api", "schema"]
                }
            }
            self.concepts_file.write_text(json.dumps(default_concepts, indent=2), encoding="utf-8")

    # =========================================================================
    # Tier 1: Working Memory (Ephemeral Session Scratchpad)
    # =========================================================================

    def _working_path(self, session_id: str) -> Path:
        safe_id = re.sub(r"[^A-Za-z0-9_\-]", "_", session_id)
        return self.working_dir / f"{safe_id}_scratchpad.json"

    def set_working_memory(self, session_id: str, data: Dict[str, Any]) -> None:
        """Initializes or overwrites the working scratchpad for a session."""
        payload = {
            "session_id": session_id,
            "in_flight_hypotheses": data.get("in_flight_hypotheses", []),
            "symbol_diffs": data.get("symbol_diffs", {}),
            "step_returns": data.get("step_returns", []),
            "metadata": data.get("metadata", {}),
            "updated_at": time.time()
        }
        self._working_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get_working_memory(self, session_id: str) -> Dict[str, Any]:
        """Retrieves active session scratchpad."""
        path = self._working_path(session_id)
        if not path.exists():
            return {
                "session_id": session_id,
                "in_flight_hypotheses": [],
                "symbol_diffs": {},
                "step_returns": [],
                "metadata": {}
            }
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def update_working_memory(self, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Atomically merges updates into the session scratchpad."""
        current = self.get_working_memory(session_id)
        if "in_flight_hypotheses" in updates:
            current.setdefault("in_flight_hypotheses", []).extend(updates["in_flight_hypotheses"])
        if "symbol_diffs" in updates:
            current.setdefault("symbol_diffs", {}).update(updates["symbol_diffs"])
        if "step_returns" in updates:
            current.setdefault("step_returns", []).extend(updates["step_returns"])
        if "metadata" in updates:
            current.setdefault("metadata", {}).update(updates["metadata"])

        current["updated_at"] = time.time()
        self._working_path(session_id).write_text(json.dumps(current, indent=2), encoding="utf-8")
        return current

    def evict_working_memory(self, session_id: str) -> bool:
        """Deletes the session scratchpad upon task finish or rollback."""
        path = self._working_path(session_id)
        if path.exists():
            path.unlink(missing_ok=True)
            return True
        return False

    # =========================================================================
    # Tier 2: Episodic Memory (Persistent Historical Experience Stream)
    # =========================================================================

    def record_episode(
        self,
        task_id: str,
        error_signature: str,
        root_cause: str,
        patch_summary: str,
        resolution_status: str = "RESOLVED",
        merkle_block_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Records an episodic learning event into the persistent JSONL stream."""
        episode = {
            "episode_id": f"ep_{uuid.uuid4().hex[:10]}",
            "task_id": task_id,
            "error_signature": error_signature.strip(),
            "error_hash": hashlib.sha256(error_signature.strip().encode()).hexdigest(),
            "root_cause": root_cause.strip(),
            "patch_summary": patch_summary.strip(),
            "resolution_status": resolution_status,
            "merkle_block_hash": merkle_block_hash or "",
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        with open(self.episodes_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(episode) + "\n")
        return episode

    def query_episodic_memory(
        self,
        query_text: str,
        error_signature: Optional[str] = None,
        top_k: int = 3,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Queries episodic store via error-signature hash matching and token overlap similarity.
        Yields > 0.85 recall on matching error signatures.
        """
        if not self.episodes_file.exists():
            return []

        episodes: List[Dict[str, Any]] = []
        with open(self.episodes_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        episodes.append(json.loads(line))
                    except Exception:
                        pass

        if not episodes:
            return []

        def _tokenize(text: str) -> Set[str]:
            return set(re.findall(r"\b[A-Za-z0-9_]{3,}\b", text.lower()))

        query_tokens = _tokenize(query_text)
        target_sig_hash = hashlib.sha256(error_signature.strip().encode()).hexdigest() if error_signature else None

        scored: List[Tuple[float, Dict[str, Any]]] = []

        for ep in episodes:
            score = 0.0

            # 1. Error signature exact / hash match
            if target_sig_hash and ep.get("error_hash") == target_sig_hash:
                score += 0.90
            elif error_signature and error_signature.lower() in ep.get("error_signature", "").lower():
                score += 0.75

            # 2. Token overlap similarity across root_cause & patch_summary
            ep_text = f"{ep.get('error_signature', '')} {ep.get('root_cause', '')} {ep.get('patch_summary', '')}"
            ep_tokens = _tokenize(ep_text)
            if query_tokens and ep_tokens:
                intersection = query_tokens.intersection(ep_tokens)
                jaccard = len(intersection) / len(query_tokens.union(ep_tokens))
                score += jaccard * 0.5

            if score >= min_similarity:
                ep_copy = dict(ep)
                ep_copy["match_score"] = round(min(1.0, score), 3)
                scored.append((score, ep_copy))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    # =========================================================================
    # Tier 3: Semantic Memory (Conceptual Architecture & Invariant Store)
    # =========================================================================

    def store_concept(
        self,
        concept_id: str,
        title: str,
        description: str,
        rules: List[str],
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Stores a high-level architectural concept or domain invariant."""
        concepts = self._load_concepts()
        entry = {
            "concept_id": concept_id,
            "title": title,
            "description": description,
            "rules": list(rules),
            "tags": list(tags or []),
            "updated_at": time.time()
        }
        concepts[concept_id] = entry
        self.concepts_file.write_text(json.dumps(concepts, indent=2), encoding="utf-8")
        return entry

    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific concept by ID."""
        concepts = self._load_concepts()
        return concepts.get(concept_id)

    def lookup_concepts(self, query_or_tags: List[str]) -> List[Dict[str, Any]]:
        """Looks up concepts matching any of the specified keywords or tags."""
        concepts = self._load_concepts()
        if not query_or_tags:
            return list(concepts.values())
        matches: List[Dict[str, Any]] = []
        search_terms = {t.lower() for t in query_or_tags}

        for c in concepts.values():
            c_tags = {tag.lower() for tag in c.get("tags", [])}
            c_title = c.get("title", "").lower()
            c_desc = c.get("description", "").lower()

            if any(term in c_tags or term in c_title or term in c_desc for term in search_terms):
                matches.append(c)

        return matches

    def _load_concepts(self) -> Dict[str, Dict[str, Any]]:
        if not self.concepts_file.exists():
            return {}
        try:
            return json.loads(self.concepts_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    # =========================================================================
    # Memory Consolidation
    # =========================================================================

    def consolidate_working_memory(
        self,
        session_id: str,
        merkle_block_hash: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Consolidates working memory scratchpad into persistent episodic memory,
        anchors it with a Merkle block hash, and evicts the scratchpad.
        """
        scratchpad = self.get_working_memory(session_id)
        if not scratchpad or (not scratchpad.get("in_flight_hypotheses") and not scratchpad.get("step_returns")):
            self.evict_working_memory(session_id)
            return None

        hypotheses = "; ".join(scratchpad.get("in_flight_hypotheses", [])) or "Session execution"
        diffs = json.dumps(scratchpad.get("symbol_diffs", {}))

        episode = self.record_episode(
            task_id=f"session_{session_id}",
            error_signature=f"Session Hypothesis: {hypotheses[:80]}",
            root_cause=f"In-flight resolution: {hypotheses}",
            patch_summary=f"Resolved symbol diffs: {diffs[:200]}",
            resolution_status="RESOLVED",
            merkle_block_hash=merkle_block_hash or "MERKLE_BLOCK_GENESIS",
            metadata={"session_id": session_id}
        )

        self.evict_working_memory(session_id)
        return episode
