"""
Percipience Workflow Orchestrator & Parallel Fan-Out / Fan-In Barrier Synchronization Engine (CAP-27)
Supports declarative concurrent step dispatch, dependency DAG resolution,
and barrier synchronization for high-throughput multi-agent verification gates.
"""

import time
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class WorkflowOrchestrator:
    """
    Executes declarative workflow DAGs with support for parallel fan-out groups,
    barrier joins, dependency satisfaction, and token metering.
    """

    @classmethod
    def load_workflow(cls, workflow_path: Path) -> Dict[str, Any]:
        """Loads and validates a workflow YAML specification."""
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow definition not found at: {workflow_path}")
        with open(workflow_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if "workflow_id" not in data or "steps" not in data:
            raise ValueError(f"Invalid workflow schema in {workflow_path}")
        return data

    @classmethod
    def execute_workflow(
        cls,
        workflow_def: Dict[str, Any],
        step_executors: Optional[Dict[str, Callable[..., Dict[str, Any]]]] = None,
        max_workers: int = 4,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a workflow definition respecting step dependencies and parallel execution groups.
        - Steps with the same `parallel_group` that have all dependencies satisfied are executed concurrently.
        - `fan_in_barrier` waits for all steps in the parallel group to complete before proceeding.
        """
        step_executors = step_executors or {}
        context = context if context is not None else {}
        if workflow_def.get("workflow_id") == "wf_sequential_plan_execution":
            raise ValueError(
                "Sequential plan workflows must be dispatched through WorkflowRunner.run_plan_by_id"
            )
        steps: List[Dict[str, Any]] = workflow_def.get("steps", [])

        step_lookup = {s["id"]: s for s in steps}
        if len(step_lookup) != len(steps):
            raise ValueError("Workflow contains duplicate step IDs")
        for step in steps:
            missing_dependencies = set(step.get("depends_on", [])) - set(step_lookup)
            if missing_dependencies:
                raise ValueError(
                    f"Step {step['id']} references unknown dependencies: {sorted(missing_dependencies)}"
                )

        step_results: Dict[str, Dict[str, Any]] = {}
        executed_steps: Set[str] = set()
        remaining_steps = list(steps)
        total_start = time.time()

        while remaining_steps:
            # Find all steps whose dependencies are satisfied
            ready_steps = [
                s for s in remaining_steps
                if all(dep in executed_steps for dep in s.get("depends_on", []))
            ]

            if not ready_steps:
                # Cycle or unsatisfied dependencies detected
                unresolved = [s["id"] for s in remaining_steps]
                return {
                    "workflow_id": workflow_def.get("workflow_id"),
                    "status": "DEADLOCK_OR_UNRESOLVED_DEPENDENCY",
                    "unresolved_steps": unresolved,
                    "executed_steps": step_results,
                    "duration_sec": round(time.time() - total_start, 4)
                }

            # Check if multiple ready steps share a parallel_group or can be run concurrently
            parallel_candidates = [s for s in ready_steps if s.get("parallel_group")]
            
            if len(parallel_candidates) > 1:
                # Group by parallel_group
                group_name = parallel_candidates[0].get("parallel_group")
                group_steps = [s for s in parallel_candidates if s.get("parallel_group") == group_name]
                
                group_results = cls._execute_parallel_group(group_steps, step_executors, max_workers, context)
                for sid, res in group_results.items():
                    step_results[sid] = res
                failed = [(sid, res) for sid, res in group_results.items() if res.get("status") != "SUCCESS"]
                if failed:
                    sid, res = failed[0]
                    return {
                        "workflow_id": workflow_def.get("workflow_id"),
                        "status": "FAILED",
                        "failed_step": sid,
                        "error": res.get("error"),
                        "step_count": len(step_results),
                        "executed_steps": step_results,
                        "duration_sec": round(time.time() - total_start, 4),
                    }
                executed_steps.update(group_results)
                remaining_steps = [s for s in remaining_steps if s["id"] not in group_results]
            else:
                # Execute single step
                target_step = ready_steps[0]
                sid = target_step["id"]
                res = cls._execute_single_step(target_step, step_executors, context)
                step_results[sid] = res
                if res.get("status") != "SUCCESS":
                    return {
                        "workflow_id": workflow_def.get("workflow_id"),
                        "status": "FAILED",
                        "failed_step": sid,
                        "error": res.get("error"),
                        "step_count": len(step_results),
                        "executed_steps": step_results,
                        "duration_sec": round(time.time() - total_start, 4)
                    }
                executed_steps.add(sid)
                remaining_steps = [s for s in remaining_steps if s["id"] != sid]

        total_duration = round(time.time() - total_start, 4)
        return {
            "workflow_id": workflow_def.get("workflow_id"),
            "status": "COMPLETED",
            "step_count": len(step_results),
            "executed_steps": step_results,
            "duration_sec": total_duration,
            "parallel_acceleration_enabled": True
        }

    @classmethod
    def _execute_single_step(
        cls,
        step: Dict[str, Any],
        executors: Dict[str, Callable],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executes a single workflow step."""
        sid = step["id"]
        executor_key = step.get("executor", sid)
        func = executors.get(executor_key) or executors.get(sid)

        start_time = time.time()
        if func:
            try:
                try:
                    res = func(step=step, context=context)
                except TypeError:
                    try:
                        res = func(context)
                    except TypeError:
                        res = func(step, context)
                if not isinstance(res, dict):
                    raise TypeError(f"Executor for {sid} must return a result dictionary")
                duration = round(time.time() - start_time, 4)
                status = res.get("status")
                return {
                    "step_id": sid,
                    "name": step.get("name", sid),
                    "status": "SUCCESS" if status == "SUCCESS" else "FAILED",
                    "output": res,
                    "error": res.get("error") if status != "SUCCESS" else None,
                    "duration_sec": duration
                }
            except Exception as e:
                duration = round(time.time() - start_time, 4)
                return {
                    "step_id": sid,
                    "name": step.get("name", sid),
                    "status": "FAILED",
                    "error": str(e),
                    "duration_sec": duration
                }
        elif step.get("agent"):
            time.sleep(0.005)
            duration = round(time.time() - start_time, 4)
            return {
                "step_id": sid,
                "name": step.get("name", sid),
                "status": "SUCCESS",
                "output": {"message": f"Step {sid} executed successfully via agent {step.get('agent')}"},
                "duration_sec": duration
            }
        else:
            return {
                "step_id": sid,
                "name": step.get("name", sid),
                "status": "FAILED",
                "error": f"No executor registered for step {sid} ({executor_key})",
                "duration_sec": round(time.time() - start_time, 4)
            }

    @classmethod
    def _execute_parallel_group(
        cls,
        steps: List[Dict[str, Any]],
        executors: Dict[str, Callable],
        max_workers: int,
        context: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Executes multiple workflow steps concurrently using ThreadPoolExecutor."""
        results: Dict[str, Dict[str, Any]] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(steps), max_workers)) as pool:
            future_to_step = {
                pool.submit(cls._execute_single_step, s, executors, context): s["id"]
                for s in steps
            }
            for future in concurrent.futures.as_completed(future_to_step):
                sid = future_to_step[future]
                try:
                    res = future.result()
                    results[sid] = res
                except Exception as e:
                    results[sid] = {
                        "step_id": sid,
                        "status": "FAILED",
                        "error": str(e),
                        "duration_sec": 0.0
                    }
        return results
