#!/usr/bin/env python3
"""
2-of-3 Multi-Agent Consensus Quorum Engine (TODO-AGT-17)
Enforces heterogeneous consensus evaluation across diverse agent personas,
single-veto quarantine escalation, and HMAC-signed cryptographic quorum receipts.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid


@dataclass
class EvaluatorVote:
    """Represents an individual agent vote in a quorum decision."""
    evaluator_id: str
    role: str
    vote: str  # "APPROVE" | "REQUEST_REVISION" | "QUARANTINE_VETO"
    rationale: str
    confidence: float = 1.0

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "EvaluatorVote":
        return cls(**data)


@dataclass
class QuorumReceipt:
    """Cryptographically signed consensus quorum decision receipt."""
    quorum_id: str
    decision_type: str
    target_artifact: str
    verdict: str  # "APPROVED" | "REVISION_REQUESTED" | "QUARANTINED" | "DEADLOCKED"
    quorum_passed: bool
    single_veto_triggered: bool
    votes: List[EvaluatorVote]
    quorum_hmac: str
    timestamp_utc: str
    required_threshold: int = 2
    merkle_block_id: Optional[str] = None

    def to_dict(self) -> Dict:
        res = asdict(self)
        res["votes"] = [v.to_dict() if isinstance(v, EvaluatorVote) else v for v in self.votes]
        return res

    @classmethod
    def from_dict(cls, data: Dict) -> "QuorumReceipt":
        votes = [EvaluatorVote.from_dict(v) for v in data.get("votes", [])]
        data_copy = dict(data)
        data_copy["votes"] = votes
        return cls(**data_copy)


class ConsensusQuorumEngine:
    """
    Evaluates 2-of-3 multi-agent consensus for critical decisions:
    - PR Gate Approvals
    - Wire Contract Deprecation
    - Security Sign-off
    - Surgical Rollbacks
    - Spec Evolution RFCs
    """

    DEFAULT_SECRET_KEY = "percipience_quorum_internal_secret_key"

    def __init__(self, workspace_root: Optional[Path] = None, secret_key: Optional[str] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self.secret_key = secret_key or os.environ.get("PERCIPIENCE_QUORUM_KEY", self.DEFAULT_SECRET_KEY)
        self.quarantine_file = self.workspace_root / "user" / "hitl" / "poisoning_quarantine.md"

    def compute_hmac(self, canonical_payload: str) -> str:
        """Computes HMAC-SHA256 signature for canonical quorum payload."""
        return hmac.new(
            self.secret_key.encode("utf-8"),
            canonical_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def record_quarantine_veto(self, receipt: QuorumReceipt, vetoing_vote: EvaluatorVote) -> None:
        """Escalates single-veto quarantine to user/hitl/poisoning_quarantine.md."""
        self.quarantine_file.parent.mkdir(parents=True, exist_ok=True)
        entry = (
            f"\n\n### 🛑 [QUORUM SINGLE-VETO QUARANTINE] {receipt.quorum_id}\n"
            f"- **Timestamp**: `{receipt.timestamp_utc}`\n"
            f"- **Decision Type**: `{receipt.decision_type}`\n"
            f"- **Target Artifact**: `{receipt.target_artifact}`\n"
            f"- **Vetoing Evaluator**: `{vetoing_vote.evaluator_id}` (Role: `{vetoing_vote.role}`)\n"
            f"- **Veto Rationale**: {vetoing_vote.rationale}\n"
            f"- **HMAC Attestation**: `{receipt.quorum_hmac}`\n"
            f"- **Status**: `HALTED_AWAITING_HUMAN_TRIAGE`\n"
        )
        with open(self.quarantine_file, "a", encoding="utf-8") as f:
            f.write(entry)

    def evaluate_quorum(
        self,
        decision_type: str,
        target_artifact: str,
        votes: List[EvaluatorVote],
        required_threshold: int = 2
    ) -> QuorumReceipt:
        """
        Processes 3 heterogeneous evaluator votes and computes quorum outcome.

        Rules:
        1. Any QUARANTINE_VETO vote immediately triggers SINGLE_VETO_QUARANTINE.
        2. >= 2 APPROVE votes -> APPROVED (Quorum Passed).
        3. >= 2 REQUEST_REVISION votes -> REVISION_REQUESTED.
        4. Split vote without consensus (e.g. 1 APPROVE, 1 REVISION, 1 ABSTAIN) -> DEADLOCKED.
        """
        quorum_id = f"qrm_{uuid.uuid4().hex[:12]}"
        timestamp_utc = datetime.now(timezone.utc).isoformat()

        if len(votes) != 3:
            raise ValueError(f"Quorum protocol requires exactly 3 heterogeneous evaluator votes, got {len(votes)}")

        # 1. Check for single-veto quarantine
        single_veto_vote = next((v for v in votes if v.vote == "QUARANTINE_VETO"), None)
        single_veto_triggered = single_veto_vote is not None

        if single_veto_triggered:
            verdict = "QUARANTINED"
            quorum_passed = False
        else:
            approve_count = sum(1 for v in votes if v.vote == "APPROVE")
            revision_count = sum(1 for v in votes if v.vote == "REQUEST_REVISION")

            if approve_count >= required_threshold:
                verdict = "APPROVED"
                quorum_passed = True
            elif revision_count >= required_threshold:
                verdict = "REVISION_REQUESTED"
                quorum_passed = False
            else:
                verdict = "DEADLOCKED"
                quorum_passed = False

        # Build canonical payload for cryptographic HMAC
        canonical_votes_str = "|".join(
            f"{v.evaluator_id}:{v.role}:{v.vote}:{v.confidence:.2f}:{v.rationale}"
            for v in sorted(votes, key=lambda x: x.evaluator_id)
        )
        canonical_str = f"{quorum_id}:{decision_type}:{target_artifact}:{verdict}:{single_veto_triggered}:{canonical_votes_str}:{timestamp_utc}"
        receipt_hmac = self.compute_hmac(canonical_str)

        merkle_block_id = f"RP_QUORUM_{quorum_id}"

        receipt = QuorumReceipt(
            quorum_id=quorum_id,
            decision_type=decision_type,
            target_artifact=target_artifact,
            verdict=verdict,
            quorum_passed=quorum_passed,
            single_veto_triggered=single_veto_triggered,
            votes=votes,
            quorum_hmac=receipt_hmac,
            timestamp_utc=timestamp_utc,
            required_threshold=required_threshold,
            merkle_block_id=merkle_block_id
        )

        if single_veto_triggered and single_veto_vote:
            self.record_quarantine_veto(receipt, single_veto_vote)

        return receipt

    def verify_receipt(self, receipt: QuorumReceipt) -> bool:
        """Verifies the HMAC cryptographic signature on an existing receipt."""
        canonical_votes_str = "|".join(
            f"{v.evaluator_id}:{v.role}:{v.vote}:{v.confidence:.2f}:{v.rationale}"
            for v in sorted(receipt.votes, key=lambda x: x.evaluator_id)
        )
        canonical_str = (
            f"{receipt.quorum_id}:{receipt.decision_type}:{receipt.target_artifact}:"
            f"{receipt.verdict}:{receipt.single_veto_triggered}:{canonical_votes_str}:{receipt.timestamp_utc}"
        )
        expected_hmac = self.compute_hmac(canonical_str)
        return hmac.compare_digest(receipt.quorum_hmac, expected_hmac)
