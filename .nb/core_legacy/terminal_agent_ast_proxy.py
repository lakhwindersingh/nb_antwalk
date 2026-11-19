#!/usr/bin/env python3
"""
Neutron Binary Percipience - Terminal Mode Agent AST Proxy & Context Injection Engine
Provides intelligent AST pruning, prompt token optimization, and environment wrapping
for terminal-based autonomous agents (Claude Code, Gemini CLI, Aider, Cursor CLI)
running directly inside IntelliJ IDEA / PyCharm embedded terminals or developer shells.
"""

import os
import sys
import json
import uuid
import time
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    from core.ast_optimizer import ASTOptimizer
    from core.token_tracker import TokenTracker
except ImportError:
    # Handle direct / relative path execution
    REPO_ROOT = Path(__file__).resolve().parents[2]
    for p in [REPO_ROOT / ".nb", REPO_ROOT / ".nb" / "core", REPO_ROOT / "workplace"]:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from core.ast_optimizer import ASTOptimizer
    from core.token_tracker import TokenTracker


class TerminalAgentASTProxy:
    """
    Manages context extraction, AST structural skeletonization,
    and terminal process wrapping for CLI-based AI agents.
    """

    SUPPORTED_AGENTS = ["claude", "claude-code", "gemini", "gemini-cli", "aider", "cursor-cli"]
    SUPPORTED_FORMATS = ["claude-code", "gemini-cli", "aider", "markdown", "json"]

    CANONICAL_OUTPUT_PATHS = {
        "claude-code": Path(".nb/context/percipience_claude_context.md"),
        "gemini-cli": Path(".nb/context/percipience_gemini_context.md"),
        "aider": Path(".nb/context/percipience_aider_context.md"),
    }

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Heuristic token estimator (approx 4 chars per token)."""
        return max(1, len(text) // 4)

    @classmethod
    def get_canonical_output_path(cls, workspace_root: Path, format_type: str = "claude-code") -> Path:
        """Returns the canonical .nb context path for the specified format."""
        workspace_root = Path(workspace_root).resolve()
        rel_p = cls.CANONICAL_OUTPUT_PATHS.get(format_type, Path(".nb/context/percipience_claude_context.md"))
        return workspace_root / rel_p

    @classmethod
    def is_context_stale(
        cls,
        workspace_root: Path,
        format_type: str = "claude-code",
        target_path: Optional[Path] = None
    ) -> Tuple[bool, float]:
        """
        High-speed (<20ms) modification-time check across workspace source files.
        Determines whether the exported AST context is stale compared to latest code changes.
        """
        workspace_root = Path(workspace_root).resolve()
        out_p = target_path or cls.get_canonical_output_path(workspace_root, format_type)
        if not out_p.exists():
            return True, 0.0

        ctx_mtime = out_p.stat().st_mtime
        workplace_dir = workspace_root / "workplace"
        if not workplace_dir.exists():
            workplace_dir = workspace_root

        check_extensions = {".py", ".ts", ".js", ".kt", ".java", ".html", ".jsx", ".tsx", ".yaml", ".json"}
        latest_src_mtime = 0.0

        # Fast scan source files in workplace
        for root, dirs, files in os.walk(workplace_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "build", "__pycache__", ".gradle", "dist")]
            for f in files:
                if any(f.endswith(ext) for ext in check_extensions):
                    try:
                        mtime = os.path.getmtime(os.path.join(root, f))
                        if mtime > latest_src_mtime:
                            latest_src_mtime = mtime
                            if latest_src_mtime > ctx_mtime:
                                return True, latest_src_mtime
                    except OSError:
                        continue

        # Also check wire contracts in .nb/context/contracts
        contracts_dir = workspace_root / ".nb" / "context" / "contracts"
        if contracts_dir.exists():
            for c_file in contracts_dir.glob("*.*"):
                try:
                    mtime = c_file.stat().st_mtime
                    if mtime > latest_src_mtime:
                        latest_src_mtime = mtime
                        if latest_src_mtime > ctx_mtime:
                            return True, latest_src_mtime
                except OSError:
                    continue

        return (latest_src_mtime > ctx_mtime), latest_src_mtime

    @classmethod
    def export_and_save_context(
        cls,
        workspace_root: Path,
        format_type: str = "claude-code",
        output_path: Optional[Path] = None,
        force: bool = False,
        target_modules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Exports AST context atomically. If not forced and context is already fresh,
        skips expensive AST regeneration in under 20ms.
        """
        workspace_root = Path(workspace_root).resolve()
        out_p = Path(output_path).resolve() if output_path else cls.get_canonical_output_path(workspace_root, format_type)

        if not force:
            stale, _ = cls.is_context_stale(workspace_root, format_type, target_path=out_p)
            if not stale and out_p.exists():
                return {
                    "status": "UP_TO_DATE",
                    "stale": False,
                    "format": format_type,
                    "context_file": str(out_p),
                    "message": f"Context file {out_p.name} is already up to date with workspace AST."
                }

        # Perform AST context extraction
        res = cls.export_context(workspace_root, format_type=format_type, target_modules=target_modules)

        # Atomic write: write to .tmp and rename
        out_p.parent.mkdir(parents=True, exist_ok=True)
        tmp_p = out_p.with_suffix(f"{out_p.suffix}.tmp.{uuid.uuid4().hex[:6]}")
        tmp_p.write_text(res["payload"], encoding="utf-8")
        tmp_p.replace(out_p)

        # Backward compatibility: update root symlink if appropriate
        if format_type == "claude-code":
            root_link = workspace_root / ".percipience_claude_context.md"
            try:
                if root_link.is_symlink() or not root_link.exists():
                    root_link.unlink(missing_ok=True)
                    rel_target = os.path.relpath(out_p, workspace_root)
                    root_link.symlink_to(rel_target)
                elif root_link.exists() and not root_link.is_symlink():
                    root_link.write_text(res["payload"], encoding="utf-8")
            except Exception:
                pass

        return {
            "status": "EXPORTED",
            "stale": True,
            "format": format_type,
            "context_file": str(out_p),
            "total_files": res["total_files"],
            "raw_tokens": res["total_raw_tokens"],
            "pruned_tokens": res["total_pruned_tokens"],
            "tokens_saved": res["tokens_saved"],
            "reduction_pct": res["reduction_pct"],
            "message": f"Successfully exported AST context to {out_p.name} ({res['reduction_pct']}% reduction)"
        }

    @classmethod
    def trigger_async_context_export(
        cls,
        workspace_root: Path,
        format_type: str = "claude-code",
        output_path: Optional[Path] = None,
        debounce_seconds: float = 3.0,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Asynchronously triggers context export in a detached background thread
        with debouncing, so foreground operations (IDE, terminal, Git) return instantly (0ms).
        """
        workspace_root = Path(workspace_root).resolve()
        out_p = Path(output_path).resolve() if output_path else cls.get_canonical_output_path(workspace_root, format_type)

        def _worker():
            try:
                # Lower process scheduling priority if OS supports nice
                if hasattr(os, "nice"):
                    try:
                        os.nice(10)
                    except Exception:
                        pass
                if debounce_seconds > 0:
                    time.sleep(debounce_seconds)
                cls.export_and_save_context(workspace_root, format_type=format_type, output_path=out_p, force=force)
            except Exception:
                pass

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        return {
            "status": "QUEUED_ASYNC",
            "debounce_seconds": debounce_seconds,
            "format": format_type,
            "target_path": str(out_p)
        }

    @classmethod
    def export_context(
        cls,
        workspace_root: Path,
        format_type: str = "claude-code",
        target_modules: Optional[List[str]] = None,
        focus_symbols: Optional[List[str]] = None,
        max_tokens: int = 100000,
        include_contracts: bool = True
    ) -> Dict[str, Any]:
        """
        Scans workspace code files, applies AST pruning, and compiles a
        high-fidelity structural context payload for terminal mode agents.
        """
        workspace_root = Path(workspace_root).resolve()
        workplace_dir = workspace_root / "workplace"
        if not workplace_dir.exists():
            workplace_dir = workspace_root

        pruned_files: Dict[str, str] = {}
        total_raw_tokens = 0
        total_pruned_tokens = 0
        file_metrics: List[Dict[str, Any]] = []

        # Find target files
        extensions = {".py", ".ts", ".js", ".kt", ".java", ".html", ".jsx", ".tsx"}
        scanned_paths: List[Path] = []

        target_dirs = []
        if target_modules:
            for mod in target_modules:
                mod_path = workplace_dir / "modules" / mod
                if mod_path.exists():
                    target_dirs.append(mod_path)
                else:
                    target_dirs.append(workplace_dir / mod)
        else:
            target_dirs = [workplace_dir]

        for base_dir in target_dirs:
            if not base_dir.exists():
                continue
            for root, _, files in os.walk(base_dir):
                if any(ignored in root for ignored in [".git", "build", "node_modules", "__pycache__", ".gradle", "dist"]):
                    continue
                for f in sorted(files):
                    p = Path(root) / f
                    if p.suffix in extensions and p.stat().st_size < 500000:
                        scanned_paths.append(p)

        for p in scanned_paths:
            try:
                rel_path = str(p.relative_to(workspace_root))
            except ValueError:
                rel_path = str(p.name)

            try:
                raw_code = p.read_text(encoding="utf-8")
            except Exception:
                continue

            raw_tokens = cls.estimate_tokens(raw_code)
            ext = p.suffix.lstrip(".")
            lang = "typescript" if ext in ["ts", "js", "tsx", "jsx"] else ("python" if ext == "py" else ("html" if ext in ["html", "htm"] else ext))
            pruned_res = ASTOptimizer.prune_source(raw_code, lang)
            if isinstance(pruned_res, tuple):
                pruned_code = pruned_res[0]
            else:
                pruned_code = str(pruned_res)
            pruned_tokens = cls.estimate_tokens(pruned_code)

            total_raw_tokens += raw_tokens
            total_pruned_tokens += pruned_tokens

            pruned_files[rel_path] = pruned_code
            file_metrics.append({
                "file": rel_path,
                "raw_tokens": raw_tokens,
                "pruned_tokens": pruned_tokens,
                "reduction_pct": round(((raw_tokens - pruned_tokens) / max(1, raw_tokens)) * 100.0, 1)
            })

        # Load active wire contracts if requested
        contracts_summary = []
        if include_contracts:
            contracts_dir = workspace_root / ".nb" / "context" / "contracts"
            if contracts_dir.exists():
                for c_file in sorted(contracts_dir.glob("*.yaml")) + sorted(contracts_dir.glob("*.json")):
                    try:
                        c_text = c_file.read_text(encoding="utf-8")
                        contracts_summary.append(f"### Contract: {c_file.name}\n```yaml\n{c_text.strip()}\n```")
                    except Exception:
                        pass

        # Format output according to agent specifications
        formatted_payload = cls._format_payload(
            format_type=format_type,
            pruned_files=pruned_files,
            contracts_summary=contracts_summary,
            total_raw=total_raw_tokens,
            total_pruned=total_pruned_tokens
        )

        savings_pct = round(((total_raw_tokens - total_pruned_tokens) / max(1, total_raw_tokens)) * 100.0, 1)

        return {
            "format": format_type,
            "total_files": len(pruned_files),
            "total_raw_tokens": total_raw_tokens,
            "total_pruned_tokens": total_pruned_tokens,
            "tokens_saved": total_raw_tokens - total_pruned_tokens,
            "reduction_pct": savings_pct,
            "payload": formatted_payload,
            "file_metrics": file_metrics
        }

    @classmethod
    def _format_payload(
        cls,
        format_type: str,
        pruned_files: Dict[str, str],
        contracts_summary: List[str],
        total_raw: int,
        total_pruned: int
    ) -> str:
        """Formats the AST pruned payload for specific terminal agent protocols."""
        if format_type == "json":
            return json.dumps({
                "meta": {
                    "provider": "Percipience AST Proxy",
                    "raw_tokens": total_raw,
                    "pruned_tokens": total_pruned,
                    "reduction_pct": round(((total_raw - total_pruned) / max(1, total_raw)) * 100.0, 1)
                },
                "files": pruned_files,
                "contracts": contracts_summary
            }, indent=2)

        if format_type == "claude-code":
            sections = [
                "# Percipience AST-Compressed Project Context for Claude Code",
                "> **Notice to Claude Code**: All source files below are presented in AST-pruned skeleton format (function signatures, docstrings, type annotations, and structural DOM tags). Full internal implementation bodies have been stripped by Percipience to optimize token efficiency (~70% savings). If you need full function implementations to perform surgical refactors, inspect specific files or lines using your file viewing tools.",
                f"> **FinOps Efficiency**: Raw Context: {total_raw:,} tokens | Pruned Context: {total_pruned:,} tokens | Savings: {((total_raw - total_pruned)/max(1, total_raw))*100:.1f}%",
                "",
                "## Active Wire Contracts & Schemas"
            ]
            if contracts_summary:
                sections.extend(contracts_summary)
            else:
                sections.append("_No wire contracts loaded._")

            sections.append("\n## Workspace Structural AST Skeletons")
            for fpath, fcontent in sorted(pruned_files.items()):
                ext = Path(fpath).suffix.lstrip(".") or "txt"
                sections.append(f"### File: `{fpath}`\n```{ext}\n{fcontent.strip()}\n```\n")

            return "\n".join(sections)

        elif format_type == "gemini-cli":
            sections = [
                "SYSTEM INSTRUCTION / WORKSPACE CONTEXT (Percipience AST Optimized):",
                f"You are operating within an AST-optimized workspace. Token footprint compressed from {total_raw:,} to {total_pruned:,} tokens.",
                "Adhere strictly to existing interface definitions, public types, and cross-module contracts.",
                "",
                "--- SYSTEM CONTRACTS ---"
            ]
            sections.extend(contracts_summary)
            sections.append("\n--- AST FILE SKELETONS ---")
            for fpath, fcontent in sorted(pruned_files.items()):
                sections.append(f"FILE: {fpath}\n{fcontent.strip()}\n---")
            return "\n".join(sections)

        elif format_type == "aider":
            sections = ["# Percipience AST Repository Map"]
            for fpath, fcontent in sorted(pruned_files.items()):
                sections.append(f"{fpath}:\n{fcontent.strip()}\n")
            return "\n".join(sections)

        else:  # markdown
            sections = [
                "# Percipience AST Context Export",
                f"**Tokens**: Raw: {total_raw:,} | Pruned: {total_pruned:,} | Saved: {total_raw - total_pruned:,}",
                "",
                "## Contracts"
            ]
            sections.extend(contracts_summary)
            sections.append("\n## AST Skeletons")
            for fpath, fcontent in sorted(pruned_files.items()):
                ext = Path(fpath).suffix.lstrip(".") or "txt"
                sections.append(f"### `{fpath}`\n```{ext}\n{fcontent.strip()}\n```\n")
            return "\n".join(sections)

    @classmethod
    def wrap_terminal_agent(
        cls,
        agent_cmd: str,
        agent_args: List[str],
        workspace_root: Path,
        format_type: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepares AST context, injects terminal environment variables,
        and provides command invocation parameters for terminal mode agents.
        """
        workspace_root = Path(workspace_root).resolve()
        session_id = session_id or f"term_{uuid.uuid4().hex[:8]}"

        # Infer format from agent command if not specified
        if not format_type:
            if "claude" in agent_cmd.lower():
                format_type = "claude-code"
            elif "gemini" in agent_cmd.lower():
                format_type = "gemini-cli"
            elif "aider" in agent_cmd.lower():
                format_type = "aider"
            else:
                format_type = "markdown"

        export_res = cls.export_context(workspace_root, format_type=format_type)

        # Write context to user/inputs/ or .nb/ context path for terminal consumption
        context_dir = workspace_root / ".nb" / "context" / "terminal"
        context_dir.mkdir(parents=True, exist_ok=True)
        context_file = context_dir / f"{session_id}_context.md"
        context_file.write_text(export_res["payload"], encoding="utf-8")

        # Also write canonical context in .nb/context/
        canonical_file = cls.get_canonical_output_path(workspace_root, format_type)
        canonical_file.parent.mkdir(parents=True, exist_ok=True)
        canonical_file.write_text(export_res["payload"], encoding="utf-8")

        # Keep root compatibility symlink
        legacy_claude_md = workspace_root / ".percipience_claude_context.md"
        try:
            if legacy_claude_md.is_symlink() or not legacy_claude_md.exists():
                legacy_claude_md.unlink(missing_ok=True)
                legacy_claude_md.symlink_to(os.path.relpath(canonical_file, workspace_root))
            else:
                legacy_claude_md.write_text(export_res["payload"], encoding="utf-8")
        except Exception:
            pass

        # Track token savings event in TokenTracker ledger
        try:
            TokenTracker.record_event(
                repo_root=workspace_root,
                file_path=f"terminal/{agent_cmd}_{session_id}",
                uncompressed_tokens=export_res["total_raw_tokens"],
                pruned_tokens=export_res["total_pruned_tokens"],
                session_or_pr=f"terminal_{agent_cmd}_{session_id}",
                model_id="claude-3-5-sonnet-20241022" if "claude" in agent_cmd else "gemini-2.0-flash"
            )
        except Exception:
            pass

        # Environment variable injections
        env_injects = {
            "PERCIPIENCE_TERMINAL_MODE": "1",
            "PERCIPIENCE_AST_COMPRESSION": "1",
            "PERCIPIENCE_SESSION_ID": session_id,
            "PERCIPIENCE_PROJECT_ROOT": str(workspace_root),
            "PERCIPIENCE_CONTEXT_FILE": str(context_file),
            "CLAUDE_CODE_PROMPT_PREFIX": f"[Percipience AST Context: {export_res['reduction_pct']}% Token Reduction Active]",
            "GEMINI_SYSTEM_INSTRUCTIONS": str(context_file)
        }

        return {
            "session_id": session_id,
            "agent_cmd": agent_cmd,
            "format": format_type,
            "context_file": str(context_file),
            "canonical_context_file": str(canonical_file),
            "raw_tokens": export_res["total_raw_tokens"],
            "pruned_tokens": export_res["total_pruned_tokens"],
            "tokens_saved": export_res["tokens_saved"],
            "reduction_pct": export_res["reduction_pct"],
            "env": env_injects,
            "command": [agent_cmd] + agent_args
        }

    @classmethod
    def generate_shell_hook(cls, shell_type: str = "zsh") -> str:
        """
        Generates shell initialization functions to transparently intercept
        and AST-optimize terminal-based agent commands in the IDE terminal.
        """
        hook_script = f"""# --- Percipience Terminal Mode Agent Hooks ({shell_type}) ---
# Automatically enables AST token pruning for Claude Code, Gemini CLI, and Aider.

if [ -n "$PERCIPIENCE_PROJECT_ROOT" ] || [ -f "./.nb/bin/percipience" ]; then
    export PERCIPIENCE_TERMINAL_MODE=1
    export PERCIPIENCE_AST_COMPRESSION=1

    # Claude Code AST-Optimized Wrapper
    claude() {{
        if [ -f "./.nb/bin/percipience" ]; then
            echo "\\u26a1 [Percipience] Injecting AST-pruned context for Claude Code..."
            ./.nb/bin/percipience context sync --format claude-code > /dev/null 2>&1
            command claude --append-system-prompt "$(cat .nb/context/percipience_claude_context.md 2>/dev/null)" "$@"
        else
            command claude "$@"
        fi
    }}

    # Gemini CLI AST-Optimized Wrapper
    gemini() {{
        if [ -f "./.nb/bin/percipience" ]; then
            echo "\\u26a1 [Percipience] Injecting AST-pruned context for Gemini CLI..."
            ./.nb/bin/percipience context sync --format gemini-cli > /dev/null 2>&1
            command gemini --context .nb/context/percipience_gemini_context.md "$@"
        else
            command gemini "$@"
        fi
    }}

    # Aider AST-Optimized Wrapper
    aider() {{
        if [ -f "./.nb/bin/percipience" ]; then
            echo "\\u26a1 [Percipience] Injecting AST-pruned context for Aider..."
            ./.nb/bin/percipience context sync --format aider > /dev/null 2>&1
            command aider "$@"
        else
            command aider "$@"
        fi
    }}

    echo "\\u2705 Percipience Terminal AST Agent Proxy active for {shell_type}."
fi
"""
        return hook_script

    @classmethod
    def get_terminal_finops_summary(cls, workspace_root: Path) -> Dict[str, Any]:
        """Reads token savings ledger and isolates terminal agent metrics."""
        workspace_root = Path(workspace_root).resolve()
        ledger_file = workspace_root / ".nb" / "context" / "ledger" / "token_savings_ledger.yaml"
        if not ledger_file.exists():
            ledger_file = workspace_root / "workplace" / "context" / "ledger" / "token_savings_ledger.yaml"

        total_terminal_events = 0
        terminal_tokens_saved = 0
        terminal_gross_saved = 0.0

        if ledger_file.exists():
            try:
                import yaml
                data = yaml.safe_load(ledger_file.read_text(encoding="utf-8")) or {}
                events = data.get("events", []) or data.get("recent_events", [])
                for ev in events:
                    pr_name = str(ev.get("session_or_pr", ""))
                    if "terminal_" in pr_name or "claude" in pr_name or "gemini" in pr_name:
                        total_terminal_events += 1
                        terminal_tokens_saved += ev.get("tokens_saved", 0)
                        terminal_gross_saved += ev.get("gross_savings_usd", 0.0)
            except Exception:
                pass

        return {
            "terminal_sessions_count": total_terminal_events,
            "terminal_tokens_saved": terminal_tokens_saved,
            "terminal_gross_saved_usd": round(terminal_gross_saved, 4),
            "status": "HEALTHY"
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Percipience Terminal Agent AST Proxy")
    parser.add_argument("action", choices=["export", "sync", "wrap", "hook", "summary"], help="Action to execute")
    parser.add_argument("--format", choices=["claude-code", "gemini-cli", "aider", "markdown", "json"], default="claude-code")
    parser.add_argument("--agent", default="claude", help="Agent command name")
    parser.add_argument("--output", help="Output file path for exported context")
    parser.add_argument("--shell", default="zsh", choices=["zsh", "bash", "fish"], help="Shell type for hook")
    parser.add_argument("--force", action="store_true", help="Force re-export ignoring cache")

    args = parser.parse_args()
    root = Path.cwd()

    if args.action == "export":
        res = TerminalAgentASTProxy.export_context(root, format_type=args.format)
        if args.output:
            Path(args.output).write_text(res["payload"], encoding="utf-8")
            print(f"\\u2705 Exported AST context to {args.output} ({res['tokens_saved']:,} tokens saved, {res['reduction_pct']}% reduction)")
        else:
            print(res["payload"])
    elif args.action == "sync":
        res = TerminalAgentASTProxy.export_and_save_context(
            root, format_type=args.format, output_path=Path(args.output) if args.output else None, force=args.force
        )
        print(json.dumps(res, indent=2))
    elif args.action == "wrap":
        wrapped = TerminalAgentASTProxy.wrap_terminal_agent(args.agent, [], root, format_type=args.format)
        print(f"\\u2705 Wrapped {args.agent} session [{wrapped['session_id']}]:")
        print(f"   Context File: {wrapped['context_file']}")
        print(f"   Tokens Saved: {wrapped['tokens_saved']:,} ({wrapped['reduction_pct']}%)\")")
        print(f"   Injected Env: {list(wrapped['env'].keys())}")
    elif args.action == "hook":
        print(TerminalAgentASTProxy.generate_shell_hook(args.shell))
    elif args.action == "summary":
        summary = TerminalAgentASTProxy.get_terminal_finops_summary(root)
        print(json.dumps(summary, indent=2))
