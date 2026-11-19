"""
Neutron Binary Percipience - Interactive Onboarding Setup Wizard (TODO-REV-19)
Guided onboarding CLI wizard prompting for project type, language, commercial tier,
and auto-provisioning MCP servers, pre-commit hooks, and genesis Merkle ledger.

Capabilities:
- Interactive terminal prompts with sensible defaults.
- Programmatic answer injection for CI/CD and automated test suites.
- Quad-Space directory partitioning (.nb, workplace, user, .claude).
- Genesis Merkle ledger initialization (Block #0).
- mcp.json generation configured for active workspace.
- Git pre-commit hook installation for autonomous contract verification.
- Starter Minimum Viable Specification (MVS) generation.
"""

import os
import sys
import json
import stat
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Tuple


@dataclass
class OnboardingConfig:
    """Answers collected during onboarding."""
    project_name: str = "percipience-app"
    project_type: str = "enterprise_application"  # monorepo, microservice, package, enterprise_application
    primary_language: str = "python"  # python, typescript, go, polyglot
    tier: str = "team"  # free, team, business, enterprise
    selected_mcp_servers: List[str] = field(default_factory=lambda: ["filesystem", "git"])
    install_git_hooks: bool = True
    enable_token_metering: bool = True


@dataclass
class OnboardingResult:
    """Summary of provisioned assets."""
    status: str  # INITIALIZED, ALREADY_CONFIGURED, FAILED
    config: OnboardingConfig
    provisioned_files: List[str] = field(default_factory=list)
    genesis_block: Dict[str, Any] = field(default_factory=dict)
    mcp_servers_configured: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


