#!/usr/bin/env python3
"""
Percipience Dynamic Task DAG Orchestrator & Runtime Sub-Goal Expansion Engine (GAP-AGT-01 / TODO-AGT-01)
Supports runtime step graph mutation, Plan-and-Solve / ReAct sub-goal synthesis,
blast-radius validation branching, and failure backtracking.
"""

import json
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) >= 3 and (Path(__file__).resolve().parents[2] / ".nb").exists() else Path(__file__).resolve().parents[1]


class DAGConstraintViolationError(Exception):
    """Raised when dynamic DAG expansion violates depth or node count limits."""
    pass


class CycleDetectedError(Exception):
    """Raised when DAG mutation introduces a cycle."""
    pass


@dataclass
class StepNode:
    id: str
    action: str
    name: str = ""
    dependencies: List[str] = field(default_factory=list)
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, BACKTRACKED, SKIPPED
    depth: int = 0
    parent_step_id: Optional[str] = None
    blast_radius: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DAGExecutionResult(dict):
    """
    Execution summary dictionary with property accessors for executed_steps,
    duration_ms, and status to ensure polymorphic compatibility across CLI and API callers.
    """
    @property
    def executed_steps(self) -> List[str]:
        return self.get("executed_steps", [])

    @property
    def duration_ms(self) -> float:
        return self.get("duration_seconds", 0.0) * 1000.0

    @property
    def status(self) -> str:
        return self.get("status", "SUCCESS")


