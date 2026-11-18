#!/usr/bin/env python3
"""
Proactive Milestone-Based HITL Interactive Checkpoints Engine (TODO-AGT-18)
Pauses autonomous pipelines at critical architectural and schema boundaries,
emits interactive Markdown/JSON cards, handles timeout policies, and enables CLI/Portal resumption.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid


@dataclass
class BlastRadiusInfo:
    """Blast radius impact analysis for a milestone checkpoint."""
    affected_modules: List[str] = field(default_factory=list)
    symbols_modified: int = 0
    breaking_changes: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "BlastRadiusInfo":
        return cls(**data)


@dataclass
class CheckpointResolution:
    """Human or automated resolution outcome for a checkpoint."""
    decision: str  # "APPROVE" | "REJECT" | "MODIFY" | "AUTO_TIMEOUT"
    reason: str
    resolver: str
    resolved_at: str

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "CheckpointResolution":
        return cls(**data)


@dataclass
class HITLCheckpoint:
    """Structured milestone checkpoint card."""
    checkpoint_id: str
    milestone_type: str
    title: str
    description: str
    status: str  # "PENDING" | "APPROVED" | "REJECTED" | "TIMED_OUT" | "AUTO_RESOLVED"
    created_at: str
    diff_preview: str = ""
    blast_radius: BlastRadiusInfo = field(default_factory=BlastRadiusInfo)
    selectable_options: List[str] = field(default_factory=lambda: ["APPROVE", "REJECT", "MODIFY"])
    timeout_seconds: int = 3600
    timeout_action: str = "AUTO_PAUSE"  # "AUTO_PAUSE" | "QUARANTINE" | "PROCEED_CONSERVATIVE"
    resolution: Optional[CheckpointResolution] = None

    def to_dict(self) -> Dict:
        res = asdict(self)
        res["blast_radius"] = self.blast_radius.to_dict()
        if self.resolution:
            res["resolution"] = self.resolution.to_dict()
        return res

    @classmethod
    def from_dict(cls, data: Dict) -> "HITLCheckpoint":
        blast = BlastRadiusInfo.from_dict(data.get("blast_radius", {}))
        res_data = data.get("resolution")
        resolution = CheckpointResolution.from_dict(res_data) if res_data else None
        data_copy = dict(data)
        data_copy["blast_radius"] = blast
        data_copy["resolution"] = resolution
        return cls(**data_copy)


class HITLCheckpointManager:
    """
    Manages interactive milestone checkpoints in user/hitl/milestones/.
    """

    def __init__(self, workspace_root: Optional[Path] = None, spool_dir: Optional[Path] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self.spool_dir = Path(
            spool_dir or (self.workspace_root / "user" / "hitl" / "milestones")
        ).resolve()
        self.spool_dir.mkdir(parents=True, exist_ok=True)

    def _render_markdown_card(self, chk: HITLCheckpoint) -> str:
        """Renders an interactive Markdown card for human review."""
        breaking_badge = "🚨 **BREAKING CHANGE DETECTED**" if chk.blast_radius.breaking_changes else "✅ Non-breaking"
        modules_str = ", ".join(chk.blast_radius.affected_modules) or "None"

        card = [
            f"# 🛡️ Percipience HITL Milestone Checkpoint: `{chk.checkpoint_id}`",
            f"> **Milestone**: `{chk.milestone_type}` | **Status**: `{chk.status}` | **Created**: `{chk.created_at}`\n",
            f"## {chk.title}",
            f"{chk.description}\n",
            "### 💥 Blast Radius & Impact Analysis",
            f"- **Breaking Status**: {breaking_badge}",
            f"- **Affected Modules**: `{modules_str}`",
            f"- **Symbols Modified**: `{chk.blast_radius.symbols_modified}`\n"
        ]

        if chk.diff_preview:
            card.extend([
                "### 📝 Diff / Specification Preview",
                "```diff",
                chk.diff_preview.strip(),
                "```\n"
            ])

        card.extend([
            "### ⚖️ Selectable Action Options",
            f"- Options: `{' | '.join(chk.selectable_options)}`",
            f"- Timeout Policy: `{chk.timeout_seconds}s` $\\rightarrow$ Action: `{chk.timeout_action}`\n",
            "### 🚀 Resolution CLI Commands",
            f"```bash",
            f"./.nb/bin/percipience hitl approve --id {chk.checkpoint_id} [--comment \"Approved for production\"]",
            f"./.nb/bin/percipience hitl reject --id {chk.checkpoint_id} --reason \"Divergent interface contract\"",
            f"```\n"
        ])

        if chk.resolution:
            card.extend([
                "---",
                "### 🏁 Resolution Recorded",
                f"- **Decision**: `{chk.resolution.decision}`",
                f"- **Resolver**: `{chk.resolution.resolver}`",
                f"- **Timestamp**: `{chk.resolution.resolved_at}`",
                f"- **Reason/Notes**: {chk.resolution.reason}\n"
            ])

        return "\n".join(card)

    def create_checkpoint(
        self,
        milestone_type: str,
        title: str,
        description: str,
        diff_preview: str = "",
        blast_radius: Optional[BlastRadiusInfo] = None,
        selectable_options: Optional[List[str]] = None,
        timeout_seconds: int = 3600,
        timeout_action: str = "AUTO_PAUSE"
    ) -> HITLCheckpoint:
        """Creates a pending milestone checkpoint, writing JSON and Markdown cards."""
        checkpoint_id = f"chk_{uuid.uuid4().hex[:10]}"
        created_at = datetime.now(timezone.utc).isoformat()

        chk = HITLCheckpoint(
            checkpoint_id=checkpoint_id,
            milestone_type=milestone_type,
            title=title,
            description=description,
            status="PENDING",
            created_at=created_at,
            diff_preview=diff_preview,
            blast_radius=blast_radius or BlastRadiusInfo(),
            selectable_options=selectable_options or ["APPROVE", "REJECT", "MODIFY"],
            timeout_seconds=timeout_seconds,
            timeout_action=timeout_action
        )

        # Write JSON card
        json_file = self.spool_dir / f"{checkpoint_id}.json"
        json_file.write_text(json.dumps(chk.to_dict(), indent=2), encoding="utf-8")

        # Write Markdown review card
        md_file = self.spool_dir / f"{checkpoint_id}.md"
        md_file.write_text(self._render_markdown_card(chk), encoding="utf-8")

        return chk

    def get_checkpoint(self, checkpoint_id: str) -> Optional[HITLCheckpoint]:
        """Loads a checkpoint by ID."""
        json_file = self.spool_dir / f"{checkpoint_id}.json"
        if not json_file.exists():
            return None
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            return HITLCheckpoint.from_dict(data)
        except Exception:
            return None

    def list_checkpoints(self, pending_only: bool = False) -> List[HITLCheckpoint]:
        """Lists all recorded checkpoints sorted by creation timestamp."""
        checkpoints: List[HITLCheckpoint] = []
        for f in self.spool_dir.glob("chk_*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                chk = HITLCheckpoint.from_dict(data)
                if not pending_only or chk.status == "PENDING":
                    checkpoints.append(chk)
            except Exception:
                continue
        checkpoints.sort(key=lambda x: x.created_at, reverse=True)
        return checkpoints

    def resolve_checkpoint(
        self,
        checkpoint_id: str,
        decision: str,
        reason: str = "",
        resolver: str = "human_operator"
    ) -> HITLCheckpoint:
        """
        Resolves a pending checkpoint with APPROVE, REJECT, or MODIFY.
        """
        chk = self.get_checkpoint(checkpoint_id)
        if not chk:
            raise KeyError(f"Checkpoint not found: {checkpoint_id}")

        decision_upper = decision.upper()
        if decision_upper not in [opt.upper() for opt in chk.selectable_options]:
            raise ValueError(f"Decision '{decision}' is not in selectable options: {chk.selectable_options}")

        resolved_status = "APPROVED" if decision_upper == "APPROVE" else (
            "REJECTED" if decision_upper == "REJECT" else "MODIFIED"
        )

        chk.status = resolved_status
        chk.resolution = CheckpointResolution(
            decision=decision_upper,
            reason=reason,
            resolver=resolver,
            resolved_at=datetime.now(timezone.utc).isoformat()
        )

        # Update JSON and Markdown files
        json_file = self.spool_dir / f"{checkpoint_id}.json"
        json_file.write_text(json.dumps(chk.to_dict(), indent=2), encoding="utf-8")

        md_file = self.spool_dir / f"{checkpoint_id}.md"
        md_file.write_text(self._render_markdown_card(chk), encoding="utf-8")

        return chk

    def check_and_handle_timeouts(self) -> List[HITLCheckpoint]:
        """
        Evaluates pending checkpoints against their timeout thresholds.
        Applies timeout action: AUTO_PAUSE | QUARANTINE | PROCEED_CONSERVATIVE.
        """
        timed_out: List[HITLCheckpoint] = []
        now = datetime.now(timezone.utc)

        for chk in self.list_checkpoints(pending_only=True):
            try:
                created_dt = datetime.fromisoformat(chk.created_at)
            except Exception:
                continue

            expiry_dt = created_dt + timedelta(seconds=chk.timeout_seconds)
            if now >= expiry_dt:
                chk.status = "TIMED_OUT"
                chk.resolution = CheckpointResolution(
                    decision=f"TIMEOUT_{chk.timeout_action}",
                    reason=f"Exceeded timeout deadline of {chk.timeout_seconds}s",
                    resolver="system_timeout_sentinel",
                    resolved_at=now.isoformat()
                )

                json_file = self.spool_dir / f"{chk.checkpoint_id}.json"
                json_file.write_text(json.dumps(chk.to_dict(), indent=2), encoding="utf-8")

                md_file = self.spool_dir / f"{chk.checkpoint_id}.md"
                md_file.write_text(self._render_markdown_card(chk), encoding="utf-8")

                timed_out.append(chk)

        return timed_out
