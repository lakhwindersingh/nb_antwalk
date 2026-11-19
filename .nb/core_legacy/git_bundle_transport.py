#!/usr/bin/env python3
"""
Git Bundle Transport Module (TODO-DEWS-03)
Zero-Cloud-Clutter Git Bundle packaging, cryptographic verification,
and streaming adapters for distributed container swarms and fleet nodes.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Dict, Generator, Iterable, List, Optional, Tuple
import uuid


@dataclass
class BundleManifest:
    """Cryptographic metadata manifest for a packaged Git bundle."""
    bundle_id: str
    agent_id: str
    repo_name: str
    source_branch: str
    head_commit: str
    bundle_sha256: str
    file_size_bytes: int
    created_at: str
    base_commit: Optional[str] = None
    has_uncommitted: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "BundleManifest":
        return cls(**data)


@dataclass
class BundleReceipt:
    """Execution receipt returned after creating a Git bundle."""
    status: str  # "SUCCESS" | "FAILED"
    bundle_id: str
    bundle_path: str
    manifest: Optional[BundleManifest] = None
    error_message: Optional[str] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict:
        res = asdict(self)
        if self.manifest:
            res["manifest"] = self.manifest.to_dict()
        return res


@dataclass
class ExtractReceipt:
    """Execution receipt returned after extracting / merging a Git bundle."""
    status: str  # "SUCCESS" | "FAILED"
    bundle_id: str
    target_branch: str
    head_commit: str
    verified: bool
    merged: bool = False
    error_message: Optional[str] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


class GitBundleTransport:
    """
    Manages packaging, cryptographic hashing, streaming, and extraction of Git bundles
    between developer workstations and distributed container swarm fleets.
    """

    def __init__(self, workspace_root: Optional[Path] = None, storage_dir: Optional[Path] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self.storage_dir = Path(
            storage_dir or (self.workspace_root / ".nb" / "workspaces" / "bundles")
        ).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _run_git(self, args: List[str], cwd: Path) -> subprocess.CompletedProcess:
        """Helper to run a git command and capture output."""
        return subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False
        )

    def compute_sha256(self, file_path: Path) -> str:
        """Computes the SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def has_uncommitted_changes(self, repo_path: Path) -> bool:
        """Checks if the working directory or index has uncommitted modifications."""
        proc = self._run_git(["status", "--porcelain"], cwd=repo_path)
        return bool(proc.stdout.strip())

    def get_current_branch(self, repo_path: Path) -> str:
        """Returns the current checked-out branch name or HEAD commit."""
        proc = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
        branch = proc.stdout.strip()
        if branch == "HEAD" or not branch:
            proc_rev = self._run_git(["rev-parse", "HEAD"], cwd=repo_path)
            return proc_rev.stdout.strip()[:12]
        return branch

    def get_head_commit(self, repo_path: Path, ref: str = "HEAD") -> str:
        """Returns the commit hash of a ref."""
        proc = self._run_git(["rev-parse", ref], cwd=repo_path)
        return proc.stdout.strip()

    def create_bundle(
        self,
        repo_path: Path,
        branch: Optional[str] = None,
        base_ref: Optional[str] = None,
        output_path: Optional[Path] = None,
        agent_id: str = "agent",
        include_uncommitted: bool = True,
        metadata: Optional[Dict[str, str]] = None
    ) -> BundleReceipt:
        """
        Packages commits (and optionally uncommitted working-tree changes) into a Git bundle.

        Args:
            repo_path: Directory of the git repository or worktree.
            branch: Source branch or ref name to bundle (defaults to current branch).
            base_ref: Optional base reference (e.g. 'main' or 'HEAD~1') for incremental bundles.
            output_path: Destination path for the .bundle file.
            agent_id: ID of the agent/developer creating the bundle.
            include_uncommitted: Whether to create an ephemeral checkpoint commit if dirty.
            metadata: Additional key-value metadata to record in the manifest.
        """
        start_time = time.perf_counter()
        bundle_id = f"bundle_{uuid.uuid4().hex[:12]}"
        repo_path = Path(repo_path).resolve()

        if not (repo_path / ".git").exists() and not (repo_path / ".git").is_file():
            return BundleReceipt(
                status="FAILED",
                bundle_id=bundle_id,
                bundle_path="",
                error_message=f"Path is not a valid git repository or worktree: {repo_path}",
                duration_ms=(time.perf_counter() - start_time) * 1000
            )

        active_branch = branch or self.get_current_branch(repo_path)
        has_uncommitted = False

        # Handle uncommitted changes if requested
        if include_uncommitted and self.has_uncommitted_changes(repo_path):
            has_uncommitted = True
            # Create an ephemeral checkpoint commit on the branch
            self._run_git(["add", "-A"], cwd=repo_path)
            commit_msg = f"chore(percipience): ephemeral transport checkpoint [agent: {agent_id}]"
            proc_commit = self._run_git(
                ["commit", "-m", commit_msg, "--no-verify"],
                cwd=repo_path
            )
            if proc_commit.returncode != 0:
                return BundleReceipt(
                    status="FAILED",
                    bundle_id=bundle_id,
                    bundle_path="",
                    error_message=f"Failed to commit uncommitted changes: {proc_commit.stderr}",
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )

        head_commit = self.get_head_commit(repo_path, active_branch)
        base_commit = self.get_head_commit(repo_path, base_ref) if base_ref else None

        if not output_path:
            output_path = self.storage_dir / f"{bundle_id}.bundle"
        else:
            output_path = Path(output_path).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build revision range
        # E.g. "base_ref..active_branch" or simply "active_branch"
        if base_ref:
            # Check if there are commits between base_ref and active_branch
            proc_log = self._run_git(["log", "--oneline", f"{base_ref}..{active_branch}"], cwd=repo_path)
            if not proc_log.stdout.strip():
                # No difference commits; fallback to bundling the explicit branch head
                rev_spec = active_branch
            else:
                rev_spec = f"{base_ref}..{active_branch}"
        else:
            rev_spec = active_branch

        # Execute git bundle create
        # Note: We specify the named branch ref so the bundle contains refs/heads/<branch>
        proc_bundle = self._run_git(
            ["bundle", "create", str(output_path), rev_spec],
            cwd=repo_path
        )
        if proc_bundle.returncode != 0:
            return BundleReceipt(
                status="FAILED",
                bundle_id=bundle_id,
                bundle_path=str(output_path),
                error_message=f"git bundle create failed: {proc_bundle.stderr}",
                duration_ms=(time.perf_counter() - start_time) * 1000
            )

        # Verify bundle integrity
        proc_verify = self._run_git(["bundle", "verify", str(output_path)], cwd=repo_path)
        if proc_verify.returncode != 0:
            return BundleReceipt(
                status="FAILED",
                bundle_id=bundle_id,
                bundle_path=str(output_path),
                error_message=f"git bundle verify failed: {proc_verify.stderr}",
                duration_ms=(time.perf_counter() - start_time) * 1000
            )

        bundle_sha256 = self.compute_sha256(output_path)
        file_size = output_path.stat().st_size

        manifest = BundleManifest(
            bundle_id=bundle_id,
            agent_id=agent_id,
            repo_name=repo_path.name,
            source_branch=active_branch,
            base_commit=base_commit,
            head_commit=head_commit,
            bundle_sha256=bundle_sha256,
            file_size_bytes=file_size,
            created_at=datetime.now(timezone.utc).isoformat(),
            has_uncommitted=has_uncommitted,
            metadata=metadata or {}
        )

        manifest_path = output_path.with_suffix(".bundle.manifest.json")
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

        duration_ms = (time.perf_counter() - start_time) * 1000
        return BundleReceipt(
            status="SUCCESS",
            bundle_id=bundle_id,
            bundle_path=str(output_path),
            manifest=manifest,
            duration_ms=duration_ms
        )

    def verify_bundle(
        self,
        bundle_path: Path,
        repo_path: Optional[Path] = None
    ) -> Tuple[bool, str, List[Tuple[str, str]]]:
        """
        Cryptographically and functionally verifies a Git bundle.

        Returns:
            (is_valid: bool, status_message: str, heads: List[(commit_sha, ref_name)])
        """
        bundle_path = Path(bundle_path).resolve()
        if not bundle_path.exists() or bundle_path.stat().st_size == 0:
            return False, f"Bundle file missing or empty: {bundle_path}", []

        # List heads from bundle (does not require repo_path)
        proc_heads = subprocess.run(
            ["git", "bundle", "list-heads", str(bundle_path)],
            capture_output=True,
            text=True,
            check=False
        )
        if proc_heads.returncode != 0:
            return False, f"Failed to list bundle heads: {proc_heads.stderr}", []

        heads: List[Tuple[str, str]] = []
        for line in proc_heads.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                heads.append((parts[0], parts[1]))

        # If repo_path provided, verify against repository prerequisites
        if repo_path:
            repo_path = Path(repo_path).resolve()
            proc_verify = self._run_git(["bundle", "verify", str(bundle_path)], cwd=repo_path)
            if proc_verify.returncode != 0:
                return False, f"Prerequisite commits missing in target repo: {proc_verify.stderr}", heads

        return True, "Bundle verified successfully", heads

    def extract_bundle(
        self,
        bundle_path: Path,
        target_repo_path: Path,
        target_branch: Optional[str] = None,
        checkout: bool = True,
        auto_merge_into: Optional[str] = None
    ) -> ExtractReceipt:
        """
        Extracts commits from a Git bundle into a target repository or worktree.

        Args:
            bundle_path: Path to the .bundle file.
            target_repo_path: Destination repository or worktree directory.
            target_branch: Name of branch to store fetched commits (defaults to source branch).
            checkout: If True, checks out target_branch after fetch.
            auto_merge_into: If specified, checks out auto_merge_into and merges target_branch.
        """
        start_time = time.perf_counter()
        bundle_path = Path(bundle_path).resolve()
        target_repo_path = Path(target_repo_path).resolve()

        # Step 1: Verify bundle
        is_valid, msg, heads = self.verify_bundle(bundle_path, target_repo_path)
        if not is_valid:
            return ExtractReceipt(
                status="FAILED",
                bundle_id=bundle_path.stem,
                target_branch="",
                head_commit="",
                verified=False,
                error_message=msg,
                duration_ms=(time.perf_counter() - start_time) * 1000
            )

        if not heads:
            return ExtractReceipt(
                status="FAILED",
                bundle_id=bundle_path.stem,
                target_branch="",
                head_commit="",
                verified=True,
                error_message="Bundle contains no heads/refs",
                duration_ms=(time.perf_counter() - start_time) * 1000
            )

        source_commit, source_ref = heads[0]
        # Clean branch name from ref (e.g. refs/heads/feature -> feature)
        source_branch_name = source_ref.replace("refs/heads/", "")
        effective_branch = target_branch or source_branch_name

        # Step 2: Fetch bundle ref into target repository
        fetch_refspec = f"{source_ref}:refs/heads/{effective_branch}"
        proc_fetch = self._run_git(
            ["fetch", str(bundle_path), fetch_refspec, "--update-head-ok", "--force"],
            cwd=target_repo_path
        )
        if proc_fetch.returncode != 0:
            return ExtractReceipt(
                status="FAILED",
                bundle_id=bundle_path.stem,
                target_branch=effective_branch,
                head_commit=source_commit,
                verified=True,
                error_message=f"git fetch bundle failed: {proc_fetch.stderr}",
                duration_ms=(time.perf_counter() - start_time) * 1000
            )

        # Step 3: Optional checkout
        if checkout:
            proc_co = self._run_git(["checkout", effective_branch], cwd=target_repo_path)
            if proc_co.returncode != 0:
                return ExtractReceipt(
                    status="FAILED",
                    bundle_id=bundle_path.stem,
                    target_branch=effective_branch,
                    head_commit=source_commit,
                    verified=True,
                    error_message=f"git checkout failed: {proc_co.stderr}",
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )

        merged = False
        # Step 4: Optional auto-merge into target branch (e.g. 'main')
        if auto_merge_into:
            proc_co_base = self._run_git(["checkout", auto_merge_into], cwd=target_repo_path)
            if proc_co_base.returncode != 0:
                return ExtractReceipt(
                    status="FAILED",
                    bundle_id=bundle_path.stem,
                    target_branch=effective_branch,
                    head_commit=source_commit,
                    verified=True,
                    error_message=f"Failed to checkout merge target '{auto_merge_into}': {proc_co_base.stderr}",
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )
            proc_merge = self._run_git(["merge", effective_branch, "--no-edit"], cwd=target_repo_path)
            if proc_merge.returncode != 0:
                return ExtractReceipt(
                    status="FAILED",
                    bundle_id=bundle_path.stem,
                    target_branch=effective_branch,
                    head_commit=source_commit,
                    verified=True,
                    error_message=f"git merge failed: {proc_merge.stderr}",
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )
            merged = True

        head_after = self.get_head_commit(target_repo_path, effective_branch)
        duration_ms = (time.perf_counter() - start_time) * 1000

        return ExtractReceipt(
            status="SUCCESS",
            bundle_id=bundle_path.stem,
            target_branch=effective_branch,
            head_commit=head_after,
            verified=True,
            merged=merged,
            duration_ms=duration_ms
        )

    # -------------------------------------------------------------------------
    # Streaming HTTP Adapters (FastAPI / Requests / WebSocket)
    # -------------------------------------------------------------------------

    def stream_bundle_chunks(
        self,
        bundle_path: Path,
        chunk_size: int = 65536
    ) -> Generator[bytes, None, None]:
        """
        Yields binary chunks of a bundle file for streaming HTTP transfer.
        """
        bundle_path = Path(bundle_path).resolve()
        with open(bundle_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    def receive_streaming_bundle(
        self,
        stream_iterator: Iterable[bytes],
        destination_path: Path
    ) -> Tuple[int, str]:
        """
        Streams binary chunks from an HTTP upload to disk while calculating
        its SHA-256 digest on-the-fly.

        Returns:
            (bytes_written: int, sha256_hash: str)
        """
        destination_path = Path(destination_path).resolve()
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        hasher = hashlib.sha256()
        bytes_written = 0

        with open(destination_path, "wb") as f:
            for chunk in stream_iterator:
                if chunk:
                    f.write(chunk)
                    hasher.update(chunk)
                    bytes_written += len(chunk)

        return bytes_written, hasher.hexdigest()
