"""
Percipience Multi-Dimensional Token Optimization & Context Compression Suite
Provides granular, optional, and multi-tier context compression strategies across:
1. AST Skeleton Pruning (Python, TypeScript, Go, Rust, JavaScript)
2. Markdown & Living Docs Pruning (badges, tables, prose boilerplate)
3. Config & JSONSchema Minification (YAML/JSON comments, empty defaults)
4. Diagnostic Log & Stack Trace Slicing (minimal failure context)
5. Git Diff & Lockfile Pruning (clamps context, excludes lockfiles/binaries)
6. Conversation Memory Compaction (multi-turn rolling state summarization)

Includes full configuration management (enable/disable, presets, custom overrides)
for both workspace CLI operations and web portal controls.
"""

import os
import re
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

try:
    import yaml
    try:
        from yaml import CSafeLoader as SafeLoader, CSafeDumper as SafeDumper
    except ImportError:
        from yaml import SafeLoader, SafeDumper
except ImportError:
    yaml = None
    SafeLoader = None
    SafeDumper = None

REPO_ROOT = Path(__file__).resolve().parents[2]


class TokenOptimizationConfig:
    """Manages workspace and portal token optimization configuration."""

    CONFIG_FILE = ".nb/config/token_compression_rules.yaml"

    DEFAULT_CONFIG = {
        "token_optimization": {
            "enabled": True,
            "mode": "standard",  # "disabled", "conservative", "standard", "aggressive", "extreme"
            "strategies": {
                "ast_skeleton_pruning": True,
                "markdown_doc_pruning": True,
                "config_schema_minification": True,
                "diagnostic_log_slicing": True,
                "git_diff_pruning": True,
                "conversation_memory_compaction": True
            },
            "excluded_paths": [
                "node_modules/**",
                ".git/**",
                "**/*.min.js",
                "**/*.min.css"
            ],
            "excluded_extensions": [
                ".lock",
                ".sum",
                ".min.js",
                ".min.css",
                ".map",
                ".png",
                ".jpg",
                ".svg"
            ],
            "portal_controls": {
                "allow_user_override": True,
                "show_realtime_roi_widget": True,
                "default_model_rate_card": "claude-3-5-sonnet-20241022"
            }
        }
    }

    @classmethod
    def get_config_path(cls, repo_root: Path = REPO_ROOT) -> Path:
        nb_p = repo_root / ".nb" / "config" / "token_compression_rules.yaml"
        if nb_p.exists():
            return nb_p
        wp_p = repo_root / "workplace" / "config" / "token_compression_rules.yaml"
        if wp_p.exists():
            return wp_p
        p = repo_root / cls.CONFIG_FILE
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def load_config(cls, repo_root: Path = REPO_ROOT) -> Dict[str, Any]:
        p = cls.get_config_path(repo_root)
        if not p.exists():
            cls.save_config(cls.DEFAULT_CONFIG, repo_root)
            return cls.DEFAULT_CONFIG

        try:
            with open(p, "r", encoding="utf-8") as f:
                if yaml and SafeLoader:
                    data = yaml.load(f, Loader=SafeLoader) or {}
                elif yaml:
                    data = yaml.safe_load(f) or {}
                else:
                    data = json.load(f) or {}

                if "token_optimization" not in data:
                    data["token_optimization"] = cls.DEFAULT_CONFIG["token_optimization"]
                return data
        except Exception:
            return cls.DEFAULT_CONFIG

    @classmethod
    def save_config(cls, config_data: Dict[str, Any], repo_root: Path = REPO_ROOT) -> None:
        p = cls.get_config_path(repo_root)
        with open(p, "w", encoding="utf-8") as f:
            if yaml and SafeDumper:
                yaml.dump(config_data, f, Dumper=SafeDumper, sort_keys=False)
            elif yaml:
                yaml.dump(config_data, f, sort_keys=False)
            else:
                json.dump(config_data, f, indent=2)

    @classmethod
    def is_enabled(cls, repo_root: Path = REPO_ROOT) -> bool:
        cfg = cls.load_config(repo_root)
        return bool(cfg.get("token_optimization", {}).get("enabled", True))

    @classmethod
    def is_strategy_enabled(cls, strategy_name: str, repo_root: Path = REPO_ROOT) -> bool:
        if not cls.is_enabled(repo_root):
            return False
        cfg = cls.load_config(repo_root)
        strategies = cfg.get("token_optimization", {}).get("strategies", {})
        return bool(strategies.get(strategy_name, True))

    @classmethod
    def set_enabled(cls, enabled: bool, repo_root: Path = REPO_ROOT) -> Dict[str, Any]:
        cfg = cls.load_config(repo_root)
        cfg.setdefault("token_optimization", {})["enabled"] = enabled
        if not enabled:
            cfg["token_optimization"]["mode"] = "disabled"
        elif cfg["token_optimization"].get("mode") == "disabled":
            cfg["token_optimization"]["mode"] = "standard"
        cls.save_config(cfg, repo_root)
        return cfg

    @classmethod
    def set_mode(cls, mode: str, repo_root: Path = REPO_ROOT) -> Dict[str, Any]:
        valid_modes = ["disabled", "conservative", "standard", "aggressive", "extreme"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of {valid_modes}")
        cfg = cls.load_config(repo_root)
        cfg.setdefault("token_optimization", {})["mode"] = mode
        cfg["token_optimization"]["enabled"] = (mode != "disabled")
        cls.save_config(cfg, repo_root)
        return cfg

    @classmethod
    def set_strategy(cls, strategy_name: str, enabled: bool, repo_root: Path = REPO_ROOT) -> Dict[str, Any]:
        cfg = cls.load_config(repo_root)
        strategies = cfg.setdefault("token_optimization", {}).setdefault("strategies", {})
        strategies[strategy_name] = enabled
        cls.save_config(cfg, repo_root)
        return cfg


class DocPruner:
    """Optimizes Markdown and Living Documentation context payloads."""

    @classmethod
    def prune_markdown(cls, markdown_text: str, mode: str = "standard") -> Tuple[str, Dict[str, int]]:
        """
        Prunes markdown text:
        - Removes badge lines (e.g. [![...](...)](...))
        - Strips excessive HTML comments
        - Compresses long markdown tables (keeps header + first 3 rows + summary row)
        - In aggressive mode: strips decorative callout boilerplate and trims prose
        """
        original_tokens = max(1, len(markdown_text) // 4)
        lines = markdown_text.splitlines()
        pruned_lines = []
        in_table = False
        table_rows = 0

        for line in lines:
            stripped = line.strip()

            # Strip badge markdown links
            if re.match(r"^\[!\[.*\]\(.*\)\]\(.*\)$", stripped) or re.match(r"^!\[.*\]\(https://img\.shields\.io/.*\)$", stripped):
                continue

            # Strip HTML comment lines
            if stripped.startswith("<!--") and stripped.endswith("-->"):
                continue

            # Handle Markdown tables
            if stripped.startswith("|") and stripped.endswith("|"):
                if not in_table:
                    in_table = True
                    table_rows = 0
                table_rows += 1

                # Keep header, separator, and top rows
                if mode in ["aggressive", "extreme"] and table_rows > 4:
                    if table_rows == 5:
                        pruned_lines.append("| ... | ... (additional rows truncated for context efficiency) |")
                    continue
                pruned_lines.append(line)
                continue
            else:
                in_table = False
                table_rows = 0

            # Aggressive prose pruning
            if mode in ["aggressive", "extreme"] and (stripped.startswith("> [!NOTE]") or stripped.startswith("> [!TIP]")):
                continue

            pruned_lines.append(line)

        pruned_text = "\n".join(pruned_lines)
        pruned_tokens = max(1, len(pruned_text) // 4)
        saved_tokens = max(0, original_tokens - pruned_tokens)

        return pruned_text, {
            "uncompressed_tokens": original_tokens,
            "pruned_tokens": pruned_tokens,
            "saved_tokens": saved_tokens,
            "reduction_pct": round(saved_tokens / original_tokens * 100.0, 1)
        }


class ConfigSchemaPruner:
    """Minifies YAML, JSON, and JSONSchema data structures for agent context."""

    @classmethod
    def prune_yaml(cls, yaml_text: str, mode: str = "standard") -> Tuple[str, Dict[str, int]]:
        original_tokens = max(1, len(yaml_text) // 4)
        lines = yaml_text.splitlines()
        pruned_lines = []

        for line in lines:
            stripped = line.strip()
            # Strip pure comment lines
            if stripped.startswith("#"):
                continue
            # Strip empty null fields in aggressive mode
            if mode in ["aggressive", "extreme"] and (stripped.endswith(": null") or stripped.endswith(": []") or stripped.endswith(": {}")):
                continue
            # Strip trailing inline comments
            if "#" in line and not ('"' in line or "'" in line):
                line = line.split("#")[0].rstrip()
            pruned_lines.append(line)

        pruned_text = "\n".join(pruned_lines)
        pruned_tokens = max(1, len(pruned_text) // 4)
        saved_tokens = max(0, original_tokens - pruned_tokens)

        return pruned_text, {
            "uncompressed_tokens": original_tokens,
            "pruned_tokens": pruned_tokens,
            "saved_tokens": saved_tokens,
            "reduction_pct": round(saved_tokens / original_tokens * 100.0, 1)
        }

    @classmethod
    def prune_json(cls, json_text: str, mode: str = "standard") -> Tuple[str, Dict[str, int]]:
        original_tokens = max(1, len(json_text) // 4)
        try:
            data = json.loads(json_text)
            if mode in ["aggressive", "extreme"]:
                # Remove descriptions and titles from schema definitions
                def clean_schema(obj):
                    if isinstance(obj, dict):
                        return {k: clean_schema(v) for k, v in obj.items() if k not in ["description", "$comment", "examples"]}
                    elif isinstance(obj, list):
                        return [clean_schema(elem) for elem in obj]
                    return obj
                data = clean_schema(data)
            minified = json.dumps(data, separators=(",", ":"))
        except Exception:
            minified = json_text

        pruned_tokens = max(1, len(minified) // 4)
        saved_tokens = max(0, original_tokens - pruned_tokens)

        return minified, {
            "uncompressed_tokens": original_tokens,
            "pruned_tokens": pruned_tokens,
            "saved_tokens": saved_tokens,
            "reduction_pct": round(saved_tokens / original_tokens * 100.0, 1)
        }


class DiagnosticLogPruner:
    """
    Advanced Multi-Dialect Diagnostic Log & Traceback Slicer.
    Slices massive test outputs, stack traces, and compiler errors down to minimal failure frames.
    Filters out-of-tree noise (site-packages, node_modules) and auto-hydrates surrounding source AST snippets.
    Supports SLA-aware tiered prompt generation for bounded 3-attempt healing loops.
    """

    OUT_OF_TREE_NOISE_PATTERNS = [
        "site-packages/",
        "_pytest/",
        "lib/python",
        "node_modules/",
        "<frozen ",
        "internal/process/",
        "target/debug/build/",
        "/usr/lib/",
        "/Library/Frameworks/"
    ]

    FRAMEWORK_FAILURE_KEYWORDS = [
        "FAILED", "ERROR", "Traceback (most recent call last):",
        "AssertionError", "SyntaxError", "KeyError", "TypeError",
        "ValueError", "InvalidTokenError", "NullPointer",
        "expect(received).toEqual(expected)", "● ", "panic:",
        "goroutine ", "assertion failed:", "error[E", "error TS"
    ]

    @classmethod
    def prune_traceback(
        cls,
        raw_log: str,
        max_frames: int = 3,
        filter_out_of_tree: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Multi-language and framework-aware traceback slicer with out-of-tree noise filtering.
        """
        original_tokens = max(1, len(raw_log) // 4)
        lines = raw_log.splitlines()

        failure_lines = []
        in_failure_block = False
        captured_frames = 0
        detected_language = "generic"

        # Detect dialect / framework
        if any("pytest" in l or "Traceback" in l or "AssertionError" in l for l in lines):
            detected_language = "python_pytest"
        elif any("jest" in l or "vitest" in l or "●" in l or "expect(" in l for l in lines):
            detected_language = "typescript_jest"
        elif any("panic:" in l or "goroutine " in l for l in lines):
            detected_language = "go_panic"
        elif any("error[E" in l or "panicked at" in l for l in lines):
            detected_language = "rust_compiler"
        elif any("error TS" in l for l in lines):
            detected_language = "typescript_compiler"

        for line in lines:
            line_str = line.strip()
            # 1. Capture failure headers, assertion lines, and exception types
            if any(k in line for k in cls.FRAMEWORK_FAILURE_KEYWORDS):
                in_failure_block = True
                failure_lines.append(line)
                continue

            if in_failure_block:
                # Filter out-of-tree runner frames if requested
                if filter_out_of_tree and any(np in line for np in cls.OUT_OF_TREE_NOISE_PATTERNS):
                    continue

                if line_str.startswith("File ") or line_str.startswith("E   ") or line_str.startswith("at ") or line_str.startswith("--> "):
                    failure_lines.append(line)
                    captured_frames += 1
                elif line_str.startswith("===") or line_str.startswith("---") or line_str.startswith("Expected:") or line_str.startswith("Received:"):
                    failure_lines.append(line)
                    if captured_frames >= max_frames:
                        in_failure_block = False

        if not failure_lines:
            # Fallback to last 15 lines if no structured failure blocks matched
            failure_lines = [l for l in lines[-15:] if not (filter_out_of_tree and any(np in l for np in cls.OUT_OF_TREE_NOISE_PATTERNS))]
            if not failure_lines:
                failure_lines = lines[-10:]

        pruned_text = "\n".join(failure_lines)
        pruned_tokens = max(1, len(pruned_text) // 4)
        saved_tokens = max(0, original_tokens - pruned_tokens)

        return pruned_text, {
            "uncompressed_tokens": original_tokens,
            "pruned_tokens": pruned_tokens,
            "saved_tokens": saved_tokens,
            "reduction_pct": round(saved_tokens / original_tokens * 100.0, 1),
            "dialect": detected_language,
            "captured_frames": captured_frames
        }

    @classmethod
    def extract_failure_site(cls, raw_log: str) -> Optional[Dict[str, Any]]:
        """
        Extracts the target file path, line number, and root error message from a raw log.
        """
        lines = raw_log.splitlines()

        # 1. Python Pytest / Traceback: File "workplace/core/auth.py", line 42, in check_jwt_signature
        for line in reversed(lines):
            if any(np in line for np in cls.OUT_OF_TREE_NOISE_PATTERNS):
                continue
            py_match = re.search(r'File "([^"]+)", line (\d+)(?:, in (\w+))?', line)
            if py_match:
                return {
                    "file_path": py_match.group(1),
                    "line_number": int(py_match.group(2)),
                    "function_name": py_match.group(3) or "",
                    "dialect": "python"
                }

        # 2. TypeScript / Jest: at Object.<anonymous> (src/app.ts:45:10)
        for line in reversed(lines):
            if any(np in line for np in cls.OUT_OF_TREE_NOISE_PATTERNS):
                continue
            ts_match = re.search(r'at (?:.*? )?\(?([^:\s\(\)]+):(\d+)(?::\d+)?\)?', line)
            if ts_match:
                return {
                    "file_path": ts_match.group(1),
                    "line_number": int(ts_match.group(2)),
                    "function_name": "",
                    "dialect": "typescript"
                }

        # 3. Compiler Error: src/index.ts:12:5 - error TS2322
        for line in lines:
            comp_match = re.search(r'^([^:\s]+):(\d+):?(?:\d+)?\s*(?:-\s*error|error)', line)
            if comp_match:
                return {
                    "file_path": comp_match.group(1),
                    "line_number": int(comp_match.group(2)),
                    "function_name": "",
                    "dialect": "compiler"
                }

        return None

    @classmethod
    def hydrate_source_snippet(
        cls,
        workspace_root: Path,
        file_path: str,
        line_number: int,
        context_lines: int = 4
    ) -> Optional[str]:
        """
        Auto-hydrates surrounding source code snippet (±context_lines) with the failure line highlighted.
        """
        target_path = Path(file_path)
        if not target_path.is_absolute():
            target_path = workspace_root / target_path

        if not target_path.exists() or not target_path.is_file():
            return None

        try:
            content = target_path.read_text(encoding="utf-8", errors="ignore")
            all_lines = content.splitlines()
            total_lines = len(all_lines)

            start_idx = max(0, line_number - 1 - context_lines)
            end_idx = min(total_lines, line_number + context_lines)

            snippet_lines = []
            for i in range(start_idx, end_idx):
                curr_line_no = i + 1
                prefix = ">> " if curr_line_no == line_number else "   "
                snippet_lines.append(f"{prefix}{curr_line_no:4d} | {all_lines[i]}")

            return "\n".join(snippet_lines)
        except Exception:
            return None

    @classmethod
    def build_tiered_diagnostic_envelope(
        cls,
        workspace_root: Path,
        raw_log: str,
        attempt: int = 1,
        max_attempts: int = 3,
        module_id: str = "mod_default",
        invariants: Optional[List[str]] = None,
        source_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Constructs an SLA-aware tiered diagnostic prompt envelope:
        - Attempt 1: Minimal leaf frame + root diff (Fast surgical repair).
        - Attempt 2: Leaf frame + wire contract invariants + AST signatures (Method-level refactor).
        - Attempt 3: Full diagnostic envelope + invariants + Final SLA Escalation Warning before surgical rollback.
        """
        invariants = invariants or [
            "NEVER hardcode API keys, tokens, or plaintext secrets. Use process.env or os.environ.",
            "DO NOT import unverified third-party dependencies.",
            "Ensure backwards compatibility with existing wire contracts.",
            "Return ONLY the unified patch diff or clean replacement function."
        ]
        pruned_trace, stats = cls.prune_traceback(raw_log, max_frames=2 if attempt == 1 else 4, filter_out_of_tree=True)
        failure_site = cls.extract_failure_site(raw_log)

        source_snippet = ""
        if failure_site:
            source_snippet = cls.hydrate_source_snippet(
                workspace_root,
                failure_site["file_path"],
                failure_site["line_number"],
                context_lines=3 if attempt == 1 else 5
            ) or ""

        envelope_lines = [
            f"# PERCIPIENCE TIERED DIAGNOSTIC ENVELOPE (ATTEMPT {attempt}/{max_attempts})",
            f"**Target Module**: `{module_id}` | **SLA Attempt**: {attempt} of {max_attempts}",
            ""
        ]

        if attempt == 1:
            envelope_lines.extend([
                "### 1. Minimal Failure Trace (Root Assertion):",
                f"```\n" + pruned_trace + "\n```",
                ""
            ])
            if source_snippet:
                envelope_lines.extend([
                    f"### 2. Source Context (`{failure_site['file_path']}:{failure_site['line_number']}`):",
                    f"```\n" + source_snippet + "\n```",
                    ""
                ])
            envelope_lines.extend([
                "### 3. Invariant & Security Constraints:",
                *[f"- {inv}" for inv in invariants],
                "",
                "### 4. Repair Directive (Attempt 1 SLA - Fast Surgical Patch):",
                "- Provide a minimal, isolated patch targeting only the assertion failure above.",
                "- Do NOT refactor unaffected methods or contracts.",
                ""
            ])

        elif attempt == 2:
            envelope_lines.extend([
                "### 1. Diagnostic Failure Frame & Traceback:",
                f"```\n" + pruned_trace + "\n```",
                ""
            ])
            if source_snippet:
                envelope_lines.extend([
                    f"### 2. Offending Source Frame (`{failure_site['file_path']}:{failure_site['line_number']}`):",
                    f"```\n" + source_snippet + "\n```",
                    ""
                ])
            envelope_lines.extend([
                "### 3. Mandatory Wire Contract & Invariant Constraints:",
                *[f"- {inv}" for inv in invariants],
                "",
                "### 4. Repair Directive (Attempt 2 SLA - Method-Level Invariant Refactor):",
                "- Attempt 1 did not clear all tests. Refactor the method logic while strictly obeying the wire contract invariants above.",
                ""
            ])

        else:  # Attempt 3 (Final SLA Attempt)
            envelope_lines.extend([
                "⚠️ **CRITICAL SLA WARNING: FINAL ATTEMPT BEFORE SURGICAL ROLLBACK (RP_k)**",
                "If this patch fails verification, Percipience will immediately quarantine the turn and rewind the culprit micro-module to the last verified Recovery Point.",
                "",
                "### 1. Full Diagnostic Traceback:",
                f"```\n" + pruned_trace + "\n```",
                ""
            ])
            if source_snippet:
                envelope_lines.extend([
                    f"### 2. Offending Code Context (`{failure_site['file_path']}:{failure_site['line_number']}`):",
                    f"```\n" + source_snippet + "\n```",
                    ""
                ])
            envelope_lines.extend([
                "### 3. All Module Invariants & Security Rules:",
                *[f"- {inv}" for inv in invariants],
                "- NEVER import unpinned or blacklisted dependencies.",
                "- Maintain 100% backward compatibility with wire contracts.",
                "",
                "### 4. Repair Directive (Attempt 3 SLA - Comprehensive Module Recovery):",
                "- Return a complete, self-contained valid module patch diff.",
                ""
            ])

        prompt_str = "\n".join(envelope_lines)
        envelope_tokens = max(1, len(prompt_str) // 4)

        return {
            "attempt": attempt,
            "max_attempts": max_attempts,
            "module_id": module_id,
            "failure_site": failure_site,
            "pruned_trace": pruned_trace,
            "source_snippet": source_snippet,
            "prompt_content": prompt_str,
            "envelope_tokens": envelope_tokens,
            "token_stats": stats,
            "sla_status": "FINAL_ATTEMPT_WARNING" if attempt >= max_attempts else f"ATTEMPT_{attempt}_ACTIVE"
        }


class GitDiffPruner:
    """Prunes noisy lockfile churn, clamp diff context lines, and strips binary diffs."""

    IGNORED_DIFF_PATTERNS = [
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Cargo.lock",
        "poetry.lock",
        "Pipfile.lock",
        ".min.js",
        ".min.css",
        ".map"
    ]

    @classmethod
    def prune_diff(cls, raw_diff: str) -> Tuple[str, Dict[str, int]]:
        original_tokens = max(1, len(raw_diff) // 4)
        lines = raw_diff.splitlines()
        pruned_lines = []
        skip_file = False

        for line in lines:
            if line.startswith("diff --git"):
                skip_file = any(p in line for p in cls.IGNORED_DIFF_PATTERNS)
                if skip_file:
                    file_name = line.split(" ")[-1]
                    pruned_lines.append(f"diff --git [LOCKFILE/BLOB SKIPPED: {file_name}]")
                    continue

            if skip_file:
                continue

            pruned_lines.append(line)

        pruned_text = "\n".join(pruned_lines)
        pruned_tokens = max(1, len(pruned_text) // 4)
        saved_tokens = max(0, original_tokens - pruned_tokens)

        return pruned_text, {
            "uncompressed_tokens": original_tokens,
            "pruned_tokens": pruned_tokens,
            "saved_tokens": saved_tokens,
            "reduction_pct": round(saved_tokens / original_tokens * 100.0, 1)
        }


class ConversationMemoryCompactor:
    """Compacts multi-turn agent interaction history into a concise state ledger."""

    @classmethod
    def compact_history(cls, messages: List[Dict[str, str]], keep_last_n: int = 4) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        original_str = json.dumps(messages)
        original_tokens = max(1, len(original_str) // 4)

        if len(messages) <= keep_last_n:
            return messages, {
                "uncompressed_tokens": original_tokens,
                "pruned_tokens": original_tokens,
                "saved_tokens": 0,
                "reduction_pct": 0.0
            }

        older_messages = messages[:-keep_last_n]
        recent_messages = messages[-keep_last_n:]

        # Extract high-level summary points from older turns
        summary_points = []
        for idx, m in enumerate(older_messages):
            role = m.get("role", "unknown")
            content = m.get("content", "")
            first_line = content.strip().splitlines()[0][:120] if content else ""
            summary_points.append(f"Turn {idx+1} ({role}): {first_line}")

        summary_msg = {
            "role": "system",
            "content": f"[COMPACTED CONVERSATION STATE: {len(older_messages)} historical turns summarized]:\n" + "\n".join(summary_points)
        }

        compacted_messages = [summary_msg] + recent_messages
        pruned_str = json.dumps(compacted_messages)
        pruned_tokens = max(1, len(pruned_str) // 4)
        saved_tokens = max(0, original_tokens - pruned_tokens)

        return compacted_messages, {
            "uncompressed_tokens": original_tokens,
            "pruned_tokens": pruned_tokens,
            "saved_tokens": saved_tokens,
            "reduction_pct": round(saved_tokens / original_tokens * 100.0, 1)
        }


class UnifiedTokenOptimizer:
    """Unified token compression dispatcher respecting workspace & portal configs."""

    @classmethod
    def optimize_content(
        cls,
        content: str,
        content_type: str,
        repo_root: Path = REPO_ROOT,
        override_mode: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Main entry point for optimizing any context payload.
        content_type can be: 'python', 'typescript', 'go', 'rust', 'markdown', 'yaml', 'json', 'log', 'diff'.
        """
        if not TokenOptimizationConfig.is_enabled(repo_root):
            tokens = max(1, len(content) // 4)
            return content, {
                "status": "DISABLED",
                "uncompressed_tokens": tokens,
                "pruned_tokens": tokens,
                "saved_tokens": 0,
                "reduction_pct": 0.0
            }

        cfg = TokenOptimizationConfig.load_config(repo_root)
        mode = override_mode or cfg.get("token_optimization", {}).get("mode", "standard")

        if content_type in ["python", "typescript", "javascript", "go", "rust"]:
            if not TokenOptimizationConfig.is_strategy_enabled("ast_skeleton_pruning", repo_root):
                tokens = max(1, len(content) // 4)
                return content, {"status": "STRATEGY_DISABLED", "uncompressed_tokens": tokens, "pruned_tokens": tokens, "saved_tokens": 0, "reduction_pct": 0.0}
            from core.ast_optimizer import ASTOptimizer
            return ASTOptimizer.prune_source(content, content_type)

        elif content_type in ["markdown", "md"]:
            if not TokenOptimizationConfig.is_strategy_enabled("markdown_doc_pruning", repo_root):
                tokens = max(1, len(content) // 4)
                return content, {"status": "STRATEGY_DISABLED", "uncompressed_tokens": tokens, "pruned_tokens": tokens, "saved_tokens": 0, "reduction_pct": 0.0}
            return DocPruner.prune_markdown(content, mode=mode)

        elif content_type in ["yaml", "yml"]:
            if not TokenOptimizationConfig.is_strategy_enabled("config_schema_minification", repo_root):
                tokens = max(1, len(content) // 4)
                return content, {"status": "STRATEGY_DISABLED", "uncompressed_tokens": tokens, "pruned_tokens": tokens, "saved_tokens": 0, "reduction_pct": 0.0}
            return ConfigSchemaPruner.prune_yaml(content, mode=mode)

        elif content_type == "json":
            if not TokenOptimizationConfig.is_strategy_enabled("config_schema_minification", repo_root):
                tokens = max(1, len(content) // 4)
                return content, {"status": "STRATEGY_DISABLED", "uncompressed_tokens": tokens, "pruned_tokens": tokens, "saved_tokens": 0, "reduction_pct": 0.0}
            return ConfigSchemaPruner.prune_json(content, mode=mode)

        elif content_type in ["log", "traceback"]:
            if not TokenOptimizationConfig.is_strategy_enabled("diagnostic_log_slicing", repo_root):
                tokens = max(1, len(content) // 4)
                return content, {"status": "STRATEGY_DISABLED", "uncompressed_tokens": tokens, "pruned_tokens": tokens, "saved_tokens": 0, "reduction_pct": 0.0}
            return DiagnosticLogPruner.prune_traceback(content)

        elif content_type == "diff":
            if not TokenOptimizationConfig.is_strategy_enabled("git_diff_pruning", repo_root):
                tokens = max(1, len(content) // 4)
                return content, {"status": "STRATEGY_DISABLED", "uncompressed_tokens": tokens, "pruned_tokens": tokens, "saved_tokens": 0, "reduction_pct": 0.0}
            return GitDiffPruner.prune_diff(content)

        # Default fallback
        tokens = max(1, len(content) // 4)
        return content, {"status": "UNSUPPORTED_TYPE", "uncompressed_tokens": tokens, "pruned_tokens": tokens, "saved_tokens": 0, "reduction_pct": 0.0}
