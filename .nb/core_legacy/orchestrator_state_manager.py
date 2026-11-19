"""
Orchestrator State Manager & Reentrancy Engine
Manages persistent execution state, enabling zero-drift resumption
across multiple sessions without re-running completed plans.
"""

import json
import os
import hmac
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class OrchestratorStateManager:
    """
    Manages persistent execution state, enabling zero-drift resumption
    across multiple sessions without re-running completed plans.
    """
    def __init__(
        self,
        state_file: str = ".nb/context/ledger/orchestrator_state.json",
        secret_key: Optional[bytes] = None,
    ):
        self.state_file = Path(state_file)
        if secret_key is None:
            configured_key = os.environ.get("BEEHIVE_ORCHESTRATOR_STATE_KEY")
            secret_key = configured_key.encode("utf-8") if configured_key else None
        if not isinstance(secret_key, bytes) or len(secret_key) < 32:
            raise ValueError(
                "A private orchestrator state signing key of at least 32 bytes is required "
                "(pass secret_key or set BEEHIVE_ORCHESTRATOR_STATE_KEY)"
            )
        self.secret_key = secret_key

    @staticmethod
    def _serialize_state(state: Dict[str, Any]) -> bytes:
        return json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def target_state_path(workspace_root: Path, target_plan_id: str) -> Path:
        if not isinstance(target_plan_id, str) or not target_plan_id:
            raise ValueError("A canonical target plan ID is required")
        target_digest = hashlib.sha256(target_plan_id.encode("utf-8")).hexdigest()[:20]
        return Path(workspace_root) / ".nb" / "context" / "ledger" / f"orchestrator_state_{target_digest}.json"

    def save_state(self, state_dict: Dict[str, Any]) -> None:
        if not isinstance(state_dict, dict):
            raise TypeError("Orchestrator state must be a mapping")
        state_dict_no_sig = {k: v for k, v in state_dict.items() if k != "hmac_state_signature"}
        serialized = self._serialize_state(state_dict_no_sig)
        sig = hmac.new(self.secret_key, serialized, hashlib.sha256).hexdigest()
        signed_state = {**state_dict_no_sig, "hmac_state_signature": sig}
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(self.state_file.parent),
                prefix=f".{self.state_file.name}.",
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                json.dump(signed_state, temporary_file, indent=2, sort_keys=True)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.state_file)
            temporary_path = None
            directory_fd = os.open(self.state_file.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)

    def load_and_verify_state(self) -> Optional[Dict[str, Any]]:
        if not self.state_file.exists():
            return None
        with self.state_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        if not isinstance(state, dict):
            raise ValueError("Cryptographic state signature mismatch: state must be a mapping")
        sig = state.get("hmac_state_signature")
        state_no_sig = {k: v for k, v in state.items() if k != "hmac_state_signature"}
        expected_sig = hmac.new(self.secret_key, self._serialize_state(state_no_sig), hashlib.sha256).hexdigest()
        
        if not sig or not hmac.compare_digest(sig, expected_sig):
            raise ValueError("Cryptographic state signature mismatch: orchestrator_state.json is tampered or corrupted.")
        return state

    def get_resume_queue(
        self,
        target_plan_id: str,
        full_topo_steps: List[Dict[str, Any]],
        handover_verifier=None,
        recovery_point_verifier=None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Skip only matching-target steps with validated handovers and recovery points.
        """
        state = self.load_and_verify_state()
        if not state:
            return full_topo_steps, {}

        if state.get("target_plan_id") != target_plan_id:
            return full_topo_steps, {}
        if not callable(handover_verifier) or not callable(recovery_point_verifier):
            return full_topo_steps, {}

        step_ids = {
            step.get("step_id") or step.get("id")
            for step in full_topo_steps
            if step.get("step_id") or step.get("id")
        }
        records = {}
        duplicate_step_ids = set()
        for record in state.get("completed_steps", []):
            if not isinstance(record, dict):
                continue
            step_id = record.get("step_id") or record.get("id")
            if step_id in records:
                duplicate_step_ids.add(step_id)
                records.pop(step_id)
            elif step_id in step_ids and step_id not in duplicate_step_ids:
                records[step_id] = record

        verified_recovery_points: Dict[str, str] = {}
        for step in full_topo_steps:
            step_id = step.get("step_id") or step.get("id")
            record = records.get(step_id)
            if not record or record.get("status") != "SUCCESS":
                continue
            dependencies = step.get("depends_on", []) or []
            if any(dependency not in verified_recovery_points for dependency in dependencies):
                continue
            recovery_point = record.get("recovery_point")
            if not isinstance(recovery_point, str) or not recovery_point:
                continue
            try:
                if not recovery_point_verifier(recovery_point) or not handover_verifier(record):
                    continue
            except Exception:
                continue
            verified_recovery_points[step_id] = recovery_point

        remaining_steps = [
            step for step in full_topo_steps
            if (step.get("step_id") or step.get("id")) not in verified_recovery_points
        ]
        return remaining_steps, verified_recovery_points
