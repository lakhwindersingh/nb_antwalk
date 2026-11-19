"""
Tests for Percipience Containerized Plan-to-Code Executor Engine (TODO-DEWS-01 & TODO-DEWS-02)
Governed by RFC: workplace/docs/proposals/rfc_containerized_worktree_swarms.md
"""

import os
import sys
import subprocess
from pathlib import Path
import pytest

try:
    from workplace.core.container_plan_executor import (
        ContainerPlanExecutor,
        PlanExecutionRequest,
        PlanExecutionReceipt
    )
    from workplace.core.worktree_engine import WorktreeEngine
except ImportError:
    from core.container_plan_executor import (
        ContainerPlanExecutor,
        PlanExecutionRequest,
        PlanExecutionReceipt
    )
    from core.worktree_engine import WorktreeEngine


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def plan_path(repo_root):
    candidates = list((repo_root / ".nb" / "plan").glob("**/detailed.md"))
    valid = [c for c in candidates if "templates" not in c.parts and "archive" not in c.parts]
    if valid:
        return str(valid[0].relative_to(repo_root))
    return ".nb/plan/master/parent-master-free-plan/detailed.md"


def test_plan_execution_request_and_receipt_models():
    """Validates PlanExecutionRequest and PlanExecutionReceipt models."""
    req = PlanExecutionRequest(
        plan_path=".nb/plan/sample.md",
        agent_id="agent_test_01",
        target_module="workplace/core",
        prompt="Implement feature X",
        base_branch="main",
        ttl_seconds=1800,
        mock_synthesized_code="# code",
        target_file_rel="sample.py"
    )
    assert req.plan_path == ".nb/plan/sample.md"
    assert req.agent_id == "agent_test_01"
    assert req.ttl_seconds == 1800

    receipt = PlanExecutionReceipt(
        status="SUCCESS",
        agent_id=req.agent_id,
        branch="wt_branch_agent_test_01",
        worktree_path="/tmp/wt",
        plan_path=req.plan_path,
        target_module=req.target_module,
        duration_ms=120.5,
        exit_code=0,
        gatekeeper_passed=True,
        stdout="Output log"
    )
    d = receipt.to_dict()
    assert d["status"] == "SUCCESS"
    assert d["agent_id"] == "agent_test_01"
    assert d["duration_ms"] == 120.5
    assert d["gatekeeper_passed"] is True


def test_build_docker_command(repo_root):
    """Validates Docker execution command formatting and volume mounts."""
    executor = ContainerPlanExecutor(workspace_root=repo_root, mock_mode=True)
    wt_path = repo_root / ".nb" / "workspaces" / "wt_test_cmd"
    
    cmd = executor.build_docker_command(
        worktree_path=wt_path,
        plan_rel_path=".nb/plan/sample.md",
        target_module="workplace/core",
        prompt="Synthesize component",
        env_vars={"ANTHROPIC_API_KEY": "test-key-123"},
        target_file_rel="core/component.py",
        mock_synthesized_code="print('ok')"
    )

    cmd_str = " ".join(cmd)
    assert "docker run --rm" in cmd_str
    assert f"-v {str(repo_root)}:/repo:rw" in cmd_str
    assert f"-v {str(wt_path)}:/workspace:rw" in cmd_str
    assert "-e ANTHROPIC_API_KEY=test-key-123" in cmd_str
    assert "-e PLAN_PATH=/repo/.nb/plan/sample.md" in cmd_str
    assert "percipience/agent-runner:latest" in cmd_str
    assert "claude --print Synthesize component" in cmd_str


def test_execute_plan_not_found(repo_root):
    """Validates rejection when plan specification file is missing."""
    executor = ContainerPlanExecutor(workspace_root=repo_root, mock_mode=True)
    req = PlanExecutionRequest(
        plan_path="non_existent_plan.md",
        agent_id="agent_missing_plan",
        target_module="workplace/core",
        prompt="Implement something"
    )
    receipt = executor.execute(req)
    assert receipt.status == "FAILED"
    assert "Plan specification file not found" in (receipt.error_message or "")


