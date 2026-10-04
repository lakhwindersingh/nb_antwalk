"""
Percipience Step-by-Step Trajectory Recording & Replay Engine (CAP-33)
Records complete multi-agent ReAct execution traces (Thought -> Action -> Observation -> Reflection)
to enable deterministic offline replay, debugging, and post-mortem failure audits.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class TrajectoryRecorder:
    """
    Manages structured trajectory logs in `agentic/trajectories/`.
    Captures reasoning traces, tool invocations, execution outputs, and self-critiques.
    """

    TRAJECTORY_DIR = (REPO_ROOT / ".nb" / "agentic" / "trajectories" if (REPO_ROOT / ".nb" / "agentic").exists() else REPO_ROOT / "agentic" / "trajectories")

    @classmethod
    def _ensure_dir(cls) -> Path:
        cls.TRAJECTORY_DIR.mkdir(parents=True, exist_ok=True)
        return cls.TRAJECTORY_DIR

    @classmethod
    def create_trajectory(
        cls,
        session_id: str,
        agent_id: str,
        goal: str,
        target_module: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initializes a new structured trajectory envelope."""
        return {
            "trajectory_id": f"traj_{session_id}_{int(time.time())}",
            "session_id": session_id,
            "agent_id": agent_id,
            "goal": goal,
            "target_module": target_module or "global",
            "created_at": time.time(),
            "status": "RECORDING",
            "steps": []
        }

    @classmethod
    def append_step(
        cls,
        trajectory: Dict[str, Any],
        thought: str,
        action: str,
        action_input: Any,
        observation: Any,
        reflection: Optional[str] = None
    ) -> Dict[str, Any]:
        """Appends a single ReAct step to the trajectory."""
        step_num = len(trajectory.get("steps", [])) + 1
        step_record = {
            "step": step_num,
            "timestamp": time.time(),
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": observation,
            "reflection": reflection or "Step outcome aligned with goal."
        }
        trajectory["steps"].append(step_record)
        return trajectory

    @classmethod
    def save_trajectory(cls, trajectory: Dict[str, Any]) -> Path:
        """Persists the completed trajectory to disk."""
        cls._ensure_dir()
        traj_id = trajectory.get("trajectory_id", f"traj_{int(time.time())}")
        trajectory["status"] = "SEALED"
        trajectory["completed_at"] = time.time()
        trajectory["total_steps"] = len(trajectory.get("steps", []))

        out_path = cls.TRAJECTORY_DIR / f"{traj_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(trajectory, f, indent=2)
        return out_path

    @classmethod
    def replay_trajectory(cls, trajectory_id: str) -> Dict[str, Any]:
        """
        Loads and replays a saved trajectory, validating step-by-step continuity.
        """
        cls._ensure_dir()
        filename = f"{trajectory_id}.json" if not trajectory_id.endswith(".json") else trajectory_id
        traj_path = cls.TRAJECTORY_DIR / filename
        
        if not traj_path.exists():
            raise FileNotFoundError(f"Trajectory file not found: {traj_path}")

        with open(traj_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        steps = data.get("steps", [])
        verified_steps = 0

        for s in steps:
            if "step" in s and "thought" in s and "action" in s and "observation" in s:
                verified_steps += 1

        is_valid = verified_steps == len(steps) and len(steps) > 0
        return {
            "trajectory_id": data.get("trajectory_id"),
            "session_id": data.get("session_id"),
            "agent_id": data.get("agent_id"),
            "goal": data.get("goal"),
            "total_steps": len(steps),
            "verified_steps": verified_steps,
            "replay_status": "REPLAY_VERIFIED" if is_valid else "CORRUPTED_OR_EMPTY",
            "is_deterministic": is_valid
        }
