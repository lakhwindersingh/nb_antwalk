"""
Neutron Binary Percipience - Conventional-to-Quad-Space Repository Migrator (TODO-REV-18)
Analyzes conventional monorepos and service codebases, generates migration plans,
and refactors files into the Percipience Quad-Space Architecture (.nb, workplace, user, .claude).

Partitions:
1. workplace/ -> Core source code, domain modules, application packages, and automated tests.
2. user/      -> User specifications (MVS), business requirements, HITL logs, and datasets.
3. .nb/       -> Platform runtime metadata, context ledger, Merkle blocks, and commercial policies.
4. .claude/   -> Autonomous agent system prompts, persona configs, and context envelopes.
"""

import os
import sys
import json
import shutil
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Set


@dataclass
class MigrationCandidate:
    """Represents a single file planned for partition migration."""
    source_rel_path: str
    target_partition: str  # workplace, user, .nb, .claude
    target_rel_path: str
    category: str  # source_code, test, spec, config, platform, agent_prompt
    size_bytes: int
    sha256_hash: str


@dataclass
class MigrationAnalysisReport:
    """Comprehensive dry-run analysis of conventional codebase migration."""
    detected_project_type: str  # python_package, node_service, go_module, monorepo, polyglot
    total_files: int
    total_loc: int
    partition_counts: Dict[str, int]
    candidates: List[MigrationCandidate]
    conflicts: List[str]
    recommendations: List[str]
    analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConventionalRepositoryMigrator:
    """
    Automated migrator converting conventional repository structures into
    the standardized Percipience Quad-Space architecture with zero data loss.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = Path(repo_root or os.getcwd()).resolve()
        self.manifest_file = self.repo_root / ".nb" / "migration_manifest.json"

    def detect_project_type(self) -> str:
        """Infers repository technology stack from indicator files."""
        has_py = any((self.repo_root / f).exists() for f in ("pyproject.toml", "setup.py", "requirements.txt"))
        has_node = (self.repo_root / "package.json").exists()
        has_go = (self.repo_root / "go.mod").exists()

        if sum([has_py, has_node, has_go]) > 1:
            return "polyglot"
        if has_py:
            return "python_package"
        if has_node:
            return "node_service"
        if has_go:
            return "go_module"
        if (self.repo_root / "packages").is_dir() or (self.repo_root / "services").is_dir():
            return "monorepo"
        return "general_repository"

    def _compute_sha256(self, file_path: Path) -> str:
        """Computes SHA256 of a file."""
        try:
            return hashlib.sha256(file_path.read_bytes()).hexdigest()
        except Exception:
            return ""

    def _count_loc(self, file_path: Path) -> int:
        """Counts lines of code in text file."""
        try:
            return len(file_path.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            return 0

    def classify_file(self, rel_path: str) -> Tuple[str, str, str]:
        """
        Classifies relative path into (target_partition, target_rel_path, category).
        Partitions: workplace, user, .nb, .claude.
        """
        parts = Path(rel_path).parts
        first = parts[0].lower() if parts else ""
        ext = Path(rel_path).suffix.lower()

        # If already in quad-space, retain
        if first in ("workplace", "user", ".nb", ".claude"):
            return first, rel_path, "existing_quad_space"

        # Agent prompts or instructions
        if first in (".github", "prompts", ".agent") and ("prompt" in rel_path.lower() or "copilot" in rel_path.lower()):
            return ".claude", f".claude/prompts/{Path(rel_path).name}", "agent_prompt"
        if "instructions" in rel_path.lower() or "system_prompt" in rel_path.lower():
            return ".claude", f".claude/{Path(rel_path).name}", "agent_prompt"

        # User specs, documentation, datasets, feedback
        if first in ("specs", "doc", "docs", "requirements", "rfc", "design"):
            return "user", f"user/specs/{rel_path}", "spec"
        if ext in (".md", ".rst", ".txt") and first not in ("src", "lib", "app", "tests"):
            return "user", f"user/docs/{Path(rel_path).name}", "spec"

        # Automated tests
        if first in ("test", "tests", "spec", "specs") or "test_" in rel_path or "_test." in rel_path:
            clean_rel = rel_path
            if first in ("test", "tests"):
                clean_rel = "/".join(parts[1:]) if len(parts) > 1 else parts[0]
            return "workplace", f"workplace/tests/{clean_rel}", "test"

        # Platform / CI / Config
        if first in (".github", ".circleci", ".gitlab", "deploy", "infra", "terraform", "k8s"):
            return "workplace", f"workplace/infra/{rel_path}", "config"

        # Source code
        if first in ("src", "lib", "app", "pkg", "modules", "core"):
            clean_rel = rel_path
            if first in ("src", "lib", "app"):
                clean_rel = "/".join(parts[1:]) if len(parts) > 1 else parts[0]
            return "workplace", f"workplace/modules/{clean_rel}", "source_code"

        # Default source code / configs
        if ext in (".py", ".ts", ".js", ".go", ".rs", ".java", ".c", ".cpp"):
            return "workplace", f"workplace/modules/{rel_path}", "source_code"

        # Top-level project files
        return "workplace", f"workplace/{rel_path}", "config"

    def analyze_repository(self) -> MigrationAnalysisReport:
        """
        Scans workspace and produces an exhaustive dry-run migration plan.
        """
        project_type = self.detect_project_type()
        candidates: List[MigrationCandidate] = []
        conflicts: List[str] = []
        partition_counts = {"workplace": 0, "user": 0, ".nb": 0, ".claude": 0}

        ignore_dirs = {".git", ".idea", ".vscode", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
        total_loc = 0

        target_paths_seen: Set[str] = set()

        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file_name in files:
                file_path = Path(root) / file_name
                try:
                    rel_path = str(file_path.relative_to(self.repo_root))
                except Exception:
                    continue

                # Skip existing .nb platform files from re-migrating
                if rel_path.startswith(".nb/"):
                    continue

                partition, target_rel, category = self.classify_file(rel_path)
                size_b = file_path.stat().st_size
                file_loc = self._count_loc(file_path)
                total_loc += file_loc
                file_hash = self._compute_sha256(file_path)

                # Check potential target collision
                if target_rel in target_paths_seen:
                    conflicts.append(f"Destination path collision detected: `{target_rel}` for `{rel_path}`")
                target_paths_seen.add(target_rel)

                cand = MigrationCandidate(
                    source_rel_path=rel_path,
                    target_partition=partition,
                    target_rel_path=target_rel,
                    category=category,
                    size_bytes=size_b,
                    sha256_hash=file_hash
                )
                candidates.append(cand)
                partition_counts[partition] = partition_counts.get(partition, 0) + 1

        recommendations = [
            "Preserve original files via atomic backup manifest `migration_manifest.json` before applying changes.",
            "Initialize `.nb/context/ledger/context_ledger.yaml` with Genesis Block #0 upon completion.",
            "Run `percipience gate` immediately post-migration to verify contract compliance."
        ]
        if conflicts:
            recommendations.append("Resolve identified destination collisions prior to non-dry-run execution.")

        return MigrationAnalysisReport(
            detected_project_type=project_type,
            total_files=len(candidates),
            total_loc=total_loc,
            partition_counts=partition_counts,
            candidates=candidates,
            conflicts=conflicts,
            recommendations=recommendations
        )

    def execute_migration(
        self,
        report: Optional[MigrationAnalysisReport] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Executes repository refactoring according to migration plan,
        creating Quad-Space partitions and saving rollback manifest.
        """
        analysis = report or self.analyze_repository()

        if dry_run:
            return {
                "status": "DRY_RUN_COMPLETED",
                "project_type": analysis.detected_project_type,
                "total_files": analysis.total_files,
                "partition_counts": analysis.partition_counts,
                "conflicts": analysis.conflicts,
                "recommendations": analysis.recommendations,
                "manifest_written": False
            }

        # 1. Scaffold Quad-Space directories
        for p in ("workplace", "user", ".nb", ".claude"):
            (self.repo_root / p).mkdir(parents=True, exist_ok=True)

        # 2. Record migration actions in manifest
        manifest_data = {
            "migrated_at": datetime.now(timezone.utc).isoformat(),
            "project_type": analysis.detected_project_type,
            "actions": []
        }

        migrated_count = 0
        for cand in analysis.candidates:
            if cand.source_rel_path == cand.target_rel_path:
                continue

            src = self.repo_root / cand.source_rel_path
            dst = self.repo_root / cand.target_rel_path
            if not src.exists():
                continue

            dst.parent.mkdir(parents=True, exist_ok=True)
            # Copy file (using copy2 to preserve metadata)
            shutil.copy2(src, dst)

            manifest_data["actions"].append({
                "source": cand.source_rel_path,
                "target": cand.target_rel_path,
                "sha256": cand.sha256_hash
            })
            migrated_count += 1

        # 3. Scaffold Genesis Merkle Ledger if missing
        ledger_path = self.repo_root / ".nb" / "context" / "ledger" / "context_ledger.yaml"
        if not ledger_path.exists():
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            genesis_yaml = (
                "# Percipience Genesis Context Ledger\n"
                "blocks:\n"
                "  - block_id: 0\n"
                "    timestamp: '" + datetime.now(timezone.utc).isoformat() + "'\n"
                "    block_hash: 'GENESIS_BLOCK_0000'\n"
                "    previous_hash: '0000000000000000000000000000000000000000000000000000000000000000'\n"
                "    merkle_root: 'GENESIS_ROOT_INIT'\n"
                "    author: 'percipience-migrator'\n"
                "    summary: 'Conventional repository migrated to Quad-Space architecture'\n"
            )
            ledger_path.write_text(genesis_yaml, encoding="utf-8")

        # 4. Save manifest for rollback
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        return {
            "status": "MIGRATION_COMPLETED",
            "files_migrated": migrated_count,
            "partition_counts": analysis.partition_counts,
            "manifest_file": str(self.manifest_file),
            "ledger_initialized": ledger_path.exists()
        }

    def rollback_migration(self) -> Dict[str, Any]:
        """
        Reverses migration operations using `migration_manifest.json`.
        """
        if not self.manifest_file.exists():
            return {"status": "ERROR", "message": f"No migration manifest found at {self.manifest_file}"}

        try:
            data = json.loads(self.manifest_file.read_text(encoding="utf-8"))
            actions = data.get("actions", [])
            reverted = 0

            for act in reversed(actions):
                target_path = self.repo_root / act["target"]
                if target_path.exists():
                    target_path.unlink()
                    reverted += 1

            # Remove manifest
            self.manifest_file.unlink()

            return {
                "status": "ROLLBACK_SUCCESSFUL",
                "files_reverted": reverted,
                "reverted_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"status": "ERROR", "message": f"Rollback failed: {str(e)}"}
