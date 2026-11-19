# 🧪 Percipience Master Test Plan Space (`.nb/plan/test/`)

> **Master Test Governance & Automated Verification Framework**  
> **Target Release**: Percipience v3.0 & Enterprise Platform v7.2.0-prod  
> **Status**: **ACTIVE & CODIFIED**  
> **Framework Stack**: **Rust Native Engine (`cargo test --workspace`) + Criterion Benchmarks + Miri Memory Verification + Playwright 1.48+ E2E + OpenTelemetry GenAI + OWASP LLM Red-Team Suite**  

---

## 📌 Space Overview

The `.nb/plan/test/` space defines the authoritative, end-to-end testing and vulnerability verification blueprint for the **Percipience Context Engineering OS & Autonomous CI/CD Ecosystem**. It establishes an AI-assisted, fully automatable testing harness covering all 18 core subsystems across all commercial tiers (**Free Community, Team, Business, and Enterprise**) and a dedicated adversarial vulnerability suite.

```text
📦 .nb/plan/test/
├── 📖 README.md              ← YOU ARE HERE (Quick Reference & Navigation)
├── 📋 MANIFEST.yaml          ← Cryptographic Hash & Line Count Version Manifest
├── 📄 concise.md             ← High-Density Test Specification for AI Context Ingestion
├── 📑 detailed.md            ← Exhaustive 360-Degree Implementation Test Plan
└── ⚙️ test_runner.py         ← Automatable AI-Assisted Test Orchestrator & Report Generator
```

---

## 🎯 Test Framework Rationale

To satisfy the dual requirements of **human developer ergonomics** and **autonomous AI coding agent orchestration**, the testing stack is standardized on:

1. **Rust Native Cargo Workspace Test Engine**:
   - High-performance, concurrent test execution across all crates (`percipience-core`, `percipience-cli`, `percipience-orchestrator`, `percipience-security`, `percipience-server`, `percipience-lsp`, `percipience-packager`).
   - Zero-overhead native execution, strict async tests (`tokio::test`), and isolated tempdir worktrees.
2. **Machine-Readable Structured Telemetry & Allure Output**:
   - Structured JSON outputs (`test_results.json`) consumed instantly by AI agents.
   - Interactive HTML visual reports with step-by-step logs, attachment diffs, and execution timelines.
3. **Quantitative LLM Evaluation & Miri Memory Checks**:
   - Native evaluation of LLM prompt outputs: **Faithfulness ($\ge 0.90$)**, **Hallucination Freedom ($\ge 0.95$)**, **Context Relevancy ($\ge 0.85$)**, and **Spec-to-Code Semantic Parity ($S_{SP} \ge 0.950$)**.
   - Miri undefined-behavior and memory-safety verification for unsafe blocks.
4. **Adversarial Security & OWASP LLM Top 10 Suite**:
   - Comprehensive vulnerability testing: Direct/indirect prompt injection, jailbreaks, PII exfiltration, AST shellcode injection, `HandoffToken` HMAC forgery/replay, Merkle collisions, and gVisor container breakouts.
5. **OpenTelemetry GenAI (OTel) Distributed Tracing**:
   - Validates W3C `traceparent` headers and GenAI semantic spans (`gen_ai.system`, `gen_ai.usage.*`) in `context/ledger/otel_spans.jsonl`.
6. **Playwright 1.48+ & Vitest 2.x / Axe-Core**:
   - Headless browser testing of the SaaS Portal, interactive AST pruner playground, and WCAG 2.1 AA accessibility benchmarks.
7. **Percipience Autonomous Self-Healing Triad**:
   - Direct integration with `crates/percipience-core/src/diagnostic.rs` to trigger bounded 3-step AI repair loops upon test failures.

---

## 🗺️ Multi-Tier Capability & Subsystem Coverage Matrix

