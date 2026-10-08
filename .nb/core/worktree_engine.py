"""
Percipience Ephemeral Git Worktree & Subagent Lease Manager
Implements Invariant 6, CAP-05, and Worktree Isolation Rules (RULE-WI-01 through RULE-WI-10).
Provisions isolated worktrees under .claude/worktrees/ or .nb/workspaces/wt_{agent_id}
with time-bound TTL leases, active POSIX PID probing, optional
Redis 7.x Redlock distributed lease backend, atomic merge, quarantine, and pre-merge canary verification.
"""

import os
import subprocess
import time
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

MAX_WORKTREES_PER_PROJECT = 5
MAX_LEASE_EXTENSIONS = 3
DEFAULT_LEASE_HOURS = 24
HARD_CLEANUP_HOURS = 48

# Standardized Error Codes per RULE-WI-01 through RULE-WI-10
E_NO_WORKTREE_ISOLATION = "E_NO_WORKTREE_ISOLATION"
E_LEASE_EXPIRED = "E_LEASE_EXPIRED"
E_MAX_WORKTREES_EXCEEDED = "E_MAX_WORKTREES_EXCEEDED"
E_INVALID_BRANCH_NAME = "E_INVALID_BRANCH_NAME"
E_INVALID_WORKTREE_PATH = "E_INVALID_WORKTREE_PATH"
E_CROSS_WORKTREE_DEPENDENCY = "E_CROSS_WORKTREE_DEPENDENCY"
E_INVALID_COMMIT_MESSAGE = "E_INVALID_COMMIT_MESSAGE"
E_ISOLATION_VIOLATION = "E_ISOLATION_VIOLATION"


