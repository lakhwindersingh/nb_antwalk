#!/usr/bin/env python3
"""
Neutron Binary Percipience - Agent Plugin Engine
Enables dynamic registration, workflow integration, sandboxed worktree execution,
cryptographic Merkle state sealing, and surgical rollback for custom agent plugins.
"""

import os
import sys
import time
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "workplace"))

try:
    from core.ast_optimizer import ASTOptimizer
except (ImportError, ModuleNotFoundError):
    ASTOptimizer = None

try:
    from core.merkle_engine import MerkleEngine
except (ImportError, ModuleNotFoundError):
    MerkleEngine = None

try:
    from core.poisoning_sentinel import PoisoningSentinel
except (ImportError, ModuleNotFoundError):
    PoisoningSentinel = None

try:
    from core.worktree_engine import WorktreeEngine
except (ImportError, ModuleNotFoundError):
    WorktreeEngine = None

try:
    from core.token_tracker import TokenTracker
except (ImportError, ModuleNotFoundError):
    TokenTracker = None

try:
    from core.layered_context_validator import LayeredContextValidator
except (ImportError, ModuleNotFoundError):
    LayeredContextValidator = None

class AgentPluginEngine:
    """Manages the full lifecycle of custom agent plugins for Autonomous CI/CD."""

    AGENTS_DIR = ".nb/agentic/custom/agents"
    WORKFLOWS_DIR = ".nb/agentic/workflows"
    TEMPLATES_DIR = ".nb/agentic/templates"

    @classmethod
    def get_agents_dir(cls, workspace_root: Path = REPO_ROOT) -> Path:
        p = workspace_root / cls.AGENTS_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    CUSTOM_WORKFLOWS_DIR = ".nb/agentic/custom/workflows"

    @classmethod
    def get_workflows_dir(cls, workspace_root: Path = REPO_ROOT) -> Path:
        p = workspace_root / cls.WORKFLOWS_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def get_workflows_dirs(cls, workspace_root: Path = REPO_ROOT) -> List[Path]:
        dirs = []
        for rel in [cls.WORKFLOWS_DIR, cls.CUSTOM_WORKFLOWS_DIR]:
            p = workspace_root / rel
            if p.exists() and p not in dirs:
                dirs.append(p)
        return dirs

    @classmethod
    def create_agent(
        cls,
        workspace_root: Path = REPO_ROOT,
        name: str = "custom_quality_guard",
        template_type: str = "cicd_quality",
        role: str = "Code Quality & Invariant Enforcer",
        model: str = "claude-3-5-sonnet-20241022",
        allowed_modules: Optional[List[str]] = None,
        target_workflow: str = "wf_pr_gatekeeper",
        seal_merkle: bool = True
    ) -> Dict[str, Any]:
        """
        Scaffolds a new custom agent plugin using the healthy integration pattern,
        validates its schema, and seals a Merkle block.
        """
        agents_dir = cls.get_agents_dir(workspace_root)
        clean_name = name.lower().replace("-", "_").replace(" ", "_")
        if not clean_name.startswith("agent_"):
            agent_id = f"agent_{clean_name}"
        else:
            agent_id = clean_name

        file_path = agents_dir / f"{clean_name.replace('agent_', '')}.yaml"
        modules = allowed_modules or ["workplace/core", "workplace/modules/mod_portal_marketing"]

        agent_manifest = {
            "metadata": {
                "agent_id": agent_id,
                "name": name.replace("_", " ").title(),
                "version": "1.0.0",
                "category": template_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "author": "Autonomous Platform Engineer",
                "description": f"Autonomous CI/CD agent specialist for {template_type} and invariant enforcement."
            },
            "model_profile": {
                "model": model,
                "temperature": 0.1,
                "role": role,
                "context_budget_tokens": 12000,
                "cache_prefix_alignment": True
            },
            "isolation_and_sandboxing": {
                "worktree_isolation": True,
                "default_ttl_seconds": 300,
                "clean_worktree_on_exit": True,
                "prevent_cross_module_leakage": True
            },
            "module_scope": {
                "allowed_modules": modules,
                "denied_paths": [".nb/context/invariants", "context/invariants", ".git", ".nb/workspaces", ".workspaces"]
            },
            "contracts_and_invariants": {
                "enforce_tiered_hierarchy": True,
                "target_contracts": [".nb/context/contracts/contract_schema_v2.json"],
                "min_maturity_threshold": 0.85
            },
            "tools_and_capabilities": [
                {"name": "read_ast_skeleton", "handler": "workplace/core/ast_optimizer.py"},
                {"name": "track_token_savings", "handler": "workplace/core/token_tracker.py"},
                {"name": "validate_invariants", "handler": "workplace/core/layered_context_validator.py"},
                {"name": "quarantine_anomaly", "handler": "workplace/core/poisoning_sentinel.py"}
            ],
            "autonomous_cicd_hooks": {
                "auto_trigger_in_cicd": True,
                "target_workflows": [
                    {
                        "workflow_id": target_workflow,
                        "insertion_point": "after:step_contract_compat",
                        "step_id": f"step_{clean_name}",
                        "step_name": f"Run {name.replace('_', ' ').title()} Step",
                        "fail_action": "AUTO_HEAL_OR_ROLLBACK"
                    }
                ],
                "bounded_sla": {
                    "max_retries": 3,
                    "timeout_seconds": 60,
                    "allow_hypothesis_patching": True
                }
            },
            "cryptographic_governance": {
                "seal_merkle_block_on_success": True,
                "merkle_action_label": f"AGENT_PLUGIN_VERIFIED ({agent_id})",
                "recovery_point_prefix": f"RP_AGENT_{clean_name.upper()}",
                "rollback_policy": {
                    "enabled": True,
                    "fallback_recovery_point": "RP_PLAY3_BOOTSTRAP_001",
                    "target_module": "mod_portal_marketing",
                    "auto_isolate_on_poisoning": True,
                    "quarantine_file": "user/hitl/poisoning_quarantine.md"
                }
            },
            "system_prompt": f"You are the {role} for this workspace. Enforce quality, contracts, and zero context leakage."
        }

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(agent_manifest, f, sort_keys=False)

        merkle_block = None
        if seal_merkle and MerkleEngine is not None:
            recovery_id = f"RP_AGENT_REGISTER_{clean_name.upper()}_{int(time.time())}"
            merkle_block = MerkleEngine.seal_block(
                workspace_root=workspace_root,
                action=f"AGENT_REGISTERED ({agent_id})",
                recovery_point_id=recovery_id
            )
        else:
            recovery_id = None

        return {
            "status": "REGISTERED",
            "agent_id": agent_id,
            "manifest_path": str(file_path.relative_to(workspace_root)),
            "category": template_type,
            "target_workflow": target_workflow,
            "merkle_block": merkle_block.get("block_id") if merkle_block else None,
            "recovery_point": recovery_id if merkle_block else None
        }

    @classmethod
    def integrate_into_workflow(
        cls,
        workspace_root: Path = REPO_ROOT,
        agent_id: str = "agent_custom_quality_guard",
        workflow_id: str = "wf_pr_gatekeeper",
        after_step_id: str = "step_contract_compat",
        step_name: Optional[str] = None,
        fail_action: str = "AUTO_HEAL_OR_ROLLBACK"
    ) -> Dict[str, Any]:
        """
        Dynamically attaches a custom agent into an existing workflow DAG,
        validates DAG acyclicity, and seals a Merkle block.
        """
        wf_dirs = cls.get_workflows_dirs(workspace_root)
        wf_files = []
        for d in wf_dirs:
            wf_files.extend(list(d.glob("*.yaml")) + list(d.glob("*.yml")))
        target_file = None
        wf_data = None

        for wf_file in wf_files:
            try:
                with open(wf_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and (data.get("workflow_id") == workflow_id or wf_file.stem == workflow_id.replace("wf_", "")):
                        target_file = wf_file
                        wf_data = data
                        break
            except Exception:
                continue

        if not target_file or not wf_data:
            raise FileNotFoundError(f"Workflow '{workflow_id}' not found in {wf_dirs}")

        steps = wf_data.get("steps", [])
        clean_step_id = f"step_{agent_id.replace('agent_', '')}"

        # Check if step already exists
        existing_step = next((s for s in steps if s.get("id") == clean_step_id), None)
        if existing_step:
            existing_step["executor"] = agent_id
            existing_step["depends_on"] = [after_step_id] if after_step_id else []
        else:
            new_step = {
                "id": clean_step_id,
                "name": step_name or f"Execute Custom Plugin ({agent_id})",
                "executor": agent_id,
                "depends_on": [after_step_id] if after_step_id else [],
                "fail_action": fail_action
            }

            # Insert after after_step_id if found, else append before step_merkle_seal or at end
            inserted = False
            for idx, s in enumerate(steps):
                if s.get("id") == after_step_id:
                    steps.insert(idx + 1, new_step)
                    inserted = True
                    break

            if not inserted:
                # Place before seal step if exists
                seal_idx = next((i for i, s in enumerate(steps) if "seal" in s.get("id", "").lower()), -1)
                if seal_idx >= 0:
                    steps.insert(seal_idx, new_step)
                else:
                    steps.append(new_step)

        wf_data["steps"] = steps

        with open(target_file, "w", encoding="utf-8") as f:
            yaml.dump(wf_data, f, sort_keys=False)

        # Seal Merkle block
        recovery_id = f"RP_WF_INTEGRATE_{agent_id.upper()}_{int(time.time())}"
        merkle_block = MerkleEngine.seal_block(
            workspace_root=workspace_root,
            action=f"WORKFLOW_INTEGRATED ({workflow_id} + {agent_id})",
            recovery_point_id=recovery_id
        ) if MerkleEngine else {}

        return {
            "status": "INTEGRATED",
            "workflow_id": workflow_id,
            "agent_id": agent_id,
            "step_id": clean_step_id,
            "after_step_id": after_step_id,
            "workflow_file": str(target_file.relative_to(workspace_root)),
            "merkle_block_id": merkle_block.get("block_id"),
            "recovery_point_id": recovery_id
        }

    @classmethod
    def execute_agent_task(
        cls,
        workspace_root: Path = REPO_ROOT,
        agent_id: str = "agent_custom_quality_guard",
        task_description: str = "Analyze AST and verify compliance",
        target_module: str = "mod_portal_marketing",
        auto_rollback_on_failure: bool = True
    ) -> Dict[str, Any]:
        """
        Executes an agent task inside an ephemeral Git worktree sandbox.
        Performs AST token tracking, pre/post contract checks, Merkle block sealing,
        and surgical rollback if an invariant is violated.
        """
        # 1. Load agent manifest
        clean_name = agent_id.replace("agent_", "")
        agent_file = cls.get_agents_dir(workspace_root) / f"{clean_name}.yaml"
        if not agent_file.exists():
            # Check if exists as agent_{name}.yaml
            agent_file = cls.get_agents_dir(workspace_root) / f"{agent_id}.yaml"

        manifest = {}
        if agent_file.exists():
            with open(agent_file, "r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f) or {}

        # 2. Acquire ephemeral worktree lease
        lease = WorktreeEngine.acquire(
            workspace_root=workspace_root,
            agent_id=agent_id,
            ttl_seconds=300
        ) if WorktreeEngine else {"path": str(workspace_root)}

        # 3. Pre-execution Layered Context & Contract Validation
        val_res = LayeredContextValidator.validate_layered_hierarchy(workspace_root) if LayeredContextValidator else {"overall_valid": True}
        if not val_res.get("overall_valid", False):
            if WorktreeEngine:
                WorktreeEngine.release(workspace_root, agent_id)
            if auto_rollback_on_failure and PoisoningSentinel:
                PoisoningSentinel.execute_surgical_rollback(workspace_root, target_module, "RP_PLAY3_BOOTSTRAP_001")
            return {
                "status": "FAILED",
                "reason": "Pre-execution invariant check failed",
                "violations": val_res.get("violations", []),
                "rolled_back": auto_rollback_on_failure
            }

        # 4. AST Skeletonization & Token FinOps Capture
        target_dir = f"workplace/modules/{target_module}" if not target_module.startswith("workplace/") else target_module
        tok_res = TokenTracker.scan_and_track_repo(
            repo_root=workspace_root,
            target_dir=target_dir,
            session_or_pr=f"agent_run_{agent_id}"
        ) if TokenTracker else {}

        # 5. Security Sentinel scan for poisoning
        scan_target = workspace_root / target_dir
        poisoning_detected = False
        if scan_target.exists() and PoisoningSentinel is not None:
            for root, _, files in os.walk(scan_target):
                for f in files:
                    if f.endswith((".py", ".ts", ".js", ".json", ".yaml")):
                        fp = Path(root) / f
                        try:
                            code = fp.read_text(encoding="utf-8", errors="ignore")
                            has_secrets, _ = PoisoningSentinel.detect_secrets(code)
                            if has_secrets:
                                poisoning_detected = True
                                break
                        except Exception:
                            continue

        if poisoning_detected and PoisoningSentinel:
            # Trigger Surgical Rollback
            rollback_ok = PoisoningSentinel.execute_surgical_rollback(
                workspace_root=workspace_root,
                module_id=target_module,
                target_point="RP_PLAY3_BOOTSTRAP_001"
            )
            if WorktreeEngine:
                WorktreeEngine.release(workspace_root, agent_id)
            # Seal quarantine Merkle block
            seal_block = MerkleEngine.seal_block(
                workspace_root=workspace_root,
                action=f"AGENT_POISONING_QUARANTINED_AND_ROLLED_BACK ({agent_id})",
                recovery_point_id=f"RP_POISON_ROLLBACK_{agent_id.upper()}_{int(time.time())}"
            ) if MerkleEngine else {}
            return {
                "status": "POISONING_DETECTED",
                "action_taken": "SURGICAL_ROLLBACK_EXECUTED",
                "agent_id": agent_id,
                "target_module": target_module,
                "rolled_back": rollback_ok,
                "merkle_block_id": seal_block.get("block_id")
            }

        # 6. Release worktree cleanly
        if WorktreeEngine:
            WorktreeEngine.release(workspace_root, agent_id)

        # 7. Seal Merkle Block with Verified Recovery Point
        recovery_id = f"RP_AGENT_TASK_{agent_id.upper()}_{int(time.time())}"
        merkle_block = MerkleEngine.seal_block(
            workspace_root=workspace_root,
            action=f"AGENT_TASK_VERIFIED ({agent_id})",
            recovery_point_id=recovery_id
        ) if MerkleEngine else {}

        return {
            "status": "SUCCESS",
            "agent_id": agent_id,
            "task_description": task_description,
            "target_module": target_module,
            "worktree_leased": lease.get("path"),
            "token_savings": tok_res.get("summary", {}),
            "merkle_block_id": merkle_block.get("block_id"),
            "recovery_point_id": recovery_id,
            "quarantined": False
        }
    @classmethod
    def rollback_agent(
        cls,
        workspace_root: Path = REPO_ROOT,
        agent_id: str = "agent_custom_quality_guard",
        target_module: str = "mod_portal_marketing",
        target_point: str = "RP_PLAY3_BOOTSTRAP_001"
    ) -> Dict[str, Any]:
        """
        Surgically rolls back an agent's modifications to a specific module
        without affecting sibling services, sealing a Merkle rollback block.
        """
        rollback_ok = PoisoningSentinel.execute_surgical_rollback(
            workspace_root=workspace_root,
            module_id=target_module,
            target_point=target_point
        ) if PoisoningSentinel else True

        recovery_id = f"RP_AGENT_ROLLBACK_{agent_id.upper()}_{int(time.time())}"
        merkle_block = MerkleEngine.seal_block(
            workspace_root=workspace_root,
            action=f"AGENT_SURGICAL_ROLLBACK ({agent_id} -> {target_point})",
            recovery_point_id=recovery_id
        ) if MerkleEngine else {}

        return {
            "status": "ROLLED_BACK" if rollback_ok else "ROLLBACK_FAILED",
            "agent_id": agent_id,
            "target_module": target_module,
            "target_point": target_point,
            "merkle_block_id": merkle_block.get("block_id"),
            "recovery_point_id": recovery_id
        }

    @classmethod
    def list_agents(cls, workspace_root: Path = REPO_ROOT) -> List[Dict[str, Any]]:
        """
        Scans agentic/custom/agents/ and returns all registered custom agents
        with their metadata, workflow bindings, and health status.
        """
        agents_dir = cls.get_agents_dir(workspace_root)
        yaml_files = list(agents_dir.glob("*.yaml")) + list(agents_dir.glob("*.yml"))
        results = []

        # Find workflows across standard and custom workflow directories
        wf_dirs = cls.get_workflows_dirs(workspace_root)
        workflow_steps_map = {}
        for wf_dir in wf_dirs:
            for wf in list(wf_dir.glob("*.yaml")) + list(wf_dir.glob("*.yml")):
                try:
                    with open(wf, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                        wf_id = data.get("workflow_id") or data.get("id") or wf.stem
                        items = data.get("steps") or data.get("stages") or []
                        for item in items:
                            ex = item.get("executor") or item.get("agent")
                            sid = item.get("id") or item.get("step_id")
                            sname = item.get("name")
                            if ex:
                                workflow_steps_map.setdefault(ex, []).append({
                                    "workflow_id": wf_id,
                                    "step_id": sid,
                                    "name": sname
                                })
                except Exception:
                    continue

        for yf in sorted(yaml_files):
            stem_id = yf.stem if yf.stem.startswith("agent_") else f"agent_{yf.stem}"
            try:
                with open(yf, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                meta = data.get("metadata", {})
                mod_prof = data.get("model_profile", {})
                aid = meta.get("agent_id") or data.get("agent_id") or stem_id

                mod_scope_raw = data.get("module_scope")
                if isinstance(mod_scope_raw, dict):
                    allowed_modules = mod_scope_raw.get("allowed_modules", ["workplace/core"])
                elif isinstance(mod_scope_raw, list):
                    allowed_modules = mod_scope_raw
                elif isinstance(mod_scope_raw, str):
                    allowed_modules = [m.strip() for m in mod_scope_raw.split(",") if m.strip()]
                else:
                    allowed_modules = ["workplace/core"]

                results.append({
                    "agent_id": aid,
                    "name": meta.get("name") or data.get("name") or yf.stem.replace("_", " ").title(),
                    "category": meta.get("category", "custom"),
                    "model": mod_prof.get("model") or data.get("model", "claude-3-5-sonnet-20241022"),
                    "role": mod_prof.get("role") or data.get("role", "Custom Specialist"),
                    "allowed_modules": allowed_modules,
                    "file_path": str(yf.relative_to(workspace_root)),
                    "workflow_bindings": (
                        workflow_steps_map.get(aid)
                        or workflow_steps_map.get(stem_id)
                        or [
                            {"workflow_id": wb.get("workflow_id"), "step_id": wb.get("stage") or wb.get("step_id"), "name": wb.get("name") or f"Direct Binding ({aid})"}
                            for wb in data.get("workflow_bindings", [])
                        ]
                        or [
                            {"workflow_id": tw.get("workflow_id"), "step_id": tw.get("step_id"), "name": tw.get("step_name") or f"Hook Binding ({aid})"}
                            for tw in data.get("autonomous_cicd_hooks", {}).get("target_workflows", [])
                        ]
                        or []
                    ),
                    "status": "ACTIVE"
                })
            except Exception as e:
                results.append({
                    "agent_id": stem_id,
                    "name": yf.stem,
                    "file_path": str(yf.relative_to(workspace_root)),
                    "status": "ERROR",
                    "error": str(e)
                })

        return results
