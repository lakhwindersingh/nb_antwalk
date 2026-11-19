#!/usr/bin/env python3
"""
Percipience Capability-Based Access Control (CBAC) Sandbox Guard (GAP-AGT-05 / TODO-AGT-05)
Enforces cryptographic capability tokens, path-bound filesystem write restrictions,
subprocess command whitelisting, and network egress firewalling for autonomous agents.
"""

import base64
import hashlib
import hmac
import json
import os
import shlex
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

REPO_ROOT = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) >= 3 and (Path(__file__).resolve().parents[2] / ".nb").exists() else Path(__file__).resolve().parents[1]


class AgentCapabilityGuard:
    """
    Validates HMAC-SHA256 capability tokens and enforces sandbox boundaries
    across filesystem operations, subprocess execution, and network egress.
    """

    DEFAULT_SECRET: str = "percipience_cbac_secret_enclave_key_2026"

    PROTECTED_DIRS = [
        ".nb/core",
        ".nb/context/rules",
        ".nb/context/invariants",
        ".git"
    ]

    WHITELISTED_COMMANDS = {
        "pytest", "git", "python3", "python", "node", "npm", "tsc", "pyright", "ruff", "flake8"
    }

    BLOCKED_COMMANDS = {
        "curl", "wget", "rm", "nc", "netcat", "bash", "sh", "zsh", "pip", "chmod", "chown", "dd", "mkfs"
    }

    LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

    @classmethod
    def mint_token(
        cls,
        agent_id: str,
        worktree_path: str,
        allowed_operations: List[str],
        ttl_seconds: int = 3600,
        secret_key: Optional[str] = None
    ) -> str:
        """
        Mints a cryptographic HMAC-SHA256 capability token bound to an agent ID,
        target worktree directory, allowed capability flags, and expiry time.
        """
        secret = (secret_key or cls.DEFAULT_SECRET).encode("utf-8")
        now = time.time()
        payload = {
            "agent_id": agent_id,
            "worktree_path": str(Path(worktree_path).resolve()),
            "allowed_operations": list(allowed_operations),
            "issued_at": now,
            "expires_at": now + ttl_seconds
        }
        raw_json = json.dumps(payload, sort_keys=True)
        encoded_payload = base64.urlsafe_b64encode(raw_json.encode("utf-8")).decode("utf-8")
        signature = hmac.new(secret, encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{encoded_payload}.{signature}"

    @classmethod
    def verify_token(
        cls,
        token_str: str,
        secret_key: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Verifies the cryptographic signature and expiration of a capability token.
        Returns (is_valid, payload, error_message).
        """
        secret = (secret_key or cls.DEFAULT_SECRET).encode("utf-8")
        parts = token_str.split(".")
        if len(parts) != 2:
            return False, None, "PERMISSION_DENIED_INVALID_TOKEN: Malformed token structure"

        encoded_payload, signature = parts
        expected_sig = hmac.new(secret, encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return False, None, "PERMISSION_DENIED_INVALID_TOKEN: Invalid cryptographic signature"

        try:
            raw_json = base64.urlsafe_b64decode(encoded_payload.encode("utf-8")).decode("utf-8")
            payload = json.loads(raw_json)
        except Exception:
            return False, None, "PERMISSION_DENIED_INVALID_TOKEN: Payload decode error"

        if time.time() > payload.get("expires_at", 0):
            return False, payload, "PERMISSION_DENIED_EXPIRED_TOKEN: Capability token has expired"

        return True, payload, None

    @classmethod
    def check_fs_access(
        cls,
        token_str: str,
        target_path: str,
        operation: str = "write",
        repo_root: Optional[Path] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Checks whether the token allows reading or writing the target file.
        Intercepts traversal attacks and protects platform core assets.
        """
        valid, payload, err = cls.verify_token(token_str)
        if not valid:
            return False, err

        allowed_ops = payload.get("allowed_operations", [])
        worktree_p = Path(payload.get("worktree_path", "")).resolve()
        target_p = Path(target_path).resolve()
        root = repo_root or REPO_ROOT

        # 1. Operation capability check
        if operation == "read":
            if "CAP_FS_READ" not in allowed_ops:
                return False, "PERMISSION_DENIED_OPERATION_NOT_PERMITTED: CAP_FS_READ required"
            return True, None

        if operation == "write":
            if "CAP_FS_WRITE_MODULE_ONLY" not in allowed_ops and "CAP_FS_WRITE" not in allowed_ops:
                return False, "PERMISSION_DENIED_OPERATION_NOT_PERMITTED: CAP_FS_WRITE_MODULE_ONLY required"

            # 2. Protected directories check (e.g. .nb/core, .nb/context/rules, .git)
            for protected in cls.PROTECTED_DIRS:
                protected_abs = (root / protected).resolve()
                if target_p == protected_abs or protected_abs in target_p.parents:
                    return False, f"PERMISSION_DENIED_PATH_RESTRICTED: Write forbidden to protected directory '{protected}'"

            # 3. Worktree path containment check (must be inside assigned worktree)
            try:
                target_p.relative_to(worktree_p)
            except ValueError:
                return False, f"PERMISSION_DENIED_PATH_RESTRICTED: Path '{target_path}' is outside assigned worktree '{worktree_p}'"

            return True, None

        return False, f"PERMISSION_DENIED_UNKNOWN_OPERATION: Operation '{operation}' unrecognized"

    @classmethod
    def check_subprocess_command(
        cls,
        token_str: str,
        command: Any
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates command execution against the capability token and command whitelist.
        Blocks dangerous binaries and shell escapes.
        """
        valid, payload, err = cls.verify_token(token_str)
        if not valid:
            return False, err

        allowed_ops = payload.get("allowed_operations", [])
        if "CAP_EXEC_SUBPROCESS" not in allowed_ops:
            return False, "PERMISSION_DENIED_OPERATION_NOT_PERMITTED: CAP_EXEC_SUBPROCESS required"

        # Extract binary name
        if isinstance(command, str):
            parts = shlex.split(command)
        elif isinstance(command, (list, tuple)):
            parts = list(command)
        else:
            return False, "PERMISSION_DENIED_INVALID_COMMAND: Command must be string or list"

        if not parts:
            return False, "PERMISSION_DENIED_INVALID_COMMAND: Empty command"

        binary = Path(parts[0]).name.lower()

        # 1. Hard blocked check
        if binary in cls.BLOCKED_COMMANDS:
            return False, f"PERMISSION_DENIED_UNAUTHORIZED_COMMAND: Command '{binary}' is strictly prohibited"

        # Check for dangerous arguments like rm -rf
        full_cmd_str = " ".join(parts).lower()
        if "rm -rf" in full_cmd_str or "rm -r" in full_cmd_str:
            return False, "PERMISSION_DENIED_UNAUTHORIZED_COMMAND: Recursive removal command prohibited"

        # 2. Whitelist check
        if binary not in cls.WHITELISTED_COMMANDS:
            return False, f"PERMISSION_DENIED_UNAUTHORIZED_COMMAND: Binary '{binary}' is not on the execution whitelist"

        return True, None

    @classmethod
    def check_network_egress(
        cls,
        token_str: str,
        host: str,
        port: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates outbound network egress. Loopback/local virtual test bridges are allowed;
        external connections require explicit CAP_NETWORK_EGRESS capability flag.
        """
        valid, payload, err = cls.verify_token(token_str)
        if not valid:
            return False, err

        allowed_ops = payload.get("allowed_operations", [])
        clean_host = host.lower().strip()

        # Local virtual loopback sockets always permitted for testing/mock services
        if clean_host in cls.LOOPBACK_HOSTS:
            return True, None

        # External host requires CAP_NETWORK_EGRESS
        if "CAP_NETWORK_EGRESS" not in allowed_ops and "CAP_NET_EGRESS" not in allowed_ops:
            return False, f"PERMISSION_DENIED_NETWORK_EGRESS_BLOCKED: External connection to {host}:{port} forbidden without CAP_NETWORK_EGRESS"

        return True, None
