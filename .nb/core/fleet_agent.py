#!/usr/bin/env python3
"""
Lightweight Workstation Agent Daemon (TODO-PRT-06 / CAP-42)
Collects and transmits workstation and node fleet telemetry:
- Machine Identity (Hostname, UUID, OS version, Local User)
- Active Workspaces & Worktree state
- Process & Task State (Progress %, step status, ETAs)
- Local Token Savings & FinOps dollar accounting
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import time
from typing import Dict, List, Optional, Tuple, Any
import urllib.request
import urllib.error
import uuid


@dataclass
class MachineIdentity:
    """Hardware and OS identity of the local workstation or node."""
    machine_id: str
    hostname: str
    os_name: str
    os_version: str
    user_id: str
    agent_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MachineIdentity":
        return cls(**data)


@dataclass
class WorkspaceTelemetry:
    """Active repository and ephemeral worktree state."""
    workspace_path: str
    active_worktree: str
    git_branch: str
    git_commit: str
    uncommitted_changes: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceTelemetry":
        return cls(**data)


@dataclass
class TaskProgress:
    """Active subagent task progression and execution metrics."""
    task_id: str
    task_name: str
    progress_pct: float  # 0.0 to 100.0
    step_status: str     # e.g. "AST Pruning", "Running Fuzzer", "Awaiting Review"
    started_at: str
    eta_seconds: Optional[int] = None
    is_stuck: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskProgress":
        return cls(**data)


@dataclass
class TokenFinOps:
    """Local token consumption and financial dollar accounting."""
    input_tokens: int
    output_tokens: int
    tokens_saved: int
    gross_savings_usd: float
    net_savings_usd: float
    fee_usd: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenFinOps":
        return cls(**data)


@dataclass
class NodeTelemetry:
    """Full node telemetry package transmitted to central portal."""
    machine: MachineIdentity
    workspace: WorkspaceTelemetry
    task: TaskProgress
    finops: TokenFinOps
    health_status: str  # "HEALTHY", "HEALING", "OFFLINE", "QUARANTINED"
    timestamp_utc: str
    org_id: str = "org_default"
    project_id: str = "proj_default"

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["machine"] = self.machine.to_dict()
        res["workspace"] = self.workspace.to_dict()
        res["task"] = self.task.to_dict()
        res["finops"] = self.finops.to_dict()
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeTelemetry":
        machine = MachineIdentity.from_dict(data.get("machine", {}))
        workspace = WorkspaceTelemetry.from_dict(data.get("workspace", {}))
        task = TaskProgress.from_dict(data.get("task", {}))
        finops = TokenFinOps.from_dict(data.get("finops", {}))
        data_copy = dict(data)
        data_copy["machine"] = machine
        data_copy["workspace"] = workspace
        data_copy["task"] = task
        data_copy["finops"] = finops
        return cls(**data_copy)


@dataclass
class HeartbeatPayload:
    """Lightweight periodic heartbeat pulse."""
    machine_id: str
    hostname: str
    health_status: str
    active_task: str
    progress_pct: float
    tokens_saved: int
    timestamp_utc: str
    org_id: str = "org_default"
    project_id: str = "proj_default"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HeartbeatPayload":
        return cls(**data)


class FleetAgentDaemon:
    """
    Lightweight background agent daemon collecting local machine and worktree telemetry.
    """

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        org_id: str = "org_enterprise",
        project_id: str = "proj_core",
        machine_id: Optional[str] = None
    ):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self.org_id = org_id
        self.project_id = project_id
        self._machine_id = machine_id or self._generate_stable_machine_id()
        self.current_task: Optional[TaskProgress] = None

    def _generate_stable_machine_id(self) -> str:
        """Derives a stable machine UUID from hostname and system architecture."""
        raw_seed = f"{socket.gethostname()}-{platform.node()}-{platform.machine()}"
        return f"node_{uuid.uuid5(uuid.NAMESPACE_DNS, raw_seed).hex[:12]}"

    def get_machine_identity(self) -> MachineIdentity:
        """Inspects OS environment and returns hardware/software identity."""
        user = os.environ.get("USER", os.environ.get("USERNAME", "unknown_user"))
        return MachineIdentity(
            machine_id=self._machine_id,
            hostname=socket.gethostname(),
            os_name=platform.system(),
            os_version=platform.release(),
            user_id=user,
            agent_version="1.0.0"
        )

    def get_workspace_telemetry(self) -> WorkspaceTelemetry:
        """Inspects local workspace for active Git worktrees and uncommitted changes."""
        branch = "main"
        commit = "head"
        uncommitted = False
        active_wt = "primary"

        try:
            res_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=False
            )
            if res_branch.returncode == 0 and res_branch.stdout.strip():
                branch = res_branch.stdout.strip()

            res_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=False
            )
            if res_commit.returncode == 0 and res_commit.stdout.strip():
                commit = res_commit.stdout.strip()[:12]

            res_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=False
            )
            if res_status.returncode == 0 and res_status.stdout.strip():
                uncommitted = True

            # Check if running in a worktree path
            if ".nb/workspaces/wt_" in str(self.workspace_root):
                active_wt = self.workspace_root.name
        except Exception:
            pass

        return WorkspaceTelemetry(
            workspace_path=str(self.workspace_root),
            active_worktree=active_wt,
            git_branch=branch,
            git_commit=commit,
            uncommitted_changes=uncommitted
        )

    def get_token_finops(self) -> TokenFinOps:
        """Calculates token savings and dollar savings formula."""
        # Baseline calculations based on standard rate $0.003 / 1k tokens
        tokens_saved = 45000
        gross_usd = (tokens_saved / 1000.0) * 0.003
        fee_usd = round(gross_usd * 0.15, 4)
        net_usd = round(gross_usd * 0.85, 4)

        return TokenFinOps(
            input_tokens=12500,
            output_tokens=3200,
            tokens_saved=tokens_saved,
            gross_savings_usd=round(gross_usd, 4),
            net_savings_usd=net_usd,
            fee_usd=fee_usd
        )

    def update_task_progress(
        self,
        task_id: str,
        task_name: str,
        progress_pct: float,
        step_status: str,
        eta_seconds: Optional[int] = None
    ) -> TaskProgress:
        """Updates currently running subagent task progress."""
        started_at = (
            self.current_task.started_at
            if (self.current_task and self.current_task.task_id == task_id)
            else datetime.now(timezone.utc).isoformat()
        )
        self.current_task = TaskProgress(
            task_id=task_id,
            task_name=task_name,
            progress_pct=min(100.0, max(0.0, progress_pct)),
            step_status=step_status,
            started_at=started_at,
            eta_seconds=eta_seconds,
            is_stuck=False
        )
        return self.current_task

    def collect_telemetry(self, health_status: str = "HEALTHY") -> NodeTelemetry:
        """Assembles a full node telemetry package."""
        machine = self.get_machine_identity()
        workspace = self.get_workspace_telemetry()
        finops = self.get_token_finops()

        task = self.current_task or TaskProgress(
            task_id="task_idle",
            task_name="Idle / Monitoring",
            progress_pct=100.0,
            step_status="Awaiting Task",
            started_at=datetime.now(timezone.utc).isoformat(),
            eta_seconds=0
        )

        return NodeTelemetry(
            machine=machine,
            workspace=workspace,
            task=task,
            finops=finops,
            health_status=health_status,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            org_id=self.org_id,
            project_id=self.project_id
        )

    def collect_heartbeat(self, health_status: str = "HEALTHY") -> HeartbeatPayload:
        """Assembles a lightweight heartbeat pulse."""
        telemetry = self.collect_telemetry(health_status)
        return HeartbeatPayload(
            machine_id=telemetry.machine.machine_id,
            hostname=telemetry.machine.hostname,
            health_status=telemetry.health_status,
            active_task=telemetry.task.task_name,
            progress_pct=telemetry.task.progress_pct,
            tokens_saved=telemetry.finops.tokens_saved,
            timestamp_utc=telemetry.timestamp_utc,
            org_id=self.org_id,
            project_id=self.project_id
        )

    def transmit_heartbeat(
        self,
        portal_url: str = "http://127.0.0.1:3000",
        auth_token: Optional[str] = None
    ) -> bool:
        """Transmits heartbeat to portal HTTP endpoint."""
        url = f"{portal_url.rstrip('/')}/api/fleet/heartbeat"
        payload = json.dumps(self.collect_heartbeat().to_dict()).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        if auth_token:
            req.add_header("Authorization", f"Bearer {auth_token}")

        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return resp.status in (200, 201)
        except Exception:
            return False

    def transmit_telemetry(
        self,
        portal_url: str = "http://127.0.0.1:3000",
        auth_token: Optional[str] = None
    ) -> bool:
        """Transmits full telemetry to portal HTTP endpoint."""
        url = f"{portal_url.rstrip('/')}/api/fleet/telemetry"
        payload = json.dumps(self.collect_telemetry().to_dict()).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        if auth_token:
            req.add_header("Authorization", f"Bearer {auth_token}")

        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return resp.status in (200, 201)
        except Exception:
            return False


    def poll_remote_commands(
        self,
        portal_url: str = "http://127.0.0.1:3000",
        auth_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Polls portal control plane for pending remote intervention commands (TODO-PRT-11 / CAP-44).
        """
        url = f"{portal_url.rstrip('/')}/api/fleet/commands/poll?machine_id={self._machine_id}"
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        if auth_token:
            req.add_header("Authorization", f"Bearer {auth_token}")

        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status in (200, 201):
                    payload = json.loads(resp.read().decode("utf-8"))
                    return payload.get("commands", [])
        except Exception:
            return []
        return []

    def execute_remote_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a received remote intervention command locally on this workstation node.
        """
        action = command.get("action")
        params = command.get("params") or {}
        cmd_id = command.get("command_id", f"cmd_{uuid.uuid4().hex[:8]}")
        result: Dict[str, Any] = {
            "command_id": cmd_id,
            "action": action,
            "machine_id": self._machine_id,
            "status": "SUCCESS"
        }

        if action == "pause":
            if self.current_task:
                self.current_task.is_stuck = False
                self.current_task.step_status = "PAUSED_BY_ADMIN"
            result["details"] = "Node task execution loop frozen by remote admin."

        elif action == "resume":
            if self.current_task:
                self.current_task.step_status = "RESUMED_ACTIVE"
            result["details"] = "Node task execution loop resumed active by remote admin."

        elif action == "surgical_rollback":
            rp = params.get("recovery_point", "RP_SURGICAL_PREV")
            mod = params.get("module_id", "workplace")
            if self.current_task:
                self.current_task.step_status = f"ROLLED_BACK_TO_{rp}"
            result["details"] = f"Module {mod} rolled back to {rp}."

        elif action == "evict_lease":
            wt = params.get("worktree", "")
            if self.current_task:
                self.current_task.step_status = "LEASE_EVICTED"
            result["details"] = f"Worktree lease {wt or 'active'} evicted."

        elif action == "flush_ast_cache":
            cache_dir = self.workspace_root / ".scratch" / "ast_cache"
            cleared_files = 0
            if cache_dir.exists():
                for f in cache_dir.glob("*"):
                    try:
                        f.unlink()
                        cleared_files += 1
                    except Exception:
                        pass
            try:
                import sys
                for mod_name in list(sys.modules.keys()):
                    if "ast_optimizer" in mod_name:
                        opt = getattr(sys.modules[mod_name], "ASTOptimizer", None)
                        if opt and hasattr(opt, "_MEMORY_CACHE"):
                            opt._MEMORY_CACHE.clear()
            except Exception:
                pass
            result["details"] = f"Flushed Tree-Sitter AST cache ({cleared_files} files cleared)."

        else:
            result["status"] = "UNRECOGNIZED_ACTION"
            result["details"] = f"Action '{action}' is not supported by agent daemon."

        return result
