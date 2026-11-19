"""
Test Suite for Percipience Master Test Governance & AI-Assisted Verification Framework (.nb/plan/test).
Validates:
- Space directory integrity, 4-file pattern, and cryptographic manifest synchronization.
- Line count invariant: N(concise) < N(detailed).
- Plan registration in .nb/plan/PLAN_INDEX.md and .nb/plan/README.md.
- Programmatic execution of PercipienceTestOrchestrator across tiers.
- Machine-readable test_results.json schema and test_summary.md generation.
- Quantitative GenAI evaluation metrics (Faithfulness, Semantic Parity, Relevancy).
- Automated AI failure triage and diagnostic reprompt advice.
- CLI subcommand 'percipience test' integration.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_PLAN_DIR = REPO_ROOT / ".nb" / "plan" / "test"

# Import test runner
sys.path.insert(0, str(TEST_PLAN_DIR))
from test_runner import PercipienceTestOrchestrator, TIER_MAPPING


class TestMasterTestPlanSpace(unittest.TestCase):
    """Test space structure, file pattern, and cryptographic manifest integrity."""

    def test_01_space_files_exist(self):
        """Verify all 5 required files exist in .nb/plan/test/."""
        self.assertTrue(TEST_PLAN_DIR.exists(), ".nb/plan/test directory missing")
        expected_files = ["README.md", "MANIFEST.yaml", "concise.md", "detailed.md", "test_runner.py"]
        for f in expected_files:
            file_path = TEST_PLAN_DIR / f
            self.assertTrue(file_path.exists(), f"Missing required file: {f}")
            self.assertGreater(file_path.stat().st_size, 100, f"File {f} is suspiciously small")

    def test_02_manifest_metadata_and_hashes(self):
        """Verify MANIFEST.yaml metadata and SHA-256 cryptographic hashes."""
        manifest_path = TEST_PLAN_DIR / "MANIFEST.yaml"
        self.assertTrue(manifest_path.exists())

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        self.assertEqual(manifest.get("plan_id"), "percipience_master_test_plan")
        self.assertEqual(manifest.get("version"), "1.0.0")
        self.assertEqual(manifest.get("status"), "active")
        self.assertEqual(manifest.get("capability_rating"), "L2")

        # Verify cryptographic hashes match disk files
        file_versions = manifest.get("file_versions", {})
        for name, info in file_versions.items():
            path_rel = info["path"]
            target_file = TEST_PLAN_DIR / path_rel
            self.assertTrue(target_file.exists(), f"Target file in manifest not found: {path_rel}")
            
            content = target_file.read_bytes()
            computed_hash = hashlib.sha256(content).hexdigest()
            self.assertEqual(info["content_hash"], computed_hash, f"Hash mismatch for {path_rel}")

    def test_03_line_count_invariant(self):
        """Verify line count invariant: N(concise) < N(detailed)."""
        concise_lines = len((TEST_PLAN_DIR / "concise.md").read_text(encoding="utf-8").splitlines())
        detailed_lines = len((TEST_PLAN_DIR / "detailed.md").read_text(encoding="utf-8").splitlines())

        self.assertGreater(detailed_lines, concise_lines, "Line count invariant violated: detailed must be longer than concise")
        self.assertGreater(concise_lines, 50, "Concise spec should have meaningful content")
        self.assertGreater(detailed_lines, 300, "Detailed spec should be comprehensive")

    def test_04_plan_catalog_registration(self):
        """Verify .nb/plan/test is registered in PLAN_INDEX.md and README.md."""
        index_text = (REPO_ROOT / ".nb" / "plan" / "PLAN_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("percipience_master_test_plan", index_text)
        self.assertIn("test/concise.md", index_text)
        self.assertIn("test/detailed.md", index_text)

        readme_text = (REPO_ROOT / ".nb" / "plan" / "README.md").read_text(encoding="utf-8")
        self.assertIn("test/ (Test Governance & Verification)", readme_text)
        self.assertIn("test/detailed.md", readme_text)


class TestAITestOrchestratorExecution(unittest.TestCase):
    """Test programmatic test runner execution, reporting, and AI evaluations."""

    def setUp(self):
        self.temp_out = Path(tempfile.mkdtemp())

    def test_05_tier_mapping_completeness(self):
        """Verify test tier mappings cover all expected functional domains."""
        expected_tiers = ["all", "unit", "integration", "portal", "guardrails", "governance", "security", "benchmarks"]
        for tier in expected_tiers:
            self.assertIn(tier, TIER_MAPPING, f"Missing tier: {tier}")
            targets = TIER_MAPPING[tier]
            self.assertIsInstance(targets, list)
            self.assertGreater(len(targets), 0)
            for t in targets:
                p = REPO_ROOT / t
                self.assertTrue(p.exists(), f"Target test path does not exist: {t}")

        # Verify dedicated vulnerability suite exists
        vuln_suite = REPO_ROOT / "workplace" / "tests" / "test_vulnerability_suite.py"
        self.assertTrue(vuln_suite.exists(), "test_vulnerability_suite.py must exist")

    def test_06_orchestrator_execution_and_reports(self):
        """Execute unit tier programmatically and verify structured report generation."""
        orchestrator = PercipienceTestOrchestrator(
            tier="unit",
            output_dir=self.temp_out,
            eval_ai=True,
            ai_triage=True
        )

        results = orchestrator.run_tests(quiet=True)
        self.assertEqual(results["status"], "PASSED")
        self.assertEqual(results["exit_code"], 0)
        
        summary = results["summary"]
        self.assertGreater(summary["total"], 0)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["pass_rate_pct"], 100.0)

        # Check JSON report
        json_file = self.temp_out / "test_results.json"
        self.assertTrue(json_file.exists())
        with open(json_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["status"], "PASSED")
        self.assertIn("execution_id", saved_data)
        self.assertIn("ai_evaluation", saved_data)

        # Check Markdown summary
        md_file = self.temp_out / "test_summary.md"
        self.assertTrue(md_file.exists())
        md_content = md_file.read_text(encoding="utf-8")
        self.assertIn("Percipience Test Execution Report", md_content)
        self.assertIn("Execution Summary", md_content)
        self.assertIn("AI & GenAI Quality Evaluation", md_content)

    def test_06b_orchestrator_security_tier_execution(self):
        """Execute dedicated security red-team tier programmatically."""
        orchestrator = PercipienceTestOrchestrator(
            tier="security",
            output_dir=self.temp_out,
            eval_ai=True
        )
        results = orchestrator.run_tests(quiet=True)
        self.assertEqual(results["status"], "PASSED")
        self.assertEqual(results["exit_code"], 0)
        self.assertGreaterEqual(results["summary"]["total"], 18)

    def test_07_genai_evaluation_metrics(self):
        """Verify quantitative GenAI evaluation metrics meet SLA thresholds."""
        orchestrator = PercipienceTestOrchestrator(
            tier="unit",
            output_dir=self.temp_out,
            eval_ai=True
        )
        ai_metrics = orchestrator._compute_ai_metrics(passed=50, failed=0)
        self.assertGreaterEqual(ai_metrics["semantic_parity_score"], 0.950)
        self.assertGreaterEqual(ai_metrics["faithfulness_score"], 0.900)
        self.assertGreaterEqual(ai_metrics["hallucination_freedom_score"], 0.950)
        self.assertGreaterEqual(ai_metrics["context_relevancy_score"], 0.850)
        self.assertGreaterEqual(ai_metrics["average_token_savings_pct"], 40.0)
        self.assertTrue(ai_metrics["governance_threshold_passed"])

    def test_08_ai_failure_triage_diagnostics(self):
        """Verify automated AI failure triage synthesizes accurate diagnostic recommendations."""
        orchestrator = PercipienceTestOrchestrator(
            tier="unit",
            output_dir=self.temp_out,
            ai_triage=True
        )

        trace_assertion = "AssertionError: Expected 0.985 >= 0.990\nassert False"
        triage_1 = orchestrator._perform_ai_triage(trace_assertion)
        self.assertEqual(len(triage_1), 1)
        self.assertEqual(triage_1[0]["issue_type"], "ASSERTION_MISMATCH")

        trace_import = "ModuleNotFoundError: No module named 'workplace.core.missing'"
        triage_2 = orchestrator._perform_ai_triage(trace_import)
        self.assertEqual(len(triage_2), 1)
        self.assertEqual(triage_2[0]["issue_type"], "MODULE_IMPORT_ERROR")


class TestPercipienceCLICommandIntegration(unittest.TestCase):
    """Test CLI integration of 'percipience test' command."""

    def test_09_cli_test_command_help(self):
        """Verify 'percipience test --help' succeeds and shows tier choices."""
        cli_bin = REPO_ROOT / ".nb" / "bin" / "percipience"
        res = subprocess.run([str(cli_bin), "test", "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI help failed: {res.stderr}")
        self.assertIn("--tier", res.stdout)
        self.assertIn("--ai-triage", res.stdout)
        self.assertIn("--eval-ai", res.stdout)

    def test_10_cli_test_command_execution(self):
        """Verify running 'percipience test --tier unit --quiet' succeeds with exit code 0."""
        cli_bin = REPO_ROOT / ".nb" / "bin" / "percipience"
        res = subprocess.run([str(cli_bin), "test", "--tier", "unit", "--quiet"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI test run failed: {res.stderr}")
        self.assertIn("Execution Complete: PASSED", res.stdout)


if __name__ == "__main__":
    unittest.main()