| Subsystem # | Architecture Subsystem & Pillar | Free | Team | Business | Enterprise | Test Suite File(s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **01** | **Quad-Space Standard Scaffolding & CLI** | ✅ | ✅ | ✅ | ✅ | `test_play3_suite.py` |
| **02** | **Structural AST Token Optimization** | ✅ | ✅ | ✅ | ✅ | `test_play3_suite.py` |
| **03** | **Cryptographic Merkle State Ledger** | ✅ | ✅ | ✅ | ✅ | `test_play3_suite.py` |
| **04** | **Immutable Cloud WORM Storage** | ❌ | ❌ | ❌ | ✅ | `test_play3_suite.py` |
| **05** | **Context Poisoning & Surgical Rollback** | ✅ | ✅ | ✅ | ✅ | `test_play3_suite.py` |
| **06** | **Sealed Binary Enclave (`.nbpack`)** | ❌ | ❌ | ✅ | ✅ | `test_play3_suite.py` |
| **07** | **Hybrid Context & Agent Plugin Engine** | ✅ | ✅ | ✅ | ✅ | `test_play3_suite.py` |
| **08** | **Bring Your Own Repository (BYOR)** | ❌ | ✅ | ✅ | ✅ | `test_play3_suite.py` |
| **09** | **Cloud SaaS Portal & Microservices** | ❌ | ❌ | ✅ | ✅ | `test_portal_*.py` |
| **10** | **FinOps Token Savings Metering** | ❌ | ❌ | ✅ | ✅ | `test_fleet_telemetry_finops.py` |
| **11** | **Corporate UI & Web Quality (WCAG 2.1)** | ❌ | ❌ | ✅ | ✅ | `test_play3_suite.py` |
| **12** | **Terraform Multi-Cloud Blueprints** | ❌ | ❌ | ❌ | ✅ | `test_play3_suite.py` |
| **13** | **Autonomous CI/CD Triad & Plugins** | ✅ | ✅ | ✅ | ✅ | `test_play3_suite.py` |
| **14** | **Anti-Drift & 6-Vector Semantic Parity** | ✅ | ✅ | ✅ | ✅ | `test_play3_suite.py` |
| **15** | **IDE Plugin Spaces (VS Code & JetBrains)**| ❌ | ✅ | ✅ | ✅ | `test_ide_plugins_space.py` |
| **16** | **Distributed Swarms (DEWS) & Docker** | ❌ | ✅ | ✅ | ✅ | `test_dynamic_dag_orchestrator.py`|
| **17** | **Runtime Guardrails & Prompt Injection** | ✅ | ✅ | ✅ | ✅ | `test_runtime_guardrails.py` |
| **18** | **Vulnerability & Red-Team Security** | ✅ | ✅ | ✅ | ✅ | `test_vulnerability_suite.py` |

---

## 🚀 Quick Execution Guide

### 1. Run Complete Automated Test Suite
```bash
cargo test --workspace
```

### 2. Run via AI-Assisted Test Orchestrator
```bash
# Execute specific tier with structured JSON output and AI evaluation
./percipience test --tier all --report json,html

# Execute with automated AI failure diagnosis and surgical repair suggestions
./percipience test --tier unit --ai-triage
```

### 3. Run Dedicated Vulnerability Red-Team Suite
```bash
cargo test -p percipience-security --test test_vulnerability_suite -v
```

### 4. Verify 6-Vector Semantic Parity
```bash
./percipience drift check --enforce-gate
```

---

## 🔗 Key Plan Documents

- **[Detailed Test Specification (`detailed.md`)](./detailed.md)**: Full 360-degree testing methodology, 4-tier matrix, vulnerability suites, edge cases, and compliance verification.
- **[Concise Test Specification (`concise.md`)](./concise.md)**: Compact reference for fast AI agent context injection.
- **[Version Manifest (`MANIFEST.yaml`)](./MANIFEST.yaml)**: Cryptographic SHA-256 integrity hashes for all files in this space.