class InteractiveOnboardingWizard:
    """
    Interactive and programmatic onboarding wizard for bootstrapping
    Percipience Quad-Space repositories with full tool contracts and ledger genesis.
    """

    AVAILABLE_PROJECT_TYPES = ["enterprise_application", "monorepo", "microservice", "package"]
    AVAILABLE_LANGUAGES = ["python", "typescript", "go", "polyglot"]
    AVAILABLE_TIERS = ["free", "team", "business", "enterprise"]
    AVAILABLE_MCPS = ["filesystem", "git", "github", "docker", "tradingview"]

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = Path(repo_root or os.getcwd()).resolve()

    def prompt_user(self, prompt_text: str, default_val: str, choices: Optional[List[str]] = None) -> str:
        """Prompts user on stdin with fallback to default."""
        choice_str = f" [{'/'.join(choices)}]" if choices else ""
        print(f"🔹 {prompt_text}{choice_str} (default: {default_val}): ", end="", flush=True)
        try:
            val = sys.stdin.readline().strip()
            if not val:
                return default_val
            if choices and val not in choices:
                print(f"   ⚠️ '{val}' not in choices, using '{default_val}'.")
                return default_val
            return val
        except Exception:
            return default_val

    def collect_answers(self, pre_seeded_answers: Optional[Dict[str, Any]] = None) -> OnboardingConfig:
        """Gathers configuration answers via prompts or pre-seeded dictionary."""
        ans = pre_seeded_answers or {}

        p_name = ans.get("project_name")
        if not p_name:
            if not pre_seeded_answers and sys.stdin.isatty():
                p_name = self.prompt_user("Enter Project Name", self.repo_root.name or "percipience-app")
            else:
                p_name = self.repo_root.name or "percipience-app"

        p_type = ans.get("project_type")
        if not p_type:
            if not pre_seeded_answers and sys.stdin.isatty():
                p_type = self.prompt_user("Select Project Architecture", "enterprise_application", self.AVAILABLE_PROJECT_TYPES)
            else:
                p_type = "enterprise_application"

        p_lang = ans.get("primary_language")
        if not p_lang:
            if not pre_seeded_answers and sys.stdin.isatty():
                p_lang = self.prompt_user("Select Primary Language", "python", self.AVAILABLE_LANGUAGES)
            else:
                p_lang = "python"

        p_tier = ans.get("tier")
        if not p_tier:
            if not pre_seeded_answers and sys.stdin.isatty():
                p_tier = self.prompt_user("Select Percipience Commercial Tier", "team", self.AVAILABLE_TIERS)
            else:
                p_tier = "team"

        mcp_servers = ans.get("selected_mcp_servers", ["filesystem", "git"])
        git_hooks = ans.get("install_git_hooks", True)
        metering = ans.get("enable_token_metering", True)

        return OnboardingConfig(
            project_name=p_name,
            project_type=p_type,
            primary_language=p_lang,
            tier=p_tier,
            selected_mcp_servers=mcp_servers,
            install_git_hooks=git_hooks,
            enable_token_metering=metering
        )

    def provision_quad_space_dirs(self) -> List[str]:
        """Creates standard Quad-Space directories."""
        dirs = [
            self.repo_root / "workplace" / "core",
            self.repo_root / "workplace" / "tests",
            self.repo_root / "user" / "specs",
            self.repo_root / "user" / "hitl",
            self.repo_root / ".nb" / "config",
            self.repo_root / ".nb" / "context" / "ledger",
            self.repo_root / ".nb" / "hooks",
            self.repo_root / ".claude" / "prompts"
        ]
        created = []
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d.relative_to(self.repo_root)))
        return created

    def provision_mcp_json(self, config: OnboardingConfig) -> str:
        """Generates mcp.json registering user-selected MCP servers."""
        mcp_path = self.repo_root / "mcp.json"
        servers_config: Dict[str, Any] = {}

        if "filesystem" in config.selected_mcp_servers:
            servers_config["filesystem"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", str(self.repo_root)],
                "env": {"WORKSPACE_ROOT": str(self.repo_root)}
            }
        if "git" in config.selected_mcp_servers:
            servers_config["git"] = {
                "command": "python",
                "args": ["-m", "core.git_bundle_transport"],
                "env": {"GIT_WORKTREE_SANDBOX": "true"}
            }
        if "tradingview" in config.selected_mcp_servers:
            servers_config["tradingview"] = {
                "command": "python",
                "args": ["-m", "mcp_tradingview"],
                "env": {"TV_SANDBOX": "true"}
            }

        mcp_data = {
            "mcpServers": servers_config,
            "version": "1.0.0",
            "percipience_tier": config.tier
        }
        mcp_path.write_text(json.dumps(mcp_data, indent=2), encoding="utf-8")
        return str(mcp_path.relative_to(self.repo_root))

    def provision_genesis_ledger(self) -> Tuple[str, Dict[str, Any]]:
        """Initializes Block #0 Genesis Merkle Ledger."""
        ledger_file = self.repo_root / ".nb" / "context" / "ledger" / "context_ledger.yaml"
        genesis_block = {
            "block_id": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "block_hash": "GENESIS_PERCIPIENCE_BLOCK_0000",
            "previous_hash": "0" * 64,
            "merkle_root": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "author": "percipience-onboarding-wizard",
            "summary": "Genesis Block sealed by Percipience Interactive Wizard",
            "contracts_sealed": ["CONTRACT_AUTH_V1", "CONTRACT_GATEKEEPER_V1"]
        }

        yaml_content = (
            "# Percipience Cryptographic Context Ledger\n"
            "chain_id: 'percipience-mainnet'\n"
            "genesis_block_id: 0\n"
            "blocks:\n"
            f"  - block_id: {genesis_block['block_id']}\n"
            f"    timestamp: '{genesis_block['timestamp']}'\n"
            f"    block_hash: '{genesis_block['block_hash']}'\n"
            f"    previous_hash: '{genesis_block['previous_hash']}'\n"
            f"    merkle_root: '{genesis_block['merkle_root']}'\n"
            f"    author: '{genesis_block['author']}'\n"
            f"    summary: '{genesis_block['summary']}'\n"
        )
        ledger_file.parent.mkdir(parents=True, exist_ok=True)
        ledger_file.write_text(yaml_content, encoding="utf-8")
        return str(ledger_file.relative_to(self.repo_root)), genesis_block

    def provision_starter_mvs(self, config: OnboardingConfig) -> str:
        """Generates starter Minimum Viable Specification template."""
        spec_file = self.repo_root / "user" / "specs" / "mvs_initial_feature.yaml"
        mvs_yaml = (
            f"# Minimum Viable Specification (MVS) - {config.project_name}\n"
            f"spec_id: 'MVS_INIT_001'\n"
            f"title: 'Bootstrap {config.project_name} Core Modules'\n"
            f"tier: '{config.tier}'\n"
            f"created_at: '{datetime.now(timezone.utc).isoformat()}'\n"
            f"contract:\n"
            f"  module: 'workplace/core'\n"
            f"  primary_language: '{config.primary_language}'\n"
            f"  token_budget_ceiling: 25000\n"
            f"  strict_types: true\n"
            f"acceptance_criteria:\n"
            f"  - 'PR Gatekeeper must pass with 0 contract violations'\n"
            f"  - 'AST pruning must achieve >= 50% token reduction'\n"
            f"  - 'Merkle block receipt sealed to ledger on commit'\n"
        )
        spec_file.parent.mkdir(parents=True, exist_ok=True)
        spec_file.write_text(mvs_yaml, encoding="utf-8")
        return str(spec_file.relative_to(self.repo_root))

    def install_git_hook(self) -> Optional[str]:
        """Installs pre-commit hook enforcing Percipience PR Gatekeeper."""
        git_hooks_dir = self.repo_root / ".git" / "hooks"
        if not git_hooks_dir.exists():
            # If not in git root, install in .nb/hooks/pre-commit
            hook_file = self.repo_root / ".nb" / "hooks" / "pre-commit"
        else:
            hook_file = git_hooks_dir / "pre-commit"

        hook_script = (
            "#!/bin/sh\n"
            "# Percipience Autonomous Gatekeeper Pre-Commit Hook\n"
            "echo '⚡ [Percipience] Running Autonomous Gatekeeper pre-commit contracts...'\n"
            "if [ -f .nb/bin/percipience ]; then\n"
            "  python3 .nb/bin/percipience gate --mode dev || exit 1\n"
            "fi\n"
        )
        hook_file.write_text(hook_script, encoding="utf-8")
        # Make executable
        try:
            hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
        except Exception:
            pass

        try:
            return str(hook_file.relative_to(self.repo_root))
        except Exception:
            return str(hook_file)

    def run_interactive(self, answers: Optional[Dict[str, Any]] = None) -> OnboardingResult:
        """
        Executes end-to-end repository onboarding sequence.
        """
        config = self.collect_answers(answers)
        provisioned: List[str] = []

        # 1. Quad-Space scaffolding
        dirs = self.provision_quad_space_dirs()
        provisioned.extend(dirs)

        # 2. mcp.json
        mcp_file = self.provision_mcp_json(config)
        provisioned.append(mcp_file)

        # 3. Genesis ledger
        ledger_file, genesis_block = self.provision_genesis_ledger()
        provisioned.append(ledger_file)

        # 4. Initial MVS
        mvs_file = self.provision_starter_mvs(config)
        provisioned.append(mvs_file)

        # 5. Git pre-commit hook
        if config.install_git_hooks:
            hook_file = self.install_git_hook()
            if hook_file:
                provisioned.append(hook_file)

        # 6. Save onboarding config
        cfg_path = self.repo_root / ".nb" / "config" / "percipience_config.yaml"
        cfg_yaml = (
            f"project_name: '{config.project_name}'\n"
            f"project_type: '{config.project_type}'\n"
            f"primary_language: '{config.primary_language}'\n"
            f"tier: '{config.tier}'\n"
            f"onboarded_at: '{datetime.now(timezone.utc).isoformat()}'\n"
            f"token_metering_enabled: {str(config.enable_token_metering).lower()}\n"
        )
        cfg_path.write_text(cfg_yaml, encoding="utf-8")
        provisioned.append(str(cfg_path.relative_to(self.repo_root)))

        next_steps = [
            "Review starter specification in user/specs/mvs_initial_feature.yaml",
            "Verify tool contracts with: `percipience gate --mode dev`",
            "Inspect token optimization status: `percipience tokens status`",
            "Launch web portal for real-time FinOps telemetry: `python workplace/portal/server.py`"
        ]

        return OnboardingResult(
            status="INITIALIZED",
            config=config,
            provisioned_files=provisioned,
            genesis_block=genesis_block,
            mcp_servers_configured=config.selected_mcp_servers,
            next_steps=next_steps
        )
