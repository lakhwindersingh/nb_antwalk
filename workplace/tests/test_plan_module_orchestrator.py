"""
Unit Tests for the Plan Module Orchestrator

Verifies deterministic discovery of plan submodules, graceful handling of plans
with no (or not-yet-authored) submodules, generation of per-submodule agents,
rules, and a sequential derivation workflow, and idempotent re-runs. Also asserts
the live enterprise design-system plan is fully materialized and in sync.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    from workplace.core.plan_module_orchestrator import PlanModuleOrchestrator
except ImportError:
    from core.plan_module_orchestrator import PlanModuleOrchestrator

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestPlanModuleOrchestrator(unittest.TestCase):

    def setUp(self):
        self.workspace_root = Path(__file__).resolve().parents[2]

    def test_dependency_synchronization_orders_and_validates_before_writing(self):
        root, target = self._make_plan(modules_dir=False)
        base = root / ".nb/plan/l1/base"
        _write(base / "MANIFEST.yaml", yaml.safe_dump({"plan_id": "base"}))
        manifest_path = target / "MANIFEST.yaml"
        manifest = yaml.safe_load(manifest_path.read_text())
        manifest["dependencies"] = {"requires": ["l1/base"]}
        _write(manifest_path, yaml.safe_dump(manifest))
        orch = PlanModuleOrchestrator(root)
        reports = orch.synchronize_dependencies("master_demo_plan", apply=False, sync_registries=False)
        self.assertEqual([report["plan_id"] for report in reports], ["base", "master_demo_plan"])
        _write(base / "MANIFEST.yaml", yaml.safe_dump({"plan_id": "base", "dependencies": ["master_demo_plan"]}))
        with self.assertRaisesRegex(ValueError, "cycle"):
            orch.synchronize_dependencies("master_demo_plan", sync_registries=False)
        self.assertFalse((root / ".nb/agentic").exists())

    def test_dependency_synchronization_rejects_missing_and_ambiguous_references(self):
        root, target = self._make_plan(modules_dir=False)
        manifest_path = target / "MANIFEST.yaml"
        manifest = yaml.safe_load(manifest_path.read_text())
        manifest["dependencies"] = {"requires": ["missing"]}
        _write(manifest_path, yaml.safe_dump(manifest))
        orch = PlanModuleOrchestrator(root)
        with self.assertRaisesRegex(ValueError, "Unknown plan dependency"):
            orch.synchronize_dependencies("master_demo_plan")
        _write(root / ".nb/plan/l1/one/MANIFEST.yaml", "plan_id: missing\n")
        _write(root / ".nb/plan/l1/two/MANIFEST.yaml", "plan_id: missing\n")
        with self.assertRaisesRegex(ValueError, "Ambiguous plan dependency"):
            orch.synchronize_dependencies("master_demo_plan")
        self.assertFalse((root / ".nb/agentic").exists())

    def _make_plan(self, modules_dir: bool = True, manifest_modules=None):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        plan = root / ".nb" / "plan" / "master" / "demo-plan"
        plan.mkdir(parents=True, exist_ok=True)
        (plan / "concise.md").write_text("# Demo Plan\n\nShort.\n", encoding="utf-8")
        (plan / "detailed.md").write_text("# Demo Plan Detailed\n\nLong.\n", encoding="utf-8")

        manifest = {
            "schema_version": "3.0.0",
            "plan_id": "master_demo_plan",
            "plan_name": "Demo Plan",
            "version": "1.0.0",
            "layer": "master",
            "status": "active",
            "modules": manifest_modules or [],
        }
        _write(plan / "MANIFEST.yaml", yaml.safe_dump(manifest, sort_keys=False))

        if modules_dir:
            _write(
                plan / "modules" / "01_alpha.md",
                "# Module 01: Alpha Foundations\n\n"
                "**Module ID**: `mod_alpha`\n\n"
                "## 1. Architectural Mission\n"
                "Establish the alpha foundation layer.\n\n"
                "## 2. Invariants\n"
                "- Never regress the alpha contract.\n"
                "- Maintain token budgets.\n",
            )
            _write(
                plan / "modules" / "nested" / "02_beta.md",
                "# Module 02: Beta Surfaces\n\n"
                "## 1. Architectural Mission\n"
                "Deliver the beta surfaces.\n\n"
                "## 2. Invariants\n"
                "- Ship behind a feature flag.\n",
            )
        self.addCleanup(tmp.cleanup)
        return root, plan

    def test_01_discovers_declared_and_filesystem_modules(self):
        """Declared present modules + extra filesystem modules are discovered; missing ones are skipped."""
        root, plan = self._make_plan(
            manifest_modules=[
                {"id": "mod_alpha", "file": "modules/01_alpha.md", "title": "Alpha Foundations"},
                {"id": "mod_unwritten", "file": "modules/99_unwritten.md", "title": "Not Yet"},
            ]
        )
        orch = PlanModuleOrchestrator(root)
        modules = orch.discover_modules(plan)
        ids = [m["id"] for m in modules]
        self.assertIn("mod_alpha", ids)
        self.assertIn("beta", ids)  # derived from nested/02_beta.md
        self.assertNotIn("mod_unwritten", ids)
        self.assertEqual(
            [m["file"] for m in orch.declared_but_missing(plan)], ["modules/99_unwritten.md"]
        )

    def test_02_generates_agents_rules_and_workflow(self):
        """A full run materializes an agent per module, a rule per module, and a sequential workflow."""
        root, plan = self._make_plan(
            manifest_modules=[{"id": "mod_alpha", "file": "modules/01_alpha.md", "title": "Alpha Foundations"}]
        )
        report = PlanModuleOrchestrator(root).synchronize(plan, sync_registries=False)
        self.assertEqual(report["status"], "SYNCHRONIZED")
        self.assertEqual(report["plan_id"], "master_demo_plan")

        root_agent = root / ".nb/agentic/custom/agents/agent_master_demo_plan.yaml"
        alpha_agent = root / ".nb/agentic/custom/agents/agent_mod_alpha.yaml"
        alpha_rule = root / ".nb/context/rules/mod_alpha_rules.md"
        workflow = root / ".nb/agentic/workflows/wf_master_demo_plan_derivation.yaml"
        for artifact in (root_agent, alpha_agent, alpha_rule, workflow):
            self.assertTrue(artifact.exists(), f"missing {artifact}")

        manifest = yaml.safe_load(alpha_agent.read_text(encoding="utf-8"))
        self.assertEqual(manifest["agent_id"], "agent_mod_alpha")
        self.assertEqual(manifest["source_module"], "modules/01_alpha.md")
        self.assertEqual(manifest["governing_rules"], [".nb/context/rules/mod_alpha_rules.md"])

        rule_text = alpha_rule.read_text(encoding="utf-8")
        self.assertIn("`mod_alpha_rules`", rule_text)
        self.assertIn("Establish the alpha foundation layer.", rule_text)

        wf = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        step_ids = [s["id"] for s in wf["steps"]]
        self.assertEqual(step_ids[0], "step_plan_root")
        self.assertEqual(step_ids[-1], "step_module_merkle_seal")
        self.assertIn("step_mod_alpha", step_ids)

    def test_03_re_run_is_idempotent(self):
        """Re-running leaves every generated artifact unchanged."""
        root, plan = self._make_plan(
            manifest_modules=[{"id": "mod_alpha", "file": "modules/01_alpha.md", "title": "Alpha Foundations"}]
        )
        orch = PlanModuleOrchestrator(root)
        orch.synchronize(plan, sync_registries=False)
        second = orch.synchronize(plan, sync_registries=False)
        for category in second["artifacts"].values():
            self.assertTrue(all(item["state"] == "unchanged" for item in category), category)

    def test_04_plan_without_modules_is_graceful(self):
        """A plan with no submodules still yields a root agent and root+seal workflow."""
        root, plan = self._make_plan(modules_dir=False)
        report = PlanModuleOrchestrator(root).synchronize(plan, sync_registries=False)
        self.assertEqual(report["modules_discovered"], 0)
        self.assertTrue((root / ".nb/agentic/custom/agents/agent_master_demo_plan.yaml").exists())
        workflow = root / ".nb/agentic/workflows/wf_master_demo_plan_derivation.yaml"
        wf = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        self.assertEqual(
            [s["id"] for s in wf["steps"]], ["step_plan_root", "step_module_merkle_seal"]
        )

    def test_05_check_does_not_write(self):
        """--check reports artifacts as pending without touching the filesystem."""
        root, plan = self._make_plan(modules_dir=False)
        report = PlanModuleOrchestrator(root).synchronize(plan, apply=False, sync_registries=False)
        self.assertEqual(report["status"], "CHECKED")
        self.assertFalse((root / ".nb/agentic/custom/agents/agent_master_demo_plan.yaml").exists())
        self.assertTrue(all(i["state"] == "created" for i in report["artifacts"]["agents"]))

    def test_06_live_enterprise_plan_is_materialized(self):
        """The live enterprise design-system plan has one agent and rule per submodule, in sync."""
        plan = self.workspace_root / ".nb/plan/master/enterprise-ui-design-system"
        if not plan.exists():
            self.skipTest("enterprise-ui-design-system plan not present")
        orch = PlanModuleOrchestrator(self.workspace_root)
        modules = orch.discover_modules(plan)
        self.assertGreaterEqual(len(modules), 6)
        report = orch.synchronize(plan, apply=False, sync_registries=False)
        self.assertEqual(report["status"], "CHECKED")
        for module in modules:
            agent = self.workspace_root / f".nb/agentic/custom/agents/agent_{module['id']}.yaml"
            rule = self.workspace_root / module["rule_rel"]
            self.assertTrue(agent.exists(), f"missing agent for {module['id']}")
            self.assertTrue(rule.exists(), f"missing rule for {module['id']}")
        for category in report["artifacts"].values():
            self.assertTrue(all(item["state"] == "unchanged" for item in category), category)

    def test_07_projects_autonomous_execution_and_lifecycle_hooks(self):
        """Verifies that autonomous_execution, lifecycle_hooks, and contracts are projected into agent and workflow."""
        root, plan = self._make_plan(modules_dir=False)
        manifest_path = plan / "MANIFEST.yaml"
        manifest = yaml.safe_load(manifest_path.read_text())
        manifest["autonomous_execution"] = {
            "orchestrator_agent": "agent_sequential_plan_orchestrator",
            "execution_engine": "dynamic_dag",
            "worktree_isolation": True,
            "max_healing_loops": 3,
            "handoff_protocol": "hmac_sha256_attested",
            "anti_drift_gate": True,
        }
        manifest["lifecycle_hooks"] = {
            "pre_spawn": "percipience worktree lease",
            "pre_execution": "percipience check --ast-prune",
            "post_execution": "pytest workplace/tests/ -v",
            "handover": "percipience handoff issue",
            "pre_merge_gate": "percipience gate",
            "self_healing": "percipience heal --max-attempts 3",
            "post_merge_seal": "percipience merkle seal",
        }
        manifest["specification_contracts"] = {
            "wire_contracts": [{"path": ".nb/context/contracts/demo.yaml", "type": "RPC", "strict_mode": True}]
        }
        _write(manifest_path, yaml.safe_dump(manifest))

        orch = PlanModuleOrchestrator(root)
        report = orch.synchronize(plan, sync_registries=False)
        self.assertEqual(report["status"], "SYNCHRONIZED")

        root_agent = root / ".nb/agentic/custom/agents/agent_master_demo_plan.yaml"
        self.assertTrue(root_agent.exists())
        agent_data = yaml.safe_load(root_agent.read_text(encoding="utf-8"))
        self.assertIn("autonomous_execution", agent_data)
        self.assertEqual(agent_data["autonomous_execution"]["execution_engine"], "dynamic_dag")
        self.assertIn("lifecycle_hooks", agent_data)
        self.assertEqual(agent_data["lifecycle_hooks"]["pre_merge_gate"], "percipience gate")
        self.assertIn("specification_contracts", agent_data)

        workflow = root / ".nb/agentic/workflows/wf_master_demo_plan_derivation.yaml"
        self.assertTrue(workflow.exists())
        wf_data = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        self.assertIn("autonomous_execution", wf_data)
        self.assertIn("lifecycle_hooks", wf_data)
        self.assertIn("specification_contracts", wf_data)


class TestPlanOrchestratorCli(unittest.TestCase):
    """Verifies the `percipience plan` CLI wiring for autonomous submodule orchestration."""

    def setUp(self):
        self.workspace_root = Path(__file__).resolve().parents[2]
        self.cli = self.workspace_root / ".nb" / "bin" / "percipience"

    def test_01_plan_status_still_works(self):
        """`percipience plan` keeps its historical status behavior."""
        res = subprocess.run([sys.executable, str(self.cli), "plan"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("Active Plan Tier", res.stdout)

    def test_02_plan_orchestrate_check(self):
        """`percipience plan orchestrate --check` discovers submodules without writing."""
        plan_rel = ".nb/plan/master/enterprise-ui-design-system"
        if not (self.workspace_root / plan_rel).exists():
            self.skipTest("enterprise plan not present")
        res = subprocess.run(
            [sys.executable, str(self.cli), "plan", "orchestrate", "--plan-dir", plan_rel, "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["status"], "CHECKED")
        self.assertGreaterEqual(payload["modules_discovered"], 6)

    def test_03_plan_orchestrate_subcommands_registered(self):
        """The plan command exposes the orchestrate and bundle actions."""
        res = subprocess.run(
            [sys.executable, str(self.cli), "plan", "--help"], capture_output=True, text=True
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("orchestrate", res.stdout)
        self.assertIn("bundle", res.stdout)


if __name__ == "__main__":
    unittest.main()