def test_execute_simulation_mode_with_code_synthesis(repo_root, plan_path):
    """Validates end-to-end plan derivation in simulation mode."""
    agent_id = "agent_sim_derive_01"
    executor = ContainerPlanExecutor(workspace_root=repo_root, mock_mode=True)
    
    req = PlanExecutionRequest(
        plan_path=plan_path,
        agent_id=agent_id,
        target_module="workplace/core",
        prompt="Implement sample helper",
        run_gatekeeper=False,
        target_file_rel="workplace/core/sim_helper.py",
        mock_synthesized_code="def helper(): return 'simulated'\n"
    )

    try:
        receipt = executor.execute(req)
        assert receipt.status == "SUCCESS"
        assert receipt.agent_id == agent_id
        assert Path(receipt.worktree_path).exists()
        
        # Verify code was written to worktree
        synthesized_file = Path(receipt.worktree_path) / "workplace" / "core" / "sim_helper.py"
        assert synthesized_file.exists()
        assert "def helper()" in synthesized_file.read_text(encoding="utf-8")
    finally:
        executor.release_worktree(agent_id)


def test_execute_live_docker_container(repo_root, plan_path):
    """Tests containerized plan derivation using live percipience/agent-runner container."""
    # Check if Docker is available on system
    if not ContainerPlanExecutor._is_docker_available():
        pytest.skip("Docker daemon not available in this test environment")

    agent_id = "agent_docker_live_01"
    executor = ContainerPlanExecutor(
        workspace_root=repo_root,
        docker_image="percipience/agent-runner:latest",
        mock_mode=False
    )

    req = PlanExecutionRequest(
        plan_path=plan_path,
        agent_id=agent_id,
        target_module="workplace/core",
        prompt="Verify container plan execution",
        run_gatekeeper=False,
        env_vars={"PERCIPIENCE_SIMULATION": "1"},
        target_file_rel="workplace/core/docker_synthesized.py",
        mock_synthesized_code="# live docker test\nVALUE = 42\n"
    )

    try:
        receipt = executor.execute(req)
        assert receipt.status == "SUCCESS"
        assert receipt.exit_code == 0
        assert receipt.agent_id == agent_id
        
        # Verify file was synthesized inside the mounted worktree
        wt_path = Path(receipt.worktree_path)
        synth_file = wt_path / "workplace" / "core" / "docker_synthesized.py"
        assert synth_file.exists()
        assert "VALUE = 42" in synth_file.read_text(encoding="utf-8")
    finally:
        executor.release_worktree(agent_id)


def test_cli_swarm_exec_subcommand(repo_root, plan_path):
    """Validates CLI invocation: ./.nb/bin/percipience swarm exec --plan ... --mock."""
    agent_id = "agent_cli_swarm_test"
    cmd = [
        str(repo_root / ".nb" / "bin" / "percipience"),
        "swarm", "exec",
        "--plan", plan_path,
        "--agent-id", agent_id,
        "--target-module", "workplace/core",
        "--prompt", "CLI swarm test",
        "--no-gate",
        "--mock"
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        assert proc.returncode == 0
        assert "Initializing Sandboxed Container Plan Derivation..." in proc.stdout
        assert "Containerized plan execution succeeded" in proc.stdout
    finally:
        WorktreeEngine.release(repo_root, agent_id)


def test_execute_plan_with_lifecycle_hooks(repo_root, plan_path):
    """Validates that ContainerPlanExecutor resolves and executes manifest lifecycle hooks."""
    agent_id = "agent_hooks_test_01"
    executor = ContainerPlanExecutor(workspace_root=repo_root, mock_mode=True)

    req = PlanExecutionRequest(
        plan_path=plan_path,
        agent_id=agent_id,
        target_module="workplace/core",
        prompt="Verify lifecycle hooks",
        run_gatekeeper=False,
        run_lifecycle_hooks=True,
        target_file_rel="workplace/core/hook_test.py",
        mock_synthesized_code="# hook test\n"
    )

    try:
        receipt = executor.execute(req)
        assert receipt.status == "SUCCESS"
        assert "pre_spawn" in receipt.lifecycle_hooks_executed
        assert receipt.lifecycle_hooks_executed["pre_spawn"] == "PASSED"
        assert "pre_execution" in receipt.lifecycle_hooks_executed
        assert receipt.lifecycle_hooks_executed["pre_execution"] == "PASSED"
        assert "post_execution" in receipt.lifecycle_hooks_executed
        assert receipt.lifecycle_hooks_executed["post_execution"] == "PASSED"
        assert "handover" in receipt.lifecycle_hooks_executed
        assert receipt.lifecycle_hooks_executed["handover"] == "ISSUED"
        assert "LIFECYCLE HOOK" in receipt.stdout
    finally:
        executor.release_worktree(agent_id)