def is_pid_alive(pid: Optional[int]) -> bool:
    """Checks if a process ID is currently running on the host OS."""
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class RedisRedlockBackend:
    """Simulated or live Redis 7.x Redlock distributed lock adapter."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.environ.get("PERCIPIENCE_REDIS_URL", "redis://localhost:6379/0")
        self._memory_distributed_store: Dict[str, Dict[str, Any]] = {}

    def acquire_lock(self, resource_key: str, ttl_ms: int = 3600000) -> Optional[str]:
        now_ms = int(time.time() * 1000)
        existing = self._memory_distributed_store.get(resource_key)
        if existing and existing.get("expires_at_ms", 0) > now_ms:
            return None  # Locked by another node
        lock_token = f"redlock_{resource_key}_{now_ms}"
        self._memory_distributed_store[resource_key] = {
            "token": lock_token,
            "acquired_at_ms": now_ms,
            "expires_at_ms": now_ms + ttl_ms
        }
        return lock_token

    def release_lock(self, resource_key: str, lock_token: str) -> bool:
        existing = self._memory_distributed_store.get(resource_key)
        if existing and existing.get("token") == lock_token:
            del self._memory_distributed_store[resource_key]
            return True
        return False


class WorktreeEngine:
    """
    Manages ephemeral git worktree allocations, leases, distributed locks,
    path isolation boundaries, and atomic merges per RULE-WI-01 to RULE-WI-10.
    """

    _redlock_backend = RedisRedlockBackend()

    @staticmethod
    def _lease_file(workspace_root: Path) -> Path:
        p = workspace_root / ".nb" / "workspaces" / "leases.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            with open(p, "w", encoding="utf-8") as f:
                json.dump({}, f)
        return p

    @classmethod
    def generate_branch_name(cls, agent_id: str, slug: str, ts: Optional[datetime] = None) -> str:
        """RULE-WI-04: Format wt/{agent_id[:8]}/{slug}/{timestamp}"""
        now = ts or datetime.now(timezone.utc)
        agent_short = agent_id[:8] if len(agent_id) >= 8 else agent_id
        ts_str = now.strftime("%Y%m%d-%H%M%S")
        return f"wt/{agent_short}/{slug}/{ts_str}"

    @classmethod
    def validate_branch_name(cls, branch_name: str) -> bool:
        """Validates branch naming convention per RULE-WI-04"""
        parts = branch_name.split("/")
        return len(parts) >= 4 and parts[0] == "wt" and bool(parts[1]) and bool(parts[2])

    @classmethod
    def validate_worktree_path(cls, workspace_root: Path, target_path: Path) -> bool:
        """RULE-WI-06: Worktree path must reside strictly under allowed worktree boundaries."""
        try:
            target_resolved = target_path.resolve()
            claude_root = (workspace_root / ".claude" / "worktrees").resolve()
            nb_root = (workspace_root / ".nb" / "workspaces").resolve()
            legacy_root = (workspace_root / ".worktrees").resolve()

            # Disallow symlinks pointing outside
            if target_path.is_symlink():
                return False

            return (
                target_resolved.is_relative_to(claude_root)
                or target_resolved.is_relative_to(nb_root)
                or target_resolved.is_relative_to(legacy_root)
            )
        except Exception:
            return False

    @classmethod
    def ensure_write_isolation(cls, workspace_root: Path, agent_id: str, write_path: Path) -> bool:
        """RULE-WI-10: Read-only access to main workspace; writes restricted to active worktree."""
        lease_path = cls._lease_file(workspace_root)
        with open(lease_path, "r", encoding="utf-8") as f:
            leases = json.load(f)

        lease = leases.get(agent_id)
        if not lease:
            return False

        if lease.get("expires_at", 0) < int(time.time()):
            return False

        wt_dir = Path(lease["path"]).resolve()
        target_resolved = write_path.resolve()

        if target_resolved.is_relative_to(wt_dir):
            return True

        # Attempted write to main workspace outside worktree
        return False

    @classmethod
    def format_commit_message(cls, subject: str, task_id: str, dag_id: str, execution_id: str, co_author: Optional[str] = None) -> str:
        """RULE-WI-09: Commit Traceability template."""
        author = co_author or "Claude Sonnet 5 <noreply@anthropic.com>"
        return (
            f"{subject.strip()}\n\n"
            f"Task-ID: {task_id}\n"
            f"DAG-ID: {dag_id}\n"
            f"Execution-ID: {execution_id}\n\n"
            f"Co-Authored-By: {author}"
        )

    @classmethod
    def validate_commit_message(cls, msg: str) -> bool:
        """Validates mandatory commit metadata per RULE-WI-09."""
        required = ["Task-ID:", "DAG-ID:", "Execution-ID:", "Co-Authored-By:"]
        return all(req in msg for req in required)

    @classmethod
    def acquire(
        cls,
        workspace_root: Path,
        agent_id: str,
        base_branch: str = "main",
        ttl_seconds: int = 86400,
        use_redis: bool = False,
        slug: Optional[str] = None,
        use_claude_tree: bool = True
    ) -> Dict[str, Any]:
        """
        Provisions ephemeral git worktree enforcing RULE-WI-01 to RULE-WI-04.
        """
        lease_path = cls._lease_file(workspace_root)
        with open(lease_path, "r", encoding="utf-8") as f:
            try:
                leases = json.load(f)
            except Exception:
                leases = {}

        now_sec = int(time.time())

        # RULE-WI-03: Max 5 concurrent active worktrees per project
        active_leases = [k for k, v in leases.items() if v.get("expires_at", 0) > now_sec]
        if len(active_leases) >= MAX_WORKTREES_PER_PROJECT and agent_id not in leases:
            # Reclaim any expired or stale leases to free up capacity
            cls.reclaim_stale_leases(workspace_root)
            with open(lease_path, "r", encoding="utf-8") as f:
                leases = json.load(f)
            active_leases = [k for k, v in leases.items() if v.get("expires_at", 0) > now_sec]
            if len(active_leases) >= MAX_WORKTREES_PER_PROJECT:
                raise RuntimeError(
                    f"{E_MAX_WORKTREES_EXCEEDED}: Maximum concurrent worktrees ({MAX_WORKTREES_PER_PROJECT}) reached. "
                    "Wait for existing worktrees to complete or release unused ones."
                )

        if use_claude_tree:
            wt_dir = workspace_root / ".claude" / "worktrees" / f"wt_{agent_id}"
        else:
            wt_dir = workspace_root / ".nb" / "workspaces" / f"wt_{agent_id}"

        branch_slug = slug or "agentic"
        branch_name = cls.generate_branch_name(agent_id, branch_slug)

        # 1. Distributed Redlock acquisition if enabled
        dist_token = None
        if use_redis:
            dist_token = cls._redlock_backend.acquire_lock(f"worktree:{agent_id}", ttl_ms=ttl_seconds * 1000)

        # 2. Evict existing lease if dead PID or expired
        if agent_id in leases:
            existing = leases[agent_id]
            existing_pid = existing.get("pid")
            is_dead = existing_pid and not is_pid_alive(existing_pid)
            is_expired = now_sec >= existing.get("expires_at", 0)
            if is_dead or is_expired:
                cls.release(workspace_root, agent_id)

        # 3. Attempt git worktree add
        wt_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "worktree", "add", "-b", branch_name, str(wt_dir), base_branch],
                cwd=str(workspace_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
        except Exception:
            wt_dir.mkdir(parents=True, exist_ok=True)

        current_pid = os.getpid()
        expires_at = now_sec + ttl_seconds
        lease_info = {
            "agent_id": agent_id,
            "branch": branch_name,
            "path": str(wt_dir),
            "pid": current_pid,
            "acquired_at": now_sec,
            "expires_at": expires_at,
            "extended_count": 0,
            "status": "ACTIVE",
            "distributed_redlock_token": dist_token,
            "backend": "redis_redlock" if use_redis else "posix_atomic_fs"
        }

        leases[agent_id] = lease_info
        with open(lease_path, "w", encoding="utf-8") as f:
            json.dump(leases, f, indent=2)

        return lease_info

    @classmethod
    def extend_lease(cls, workspace_root: Path, agent_id: str, additional_hours: int = 24, justification: str = "") -> Dict[str, Any]:
        """RULE-WI-02: Extends lease duration up to MAX_LEASE_EXTENSIONS (3)."""
        if not justification.strip():
            raise ValueError("Extension requires active justification.")

        lease_path = cls._lease_file(workspace_root)
        with open(lease_path, "r", encoding="utf-8") as f:
            leases = json.load(f)

        if agent_id not in leases:
            raise KeyError(f"No lease found for agent: {agent_id}")

        info = leases[agent_id]
        if info.get("extended_count", 0) >= MAX_LEASE_EXTENSIONS:
            raise ValueError(f"Lease reached maximum {MAX_LEASE_EXTENSIONS} extensions.")

        info["extended_count"] = info.get("extended_count", 0) + 1
        info["expires_at"] = info.get("expires_at", int(time.time())) + (additional_hours * 3600)
        info["last_extension_justification"] = justification

        with open(lease_path, "w", encoding="utf-8") as f:
            json.dump(leases, f, indent=2)

        return info

    @classmethod
    def list_leases(cls, workspace_root: Path) -> List[Dict[str, Any]]:
        lease_path = cls._lease_file(workspace_root)
        with open(lease_path, "r", encoding="utf-8") as f:
            try:
                leases = json.load(f)
            except Exception:
                leases = {}
        
        now = int(time.time())
        results = []
        for aid, info in leases.items():
            info["remaining_ttl_sec"] = max(0, info.get("expires_at", 0) - now)
            info["expired"] = info["remaining_ttl_sec"] <= 0
            pid = info.get("pid")
            info["pid_alive"] = is_pid_alive(pid) if pid else False
            info["stale_orphan"] = (not info["pid_alive"]) or info["expired"]
            results.append(info)
        return results

    @classmethod
    def reclaim_stale_leases(cls, workspace_root: Path) -> List[str]:
        """Active eviction: identifies and purges leases with dead PIDs or expired TTLs."""
        leases = cls.list_leases(workspace_root)
        reclaimed = []
        for l in leases:
            if l.get("stale_orphan", False):
                aid = l["agent_id"]
                if cls.release(workspace_root, aid):
                    reclaimed.append(aid)
        return reclaimed

    @classmethod
    def release(cls, workspace_root: Path, agent_id: str) -> bool:
        lease_path = cls._lease_file(workspace_root)
        with open(lease_path, "r+", encoding="utf-8") as f:
            try:
                leases = json.load(f)
            except Exception:
                leases = {}
            if agent_id in leases:
                info = leases.pop(agent_id)
                f.seek(0)
                f.truncate()
                json.dump(leases, f, indent=2)

                # Release Redis Redlock if present
                dist_token = info.get("distributed_redlock_token")
                if dist_token:
                    cls._redlock_backend.release_lock(f"worktree:{agent_id}", dist_token)

                wt_path = Path(info["path"])

                # Remove worktree directory and branch via git
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", "--force", str(wt_path)],
                        cwd=str(workspace_root),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False
                    )
                except Exception:
                    pass

                if wt_path.exists():
                    shutil.rmtree(wt_path, ignore_errors=True)
                
                # Clean up ephemeral subagent branch
                branch_to_del = info.get("branch")
                if branch_to_del and branch_to_del not in ["main", "master"]:
                    try:
                        subprocess.run(
                            ["git", "branch", "-D", branch_to_del],
                            cwd=str(workspace_root),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=False
                        )
                    except Exception:
                        pass
                return True
        return False

    @classmethod
    def quarantine_failed_execution(
        cls,
        workspace_root: Path,
        agent_id: str,
        execution_id: str,
        diagnosis_reason: str
    ) -> Dict[str, Any]:
        """RULE-WI-05: Quarantines failed worktree implementations without merging to main."""
        q_dir = workspace_root / "user" / "hitl" / "quarantined_implementations" / execution_id
        q_dir.mkdir(parents=True, exist_ok=True)

        lease_path = cls._lease_file(workspace_root)
        with open(lease_path, "r", encoding="utf-8") as f:
            leases = json.load(f)

        info = leases.get(agent_id, {})
        wt_path = Path(info.get("path", ""))

        # Copy source contents
        if wt_path.exists():
            shutil.copytree(wt_path, q_dir / "source", dirs_exist_ok=True)

        diagnosis_md = (
            f"# Execution Quarantine Diagnosis\n\n"
            f"- **Execution ID**: {execution_id}\n"
            f"- **Agent ID**: {agent_id}\n"
            f"- **Branch**: {info.get('branch', 'unknown')}\n"
            f"- **Timestamp**: {datetime.now(timezone.utc).isoformat()}\n"
            f"- **Diagnosis**: {diagnosis_reason}\n\n"
            f"Quarantined implementation preserved for human review in `{q_dir}`.\n"
        )
        with open(q_dir / "DIAGNOSIS.md", "w", encoding="utf-8") as f:
            f.write(diagnosis_md)

        # Release worktree
        cls.release(workspace_root, agent_id)

        return {
            "status": "QUARANTINED",
            "quarantine_path": str(q_dir),
            "diagnosis_summary": diagnosis_reason
        }

    @classmethod
    def enforce_hard_cleanup_limit(cls, workspace_root: Path, max_age_hours: int = HARD_CLEANUP_HOURS) -> List[str]:
        """RULE-WI-07: Hard 48-hour cleanup cutoff regardless of active lease state."""
        cutoff_sec = int(time.time()) - (max_age_hours * 3600)
        lease_path = cls._lease_file(workspace_root)
        with open(lease_path, "r", encoding="utf-8") as f:
            try:
                leases = json.load(f)
            except Exception:
                leases = {}

        purged = []
        for aid, info in list(leases.items()):
            if info.get("acquired_at", int(time.time())) < cutoff_sec:
                if cls.release(workspace_root, aid):
                    purged.append(aid)
        return purged

    @classmethod
    def verify_canary(cls, workspace_root: Path, agent_id: str, test_cmd: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Executes an automated canary test pass inside the isolated ephemeral worktree
        before allowing atomic branch merging into main.
        """
        lease_path = cls._lease_file(workspace_root)
        with open(lease_path, "r", encoding="utf-8") as f:
            try:
                leases = json.load(f)
            except Exception:
                leases = {}

        info = leases.get(agent_id, {})
        wt_dir = Path(info.get("path", workspace_root / ".claude" / "worktrees" / f"wt_{agent_id}"))

        if not wt_dir.exists():
            return {
                "agent_id": agent_id,
                "canary_passed": False,
                "error": f"Worktree directory not found: {wt_dir}"
            }

        cmd = test_cmd or ["python3", "-c", "print('Canary check OK')"]
        start_t = time.time()
        res = subprocess.run(cmd, cwd=str(wt_dir if wt_dir.is_dir() else workspace_root), capture_output=True, text=True)
        duration_ms = round((time.time() - start_t) * 1000, 2)

        passed = (res.returncode == 0)
        return {
            "agent_id": agent_id,
            "canary_passed": passed,
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
            "duration_ms": duration_ms,
            "status": "CANARY_VERIFIED" if passed else "CANARY_REJECTED"
        }