class DynamicDAGOrchestrator:
    """
    Manages non-linear, dynamic task graphs capable of runtime sub-goal expansion,
    blast-radius branching, and backtrack routing.
    """

    MAX_RECURSION_DEPTH: int = 3
    MAX_TOTAL_STEPS: int = 20

    def __init__(
        self,
        dag_id: str = "dynamic_dag",
        max_depth: int = MAX_RECURSION_DEPTH,
        max_steps: int = MAX_TOTAL_STEPS,
        trace_log_path: Optional[Path] = None
    ):
        self.dag_id = dag_id
        self.max_depth = max_depth
        self.max_steps = max_steps
        self.nodes: Dict[str, StepNode] = {}
        self.trace_log_path = trace_log_path or (REPO_ROOT / ".nb" / "context" / "ledger" / "dynamic_dag_traces.jsonl")
        self.execution_log: List[Dict[str, Any]] = []

    def load_graph(self, dag_def: Dict[str, Any]) -> None:
        """Loads and validates an initial DAG definition."""
        self.dag_id = dag_def.get("dag_id", self.dag_id)
        self.max_depth = dag_def.get("max_recursion_depth", self.max_depth)
        self.max_steps = dag_def.get("max_total_steps", self.max_steps)
        self.nodes.clear()

        raw_nodes = dag_def.get("nodes", [])
        if len(raw_nodes) > self.max_steps:
            raise DAGConstraintViolationError(
                f"Initial node count ({len(raw_nodes)}) exceeds max limit ({self.max_steps})"
            )

        for n in raw_nodes:
            node = StepNode(
                id=n["id"],
                action=n["action"],
                name=n.get("name", n["id"]),
                dependencies=list(n.get("dependencies", [])),
                status=n.get("status", "PENDING"),
                depth=n.get("depth", 0),
                parent_step_id=n.get("parent_step_id"),
                blast_radius=list(n.get("blast_radius", [])),
                metadata=dict(n.get("metadata", {}))
            )
            self.nodes[node.id] = node

        # Verify initial acyclicity
        self.topological_sort()
        self._record_trace("GRAPH_LOADED", {"total_nodes": len(self.nodes)})

    def add_node(self, node: StepNode) -> None:
        """Adds a single node to the DAG with constraint checks."""
        if len(self.nodes) >= self.max_steps:
            raise DAGConstraintViolationError(
                f"Adding node '{node.id}' exceeds max total steps ({self.max_steps})"
            )
        if node.depth > self.max_depth:
            raise DAGConstraintViolationError(
                f"Node '{node.id}' depth ({node.depth}) exceeds max recursion depth ({self.max_depth})"
            )
        self.nodes[node.id] = node
        self.topological_sort()

    def topological_sort(self) -> List[str]:
        """
        Computes a valid topological execution order using Kahn's algorithm (O(V+E)).
        Raises CycleDetectedError if a cycle is present.
        """
        in_degree: Dict[str, int] = {nid: 0 for nid in self.nodes}
        adj: Dict[str, List[str]] = defaultdict(list)

        for nid, node in self.nodes.items():
            for dep in node.dependencies:
                if dep in self.nodes:
                    adj[dep].append(nid)
                    in_degree[nid] += 1

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        ordered: List[str] = []

        while queue:
            curr = queue.popleft()
            ordered.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered) != len(self.nodes):
            unresolved = [nid for nid, deg in in_degree.items() if deg > 0]
            raise CycleDetectedError(f"Cycle detected in dynamic DAG involving nodes: {unresolved}")

        return ordered

    def expand_subgoals(
        self,
        parent_step_id: str,
        subgoals: List[Any]
    ) -> List[str]:
        """
        Dynamically inserts runtime sub-goals under parent_step_id.
        Rewires downstream dependents of parent_step_id to wait for terminal subgoals.
        Enforces depth and step count limits.
        """
        if parent_step_id not in self.nodes:
            raise ValueError(f"Parent step '{parent_step_id}' does not exist in DAG")

        parent = self.nodes[parent_step_id]
        new_depth = parent.depth + 1

        if new_depth > self.max_depth:
            raise DAGConstraintViolationError(
                f"Dynamic expansion depth ({new_depth}) exceeds ceiling ({self.max_depth}) for '{parent_step_id}'"
            )

        if len(self.nodes) + len(subgoals) > self.max_steps:
            raise DAGConstraintViolationError(
                f"Dynamic expansion of {len(subgoals)} subgoals exceeds max node count ({self.max_steps})"
            )

        # Identify downstream dependents that originally waited on parent
        original_dependents = [
            nid for nid, n in self.nodes.items()
            if parent_step_id in n.dependencies
        ]

        created_ids: List[str] = []
        prev_subgoal_id = parent_step_id

        # Normalize and insert subgoals sequentially
        for idx, sg in enumerate(subgoals):
            if isinstance(sg, dict):
                sg_id = sg.get("id", f"{parent_step_id}_sub_{idx+1}")
                sg_node = StepNode(
                    id=sg_id,
                    action=sg.get("action", "subgoal_task"),
                    name=sg.get("name", sg_id),
                    dependencies=sg.get("dependencies", [prev_subgoal_id]),
                    status="PENDING",
                    depth=new_depth,
                    parent_step_id=parent_step_id,
                    blast_radius=sg.get("blast_radius", parent.blast_radius),
                    metadata=sg.get("metadata", {})
                )
            elif isinstance(sg, StepNode):
                sg_node = sg
                sg_node.depth = new_depth
                sg_node.parent_step_id = parent_step_id
                if not sg_node.dependencies:
                    sg_node.dependencies = [prev_subgoal_id]
            else:
                raise TypeError(f"Unsupported subgoal type: {type(sg)}")

            self.nodes[sg_node.id] = sg_node
            created_ids.append(sg_node.id)
            prev_subgoal_id = sg_node.id

        # Rewire original downstream dependents to wait on terminal subgoal
        if created_ids:
            terminal_id = created_ids[-1]
            for dep_id in original_dependents:
                node = self.nodes[dep_id]
                node.dependencies = [terminal_id if d == parent_step_id else d for d in node.dependencies]

        # Verify graph remains acyclic
        self.topological_sort()

        self._record_trace("SUBGOALS_EXPANDED", {
            "parent_step_id": parent_step_id,
            "created_subgoals": created_ids,
            "new_depth": new_depth,
            "total_nodes": len(self.nodes)
        })

        return created_ids

    def generate_blast_radius_subgraph(
        self,
        parent_step_id: str,
        affected_files: List[str],
        affected_symbols: Optional[List[str]] = None
    ) -> List[StepNode]:
        """
        Synthesizes a targeted 3-stage validation sub-graph based on modified files and AST symbols:
        1. validate_syntax -> 2. run_focused_tests -> 3. check_contract_parity
        """
        parent = self.nodes.get(parent_step_id)
        depth = (parent.depth + 1) if parent else 1
        symbols = affected_symbols or []

        step1 = StepNode(
            id=f"{parent_step_id}_val_syntax",
            action="validate_syntax",
            name=f"Validate Syntax ({len(affected_files)} files)",
            dependencies=[parent_step_id],
            depth=depth,
            parent_step_id=parent_step_id,
            blast_radius=affected_files,
            metadata={"files": affected_files}
        )

        step2 = StepNode(
            id=f"{parent_step_id}_focused_tests",
            action="run_focused_tests",
            name=f"Run Focused Tests ({len(symbols)} symbols)",
            dependencies=[step1.id],
            depth=depth,
            parent_step_id=parent_step_id,
            blast_radius=affected_files,
            metadata={"symbols": symbols, "files": affected_files}
        )

        step3 = StepNode(
            id=f"{parent_step_id}_contract_parity",
            action="check_contract_parity",
            name="Verify Wire Contract Parity",
            dependencies=[step2.id],
            depth=depth,
            parent_step_id=parent_step_id,
            blast_radius=affected_files,
            metadata={"check_contracts": True}
        )

        return [step1, step2, step3]

    def backtrack_and_route(
        self,
        failed_step_id: str,
        alternate_branches: List[Dict[str, Any]],
        worktree_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        When an exploratory branch fails, rolls back the failure branch,
        marks node as BACKTRACKED, and routes execution to an alternate strategy branch.
        """
        if failed_step_id not in self.nodes:
            return None

        failed_node = self.nodes[failed_step_id]
        failed_node.status = "BACKTRACKED"

        # Mark all downstream descendants as SKIPPED or BACKTRACKED
        descendants = self._get_descendants(failed_step_id)
        for desc_id in descendants:
            self.nodes[desc_id].status = "SKIPPED"

        if not alternate_branches:
            self._record_trace("BACKTRACK_EXHAUSTED", {
                "failed_step_id": failed_step_id,
                "reason": "No alternate branches provided"
            })
            return None

        # Select first alternate branch
        alt_branch = alternate_branches[0]
        alt_id = alt_branch.get("id", f"{failed_step_id}_alt_branch")
        alt_node = StepNode(
            id=alt_id,
            action=alt_branch.get("action", "alternate_strategy"),
            name=alt_branch.get("name", alt_id),
            dependencies=failed_node.dependencies,
            depth=failed_node.depth,
            parent_step_id=failed_node.parent_step_id,
            metadata={"alternate_to": failed_step_id, **alt_branch.get("metadata", {})}
        )

        self.nodes[alt_id] = alt_node

        self._record_trace("BACKTRACK_ROUTED", {
            "failed_step_id": failed_step_id,
            "alternate_step_id": alt_id,
            "skipped_descendants": list(descendants)
        })

        return alt_id

    def execute(
        self,
        step_executors: Optional[Dict[str, Callable[[StepNode, "DynamicDAGOrchestrator"], Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """
        Executes the dynamic DAG in topological order, supporting runtime graph mutation.
        """
        executors = step_executors or {}
        executed_steps: List[str] = []
        start_time = time.time()

        while True:
            # Recompute topological sort to capture runtime mutations
            try:
                order = self.topological_sort()
            except CycleDetectedError as e:
                return DAGExecutionResult({
                    "status": "FAILED",
                    "error": str(e),
                    "executed_steps": executed_steps,
                    "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()}
                })

            # Find next PENDING node whose dependencies are all COMPLETED
            candidate: Optional[StepNode] = None
            for nid in order:
                node = self.nodes[nid]
                if node.status == "PENDING":
                    deps_satisfied = all(
                        self.nodes[d].status == "COMPLETED"
                        for d in node.dependencies
                        if d in self.nodes
                    )
                    if deps_satisfied:
                        candidate = node
                        break

            if candidate is None:
                # No more executable nodes
                break

            candidate.status = "RUNNING"
            self._record_trace("STEP_RUNNING", {"step_id": candidate.id, "action": candidate.action})

            executor_fn = executors.get(candidate.action) or executors.get(candidate.id)
            if executor_fn:
                try:
                    result = executor_fn(candidate, self)
                    candidate.result = result
                    if result.get("status") in ("FAILED", "ERROR"):
                        candidate.status = "FAILED"
                    else:
                        candidate.status = "COMPLETED"
                except Exception as ex:
                    candidate.status = "FAILED"
                    candidate.result = {"error": str(ex)}
            else:
                # Default no-op executor
                candidate.status = "COMPLETED"
                candidate.result = {"status": "SUCCESS", "message": f"Executed action {candidate.action}"}

            executed_steps.append(candidate.id)
            self._record_trace("STEP_COMPLETED", {
                "step_id": candidate.id,
                "status": candidate.status,
                "result": candidate.result
            })

        all_completed = all(n.status in ("COMPLETED", "SKIPPED", "BACKTRACKED") for n in self.nodes.values())
        has_failed = any(n.status == "FAILED" for n in self.nodes.values())

        overall_status = "COMPLETED" if (all_completed and not has_failed) else "FAILED"

        summary = {
            "dag_id": self.dag_id,
            "status": overall_status,
            "duration_seconds": round(time.time() - start_time, 4),
            "executed_steps": executed_steps,
            "total_nodes": len(self.nodes),
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()}
        }

        self._record_trace("DAG_FINISHED", summary)
        return DAGExecutionResult(summary)

    def _get_descendants(self, step_id: str) -> Set[str]:
        """Finds all downstream descendant node IDs."""
        descendants: Set[str] = set()
        queue = [step_id]
        while queue:
            curr = queue.pop(0)
            for nid, node in self.nodes.items():
                if curr in node.dependencies and nid not in descendants:
                    descendants.add(nid)
                    queue.append(nid)
        return descendants

    def _record_trace(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Appends a trace event to in-memory log and persistent traces JSONL."""
        entry = {
            "timestamp": time.time(),
            "dag_id": self.dag_id,
            "event": event_type,
            "payload": payload
        }
        self.execution_log.append(entry)
        try:
            self.trace_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.trace_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass
