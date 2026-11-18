#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${PLAN_ROOT}/../.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Percipience Plan Automated Verification Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Repo Root: ${REPO_ROOT}"
echo "Plan Root: ${PLAN_ROOT}"
echo ""

echo "▶ Step 1: Validating Dependency DAG, Schema v3.0 & Cycle Freedom..."
python3 "${SCRIPT_DIR}/validate_dag.py"

echo ""
echo "▶ Step 2: Validating Cryptographic Content Hashes..."
python3 "${SCRIPT_DIR}/verify_hashes.py"

echo ""
echo "▶ Step 3: Regenerating Capability Matrix & Index..."
python3 "${SCRIPT_DIR}/generate_capability_index.py"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 ALL PLAN QUALITY & INTEGRITY GATES PASSED (100% CERTIFIED)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
