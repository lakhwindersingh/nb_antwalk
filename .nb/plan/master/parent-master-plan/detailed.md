---
sessionId: session-260913-master-parent-plan
---

# Requirements

### Overview & Goals
The objective is to establish an enterprise-grade, generic, mature, domain-agnostic **Parent Master Context Engineering Framework** that synthesizes and elevates domain-specific plans (such as IoT, GenAI, Neural Networks, Database Migration, Mobile, Web, and Robotics spaces) into a unified, scalable agentic orchestration standard. This parent plan introduces **thirty-six (36)** core foundational capabilities (each referenced by a stable identifier `CAP-01` through `CAP-35`, in list order below) required for high-efficiency, zero-drift, tamper-evident, multi-module scalable, and cost-optimized AI-driven software engineering:

1. **Autonomous Operations on Multi-Format Minimum Viable Set (MVS) Inputs**: An auto-intelligent derivation engine that consumes sparse initial user inputs across multiple standardized formats (Markdown feature specifications, OpenAPI contracts, AsyncAPI event streams, ADR blueprints, structured Jira/Linear issue exports, and UI/UX design tokens) in `user/inputs/` (or `input/templates/`), normalizing them into a canonical Abstract Semantic Graph (ASG) to autonomously bootstrap, derive, scaffold, test, build, and document the complete project without human intervention unless explicit ambiguity gates are triggered.
2. **Context Poisoning Detection, Recovery Point Rollback & Incremental Replay Engine**: A resilient state control engine that continuously audits context purity. If context poisoning, hallucination drift, or invalid state propagation occurs, the engine rewinds project artifacts, git commit history, and agent state to a verified clean recovery point (`recovery_point`), quarantines and removes the poisoning culprit in `user/hitl/poisoning_quarantine.md`, and replays subsequent valid incremental enhancements seamlessly.
3. **Context Compression & GenAI Optimization Engine**: A systematic framework for context compression, token budget management, prompt caching optimization, AST symbol pruning, unified diff-based state updates, and context window tiering to drastically reduce token consumption and API expenses by 50–70%.
4. **Model-Agnostic Dynamic Multi-Model Cascading & Cost-Aware Token Tiering**: An intelligent, vendor-neutral multi-model routing layer that delegates tasks based on cognitive complexity while remaining fully decoupled from any single LLM provider (supporting Anthropic Claude, Google Gemini, OpenAI GPT, DeepSeek, AWS Bedrock, Azure OpenAI, and local/private vLLM endpoints):
    - **Tier A (Frontier / High-Reasoning)**: Architecture derivation, cross-module contract verification, invariant gates, security audits, and context poisoning root-cause diagnosis. Reference models: `claude-3-7-sonnet / pro`, `gemini-2.0-pro`, `gpt-4o / o1`, `deepseek-r1`.
    - **Tier B (Fast / Compact / High-Throughput)**: AST symbol extraction, unified diff application, test scaffolding, commit drafting, and dashboard JSON serialization. Reference models: `claude-3-5-haiku / flash`, `gemini-2.0-flash`, `gpt-4o-mini`.
    - **Tier C (Deterministic / Offline Rules Engine)**: Local AST pruning, cryptographic SHA-256 Merkle chain verification, and offline regex sentinel scanning.
    - Backed by hard budget ceilings, token burn monitoring, and automatic throttle/down-shift policies.
5. **Git Worktree Workspace Isolation for Concurrent Subagents**: An isolated concurrent execution engine leveraging ephemeral Git worktrees (`.nb/workspaces/subagent_<id>/`). Subagents develop in sandboxed worktrees with independent working directories, preventing concurrent file merge collisions and ledger write races, backed by atomic verification gate merges back to `main`.
6. **Automated Spec-to-Code Semantic Parity & Anti-Drift Engine**: A quantitative anti-drift subsystem measuring semantic parity (0.00 to 1.00) between `user/inputs/` specs and `workplace/src/` implementations via AST contract analysis and semantic embeddings. Features a bi-directional reconciliation protocol supporting both *Revert Mode* (restoring drifted code to spec) and *Evolve Mode* (updating the specification delta via HITL approval).
7. **Bounded TDD Self-Healing Engine with Test Quarantine Ledger**: A strictly bounded self-healing loop (configurable max retry attempts, default: 3) for test failures. Prevents infinite looping and token thrashing by automatically quarantining persistently failing or flaky tests into `quarantined_tests` in `context_ledger.yaml`, auto-filing high-priority tickets in `remaining_issues`, and safely pausing at `user/hitl/`.
8. **Cryptographic Ledger Hash-Chain & Tamper-Evident Audit Trail**: A tamper-evident Merkle block chaining mechanism (`ledger_chain`) securing every transition in `context_ledger.yaml`. Each ledger block records `{ block_id, prev_block_hash, current_block_hash, merkle_root, timestamp }`, guaranteeing non-repudiation and enterprise regulatory auditability (SOC2 Type II, ISO 27001, HIPAA).
9. **Time-Travel Debugging & Visual DAG Dashboard**: A lightweight, static web dashboard generated at `user/outputs/dashboard/index.html`. Provides interactive DAG graph visualization of artifact lineage, visual diffing between any two recovery points ($RP_a$ vs $RP_b$), real-time token burn and prompt cache hit rate tracking, and one-click HITL review and clarification management.
10. **Multi-Dimensional Context Maturity Evaluation Report**: A comprehensive, quantitative evaluation matrix in `user/outputs/` and `.nb/context/reports/` assessing project context across six dimensions (Requirement Coverage, Architecture & Design Grounding, Code & Config Quality, Test & Verification Coverage, Security & Compliance, and Token/GenAI Efficiency).
11. **Master Context Ledger (`context_ledger.yaml`) with Integrated Git Commit & Issue Tracker**: A machine-readable DAG in `context/` that logs all artifact lineage, tracks issued Git commits with full requirement traceability, manages open remaining issues, enforces a standard checklist of common technical issues, captures model-suggested improvements, and registers recovery point snapshots in a standardized format.
12. **Universal Quad-Space Clean Folder Bootstrapping & Multi-Agent Flow**: Standardized scaffolding strictly partitioning customer-owned mutable directories (`workplace/` with `config/`, and `user/` with `inputs/`, `hitl/`, `outputs/`) from Neutron Binary proprietary logic (`.nb/context/` and `.nb/agentic/`). In enterprise deployments, `.nb/context/` (governance, schemas, DAG state engine) and `.nb/agentic/` (system prompts, bootstrapping/derivation metaprompts, model tiering router, workflows) are obfuscated, compiled, and cryptographically sealed inside `.nbpack` envelopes, hydrated exclusively inside an in-memory enclave to protect proprietary IP while leaving customer workspaces clean.
13. **Zero-Overhead Dual-Mode Architecture (Single-Module vs. Poly-Module Ecosystem)**: A dual-operating mode configured via `project.mode: single_module | multi_module`. In `single_module` mode, the framework maintains absolute simplicity with zero nested directory overhead (flat `workplace/src/` and `workplace/config/`). In `multi_module` mode, the framework coordinates heterogeneous multi-system projects (such as consumer interfaces communicating with provider services, event-driven microservices, or distributed data/ML pipelines) via isolated module subtrees (`workplace/modules/<module_id>/`), shared wire contracts (`workplace/shared/protos/` or schemas), cross-module interface specifications (`.nb/context/contracts/`), surgical module-scoped rollbacks, and virtual simulator loopback bridges.
14. **Proprietary Context & Agentic Space Obfuscation, Anti-Exfiltration & Cryptographic Package Sealing (`.nbpack`)**: A binary compilation, AST minification, and authenticated envelope encryption engine (`percipience pack`). Compiles proprietary markdown master plans, `agentic/` prompt suites, and `context/` governance/schema machinery into tamper-proof, Ed25519-signed AES-256-GCM binary envelopes (`.nbpack`). Hydrates both proprietary spaces directly into volatile RAM / secure sandbox memory without persisting plaintext files to the client's physical filesystem, preventing intellectual property theft, prompt injection, and LLM context exfiltration during `percipience init`.
15. **External Issue Tracker & Jira MCP Server Integration Layer**: A bi-directional Model Context Protocol (MCP) bridge connecting enterprise issue tracking systems (Jira Software, Linear, GitHub Issues, Azure DevOps). The engine continuously polls or subscribes to Jira via MCP servers (e.g., `@modelcontextprotocol/server-jira`), ingests "Ready for Dev" stories directly into the MVS processing queue, drives subagents through derivation and test verification, and automatically synchronizes issue states, test evidence, and Merkle block audit proofs back to Jira upon completion.
16. **Autonomous Closed-Loop CI/CD Triad (Self-Sustaining, Self-Recovering, Self-Improving)**: A fully autonomous continuous delivery engine (`.nb/core/autonomous_cicd.py`) that elevates CI/CD from a passive blocker to an active, closed-loop orchestrator. It comprises three unified capabilities:
    - *Self-Sustaining*: Proactively reclaims expired subagent worktree leases, purges uncommitted scratch diffs, garbage-collects zombie branches, validates WORM Merkle continuity, and enforces sprint token budget caps before resource exhaustion occurs.
    - *Self-Recovering*: Isolates regression faults into dedicated diagnostic worktrees, executes bounded TDD auto-patching ($\le 3$ retries), and, if unresolvable, triggers sub-1.2s surgical module rollbacks to verified recovery points ($\text{RP}_k$) without disturbing unaffected sibling microservices.
    - *Self-Improving*: Analyzes post-run pipeline telemetry, dynamically calibrates AST pruning thresholds (escalating from standard body stripping to aggressive internal helper pruning for high-token files to capture $+12.5\%$ additional savings), aligns prompt cache prefixes, and persists lessons learned into `.nb/context/ledger/self_improving_ledger.yaml`.
17. **Extensible Custom Agent Plugin Architecture & Workflow DAG Injection**: A standardized plugin model and engine (`.nb/core/agent_plugin_engine.py`) allowing teams to scaffold, configure, and integrate custom agent specialists into existing workflow DAGs (e.g. `.nb/agentic/workflows/pr_gatekeeper.yaml`). Follows the *Healthy Integration Pattern* enforcing ephemeral worktree sandboxing, AST token budgeting, pre/post contract verification, and cryptographic Merkle state sealing (`RP_AGENT_*`). If a custom plugin injects anomalies, the engine triggers surgical rollback to recovery points without collateral disruption.
18. **Production Token FinOps & Rev-Share Performance Metering Engine**: An integrated financial observability engine (`.nb/core/token_tracker.py`) that captures raw vs. AST-pruned token metrics across heterogeneous languages in real time. Automatically logs transparent accounting entries to `.nb/context/ledger/token_savings_ledger.yaml`, computing gross customer savings ($0.003/1K tokens) and 15% rev-share performance fees, backed by automated scorecard and whitepaper generation (`workplace/docs/reports/token_savings_report.md`, `workplace/docs/reports/token_savings_whitepaper.md`).
19. **5-Tab Enterprise Context Observability Hub & Telemetry Gateway**: A unified, zero-dependency browser observability control plane (`user/outputs/dashboard/index.html`) coupled with a production-grade HTTP/API gateway server (`workplace/portal/server.py`). Features 5 specialized operational tabs: (1) 6-Dimensional Context Maturity Radar & Remediation Diagnostics, (2) Autonomous Agent Swarm & Custom Plugin Manager, (3) Declarative Workflow DAGs & Invariant Gates, (4) FinOps Token Metering & ROI Calculator, and (5) Autonomous CI/CD Triad & Self-Healing Control Plane.
20. **3-Tier Layered Context Precedence Hierarchy & Bring-Your-Own-Repository (BYOR) Adapter**: A security and configuration architecture (`.nb/core/layered_context_validator.py`, `.nb/core/byor_adapter.py`) that enforces non-overridable platform invariants:
    - *Tier 1 (Base Platform Invariants)*: Core security contracts, Merkle schemas, and tamper proofs in `.nb/context/invariants/` (or encrypted `.nbpack` enclaves) that cannot be overridden by user prompts.
    - *Tier 2 (Enterprise Global Rules)*: Organization-wide policies and API contracts in `.nb/context/rules/` and `.nb/context/contracts/`.
    - *Tier 3 (Team / User Custom Context)*: Unencrypted domain schemas, custom agent plugins, and prompt templates in `.nb/context/custom/` and `.nb/agentic/custom/agents/`.
    - *BYOR Adapter*: Native multi-VCS adapter supporting self-hosted GitLab, GitHub Enterprise Server, and Bitbucket Data Center via SSH deploy keys and internal Root CA validation.
21. **Autonomous Living Documentation Engine & Architecture Visualizer (`agent_living_doc_architect`)**: An in-workflow living documentation engine (`.nb/core/living_doc_engine.py`) and specialist documentation subagent (`.nb/agentic/custom/agents/agent_living_doc_architect.yaml`) that executes autonomously during workflow runs, PR verification gates, and release cuts to create and continuously update living, drift-free documentation in `workplace/docs/`. It programmatically inspects codebase Abstract Syntax Trees (ASTs), wire contracts (`.nb/context/contracts/`), runtime configurations, and active layered domain specifications to synthesize: (1) Module Catalogs & Public API surfaces, (2) High-Level System Architecture & C4 Topologies, (3) Runtime Execution & Cross-Module Sequence Flows, (4) Data Transformation Pipelines & Event Streams, (5) Entity-Relationship & Relational Data Models, and (6) Layered Plan Domain Extensions (such as IoT BLE GATT profiles, Web3 P2P capability loans, or SaaS multi-tenant RBAC policies). It strongly prefers rich, executable **Mermaid** diagrams across all documents, hashes source files to enable incremental zero-token-overhead doc updates, and seals document revision proofs into the cryptographic Merkle ledger (`context_ledger.yaml`).
22. **Distributed Concurrency Leasing (Redis Redlock) & Pre-Merge Canary Verification**: A multi-agent distributed concurrency engine (`WorktreeEngine` / `RedisWorktreeManager`) using Redis-backed Redlock consensus tokens (`lock:subagent:<id>`) to coordinate concurrent agent swarms across distributed CI workers and local machines without worktree or ledger write collisions. Features automated pre-merge canary verification runs that validate transient AST mutations against target branches before atomic ledger commits.
23. **SEC 17a-4 / FINRA Compliant Immutable Cloud WORM Vault Egress Mirroring**: An enterprise compliance and legal-hold storage subsystem (`WORMEgressManager`) that mirrors every Merkle state block, verification receipt, and audit snapshot in real-time to cloud Write-Once-Read-Many (WORM) storage. Supports AWS S3 Object Lock (`COMPLIANCE` mode with `LegalHold: ON`) and Google Cloud Storage Bucket Lock (Locked Retention Policies), preventing record modification, truncation, or deletion by any entity, including root AWS account holders.
24. **High-Throughput Tree-Sitter AST Daemon & Polyglot Parsing Engine**: A high-speed, native AST parsing daemon (`TreeSitterDaemonClient`) utilizing Rust/C bindings to parse TypeScript, JavaScript, Python, Go, Rust, and C++ at >10,000 LOC/sec. Extracts public interface skeletons, docstrings, type invariants, and symbol dependency graphs with sub-millisecond latency.
25. **Multi-Dimensional 6D Token Compression Suite & Interactive Portal FinOps Engine**: A comprehensive context compression suite (`.nb/core/token_optimizer_suite.py`) featuring six discrete compression pruners (`ASTSkeletonPruner`, `DocPruner`, `ConfigSchemaPruner`, `DiagnosticLogPruner`, `GitDiffPruner`, `ConversationMemoryCompactor`). Delivers 50%–75% net token savings with granular per-strategy switches in `.nb/config/token_compression_rules.yaml` and interactive browser toggles on the Web Portal.
26. **Multi-Dialect Diagnostic Log & Traceback Slicing Engine (`DiagnosticLogPruner`) with Out-of-Tree Noise Filtering, Source AST Snippet Auto-Hydration & 3-Attempt Tiered SLA Envelopes**: An intelligent test and compiler error pruner that slices multi-language tracebacks (Pytest, Jest, Vitest, Go panics, Rust errors, and TypeScript/Mypy diagnostics), eliminates out-of-tree runtime noise (`site-packages/`, `node_modules/`), auto-hydrates offending source code context (line ±4) with line highlighting (`>>`), and constructs SLA-aware tiered prompt envelopes across 3 bounded healing attempts before triggering surgical micro-module rollback (`RP_k`).
27. **Declarative Quad-Space Runtime Boundary & Deduplication Facade Pattern (`CAP-27`)**: Strict architectural isolation separating customer-owned mutable directories (`workplace/`, `user/`) from proprietary execution logic (`context/`, `agentic/`). Eliminates implementation duplication by ensuring `.nb/agentic/runtime/` strictly serves as declarative, zero-logic facade wrappers importing core execution engines directly from `.nb/core/`.
28. **Parallel Fan-Out / Fan-In Barrier Synchronization Engine (`CAP-28`) (`WorkflowOrchestrator`)**: High-throughput multi-agent execution orchestrator (`.nb/core/workflow_orchestrator.py`) supporting declarative `parallel_group` step dispatching, dependency DAG resolution, cycle/deadlock detection, and barrier join synchronization for concurrent gates, multi-linter scans, and security verifications.
29. **4-Pillar Fine-Grained Error Taxonomy & Adaptive Recovery Playbooks (`CAP-29`) (`ErrorRecoveryOrchestrator`)**: Granular runtime failure classification system (`.nb/core/error_recovery_orchestrator.py`) categorizing errors into 4 distinct pillars (`TRANSIENT`, `STRUCTURAL`, `INVARIANT`, `HALLUCINATORY`) and dispatching specialized recovery playbooks (exponential jitter retry, AST diagnostic re-prompts, spec evolution RFCs, quarantine rollbacks).
30. **Cryptographic Prompt SemVer Manifest, Golden Invariant Evals & Static Prefix Pinning (`CAP-30`) (`PromptDriftSentinel`)**: Cryptographic SHA-256 integrity verification of all prompt templates (`prompt_manifest.yaml`), structural drift detection, golden invariant assertions, and strict static prefix pinning (`<!-- STATIC_PREFIX_START -->` preceding dynamic payloads) for maximum LLM KV-cache reuse.
31. **4-Tier Hierarchical Swarm Authority Tree & Anti-Usurpation Spawning Interception (`CAP-31`) (`SwarmGovernor`)**: Formal agent authorization hierarchy (`ORCHESTRATOR` > `DOMAIN_ARCHITECT` > `SPECIALIST_WORKER` > `GATEKEEPER_SENTINEL`), action permission matrix, bounded recursion depth ($D_{\max} = 2$), and anti-usurpation spawning validation preventing worker agents from launching unconstrained shadow subagents.
32. **Adversarial Red-Team & Mutation Fuzzing Engine (`CAP-32`) (`AdversarialFuzzer`)**: Proactive security and resilience testing generating boundary numbers ($\pm \infty$, NaN, $2^{63}-1$), SQL/XSS injections, null/empty mutations, prototype pollution, and AST branch mutations to verify software resilience before PR merge.
33. **Context Attention Slicing & Proportional Token Budgeting (`CAP-33`) (`AttentionBudgeter`)**: Mathematical budget quota partitioning across prompt sections (15% Invariants, 25% Contracts, 35% AST, 10% Memory/Trajectories, 15% Output) preventing context overflow and mitigating lost-in-the-middle degradation.
34. **Structured Step-by-Step ReAct Trajectory Recording & Replay Engine (`CAP-34`) (`TrajectoryRecorder`)**: Deterministic capture of agent reasoning cycles (Thought $
ightarrow$ Action $
ightarrow$ Observation $
ightarrow$ Reflection) persisted in `agentic/trajectories/` for post-mortem debugging and verification replay.
36. **Commercial Pricing Tier Packaging, Cross-Platform Provisioning & Tier Permissioning Engine (`CAP-36`) (`CommercialPackagerProvisioner`)**: An end-to-end commercial distribution and license provisioning engine (`.nb/core/commercial_packager_provisioner.py`) that filters, compiles, and packages platform configurations, executables, scripts, core engines, contracts, and workflows according to the Commercial Pricing and Revenue Model:
    - **Free Community Tier ($0/mo)**: 1 local seat, 25 essential core engines, safe gatekeeper CLI commands, unexposed basic platform developer tools, plaintext user plans.
    - **Team Tier ($1,499/mo)**: 15 seats, 5 concurrent worktrees, 5,000 PR audits, team worktree coordination, team delivery workflows, 15% net token savings rev-share.
    - **Business Tier ($4,499/mo)**: 50 seats, 20 concurrent worktrees, 25,000 PR audits, `.nbpack` AES-256 encryption, user plan encryption, standard platform developer tools exposure (`percipience pack`, custom agent creation SDK).
    - **Enterprise Dedicated ($9,999/mo)**: Unlimited seats/worktrees/PR audits, Private VPC deployment, WORM egress audit vault, multi-tenant RBAC gateway, mTLS IoT provisioning, 24/7 Slack SLA.
    - **Multi-IDE & Portal Provisioning**: Automatically packages and deploys licensed runtime bundles to IntelliJ IDEA / PyCharm (`src/main/resources/percipience/`), VSCode (`percipience_runtime/`), and SaaS Portal Multi-Tenant Gateway (`tenant_hierarchy.json`), sealed with SHA-256 digital signatures and cryptographic Merkle state ledger blocks.
35. **Autonomous Requirement Ambiguity Resolution & Interactive Clarification RFCs (`CAP-35`) (`AmbiguityResolver`)**: Quantitative entropy analysis of input requests detecting vague buzzwords, missing technical anchors, and drafting structured clarification RFCs in `user/hitl/clarification_requests/` before unblocking autonomous implementation.


---

## 2. Plan Tier Matrix & Boundary Ceilings

| Feature / Dimension | Free Community Plan (`plan_free`) | Team Plan (`plan_team`) | Business Plan (`plan_business`) | Enterprise Dedicated (`plan_enterprise`) |
| :--- | :--- | :--- | :--- | :--- |
| **Monthly Base Price** | **$0.00 / Free Forever** | $1,499 / mo | $4,499 / mo | $9,999 / mo |
| **Included Seats** | **1 Developer Seat** | 15 Seats | 50 Seats | Unlimited |
| **Concurrent Worktrees** | **1 Local Worktree** | 5 Worktrees | 20 Worktrees | Unlimited Distributed |
| **Monthly PR Audits** | **500 Audits / mo** | 5,000 Audits / mo | 25,000 Audits / mo | Unlimited |
| **AST Token Reduction** | **✅ Full (60%–80% savings)** | ✅ Full | ✅ Full | ✅ Full + Tree-Sitter Daemon |
| **Cryptographic Merkle Chain** | **✅ Local Linear SHA-256** | ✅ Local + Remote Sync | ✅ Local + Remote Sync | ✅ Multi-Region WORM S3/GCS |
| **Autonomous CI/CD** | **✅ Basic Setup (`basic_autonomous_cicd.yaml`)** | ✅ Advanced (3-Retry) | ✅ Full Multi-Stage | ✅ Closed-Loop Swarm Triad |
| **Packaging & Obfuscation** | 🔒 Platform Core Encrypted (percipience readable) / User Plans Plaintext (Non-Encryptable) | 🔒 Platform Core Encrypted / User Plans Plaintext | ✅ `.nbpack` AES-256 (Platform & User Plans) | ✅ `.nbpack` RAM Enclave (Zero-Disk Plaintext) |
| **Basic Platform Tools Exposure** | ❌ Unexposed (No Plan to Expose Basic Tools) | ❌ Unexposed | ✅ Standard Tool Access | ✅ Full Unrestricted Platform SDK & Tool APIs |
| **Deployment Model** | **Local IDE & Git Worktree** | Cloud Shared Gateway | Cloud Shared Gateway | Dedicated Private VPC |
| **IDE Plugin Support** | **✅ IntelliJ & VSCode** | ✅ IntelliJ & VSCode | ✅ IntelliJ & VSCode | ✅ IntelliJ & VSCode + JCEF |
| **Sandbox Source Permissions** | **✅ Local Sandbox Broker** | ✅ Team RBAC | ✅ Enterprise RBAC | ✅ Zero-Trust Fine-Grained |

The Free Community Plan (`plan_free`) provides high-efficiency AST Token Reduction, a local cryptographic Merkle state ledger (`context_ledger.yaml`), and basic autonomous CI/CD via `basic_autonomous_cicd.yaml`. Platform core components (`.nb/context/`, `.nb/config/`, `.nb/core/`, and master plans) stay encrypted and readable by the canonical `percipience` command, while free tier users' custom plans remain plaintext (non-encryptable), and basic platform tools remain unexposed to free tier users.

### Scope
#### In Scope
- **Proprietary Context & Agentic Space Obfuscation & Encrypted Packaging Engine**: Compiles markdown plans, `agentic/` prompt trees, and `context/` governance/validation logic into `.nbpack` envelopes; provides cryptographic signature validation and zero-knowledge in-memory hydration.
- **Quad-Space Clean Folder Partitioning & Isolation Engine**: Scaffolding and runtime isolation logic separating customer-owned transparent spaces (`workplace/` and `user/`) from obfuscated, encrypted, and enclave-hydrated proprietary spaces (`context/` and `agentic/`).
- **Zero-Overhead Dual-Mode Operating Engine**:
  - `mode: single_module`: Direct flat layout (`workplace/src/`, `workplace/config/`, single linear DAG, global recovery point). Zero overhead for standalone apps.
  - `mode: multi_module`: Module subtrees (`workplace/modules/<module_id>/`), shared wire formats (`workplace/shared/`), versioned cross-module interface contracts (`.nb/context/contracts/`), and federated DAG state in `context_ledger.yaml`.
- **Cross-Module Contract Compatibility & Interface Gate**:
  - Formal interface contract management in `.nb/context/contracts/` (OpenAPI 3.1 specifications, JSON Schema definitions, gRPC/Protobuf DTOs, AsyncAPI event streams, and shared data schemas).
  - Independent verification gate (`gate_contract_compatibility`) validating that producer modules and consumer modules adhere strictly to shared contracts before merging.
- **Surgical Module-Scoped Poisoning Isolation & Rollback**:
  - Module-scoped recovery points in `context_ledger.yaml` (e.g., `RP_PROV_003`, `RP_CONS_004`) alongside global system snapshots (`RP_SYS_001`).
  - Targeted rollback capability: when context poisoning or contract drift occurs in one module (e.g., consumer interface schema mismatch or API payload drift), only the contaminated module is rolled back and quarantined; unaffected modules (e.g., provider service engine or data worker) remain untouched, preventing collateral re-compilation and token waste.
- **Virtual End-to-End Emulation & Simulator Bridge**:
  - Cross-module test harnesses wiring together heterogeneous component emulators (e.g., client application simulator communicating with backend service daemon over a local virtual loopback socket or mock API bridge) for automated end-to-end integration validation.
- **Multi-Format MVS Ingestion & Parsing Engine**: Standardized ingestion templates in `user/inputs/templates/` (and `input/templates/`) supporting 6 industry-standard formats: Markdown Feature Specs (`mvs_feature_spec.md`), OpenAPI 3.1 Schemas (`mvs_api_contract.yaml`), AsyncAPI Event Streams (`mvs_event_stream.yaml`), ADR System Blueprints (`mvs_adr_blueprint.md`), Structured Jira Issues (`mvs_jira_story.json`), and UI Design Tokens (`mvs_design_tokens.json`).
- **External Issue Tracker MCP Integration (Jira / Linear / GitHub Issues)**: Native MCP tool bindings to pull "Ready for Dev" user stories, epics, and acceptance criteria into the active derivation queue, update issue progress, attach verification reports, and link SHA-256 Merkle block commit hashes.
- **Context Poisoning Detection, Rollback & Replay Engine**:
  - Continuous context purity auditing via verification gates, schema validators, and drift detectors.
  - Automated snapshotting of verified recovery points (`recovery_points`) linked to clean Git commit SHAs and ledger states.
  - Rollback protocol: Rewinding workspace files, git commit history, and agent state to clean recovery point `RP_k` upon context contamination.
  - Culprit quarantine protocol: Identifying, logging, and removing the context poisoning culprit into `user/hitl/poisoning_quarantine.md`.
  - Incremental replay engine: Re-executing downstream valid increments with sanitized context to restore full functionality without full project restart.
- **Dynamic Multi-Model Cascading & Cost-Aware Token Tiering**:
  - Model tier router directing tasks to Tier A (Frontier/Reasoning) or Tier B (Fast/Compact).
  - Configurable increment budget limits (e.g., maximum dollar/token cap per milestone).
  - Spend velocity monitoring with automatic down-shifting to Tier B when approaching 85% budget threshold.
- **Git Worktree Concurrency Engine**:
  - Ephemeral branch and worktree provisioning under `.nb/workspaces/subagent_<id>/`.
  - Concurrency locks protecting `context_ledger.yaml` writes.
  - Atomic merge verification gate merging completed subagent worktrees into `main`.
- **Automated Spec-to-Code Semantic Parity & Anti-Drift Engine**:
  - Quantitative Semantic Parity metric scoring (0.00 – 1.00).
  - Dual reconciliation: *Revert Mode* (auto-generating code diff to eliminate unauthorized drift) vs *Evolve Mode* (updating specification delta for HITL sign-off).
- **Bounded TDD Self-Healing Engine**:
  - Strict retry budget (configurable, default: 3 attempts) for autonomous test fixing.
  - Automatic test quarantine logging to `quarantined_tests` in `context_ledger.yaml` and ticket creation in `remaining_issues`.
  - Clean pause at `user/hitl/` with clear diagnostic logs to prevent token burn loops.
- **Cryptographic Merkle Ledger Hash-Chain**:
  - SHA-256 block hashing on every state transition in `context_ledger.yaml`.
  - Merkle root computation over all tracked artifact hashes.
  - Tamper detection validator verifying chain continuity ($H_i = \text{SHA256}(H_{i-1} + \Delta_i + T_i)$).
- **Time-Travel Debugging & Visual DAG Dashboard**:
  - Automated generation of `user/outputs/dashboard/index.html`.
  - Interactive visual rendering of artifact DAG, recovery checkpoints, module subgraphs, and agent handoffs.
- **Autonomous CI/CD Triad Control Plane**:
  - Closed-loop orchestration in `.nb/core/autonomous_cicd.py` implementing `SelfSustainingEngine`, `AutonomousHealer`, `SelfImprovingEngine`, and `AutonomousCICDOrchestrator`.
  - Multi-phase engineering roadmap in `workplace/docs/reports/autonomous_cicd_roadmap.md`.
- **Custom Agent Plugin Architecture & Workflow DAG Injection**:
  - Plugin scaffolding and lifecycle management in `.nb/core/agent_plugin_engine.py`.
  - Standardized plugin template in `agentic/templates/custom_agent_template.yaml` and guide in `workplace/docs/guides/AGENT_PLUGIN_GUIDE.md`.
  - Dynamic workflow DAG injection into `.nb/agentic/workflows/pr_gatekeeper.yaml` with pre/post-execution Merkle seals.
- **Token FinOps & Rev-Share Performance Metering Engine**:
  - Real-time token tracking in `.nb/core/token_tracker.py` logging to `.nb/context/ledger/token_savings_ledger.yaml`.
  - Automated generation of executive scorecard (`workplace/docs/reports/token_savings_report.md`) and benchmark whitepaper (`workplace/docs/reports/token_savings_whitepaper.md`).
- **Multi-Dimensional 6D Token Optimization Suite**:
  - Six discrete compression pruners (`ASTSkeletonPruner`, `DocPruner`, `ConfigSchemaPruner`, `DiagnosticLogPruner`, `GitDiffPruner`, `ConversationMemoryCompactor`) in `.nb/core/token_optimizer_suite.py`.
  - Configurable compression presets (`disabled`, `conservative`, `standard`, `aggressive`, `extreme`) and granular per-strategy toggles.
- **Multi-Agent Handover Integrity & 6-Vector Semantic Parity Engine (CAP-27)**:
  - Cryptographic HMAC-SHA256 `HandoffToken` generation and JSON Schema Draft-07 payload validation (`agentic/schemas/handoff_schema.yaml`) in `.nb/core/handoff_validator.py`.
  - Composite mathematical parity formulation in `.nb/core/semantic_parity_engine.py`: $S_{SP} = 0.20 S_{\text{AST}} + 0.25 S_{\text{Contract}} + 0.20 S_{\text{Behavior}} + 0.15 S_{\text{Handover}} + 0.10 S_{\text{Doc}} + 0.10 S_{\text{SupplyChain}}$.
  - Automated Dual-Reconciliation Protocol in `.nb/core/reconciliation_engine.py` (automated surgical reverse diffing in Revert Mode vs. HITL RFC spec evolution in `user/hitl/proposed_spec_delta.md` in Evolve Mode).
  - Multi-agent swarm governance with recursion ceiling ($D_{\max} = 2$) and active worktree lease eviction preventing shadow subagent spawning.
- **Enhanced Multi-Dialect Diagnostic Log Slicer & Tiered SLA Prompt Envelopes**:
  - Specialized slicing for Python/pytest, JS/Jest, Go panics, Rust compiler errors, and TSC typechecks.
  - Out-of-tree framework frame filtering (stripping `site-packages/` and `node_modules/`).
  - Offending source AST snippet auto-hydration with `>>` line highlighting.
  - Tiered prompt escalation across 3 bounded SLA attempts before surgical rollback.
- **SEC 17a-4 / FINRA Compliant Cloud WORM Vault Egress**:
  - Real-time egress mirroring of Merkle blocks to AWS S3 Object Lock (Compliance Mode) and GCP GCS Retention Policies.
  - Verification receipts, legal hold flags, and immutable audit logs.
- **Distributed Concurrency Leasing (Redis Redlock)**:
  - Redis-backed distributed lock coordination for multi-host and CI-scale agent swarms.

- **Enterprise Context Observability Hub & Telemetry Gateway**:
  - Interactive 5-tab browser control plane (`user/outputs/dashboard/index.html`) with real-time REST API integration (`workplace/portal/server.py`).
  - Self-healing trigger, agent plugin manager, ROI calculator, and context maturity radar with automated remediation playbooks.
- **3-Tier Layered Context Precedence Hierarchy & Multi-VCS BYOR Adapter**:
  - Invariant protection in `.nb/core/layered_context_validator.py` maintaining strict priority: Tier 1 (Platform) > Tier 2 (Enterprise) > Tier 3 (User).
  - Multi-VCS remote adapter in `.nb/core/byor_adapter.py` connecting self-hosted GitLab, GitHub Enterprise, Bitbucket Data Center.
  - Checkpoint state diffing, token burn charts, and interactive HITL clarification review.
- **Autonomous Living Documentation Engine & Architecture Visualizer (`agent_living_doc_architect`)**:
  - Automated generation and continuous in-workflow synchronization of structured documentation under `workplace/docs/` (`architecture.md`, `module_catalog.md`, `sequence_flows.md`, `data_flow.md`, `entity_relationship.md`, `domain_extensions.md`).
  - Deep AST symbol extraction and contract-to-doc synthesis for classes, functions, routes, schemas, and event channels.
  - Mandatory preference for expressive, valid **Mermaid** diagrams (`graph TD/LR`, `sequenceDiagram`, `flowchart TD`, `erDiagram`, `stateDiagram-v2`, `classDiagram`) embedded directly within Markdown artifacts.
  - Dynamic layered domain plan awareness: introspecting active domain layers (e.g. `domain_blockchained_audio`, `domain_iot_mobile`, `domain_saas_portal`) to generate specialized domain models and sequence flows.
  - Incremental documentation caching via SHA-256 AST hashing to eliminate redundant LLM token spend on unchanged files during continuous workflow runs.
  - Integration into verification gatekeepers (`wf_pr_gatekeeper.yaml`, `.nb/bin/percipience gate`) to block code merges if documentation drifts or Mermaid syntax fails validation.
- **Context Compression & GenAI Optimization Engine**:
  - Token budget management and dynamic context window allocation rules.
  - AST / symbol table extraction for code compression (transmitting interface signatures instead of full implementations during planning).
  - Incremental diff-based context updates (transmitting file deltas rather than re-transmitting whole files).
  - Semantic sliding-window context summaries for multi-turn subagent execution.
  - Prompt caching optimization (reusing system and tool definitions with static prefix alignment).
- **Multi-Dimensional Context Maturity Evaluation Report**:
  - Evaluation scorecard generation across 6 core dimensions.
  - Maturity phase progression tracking: `MVS_Ingested` -> `Derived` -> `Scaffolded` -> `Trained/Simulated` -> `Evaluated` -> `Built/Signed` -> `Deployed`.
  - Emitted as structured JSON (`eval_report.json`) and formatted Markdown (`context_maturity_report.md`) in `user/outputs/`.
- **Integrated Master Context Ledger (`context_ledger.yaml`)**:
  - Full DAG tracking across all artifacts, module registries, contracts, recovery points, poisoning incidents, model tiering policies, worktrees, semantic parity metrics, quarantined tests, cryptographic ledger chains, git commits, remaining issues, checklist items, and model suggestions.
- **Universal Six-Phase Prompt Suite Architecture**:
  - `system_prompt.md`, `bootstrapping_prompt.md`, `derivation_prompt.md`, `evaluation_refinement_prompt.md`, `lifecycle_delivery_prompt.md`, and `workflow_orchestration_prompt.md`.

#### Out of Scope
- Direct cloud infrastructure runtime deployment execution inside the agentic AI engine's immediate inference loop (the AI engine provides full deployment manifests, CI/CD scripts, Dockerfiles, and provisioning manifests; Claude, Gemini, or GPT can be used as the reference reasoning engine).
- Physical hardware or bare-metal environment execution (automated integration testing is executed via containerized virtual bridges and loopback mock daemons; specialized hardware/embedded firmware concerns are encapsulated in layerable domain plans).

### User Stories
- **As a Commercial Software Vendor & Enterprise Architect**, I want to obfuscate and cryptographically compile parent master plans, `context/` governance schemas, and `agentic/` prompt suites into signed `.nbpack` bundles so that client installations (`percipience init`) run securely without exposing proprietary architecture IP, recovery state algorithms, or risking prompt exfiltration.
- **As an AI Systems Architect & Lead**, I want a universal, model-agnostic parent context engineering plan so that any project domain (IoT, GenAI, Web, Mobile, Neural, DB Migration) adopts a standardized, mature agentic structure that operates seamlessly across Claude, Gemini, GPT, or local models with zero vendor lock-in.
- **As a Poly-Module Solution Architect**, I want a unified space to manage multi-module systems (e.g., Client Application communicating with Core Backend Service via shared wire contracts) without breaking the simple structure of standalone single-module projects.
- **As a Polyglot Systems Lead**, I want versioned cross-module interface contracts in `.nb/context/contracts/` so that changes to API schemas, gRPC definitions, or event payloads are automatically verified against all producer and consumer modules before merge.
- **As a System Reliability Engineer**, I want surgical module-scoped rollbacks so that if context poisoning occurs in a consumer interface or client module, only the contaminated module is rolled back and replayed without throwing away verified provider service builds.
- **As a QA & Systems Engineer**, I want an automated end-to-end simulator bridge linking client application test suites with virtual service daemons so that full request/response, event streams, and contract lifecycles can be validated autonomously.
- **As an Autonomous Software Product Owner**, I want the agent suite to operate autonomously starting from a Minimum Viable Set (MVS) of sparse inputs so that complete systems are derived, built, tested, and documented with minimal manual overhead.
- **As a Financial & Engineering Manager**, I want vendor-neutral multi-model cascading and context compression across Anthropic, Google, and OpenAI models so that long-running agent workflows reduce token expenses by up to 70% by routing lightweight tasks to fast models (`claude-3-5-haiku / flash`, `gemini-2.0-flash`, `gpt-4o-mini`) and caching static prompt prefixes across any supported LLM provider.
- **As a Concurrency & Platform Lead**, I want subagents to work in isolated Git worktrees so that multiple specialized agents can develop and test features concurrently without file lock collisions or merge conflicts.
- **As an Autonomous DevOps Lead**, I want a self-sustaining and self-recovering CI/CD control plane so that build failures and test regressions are automatically diagnosed and patched within 3 retries or surgically rolled back without human firefighting.
- **As an Extensibility & Tools Architect**, I want a custom agent plugin template and automated workflow DAG injection so that new domain agents can be onboarded safely inside sandboxed worktrees without risking repository state corruption or context poisoning.
- **As an Enterprise FinOps Director**, I want real-time cryptographic metering of token savings and transparent 15% performance fee accounting so that our 62% AI cost reduction is auditable and budget-enforced.
- **As a Compliance & Audit Officer**, I want a cryptographic Merkle hash-chain in the context ledger so that all AI decisions, code changes, and test approvals are tamper-evident and compliant with SOC2/ISO27001 standards.
- **As a QA & Test Lead**, I want a bounded TDD self-healing engine that quarantines intractable tests after 3 attempts, preventing runaway token spend while alerting human engineers via `user/hitl/`.
- **As a Technical Director**, I want a visual DAG dashboard and time-travel inspection tool at `user/outputs/dashboard/index.html` so that I can visually audit project evolution, diff recovery points, inspect module subgraphs, and track token spend in real-time.
- **As a Product Manager & Scrum Master**, I want Percipience to connect via Jira MCP servers to automatically ingest user stories marked "Ready for Dev", so that AI coding swarms begin implementing verified features directly from our Jira backlog without manual copy-pasting.
- **As an API Architect & Systems Engineer**, I want to submit schema-first OpenAPI and AsyncAPI MVS contracts in `user/inputs/` so that Percipience derives type-safe server stubs, client SDKs, integration tests, and database schemas with zero semantic drift.
- **As a Principal Architect & Full-Stack Developer**, I want an autonomous documentation agent (`agent_living_doc_architect`) running within our continuous workflow to synthesize and update comprehensive living documentation in `workplace/docs/` with Mermaid diagrams for architecture, sequence flows, data pipelines, entity relationships, and module catalogs, so that system architecture and code never drift apart and new team members can immediately visualize system internals.

### Functional Requirements
- **Proprietary Context & Agentic Space Obfuscation & Encrypted Bundle Compilation**:
  - Implement `percipience pack` CLI engine that tokenizes, minifies ASTs, mangles prompt identifier references, and compiles master plans alongside `context/` and `agentic/` into binary `.nbpack` packages.
  - Sign compiled `.nbpack` packages using Ed25519 digital signatures and encrypt payloads using authenticated AES-256-GCM.
  - Implement zero-disk plaintext hydration inside volatile RAM / gVisor sandboxes during `percipience init --parent-plan <file.nbpack>`.
  - Prevent any plaintext writing of `agentic/` prompt files or `context/` proprietary validation schemas to the host disk; mount them as an in-memory virtual filesystem (RAM enclave / tmpfs) accessible solely by the Percipience agent daemon.
  - Emit a sanitized, read-only public projection of state (`.nb/context/ledger/context_ledger.public.yaml`) for client visibility while shielding internal state transition rules and schemas.
- **Dual-Mode Operating Engine**:
  - Support `project.mode: single_module` (default: flat `workplace/src/` and `workplace/config/`, global recovery point, zero nested folder overhead).
  - Support `project.mode: multi_module` (scoped `workplace/modules/<module_id>/`, `workplace/shared/`, `.nb/context/contracts/`, federated ledger).
- **Cross-Module Contract Registry & Verification**:
  - Formalize shared interface contracts in `.nb/context/contracts/` (e.g., OpenAPI 3.1 specifications, Protobuf/gRPC DTOs, AsyncAPI event streams, shared JSON schemas).
  - Enforce `gate_contract_compatibility` ensuring both producer and consumer modules pass schema validation.
- **Surgical Module-Scoped Poisoning Isolation & Rollback**:
  - Support module-scoped checkpoints in `recovery_points` (`module_scope: <module_id> | global_system`).
  - Isolate context poisoning incidents to the culprit module (`culprit_module: <module_id>`), allowing unaffected modules to remain active without rollbacks.
- **Cross-Module Emulation Bridge**:
  - Scaffold cross-module integration test suites in `workplace/tests/integration/` connecting simulated components (e.g., client application communicating with virtual service daemon over local TCP loopback).
- **Quad-Space Directory Bootstrapping**: Automated creation and strict isolation of `context/`, `agentic/`, `workplace/` (with `workplace/config/` or `workplace/modules/`), and `user/` (`inputs/`, `hitl/`, `outputs/`).
- **Multi-Format Autonomous MVS Ingestion & Template Catalog**:
  - Provide and support 6 standardized MVS templates in `user/inputs/templates/` (accessible also via `input/templates/`):
    1. `mvs_feature_spec.md`: Natural language user stories, Gherkin acceptance criteria, business constraints, and non-goals.
    2. `mvs_api_contract.yaml`: OpenAPI 3.1 schema-first endpoints, request/response models, and error responses.
    3. `mvs_event_stream.yaml`: AsyncAPI pub/sub message schemas, Kafka/RabbitMQ channels, and idempotency guarantees.
    4. `mvs_adr_blueprint.md`: Architectural decisions, Redis/PostgreSQL topology, DDL schemas, and compliance trade-offs.
    5. `mvs_jira_story.json`: Standardized Jira / Linear JSON export format with issue keys, acceptance criteria, story points, and epics.
    6. `mvs_design_tokens.json`: Design system tokens (colors, typography, spacing, WCAG 2.1 AA accessibility rules).
  - Ingestion Normalizer: Parses heterogeneous MVS inputs into a canonical Abstract Semantic Graph (ASG) before triggering derivation.
  - Automatically infer database DDLs, configurations in `workplace/config/`, wire contracts in `.nb/context/contracts/`, implementation files in `workplace/src/` (or `workplace/modules/`), and test harnesses.
- **External Issue Tracker MCP Integration (Jira, Linear, GitHub Issues)**:
  - Configure issue tracker MCP connections via `.nb/config/issue_tracker_mcp.yaml`.
  - Implement JQL query polling and webhook receivers via Jira MCP server (`@modelcontextprotocol/server-jira` or Atlassian REST bridge).
  - Support automatic ingestion queries, e.g. `project = PERC AND status = "Ready for Dev" AND labels = "percipience-ready"`.
  - Translate queried Jira stories into `mvs_jira_story.json` format and inject them into the active subagent worktree queue.
  - Bi-Directional State Synchronization:
    - Transition Jira issue to `In Progress` when an ephemeral worktree is leased.
    - Transition Jira issue to `In Review` / `Done` upon successful verification gate execution (`gate_contract_compatibility`, `gate_test_verification`).
    - Automatically append a structured Jira comment with the Context Maturity Scorecard, test coverage metrics, Git commit SHA, and SHA-256 Merkle block proof.
    - If bounded TDD fails (exceeding 3 retries), transition Jira issue to `Needs HITL Review`, link to `user/hitl/poisoning_quarantine.md`, and tag the issue reporter.
- **Context Poisoning Detection, Rollback & Incremental Replay**:
  - Create an immutable recovery point (`recovery_point`) snapshot in `context_ledger.yaml` at each verified milestone, committing workspace state to Git.
  - Continuously audit context against schema validators and independent verification gates for context poisoning or hallucination drift.
  - Upon detecting poisoning: (1) trigger `rollback_to_recovery_point(RP_k)`, (2) isolate and quarantine the poisoning culprit in `user/hitl/poisoning_quarantine.md`, (3) sanitize active agent memory and ledger state, and (4) execute `replay_incremental_enhancements()` for subsequent valid steps.
- **Model-Agnostic Dynamic Multi-Model Cascading & Token Throttling**:
  - Maintain a provider-agnostic model tiering map in `.nb/config/token_compression_rules.yaml`.
  - Support multi-provider switching (`active_provider: anthropic | google | openai | bedrock | azure | local_vllm`) with standardized cognitive tier mappings.
  - Automatically route tasks: Tier A (`claude-3-7-sonnet / pro`, `gemini-2.0-pro`, `gpt-4o`) for complex derivation, verification gates, and security audits; Tier B (`claude-3-5-haiku / flash`, `gemini-2.0-flash`, `gpt-4o-mini`) for AST parsing, diff updates, docstrings, and commit formatting.
  - Enforce token budget limits per sprint milestone; pause or down-shift when spend exceeds 85% of ceiling.
- **Git Worktree Isolation & Atomic Merging**:
  - Automatically spin up isolated ephemeral worktrees in `.nb/workspaces/subagent_<id>/` for concurrent tasks.
  - Require verification gate pass before executing atomic merge back to `main`.
- **Automated Spec-to-Code Semantic Parity & Drift Reconciliation**:
  - Compute a continuous semantic parity score ($0.00 - 1.00$).
  - Execute automated *Revert Mode* (generate diff to undo unauthorized code drift) or *Evolve Mode* (propose spec delta for human sign-off via HITL).
- **Bounded TDD Self-Healing with Test Quarantine**:
  - Restrict test fix attempts to a maximum budget of 3 retries per test failure.
  - On 3rd failure, move test case into `quarantined_tests` in `context_ledger.yaml`, log an issue in `remaining_issues`, and halt at `user/hitl/`.
- **Cryptographic Hash-Chaining (`ledger_chain`)**:
  - Compute SHA-256 Merkle block headers linking each ledger revision to its predecessor.
  - Provide tamper-evident verification script (`ledger_chain_verifier.py`).
- **Visual DAG Dashboard Generation**:
  - Emit standalone HTML/JS/CSS dashboard to `user/outputs/dashboard/index.html`.
  - Render artifact lineage DAG, recovery points, module subgraphs, diff inspector, and HITL clarification actions.
- **Multi-Dimensional Maturity Assessment**:
  - Calculate scores (0.00 to 1.00) across 6 dimensions (Requirement Coverage, Architectural Grounding, Code/Config Quality, Test Coverage, Security, Token Efficiency).
  - Automatically emit context maturity scorecards to `workplace/docs/reports/context_maturity_report.md`.
- **Integrated State Ledger (`context_ledger.yaml`)**:
  - Maintain unified tracking across all 21 capabilities (`CAP-01`..`CAP-27`).
- **Autonomous Living Documentation & In-Workflow Mermaid Visualizer (`agent_living_doc_architect`)**:
  - *In-Workflow Lifecycle Hook*: `.nb/core/living_doc_engine.py` hooks directly into pre-PR verification gates, release workflows, and post-derivation stages to evaluate codebase deltas.
  - *Standardized Document Taxonomy in `workplace/docs/`*:
    1. `workplace/docs/README.md`: Central documentation index, system overview, and links to visual specifications.
    2. `workplace/docs/architecture.md`: System topology, component decomposition, communication channels, and C4 container diagrams rendered in Mermaid `graph TD` or `graph LR`.
    3. `workplace/docs/module_catalog.md`: Module boundaries, responsibilities, public interface signatures, types, and module-to-module dependency matrices.
    4. `workplace/docs/sequence_flows.md`: Critical runtime execution flows, cross-module request-response lifecycles, authentication handshakes, and error-recovery paths rendered in Mermaid `sequenceDiagram` with step autonumbering.
    5. `workplace/docs/data_flow.md`: End-to-end data ingestion, asynchronous event streaming, message broker routing, and state transition lifecycles rendered in Mermaid `flowchart` and `stateDiagram-v2`.
    6. `workplace/docs/entity_relationship.md`: Database tables, DDL relationships, wire contract DTO structures, and domain entities rendered in Mermaid `erDiagram` with explicit foreign key cardinality (`||--o{`, `}|--||`).
    7. `workplace/docs/domain_extensions.md`: Domain-specific documentation tailored dynamically to whichever layered plan is active (e.g., P2P torrent swarm topology and EIP-712 capability loans for `domain_blockchained_audio`; BLE GATT characteristic tables and A/B OTA partitions for `domain_iot_mobile`; RBAC roles and webhook handlers for `domain_saas_portal`).
  - *Mermaid Robustness Rules*: All generated Mermaid diagrams must enclose node labels containing parentheses, brackets, or punctuation in quotes (e.g. `node["FastAPI Provider (Port 8000)"]`), avoid raw HTML formatting, and pass offline syntax validation.
  - *Incremental AST Change Detection*: Maintain an AST skeleton hash store (`.scratch/doc_ast_hashes.json`); only re-render document sections and Mermaid blocks whose underlying source files or wire contracts have changed, avoiding token burn.
  - *Cryptographic Ledger Verification*: Register each documentation synchronization event in `context_ledger.yaml` under `living_docs`, sealing document hashes and diagram types into the active Merkle block.
- **Enterprise Reliability Hardening (Phases 1-3)**:
  - *Atomic Temporary Disk Serialization*: All critical state transitions (Merkle state sealing, token FinOps recordings, recovery snapshots) must execute via temporary file creation + `os.fsync()` + atomic `os.replace()`, eliminating corrupt, partial, or zero-byte ledger files during process crashes or concurrency collisions.
  - *Active POSIX PID-Probing & Stale Lease Eviction*: Ephemeral subagent worktrees must register their owning OS PID (`os.getpid()`). The runtime actively probes `os.kill(pid, 0)` upon lease operations, automatically reclaiming dead leases and running `git worktree remove --force` to eliminate zombie directory deadlocks without human intervention.
  - *Deep Schema-Driven Wire Contract Runtime Gate*: Wire contracts under `.nb/context/contracts/` must validate against JSON Schema Draft-07 specifications. Both inbound and outbound event payloads must undergo runtime validation (`validate_sample_payload()`), halting pipelines before schema mismatches reach production.
- **Scalability Hardening (Phases 1-3)**:
  - *Content-Addressable AST Skeleton Caching*: Structural AST pruning must employ SHA-256 content-addressable caching across memory and persistent disk (`.scratch/ast_cache/`), accelerating re-scans to sub-millisecond speeds (0.1ms) on unchanged source files and reducing AST parsing overhead by >85%.
  - *Rolling Merkle Epoch Checkpointing*: Scalable ledger verification must archive historical Merkle blocks into `.nb/context/ledger/archive/epoch_{start}_{end}.json` once height exceeds rolling thresholds, preserving constant $O(1)$ ledger read/write times while maintaining end-to-end cryptographic continuity through sealed `epoch_rollup_hash` references.
  - *Model-Agnostic Cognitive Tiering Router*: Runtime model dispatching dynamically routes routine subagent tasks (AST extraction, linting, docs, test runs) to **Tier B** (`claude-3-5-haiku / flash`, `gemini-2.0-flash`), delivering a 90% cost arbitrage while strictly reserving **Tier A** (`claude-3-7-sonnet / pro`, `gemini-2.0-pro`) for high-reasoning tasks (SemVer diffing, security audits, PR gate decisions).
- **Multi-Dialect Diagnostic Log Slicing & Tiered SLA Remediation**:
  - Automatically intercept test runner and compiler failure logs in CI/CD pipelines.
  - Apply `DiagnosticLogPruner.prune_traceback()` to strip out-of-tree noise and keep only in-repo frames.
  - Auto-hydrate `failure_site` source context (±4 lines) and build tiered prompt envelopes for Attempt 1 (Surgical Patch), Attempt 2 (Wire Invariant Refactor), and Attempt 3 (Final SLA Warning).
  - Enforce strict 3-attempt SLA before triggering surgical micro-module rollback to `RP_k`.
- **Cloud WORM Vault Egress & SEC 17a-4 Legal Hold Mirroring**:
  - Automatically mirror sealed Merkle blocks to S3 Object Lock and GCS WORM vaults upon PR gatekeeper completion.
  - Verify block hashes against remote WORM storage to guarantee immutable state retention.

- **Autonomous CI/CD Specialist Agent Plugins**:
  - Standardize five pre-configured specialist agent plugins under `.nb/agentic/custom/agents/`:
    1. `agent_flaky_test_detector`: Multi-run test stability analysis, quarantining intermittent non-deterministic test suites into `user/hitl/flaky_quarantine.yaml` as non-blocking.
    2. `agent_contract_compatibility_checker`: SemVer evolution guard, diffing wire contracts in `.nb/context/contracts/` to block breaking field removals or type mutations.
    3. `agent_dependency_cve_sentinel`: Supply-chain security, auditing source AST imports and manifests for CVEs, typosquatting packages, and restrictive licenses (AGPL).
    4. `agent_doc_drift_synchronizer`: Architecture sync, auditing exported AST interface symbols against `.nb/plan/` specifications to flag documentation drift.
    5. `agent_living_doc_architect`: In-workflow living documentation engine, synthesizing Mermaid visual architecture, sequences, data pipelines, entity-relationships, and module catalogs directly in `workplace/docs/`.
  - Wire all specialist plugins into a unified verification gatekeeper (`wf_pr_gatekeeper.yaml`, `.nb/bin/percipience gate`).

### Non-Functional Requirements
- **Intellectual Property Protection**: Zero plaintext markdown or YAML leakage for `context/` and `agentic/` on client filesystems when executing from compiled `.nbpack` bundles.
- **Zero-Drift & Determinism**: All derived code and configs in `workplace/` must maintain 100% lineage traceability to `user/inputs/`.
- **Context Integrity & Poisoning Resilience**: Guaranteed recovery to clean state within < 1 step upon detecting context contamination or severe hallucination.
- **Zero-Overhead Single-Module Simplicity**: Single-module projects incur zero structural bloat, using direct flat directories.
- **Token Cost Efficiency**: *Target* of >= 50–70% token reduction in long-running agentic conversations compared to uncompressed context passing, validated by the benchmark harness (see *Benchmark & Metrics Provenance*). All percentage figures in this plan are targets until reproduced by that harness.
- **Concurrency & Merge Safety**: Zero merge collisions during multi-agent concurrent execution via worktree isolation.
- **Tamper Evidence**: Cryptographic non-repudiation of all ledger state transitions via SHA-256 block hashing.

### Benchmark & Metrics Provenance
All quantitative figures stated throughout this plan (e.g., "50–70% token reduction", "62% savings", "90% cost arbitrage", "+12.5% additional savings", "sub-1.2s surgical rollback", "0.1ms AST retrieval", ">85% parsing reduction", "cache_hit_ratio", "estimated_token_savings_pct") are **targets/design goals, not measured results**, until reproduced by the benchmark suite. Each figure MUST be tied to a reproducible methodology recorded under `benchmarks/`:
- `workplace/docs/benchmarks/methodology.md`: workload definition, corpus size, model/provider + version, measurement harness, warm/cold cache policy, and statistical treatment (median over N runs, confidence interval).
- `benchmarks/results/<date>_<provider>_<model>.json`: raw measurements linked back to a Merkle ledger block so a claimed number is auditable to the run that produced it.
- Until a figure is backed by a `benchmarks/results/*` entry it is rendered as a *target* in prose and in the dashboard FinOps tab.

### Canonical Model Tiering & ID Centralization
To prevent staleness and drift, concrete model IDs are **not** authoritative in this narrative. The single source of truth is `.nb/config/token_compression_rules.yaml`, which maps abstract tiers to provider-specific IDs:
- Prose and diagrams refer only to abstract tiers — **Tier A** (Frontier / High-Reasoning), **Tier B** (Fast / Compact / High-Throughput), **Tier C** (Deterministic / Offline Rules). Any concrete model name appearing elsewhere (`claude-3-7-sonnet`, `gemini-2.0-*`, `gpt-4o/o1`, `deepseek-r1`, etc.) is an **illustrative reference for the current epoch only** and is superseded by the config.
- The config carries a `models_epoch` date and a `review_by` date so tier→ID mappings are refreshed on a schedule rather than hard-coded across the document.

### Security Hardening: `.nbpack` Threat Model, TEE Attestation & Key Management
The "zero disk plaintext" + "RAM-only enclave" design raises the cost of exfiltration but does **not** by itself prevent IP theft on a host the client fully controls (the client can attach a debugger/ptrace, dump `tmpfs`/`ramfs`, or read process memory). The security claim is therefore restated and hardened:
- **Honest claim**: On an untrusted client host, RAM-only hydration *raises the cost of and complicates* exfiltration; it does not guarantee prevention. A hard IP-protection guarantee requires a hardware **Trusted Execution Environment** (Intel SGX, AMD SEV-SNP, or AWS Nitro Enclaves) with **remote attestation**: the enclave proves its measured identity to the Neutron Binary key server before any decryption key is released.
- **Key management**: The AES-256-GCM content key is never shipped inside the `.nbpack`. At `percipience init`, the enclave performs remote attestation and receives a short-lived, memory-only content key from a KMS/HSM (or the attestation authority) bound to the attested measurement; the key is zeroized on teardown and never touches disk. Ed25519 signing keys live in an HSM; only public keys ship to clients.
- **Anti-tamper degradation**: If no TEE is available, the runtime downgrades to a clearly-labeled "obfuscation-only" posture (documented as best-effort, not IP-guaranteeing) rather than overclaiming protection.

### Merkle Terminology Clarification (Tree vs. Chain vs. Epoch Rollup)
The ledger combines three distinct constructs, and the term "Merkle" is used precisely as follows:
- **Per-block Merkle tree**: within a single ledger block, a Merkle tree is built over all tracked artifact hashes, yielding `merkle_root`. This supports **inclusion proofs** (an artifact can be proven to belong to a block without revealing the whole block).
- **Linear hash-chain across blocks**: blocks are linked by $H_i = \text{SHA256}(H_{i-1} + \text{canonical\_json}(\Delta_i) + T_i)$, giving append-only tamper evidence across time (this is a hash-chain, not a tree).
- **Epoch rollup**: when height exceeds a threshold, a range of blocks is archived and summarized by an `epoch_rollup_hash` that commits to the archived segment, preserving continuity in $O(1)$ active state.

### Ledger Concurrency & Hash-Chain Serialization
Atomic `os.replace()` guarantees each write is all-or-nothing, but the hash-chain append (`prev_block_hash` → `current_block_hash`) must be **serialized** so two subagents cannot fork the chain:
- **Single-host / multi-worktree**: a single advisory file lock (`flock` on `.nb/context/ledger/.ledger.lock`) plus an in-process mutex guards the read-modify-append critical section; `prev_block_hash` is read, the new block computed, and the file atomically replaced while the lock is held.
- **Multi-host (BYOR / distributed)**: a distributed lock (e.g., DB row lock, Redis Redlock, or object-store conditional-put/compare-and-swap) provides the same single-writer guarantee; conflicting appends are rejected and retried against the new head.
- **Ordering guarantee**: appends are strictly linearized (each block's `prev_block_hash` equals the previous committed `current_block_hash`); a losing writer re-reads the head and recomputes rather than forking.

### Append-Only HITL & Quarantine Stores
To avoid reintroducing the write races that worktree isolation solves, mutable single-file HITL stores are replaced by append-only, incident-scoped directories routed through the locked ledger:
- Poisoning incidents: `user/hitl/poisoning/<incident_id>.md` (one immutable file per incident) instead of a single mutable `poisoning_quarantine.md`.
- Flaky tests: `user/hitl/flaky/<test_id>.yaml` instead of a single mutable `flaky_quarantine.yaml`.
- Each new incident file is registered in `context_ledger.yaml` under the ledger lock, so concurrent worktrees never contend on the same physical file. (The legacy single-file paths may remain as read-only rolled-up views generated from the directory.)

### Operational Semantics: Rollback Data Loss, Determinism, Observability & Secrets
- **Rollback data-loss semantics**: surgical rollback rewinds *agent-authored* artifacts and ledger nodes only. In-flight user-owned data in `user/` and externally-committed side effects (e.g., already-sent Jira transitions, pushed commits) are **not** silently discarded — they are captured in a `rollback_manifest` recording what was reverted, what was preserved, and any compensating actions required, surfaced to HITL before destructive rewind.
- **Replay determinism**: because LLM outputs are non-deterministic, "incremental replay" reproduces state via a **determinism contract** — pinned model tier + provider/version, fixed `seed`/`temperature=0` where the provider supports it, and a **cached-response store** keyed by `(prompt_hash, model_epoch)`. Replay first serves cached responses; only cache misses re-invoke a model, and any divergence is flagged as a replay-drift incident rather than silently accepted.
- **Engine self-observability**: beyond the customer dashboard, the agent engine emits its own structured telemetry (spans/metrics/logs, e.g., OpenTelemetry) for scheduler decisions, tier routing, lock contention, and enclave attestation events, so the *engine itself* — not just derived artifacts — is observable.
- **Secrets handling**: all secrets (issue-tracker tokens, VCS deploy keys, KMS/HSM handles) are referenced only by secret-manager ARNs/URIs (as with the Jira `auth_secret_arn` example) — never inlined in `context_ledger.yaml`, `.nbpack`, or logs — and are resolved at runtime into the enclave with least-privilege scoping and rotation.

### Input Template Path Canonicalization
The canonical location for MVS ingestion templates is **`user/inputs/templates/`**. Earlier references to `input/templates/` are deprecated aliases retained only for backward compatibility and resolve (via symlink/shim) to the canonical path; new content and tooling MUST target `user/inputs/templates/`.

---

# Technical Design

### Key Decisions
- **Multi-Format MVS Parsing & Canonical Normalization Pipeline**: Enterprise teams produce intent across varied mediums: product managers write markdown stories, backend architects write OpenAPI specs, distributed systems teams write AsyncAPI schemas, and UI designers produce JSON design tokens. Rather than forcing a single rigid input format, Percipience implements a multi-format ingestion engine with pre-scaffolded templates in `user/inputs/templates/` (and `input/templates/`). An AST normalizer maps any template format into an internal Abstract Semantic Graph (ASG), preserving typed constraints while allowing autonomous derivation to synthesize full codebases deterministically.
- **Jira & Issue Tracker MCP Protocol Bridge**: Rather than building proprietary issue-sync integrations for every ticketing vendor, Percipience leverages the open Model Context Protocol (MCP). By connecting to Jira, Linear, and GitHub MCP servers, the engine natively accesses issue details, acceptance criteria, attachments, and comments. A bidirectional reconciliation loop pulls "Ready for Dev" stories into the derivation queue and writes back verified commit proofs, maturity scorecards, and state updates upon completion.
- **Proprietary Context & Agentic Space Obfuscation & Sealed Bundle Architecture (`.nbpack`)**:
  - Master plans, `agentic/` (metaprompts, workflows, methodologies), and `context/` (schemas, validation logic, Merkle DAG engine) are compiled into `.nbpack` binary packages via `percipience pack`.
  - Features AST minification, identifier scrambling, Ed25519 digital signature sealing, and AES-256-GCM envelope encryption.
  - Plaintext proprietary logic is never persisted to client disk; hydrated directly in volatile sandbox memory during `percipience init`.
  - Customer workspaces expose only transparent spaces (`workplace/` and `user/`), with a sanitized state projection (`context_ledger.public.yaml`) for observability.
- **Zero-Overhead Dual-Mode Operating Model**:
  - Configured via `project.mode: single_module | multi_module`.
  - *Single-Module Mode*: Code lives directly in `workplace/src/` and `workplace/config/`. Single linear DAG. Global recovery points.
  - *Multi-Module Mode*: Code lives in `workplace/modules/<module_id>/` with shared DTOs/stubs in `workplace/shared/`. Versioned interface contracts in `.nb/context/contracts/`.
- **Cross-Module Contract Architecture**:
  - `.nb/context/contracts/` houses single sources of truth for cross-module boundaries (e.g., `service_contract.yaml`, `api_schema.json`, `event_stream_spec.yaml`).
  - Code generators (`protoc`, code-stubs) compile these contracts into module stubs in `workplace/shared/generated/`.
- **Surgical Module Rollbacks**:
  - In multi-module mode, recovery points are scoped by `module_scope: <module_id> | global_system`.
  - If context poisoning occurs in `mod_service_consumer` (e.g., hallucinated endpoint or invalid payload schema), only the `mod_service_consumer` working tree and its ledger nodes are rewound. The `mod_service_provider` remains untouched.
- **End-to-End Emulation Bridge**:
  - In integrated systems, client and service components are connected via virtual loopback sockets (e.g., WebSocket/TCP bridge or mock HTTP server) allowing automated end-to-end integration tests to execute in CI/CD without external infrastructure.
- **Quad-Space Clean Folder Architecture**: Standardize on four isolated clean domains with strict architectural separation between platform infrastructure and project application logic:
  - `.nb/` (Platform Agentic CI/CD System): Houses the complete context engineering operating system, execution engines (`.nb/core/`), gatekeeper CLI (`.nb/bin/percipience`), platform configurations (`.nb/config/`), contracts and Merkle state chain ledgers (`.nb/context/`), declarative workflows and prompt suites (`.nb/agentic/`), CI/CD git hooks (`.nb/scripts/`), and platform verification suites (`.nb/tests/`).
  - `workplace/` (Project-Specific Layered Plan Implementations): Strictly reserved for customer project source code, layered domain modules (`workplace/modules/mod_*`), SaaS web portals (`workplace/portal/`), UI source trees (`workplace/src/`), project configurations (`workplace/config/site_config.yaml`), cross-module shared DTOs/primitives (`workplace/shared/`), living documentation (`workplace/docs/`), and project-specific tests (`workplace/tests/`). Zero platform execution engine logic lives in `workplace/`.
  - `user/` (User Enclave): Dedicated input/output/HITL directory (`user/inputs/` for MVS specifications, `user/hitl/` for human review/quarantines, and `user/outputs/` for generated dashboards and maturity reports).
  - `.nb/workspaces/` (Ephemeral Concurrency Enclave): Isolated subagent git worktrees and process lease locks managed by `.nb/core/worktree_engine.py`.
- **Dynamic Model Tier Router**:
  - Tier A (Frontier / High Reasoning): Complex MVS derivation, cross-module contract validation, architectural verification gates, security audits, context poisoning diagnosis.
  - Tier B (Fast / Compact): AST symbol extraction, unified diff application, test scaffolding, commit drafting, dashboard data serialization, routine living documentation extraction.
- **Git Worktree Isolation Engine**:
  - Ephemeral subagent working directories created via `git worktree add .nb/workspaces/<agent_id> -b feature/<task>`.
  - Atomic verification gate checks out isolated branch, executes test suite, and merges to `main` upon approval.
- **Semantic Parity & Anti-Drift Engine**:
  - Quantitative contract matching between input specs and code symbols.
  - Dual reconciliation: auto-revert unapproved drift or escalate approved evolutions to HITL.
- **Bounded TDD Loop & Test Quarantine**:
  - Self-healing retry ceiling = 3. Flaky or contradictory tests quarantined to prevent thrashing.
- **Cryptographic Merkle Hash Chaining**:
  - Block header formula: $H_i = \text{SHA256}(H_{i-1} + \text{canonical\_json}(\Delta_i) + T_i)$.
- **Time-Travel Visual Dashboard**:
  - Single-file zero-dependency HTML/SVG dashboard generated at `user/outputs/dashboard/index.html`.
- **The Triad of Autonomous Delivery (Self-Sustaining, Self-Recovering, Self-Improving)**:
  - *Self-Sustaining*: Proactive lease reclamation, zombie branch cleanup, and WORM Merkle continuity validation executed on scheduled cycles or pre-PR checks.
  - *Self-Recovering*: Autonomous fault diagnosis, ephemeral worktree test execution, bounded TDD auto-patching ($\le 3$ retries), and sub-1.2s surgical module rollback fallback sparing sibling services.
  - *Self-Improving*: Closed-loop telemetry feedback analyzing token burn and test pass velocities, dynamically tuning AST pruning thresholds (+12.5% compression gains) and prompt cache prefix alignment.
- **Healthy Custom Agent Plugin Integration Pattern**:
  - All custom agents conform to `agentic/templates/custom_agent_template.yaml` and the .
  - Scaffolding, workflow DAG injection (`wf_pr_gatekeeper.yaml`), ephemeral worktree sandboxing, and pre/post Merkle block sealing (`RP_AGENT_*`) are governed by `AgentPluginEngine`.
- **Autonomous In-Workflow Living Documentation Engine & Mermaid Visualizer (Living Docs)**:
  - Software architecture documentation historically suffers from severe drift, rapidly becoming obsolete as code evolves. Percipience solves this by treating documentation as a compiled, living artifact of the codebase itself.
  - `.nb/core/living_doc_engine.py` and `.nb/agentic/custom/agents/agent_living_doc_architect.yaml` run directly within workflow executions (such as PR gatekeeper checks, post-derivation runs, and release cuts).
  - The engine inspects ASTs, wire contracts, and active layered domain plans, generating standardized Markdown documents in `workplace/docs/` with embedded Mermaid diagrams for architecture, module interfaces, sequence flows, data pipelines, entity-relationships, and domain specifics.
  - Changes are tracked incrementally via content-addressable AST hashes so that unchanged modules cost zero extra tokens.
  - A dedicated verification gate (`gate_doc_drift_verification`) ensures zero drift and verifies Mermaid syntax before code merge.
- **Token FinOps & 15% Performance Fee Accounting Engine**:
  - Real-time token tracking (`TokenTracker`) capturing raw vs. AST-pruned tokens across multiple programming languages.
  - Transparent accounting logged to `.nb/context/ledger/token_savings_ledger.yaml` computing gross customer savings ($0.003/1K tokens) and 15% performance fee.
- **3-Tier Layered Context Precedence Hierarchy & BYOR Multi-VCS Adapter**:
  - Guarantees Tier 1 (Platform Invariants / Enclave) cannot be overridden by user prompts or custom schemas.
  - Native BYOR adapter (`BYORAdapter`) connecting self-hosted GitLab, GitHub Enterprise, and Bitbucket Data Center with SSH deploy keys and internal Root CA validation.
- **Decoupled Enterprise Observability Hub & Telemetry Gateway**:
  - Zero-dependency interactive 5-tab dashboard (`user/outputs/dashboard/index.html`) backed by production HTTP/API gateway (`workplace/portal/server.py`).
- **Atomic Ledger Disk Serialization & Rolling Epoch Checkpointing (Reliability & Scalability)**:
  - Eliminates file truncation risks via write-to-temp, `os.fsync()`, and atomic `os.replace()` in `MerkleEngine` and `TokenTracker`.
  - Checkpoints historical Merkle blocks into `.nb/context/ledger/archive/epoch_{start}_{end}.json` once chain height reaches scale thresholds, sealing an `epoch_rollup_hash` in `context_ledger.yaml` to maintain $O(1)$ disk/memory access times while guaranteeing 100% cryptographic audit continuity.
- **Active POSIX PID-Probing & Worktree Lease Lifecycle Engine (Reliability)**:
  - Attaches OS process IDs to worktree leases in `.nb/workspaces/leases.json`. Actively probes `os.kill(pid, 0)` upon lease acquisition, listing, and maintenance. Automatically purges dead leases and invokes `git worktree remove --force` to eliminate zombie worktree deadlocks without human intervention.
- **Deep Schema-Driven Wire Contract Runtime Gate (Reliability)**:
  - Wire contracts under `.nb/context/contracts/` strictly conform to JSON Schema Draft-07 specs. `LayeredContextValidator` and `pr_gatekeeper.yaml` enforce runtime event and payload validation, preventing cross-module interface drift.
- **Content-Addressable AST Skeleton Caching (Scalability)**:
  - `ASTOptimizer` indexes structural skeletons by SHA-256 content hashes in-memory and in `.scratch/ast_cache/`, providing sub-millisecond retrieval on incremental commits and saving over 85% in syntax tree parsing compute.
- **Model-Agnostic Cognitive Tiering Router (Scalability & FinOps Arbitrage)**:
  - Dynamically routes routine subagent tasks (AST pruning, linting, docs, test runs) to **Tier B** (`claude-3-5-haiku / flash`), delivering a 90% cost arbitrage while reserving **Tier A** (`claude-3-7-sonnet / pro`) for high-complexity reasoning (SemVer contract diffs, security audits, PR gate merge decisions).
- **Autonomous CI/CD Specialist Agent Plugin Fleet & 6-Stage PR Gatekeeper (Ecosystem Extensibility)**:
  - Standardizes five built-in specialist plugins in `.nb/agentic/custom/agents/`: `agent_flaky_test_detector`, `agent_contract_compatibility_checker`, `agent_dependency_cve_sentinel`, `agent_doc_drift_synchronizer`, and `agent_living_doc_architect`.
  - Integrates all five into the unified PR gatekeeper workflow (`wf_pr_gatekeeper.yaml`, `.nb/bin/percipience gate`).

---

### Data Models / Contracts

```yaml
# Master Parent Context Ledger Schema (context_ledger.yaml)
# Includes external issue tracker MCP configuration
mcp_integrations:
  jira:
    enabled: true
    server_package: "@modelcontextprotocol/server-jira"
    endpoint: "https://company.atlassian.net"
    auth_secret_arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret/jira-api-token"
    jql_query: "project = PERC AND status = 'Ready for Dev' AND labels = 'percipience-ready'"
    poll_interval_seconds: 300
    auto_transition:
      on_start: "In Progress"
      on_verify_pass: "Done"
      on_hitl_quarantine: "Needs HITL Review"
    attach_maturity_report: true
    attach_merkle_proof: true
ledger_version: "7.3.0"
project:
  name: "Enterprise_Unified_Ecosystem"
  domain: "Universal Multi-Module Enterprise Space"
  mode: "multi_module"  # Options: "single_module" | "multi_module"
  methodology: "Agile / Hybrid SDLC"
  tech_stack:
    language: "Polyglot (TypeScript / Python / Go / Java / Rust)"
    framework: "Multi-Service Architecture / Modern Full-Stack"
    orchestration: "Multi-Agent Framework"
  code_config: "workplace/config/project_master_config.yaml"

plan_security:
  bundle_mode: "encrypted_nbpack"  # Options: "plaintext_md" | "encrypted_nbpack"
  bundle_path: ".percipience/parent_master.nbpack"
  bundle_hash: "f4a8e2b9c1d3e5f7a8b0c2d4e6f8a9b1c3d5e7f9a0b2c4d6e8f0a2b4c6d8e0f2"
  signature_verified: true
  encryption_algorithm: "AES-256-GCM"
  signer_public_key: "ed25519:neutron_binary_pub_91823"
  obfuscated_spaces:
    - space: "agentic/"
      status: "Enclave_Encrypted"
      runtime_mount: "ramfs://percipience/enclave/agentic"
      contents: ["prompts", "workflows", "methodologies", "model_tiering_router"]
    - space: "context/"
      status: "Enclave_Encrypted"
      runtime_mount: "ramfs://percipience/enclave/context"
      contents: ["schemas", "contracts_engine", "merkle_verifier", "ledger_internal"]
  public_spaces:
    - space: "workplace/"
      status: "Transparent_Filesystem"
    - space: "user/"
      status: "Transparent_Filesystem"

ledger_chain:
  block_id: 110
  prev_block_hash: "8f2b7a91c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c"
  current_block_hash: "4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b"
  merkle_root: "9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b"
  timestamp: "2026-09-13T14:45:00Z"
  verified: true

# Module Registry for Multi-Module Mode
modules:
  - id: "mod_service_provider"
    name: "Core Business & State Provider Service"
    path: "workplace/modules/mod_service_provider"
    domain: "Provider Engine & Business Logic"
    tech_stack: "Python / FastAPI / SQLModel"
    maturity: "Scaffolded"
    current_recovery_point: "RP_PROV_003"

  - id: "mod_service_consumer"
    name: "Downstream Consumer & Client Application"
    path: "workplace/modules/mod_service_consumer"
    domain: "Interface Layer & API Consumer"
    tech_stack: "TypeScript / React / Tailwind"
    maturity: "Scaffolded"
    current_recovery_point: "RP_CONS_004"

# Versioned Cross-Module Interface Contracts
contracts:
  - id: "contract_service_api"
    name: "Core Service OpenAPI Interface"
    spec_path: ".nb/context/contracts/service_contract.yaml"
    producer_module: "mod_service_provider"
    consumer_modules: ["mod_service_consumer"]
    version: "1.2.0"
    hash: "d4e5f67a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e"
    status: "Verified_Compatible"

  - id: "contract_event_stream"
    name: "Async Event Stream Specification"
    spec_path: ".nb/context/contracts/event_stream_spec.yaml"
    producer_module: "mod_service_provider"
    consumer_modules: ["mod_service_consumer"]
    version: "2.0.0"
    hash: "a1b2c3d4e5f67890123456789abcdef012345678"
    status: "Verified_Compatible"

# Autonomous Living Documentation Engine Tracking (CAP-21)
living_docs:
  engine_enabled: true
  docs_root: "workplace/docs/"
  preferred_diagram_engine: "mermaid"
  auto_sync_on_workflow_run: true
  documents:
    - id: "doc_arch_overview"
      path: "workplace/docs/architecture.md"
      title: "System Architecture & C4 Topology"
      diagram_types: ["mermaid:graph", "mermaid:c4Component"]
      source_hashes:
        modules_hash: "7f8b9a1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a"
        contracts_hash: "d4e5f67a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e"
      last_synced_commit: "9c8b7a6f"
      merkle_block_id: 110
      status: "Synchronized"
    - id: "doc_module_catalog"
      path: "workplace/docs/module_catalog.md"
      title: "Poly-Module Interface Catalog & Responsibilities"
      diagram_types: ["mermaid:graph", "table:api_matrix"]
      source_hashes:
        ast_skeleton_hash: "3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f"
      last_synced_commit: "9c8b7a6f"
      merkle_block_id: 110
      status: "Synchronized"
    - id: "doc_sequence_flows"
      path: "workplace/docs/sequence_flows.md"
      title: "Runtime Execution & Cross-Module Sequence Flows"
      diagram_types: ["mermaid:sequenceDiagram"]
      source_hashes:
        workflows_hash: "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b"
      last_synced_commit: "9c8b7a6f"
      merkle_block_id: 110
      status: "Synchronized"
    - id: "doc_data_flows"
      path: "workplace/docs/data_flow.md"
      title: "Data Transformation Pipelines & Event Streams"
      diagram_types: ["mermaid:flowchart", "mermaid:stateDiagram-v2"]
      source_hashes:
        event_stream_hash: "a1b2c3d4e5f67890123456789abcdef012345678"
      last_synced_commit: "9c8b7a6f"
      merkle_block_id: 110
      status: "Synchronized"
    - id: "doc_entity_rel"
      path: "workplace/docs/entity_relationship.md"
      title: "Domain Models & Entity-Relationship Schema"
      diagram_types: ["mermaid:erDiagram", "mermaid:classDiagram"]
      source_hashes:
        schemas_hash: "5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b"
      last_synced_commit: "9c8b7a6f"
      merkle_block_id: 110
      status: "Synchronized"
    - id: "doc_domain_extensions"
      path: "workplace/docs/domain_extensions.md"
      title: "Active Layered Domain Deep Dive"
      active_layer_id: "domain_blockchained_audio"  # e.g., domain_iot_mobile, domain_saas_portal
      diagram_types: ["mermaid:graph", "mermaid:sequenceDiagram"]
      last_synced_commit: "9c8b7a6f"
      merkle_block_id: 110
      status: "Synchronized"

model_tiering_policy:
  provider_agnostic: true
  active_provider: "anthropic"  # Options: "anthropic" | "google" | "openai" | "bedrock" | "azure" | "local_vllm"
  tier_a_model: "claude-3-7-sonnet / pro"
  tier_b_model: "claude-3-5-haiku / flash"
  tier_a_reference_models:
    anthropic: "claude-3-7-sonnet"
    google: "gemini-2.0-pro"
    openai: "gpt-4o / o1"
    deepseek: "deepseek-r1"
  tier_b_reference_models:
    anthropic: "claude-3-5-haiku"
    google: "gemini-2.0-flash"
    openai: "gpt-4o-mini"
  tier_a_fallback: "gemini-2.0-pro"
  tier_b_fallback: "gemini-2.0-flash"
  budget_cap_usd: 35.00
  current_spend_usd: 8.20
  spend_alert_threshold: 0.85
  auto_downshift_enabled: true

token_optimization:
  context_compression_enabled: true
  ast_extraction_level: "signatures_only"
  diff_mode: "unified_diff"
  prompt_caching_aligned: true
  cache_hit_ratio: 0.81
  estimated_token_savings_pct: 66.4

worktrees:
  - worktree_id: "wt_provider_dev_01"
    subagent_role: "agent_provider_developer"
    module_scope: "mod_service_provider"
    branch: "feature/provider-service"
    path: ".nb/workspaces/provider_dev_01"
    status: "Active"
    isolated_commits: 4
  - worktree_id: "wt_consumer_dev_01"
    subagent_role: "agent_consumer_developer"
    module_scope: "mod_service_consumer"
    branch: "feature/consumer-service"
    path: ".nb/workspaces/consumer_dev_01"
    status: "Active"
    isolated_commits: 3

semantic_parity:
  current_parity_score: 0.97
  drift_status: "Aligned"
  unmapped_spec_items: []
  unauthorized_code_symbols: []
  reconciliation_mode: "Revert"

recovery_points:
  - snapshot_id: "RP_PROV_003"
    module_scope: "mod_service_provider"
    timestamp: "2026-09-13T14:40:00Z"
    git_commit_sha: "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b"
    clean_artifacts_hash: "3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b"
    verified_maturity: "Scaffolded"
    status: "Active_Clean"

  - snapshot_id: "RP_CONS_004"
    module_scope: "mod_service_consumer"
    timestamp: "2026-09-13T14:45:00Z"
    git_commit_sha: "1f2e3d4c5b6a7890123456789abcdef012345678"
    clean_artifacts_hash: "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d"
    verified_maturity: "Scaffolded"
    status: "Active_Clean"

  - snapshot_id: "RP_SYS_001"
    module_scope: "global_system"
    timestamp: "2026-09-13T14:46:00Z"
    git_commit_sha: "5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d"
    clean_artifacts_hash: "0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d"
    verified_maturity: "Integrated"
    status: "Active_Clean"

poisoning_incidents:
  - incident_id: "POI_002"
    detected_at: "2026-09-13T14:42:00Z"
    culprit_type: "Payload_Schema_Contract_Mismatch"
    culprit_module: "mod_service_consumer"
    isolated_from: ["mod_service_provider"]
    rolled_back_to: "RP_CONS_004"
    quarantine_file: "user/hitl/poisoning_quarantine.md"
    replay_status: "Successfully_Replayed"

quarantined_tests:
  - test_id: "test_cross_module_payload_stream"
    test_file: "workplace/tests/integration/test_cross_module_e2e.py"
    quarantined_at: "2026-09-13T14:35:00Z"
    failure_reason: "AssertionError: Consumer payload validation failed against service contract schema"
    retry_count: 3
    retry_budget_max: 3
    linked_issue_id: "ISSUE-003"
    status: "Quarantined_Awaiting_HITL"

artifacts:
  - id: "art_contract_api_01"
    name: "service_contract.yaml"
    type: "CrossModuleContract"
    source: ".nb/context/contracts/service_contract.yaml"
    hash: "d4e5f67a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e"
    maturity: "Derived"

  - id: "art_provider_service_01"
    name: "service_handler.py"
    type: "SourceCode"
    source: "workplace/modules/mod_service_provider/src/service_handler.py"
    module: "mod_service_provider"
    derived_from: ["art_contract_api_01"]
    maturity: "Scaffolded"

  - id: "art_consumer_client_01"
    name: "client_controller.ts"
    type: "SourceCode"
    source: "workplace/modules/mod_service_consumer/src/client_controller.ts"
    module: "mod_service_consumer"
    derived_from: ["art_contract_api_01"]
    maturity: "Scaffolded"

  - id: "art_living_docs_bundle"
    name: "workplace_docs"
    type: "LivingDocumentation"
    source: "workplace/docs/"
    derived_from: ["art_provider_service_01", "art_consumer_client_01", "art_contract_api_01"]
    maturity: "Verified"

git_commits:
  - commit_sha: "5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d"
    timestamp: "2026-09-13T14:46:00Z"
    author: "Percipience Agentic Engine (Claude / Gemini / GPT) <agent@antigravity.ai>"
    message: "feat(cross-module): integrate consumer module with provider service contract"
    linked_requirements: ["REQ-PROVIDER-API-01", "REQ-CONSUMER-INT-01"]
    touched_artifacts: ["art_contract_api_01", "art_provider_service_01", "art_consumer_client_01", "art_living_docs_bundle"]

remaining_issues:
  - issue_id: "ISSUE-003"
    category: "Cross_Module_Integration"
    severity: "Medium"
    description: "test_cross_module_payload_stream failed 3 self-healing attempts; quarantined."
    status: "Quarantined"
    target_milestone: "Sprint-2"

standard_issue_checklist:
  - check_id: "CHK_UNHANDLED_EXCEPTIONS"
    passed: true
  - check_id: "CHK_MISSING_UNIT_TESTS"
    passed: true
  - check_id: "CHK_TOKEN_BUDGET_EXCEEDED"
    passed: true
  - check_id: "CHK_UNVERIFIED_SCHEMAS"
    passed: true
  - check_id: "CHK_SECURITY_VULNERABILITIES"
    passed: true
  - check_id: "CHK_MEMORY_LEAK_RISK"
    passed: true
  - check_id: "CHK_CONTEXT_POISONING_FREE"
    passed: true
  - check_id: "CHK_SEMANTIC_PARITY_PASSED"
    passed: true
  - check_id: "CHK_LEDGER_CHAIN_INTEGRITY"
    passed: true
  - check_id: "CHK_CONTRACT_COMPATIBILITY_PASSED"
    passed: true
  - check_id: "CHK_PLAN_ENVELOPE_SIGNATURE_VALID"
    passed: true
  - check_id: "CHK_PROPRIETARY_SPACES_OBFUSCATED"
    passed: true
  - check_id: "CHK_LIVING_DOCS_IN_SYNC"
    passed: true
  - check_id: "CHK_MERMAID_SYNTAX_VALID"
    passed: true

workflow:
  id: "wf_cross_module_delivery_01"
  spec_input: "user/inputs/user_requirement_spec.yaml"
  hitl_dir: "user/hitl/"
  output_dir: "user/outputs/"
  auto_complete: true
  status: "In_Progress"
  agents:
    - id: "agent_architect"
      role: "System Architect"
      model_tier: "Tier_A"
      stage: "architect"
      task_status: "Verified"
      output_artifact: "art_contract_api_01"
      verified_by_gate: "gate_arch_review"
      handoff_hook: "hook_arch_to_devs"
    - id: "agent_provider_developer"
      role: "Service Provider Specialist"
      model_tier: "Tier_A"
      stage: "develop_provider_service"
      worktree: "wt_provider_dev_01"
      task_status: "Verified"
      output_artifact: "art_provider_service_01"
      verified_by_gate: "gate_provider_review"
      handoff_hook: "hook_provider_to_integration"
    - id: "agent_consumer_developer"
      role: "Service Consumer Specialist"
      model_tier: "Tier_A"
      stage: "develop_consumer_service"
      worktree: "wt_consumer_dev_01"
      task_status: "Verified"
      output_artifact: "art_consumer_client_01"
      verified_by_gate: "gate_consumer_review"
      handoff_hook: "hook_consumer_to_integration"
    - id: "agent_integration_verifier"
      role: "Cross-Module Integration Verifier"
      model_tier: "Tier_A"
      stage: "verify_integration"
      task_status: "Verified"
      verified_by_gate: "gate_cross_module_compatibility"
      handoff_hook: "hook_integration_to_docs"
    - id: "agent_living_doc_architect"
      role: "Living Documentation & Architecture Visualizer"
      model_tier: "Tier_B"
      stage: "generate_living_documentation"
      worktree: "wt_living_docs_01"
      task_status: "Verified"
      output_artifact: "art_living_docs_bundle"
      verified_by_gate: "gate_doc_drift_verification"
      handoff_hook: "hook_docs_to_eval"
  gates:
    - id: "gate_arch_review"
      type: "IndependentVerification"
      verifier_agent: "agent_verifier"
      checks: ["schema_validity", "token_budget_passed", "zero_drift", "poisoning_check"]
      result: "Passed"
    - id: "gate_provider_review"
      type: "ServiceVerification"
      verifier_agent: "agent_verifier"
      checks: ["contract_implementation_valid", "unit_test_coverage", "no_quarantine_breach"]
      result: "Passed"
    - id: "gate_consumer_review"
      type: "ClientVerification"
      verifier_agent: "agent_verifier"
      checks: ["mock_provider_e2e_pass", "schema_validation_strict", "ast_type_valid"]
      result: "Passed"
    - id: "gate_cross_module_compatibility"
      type: "CrossModuleCompatibility"
      verifier_agent: "agent_integration_verifier"
      checks: ["contract_schema_valid", "interface_payload_alignment", "e2e_sim_test_passed"]
      result: "Passed"
    - id: "gate_doc_drift_verification"
      type: "LivingDocSyncGate"
      verifier_agent: "agent_doc_drift_synchronizer"
      checks: ["ast_symbol_coverage", "mermaid_syntax_validity", "contract_doc_alignment", "zero_stale_diagrams"]
      result: "Passed"
  hooks:
    - id: "hook_arch_to_devs"
      trigger: "on_gate_pass:gate_arch_review"
      from_agent: "agent_architect"
      to_agents: ["agent_provider_developer", "agent_consumer_developer"]
      payload_artifact: "art_contract_api_01"
      status: "Fired"
    - id: "hook_provider_to_integration"
      trigger: "on_gate_pass:gate_provider_review"
      from_agent: "agent_provider_developer"
      to_agents: ["agent_integration_verifier"]
      payload_artifact: "art_provider_service_01"
      status: "Fired"
    - id: "hook_consumer_to_integration"
      trigger: "on_gate_pass:gate_consumer_review"
      from_agent: "agent_consumer_developer"
      to_agents: ["agent_integration_verifier"]
      payload_artifact: "art_consumer_client_01"
      status: "Fired"
    - id: "hook_integration_to_docs"
      trigger: "on_gate_pass:gate_cross_module_compatibility"
      from_agent: "agent_integration_verifier"
      to_agents: ["agent_living_doc_architect"]
      payload_artifact: "art_provider_service_01"
      status: "Fired"
    - id: "hook_docs_to_eval"
      trigger: "on_gate_pass:gate_doc_drift_verification"
      from_agent: "agent_living_doc_architect"
      to_agents: ["platform.merkle_ledger"]
      payload_artifact: "art_living_docs_bundle"
      status: "Fired"
```

### Standardized Workflow Hook Lifecycle, Layered Plan Integration & Skippability Engine

To ensure continuous, deterministic execution across platform and layered domain workflows, Percipience implements a standardized five-stage hook lifecycle, multi-tier agent discovery, reliable supervisor spawning, and differential skippability assessment:

#### 1. Five-Stage Hook Lifecycle Taxonomy
```mermaid
graph LR
  A["pre_step_hook<br/>(Differential State Fingerprinting)"] --> B{"Assessment"}
  B -- "Unchanged (Hash Match)" --> S["[SKIPPABLE]<br/>Reuse Cached Outputs<br/>Zero Compute/Tokens"]
  B -- "Delta Detected" --> C["spawn_hook<br/>(Pre-flight & Worktree Isolation)"]
  C --> D["step_execution<br/>(Supervised Worker N_max=3)"]
  D --> E["handoff_hook<br/>(Cryptographic HandoffToken)"]
  E --> F["post_step_hook / gate<br/>(Schema Invariant Validation)"]
  F --> G["sealing_hook<br/>(Merkle Ledger Block Append)"]
```

1. **`pre_step_hook` (Differential State Fingerprinting)**:
   - Computes deterministic SHA-256 digest of input artifacts, contract schemas, and AST symbols.
   - Evaluates `.nb/context/ledger/step_cache.json`.
   - If inputs match cached receipt and declared outputs exist on disk, step is marked `SKIPPABLE`.
   - Emits verbose output:
     ```text
     [HOOK_ASSESSMENT][SKIPPABLE] Step '<step_id>' [Executor: <executor>]: SKIPPED
       - Reason: Input artifacts and contracts unchanged (SHA-256: <hash> matches receipt). Output verified.
       - Action: Reusing cached output artifacts; skipping agent spawn.
       - Resource Conservation: ~4,500 tokens saved.
     ```
2. **`spawn_hook` (Reliable Agent Sandbox Provisioning)**:
   - Resolves agent specifications across multi-tier search paths (`.nb/agentic/custom/agents/`, `.nb/plan/agents/`, `.nb/plan/packages/*/agents/`, `user/hitl/orphaned_context_files/agents/`).
   - Provisions isolated ephemeral worktree sandbox (`.nb/workspaces/subagent_<executor>/`).
   - Asserts concurrency lease lock, preventing race conditions.
3. **`handoff_hook` (Cross-Agent Cryptographic Continuity)**:
   - Encapsulates inter-agent artifacts within a signed `HandoffToken` containing predecessor block hash, artifact Merkle root, and schema version.
   - Successor agent validates token signature before ingesting payloads, eliminating context poisoning.
4. **`post_step_hook` / `verification_gate_hook`**:
   - Executes independent verification gates (`gate_arch_review`, `gate_provider_review`, `gate_consumer_review`, `gate_cross_module_compatibility`, `gate_doc_drift_verification`).
   - Rejects unverified artifacts and triggers bounded auto-healing ($N \le 3$).
5. **`sealing_hook` (Merkle State Sealing)**:
   - Appends verified block to `.nb/context/ledger/context_ledger.yaml`.
   - Updates `step_cache.json` with execution receipt and input/output fingerprints.

#### 2. Cross-Layer Agent Hook Setup
Workflows dynamically orchestrate agents defined in domain-specific layered plans without manual registration:
- **JetBrains IDE Domain**: `agent_jetbrains_plugin_architect`, `agent_psi_ast_bridge_specialist`, `agent_intellij_ui_ux_engineer`.
- **VSCode Extension Domain**: `agent_vscode_extension_architect`, `agent_lsp_language_features_specialist`, `agent_vscode_webview_ux_engineer`.
- **Morphogenetic MoE Domain**: `agent_moe_evolution_architect`, `agent_expert_training_specialist`, `agent_morphogenesis_engineer`.
- **Decentralized Audio & Crypto Domain**: `agent_blockchain_audio_streaming_architect`, `agent_crypto_defi_risk_architect`.
- **Platform & Living Docs**: `agent_living_doc_architect`, `agent_verifier`, `platform.self_sustaining_engine`, `platform.ast_pruner`, `platform.contract_verifier`, `platform.merkle_ledger`.

#### 3. Reliable Subagent Spawning & Supervisor Protocol
To eliminate agent spawn and runtime unreliability:
- **Pre-Flight Contract Assertion**: Verifies all input files, contract schemas, and directory mounts exist prior to spawning the process or subagent session.
- **Hermetic Worktree Sandbox**: Each spawned agent operates in an isolated worktree directory (`.nb/workspaces/subagent_<id>`), preventing concurrent filesystem collisions.
- **Bounded Supervisor Retry Loop**: If an agent process fails due to transient API timeouts or memory spikes, the supervisor retries up to $N_{\max} = 3$ times with exponential backoff before escalating to HITL quarantine (`user/hitl/`).

---

### Issue Tracker MCP Ingestion & Bi-Directional Lifecycle Architecture

```mermaid
sequenceDiagram
  autonumber
  participant Jira as Atlassian Jira Software
  participant MCP as Jira MCP Server (@modelcontextprotocol/server-jira)
  participant Ingest as Percipience MVS Ingest Engine
  participant Worktree as Ephemeral Subagent Worktree
  participant Verifier as Independent Verification Gate
  participant DocAgent as agent_living_doc_architect
  participant Merkle as Merkle Ledger Engine

  Note over Jira,MCP: 1. Story Prepared by Product Owner
  Jira->>Jira: Issue PERC-1042 moved to "Ready for Dev" (label: percipience-ready)
  
  Note over MCP,Ingest: 2. MCP JQL Query & Ingestion
  Ingest->>MCP: call_tool: jira_search_issues(jql='status="Ready for Dev" AND labels="percipience-ready"')
  MCP->>Jira: REST API: /rest/api/3/search
  Jira-->>MCP: Returns Issue AST (Summary, Description, AC, Story Points)
  MCP-->>Ingest: Normalized Issue JSON
  Ingest->>Ingest: Convert to user/inputs/templates/mvs_jira_story.json
  
  Note over Ingest,Worktree: 3. Execution & Progress Update
  Ingest->>MCP: call_tool: jira_transition_issue(issue_key='PERC-1042', status='In Progress')
  MCP->>Jira: Update Issue Status to "In Progress"
  Ingest->>Worktree: Mount .nb/workspaces/subagent_PERC_1042/ & Derivation
  Worktree->>Worktree: Generate workplace/ code, configs & tests

  Note over Worktree,Verifier: 4. Verification & Self-Healing
  Worktree->>Verifier: Run gate_contract_compatibility & gate_test_verification
  Verifier-->>Worktree: Verification Passed (Coverage >= 85%, Zero Drift)

  Note over Verifier,DocAgent: 5. Living Documentation & Visual Synthesis (CAP-21)
  Verifier->>DocAgent: Trigger AST & contract introspection
  DocAgent->>DocAgent: Synthesize Mermaid diagrams (architecture, sequence, data flow, ERD)
  DocAgent->>DocAgent: Update workplace/docs/ (modules, sequences, architecture, domain)

  Note over DocAgent,Jira: 6. Merkle Seal & Bi-Directional Closure
  DocAgent->>Merkle: Append Block H_i, compute Merkle Root with living_docs hashes
  Merkle-->>Ingest: Merkle Block Hash (SHA-256) & Git Commit SHA
  Ingest->>MCP: call_tool: jira_add_comment(issue_key='PERC-1042', comment='Maturity: 0.94, Merkle SHA: e3b0c4..., Docs: workplace/docs/ synchronized with Mermaid models')
  Ingest->>MCP: call_tool: jira_transition_issue(issue_key='PERC-1042', status='Done')
  MCP->>Jira: Issue PERC-1042 updated with audit evidence and closed
```

### Architecture Diagram

```mermaid
graph TD
  PlanSource["Proprietary Parent Master Plan (.md)<br/>+ agentic/ (Prompt Suites & Workflows)<br/>+ context/ (Schemas & State Engines)"] --> Compiler["percipience pack Compiler<br/>(AST Minification + Mangling + Ed25519 Signer)"]
  Compiler --> SealedPack[".percipience/parent_master.nbpack<br/>(AES-256-GCM Encrypted Binary Envelope)"]
  
  SealedPack --> Boot["percipience init --mode multi_module --parent-plan parent_master.nbpack"]
  Boot --> MemoryHydrate["In-Memory Enclave Hydrator<br/>(RAM-Only Hydration of context/ & agentic/<br/>Zero Disk Plaintext)"]

  A["Sparse User MVS Inputs in user/inputs/<br/>(e.g., Provider Spec + Consumer Spec)"] --> B["Model-Agnostic Agentic Engine<br/>(Mediated via Percipience RAM Enclave<br/>Reference: Claude / Gemini / GPT)"]
  MemoryHydrate --> B
  B --> C{"project.mode in context_ledger.yaml"}
  
  C -- "mode: single_module" --> SM["Single Module Scaffolding:<br/>Flat workplace/src/, workplace/config/<br/>Single Linear DAG & Global Recovery Points"]
  
  C -- "mode: multi_module" --> MM["Poly-Module Bootstrapping:<br/>Initialize .nb/context/contracts/, workplace/shared/<br/>workplace/modules/mod_service_provider/, workplace/modules/mod_service_consumer/"]
  
  subgraph Cross-Module Contract & Model Router
    MM --> CR["Contract Derivation Engine:<br/>Generate OpenAPI, AsyncAPI, Protobuf Specs in .nb/context/contracts/"]
    CR --> TR["Dynamic Model Tier Router<br/>(Tier A: Sonnet/Pro/GPT-4o vs Tier B: Haiku/Flash/Mini)"]
  end

  subgraph Concurrent Sandboxed Worktrees
    TR --> WT1["Worktree 1 (.nb/workspaces/provider_dev): agent_provider_developer"]
    TR --> WT2["Worktree 2 (.nb/workspaces/consumer_dev): agent_consumer_developer"]
    WT1 --> G1["Provider Gate (FastAPI / Contract Unit Tests)"]
    WT2 --> G2["Consumer Gate (Client / Interface Contract Tests)"]
  end

  G1 --> CCG{"Cross-Module Compatibility Gate (gate_cross_module_compatibility)"}
  G2 --> CCG
  
  subgraph End-to-End Emulation Bridge
    CCG --> SIM["Cross-Module Simulator Loopback Bridge:<br/>Consumer Simulator <--> Virtual Provider Loopback Mock"]
    SIM --> SIM_PASS{E2E Tests Pass?}
  end

  SIM_PASS -- Yes --> DOC["Living Documentation Agent (agent_living_doc_architect)<br/>AST Introspection & Mermaid Synthesis into workplace/docs/"]
  SIM_PASS -- "Poisoning Detected in Consumer" --> SRM["Surgical Rollback: Rewind Consumer to RP_CONS_k<br/>Provider Service remains untouched!<br/>Quarantine culprit in user/hitl/poisoning_quarantine.md"]
  SRM --> WT2

  DOC --> E["Atomic Merge to main & Log Multi-Module Recovery Point (RP_SYS_k)"]
  E --> F["Reconcile Master Context Ledger & Merkle Block Chaining"]
  F --> G["Multi-Dimensional Context Maturity & Multi-Module Dashboard<br/>(user/outputs/dashboard/index.html)"]
  G --> H{Final Gate Passed?}
  H -- Yes --> K["Release Manifest & Deployment Bundles in user/outputs/"]
```

---


### Contract & Artifact Standardization Governance Protocol

To guarantee that autonomous multi-agent pipelines execute without data corruption, runtime hallucination, or contract drift, the framework enforces strict **Contract & Artifact Standardization Rules**:

#### 1. Wire Contract Standardization Rules (`.nb/context/contracts/`)
1. **Formal Schema Standards**: All interface contracts between modules, agents, and external systems must be authored in `.nb/context/contracts/` using formal schema standards:
   - **JSON Schema (Draft-07 / 2020-12)** for data structures, DTOs, AST exchange envelopes, and configuration schemas (`*.json`).
   - **OpenAPI 3.1** for synchronous RESTful API endpoints, request/response models, and status codes (`*.yaml`).
   - **AsyncAPI 3.0** for event-driven message brokers, WebSockets, Kafka topics, and stream payloads (`*.yaml`).
   - **Protocol Buffers (Proto3)** for binary RPC communication and high-throughput serialization (`*.proto`).
2. **Mandatory Contract Metadata**: Every contract file must contain top-level metadata:
   - `contract_id`: Unique identifier (e.g., `audio_manifest_segment_contract`, `lsp_protocol_contract`).
   - `schema_version`: Semantic version string adhering to SemVer (`MAJOR.MINOR.PATCH`).
   - `contract_type`: `data_schema` | `api_rest` | `event_stream` | `rpc_protobuf` | `ast_envelope`.
   - `governing_rules`: Array of relative paths to invariant rules in `.nb/context/rules/` that govern this contract.
3. **Immutability & SemVer Breaking Change Policy**:
   - Minor enhancements (additive, non-breaking optional fields) increment `MINOR` version.
   - Any field deletion, type alteration, or constraint tightening increments `MAJOR` version and requires explicit deprecation cycles.
   - PR Gatekeeper **Stage 2** (`gate_cross_module_compatibility`) automatically executes schema diff validation; breaking changes without migration adapters fail the build immediately.

#### 2. Workflow Artifact Standardization Rules
1. **Deterministic Artifact Taxonomy**: Every workflow step must declare and emit standardized, verifiable artifacts written to canonical directory targets:
   - **Source Code & Binary Outputs**: `workplace/modules/<module_id>/src/` or `workplace/src/`
   - **Living Documentation Artifacts**: `workplace/docs/` (`<domain>_architecture.md`, `<domain>_sequence.md`, `<domain>_data_flow.md`, `<domain>_entity_relation.md`, `<domain>_contracts_registry.md`)
   - **Verification & Test Receipts**: `workplace/modules/<module_id>/tests/` and `.nb/context/ledger/test_receipts/`
   - **Cryptographic State Anchors**: `.nb/context/ledger/context_ledger.yaml` (sealed Merkle recovery points `RP_<domain>_<k>`)
2. **Upstream-to-Downstream Consumption Guarantees**:
   - A successor agent must NEVER guess or infer the location or format of an upstream artifact.
   - Every workflow step explicitly enumerates `inputs` (referencing contract IDs and upstream step output names) and `outputs` (referencing standardized artifact names).
   - Before executing a step, the `WorkflowEngine` validates that all declared `inputs` exist on disk and satisfy their corresponding contract schemas via cryptographic HMAC-SHA256 `HandoffToken` verification.

---

### Topological Predecessor-Successor Execution & Embedded Agent Architecture

#### 1. Declarative Workflow DAG Specification
All workflow definitions located in `.nb/agentic/custom/workflows/` (and embedded within layered domain plans) adhere to the following declarative schema:

```yaml
workflow_id: "wf_<domain>_<lifecycle>"
name: "Domain Lifecycle & Verification Flow"
description: "Detailed description of multi-stage execution pipeline"
steps:
  - step_id: "step_initialize_domain"
    executor: "agent_<domain>_architect"
    action: "validate_domain_manifest_and_contracts"
    inputs: [".nb/context/contracts/<domain>_contract.json"]
    outputs: ["validated_manifest_receipt", "domain_ast_symbol_table"]
    depends_on: [] # Root entry point

  - step_id: "step_implement_core_logic"
    executor: "agent_<domain>_specialist"
    action: "synthesize_domain_implementation"
    inputs: [".nb/context/contracts/<domain>_contract.json", "validated_manifest_receipt", "domain_ast_symbol_table"]
    outputs: ["compiled_source_modules", "unit_test_receipts"]
    depends_on: ["step_initialize_domain"]

  - step_id: "step_update_living_docs"
    executor: "agent_living_doc_architect"
    action: "synthesize_domain_docs_and_mermaid_models"
    inputs: ["compiled_source_modules", "validated_manifest_receipt"]
    outputs: ["workplace_docs_updated"]
    depends_on: ["step_implement_core_logic"]

  - step_id: "step_merkle_block_seal"
    executor: "platform.merkle_ledger"
    action: "append_block_and_seal_recovery_point"
    inputs: ["workplace_docs_updated", "unit_test_receipts"]
    outputs: ["merkle_block_sealed"]
    depends_on: ["step_update_living_docs"]
```

#### 2. Automatic Topological DAG Resolution
The `WorkflowEngine` executes Kahn’s algorithm to analyze and validate workflow execution trees:
1. **Acyclicity Assertion**: Validates that no cyclic dependencies exist ($\mathcal{O}(V + E)$).
2. **Predecessor & Successor Resolution**: Automatically computes the explicit `_predecessors` (via `depends_on`) and `_successors` (via adjacency inverse mapping) for every step.
3. **Execution Depth & Concurrency Partitioning**: Assigns topological depth indices to each step, allowing independent parallel subagent tasks at the same depth to execute concurrently within isolated worktrees (`.nb/workspaces/subagent_<id>/`).
4. **Contract-Bound Handoffs**: Maps predecessor output artifacts directly to successor input parameters, verifying schema conformity before triggering successor agents.

#### 3. Co-Located & Embedded Agent Specifications
Every executor referenced in a workflow must be specified in the plan’s co-located agent directory (`.nb/plan/agents/<agent_id>.yaml`) and embedded in Section 3 of the plan. When a layer is applied via `./.nb/bin/percipience layer apply`, the hydration engine automatically instantiates these agents into `.nb/agentic/custom/agents/` with full role, model tier (`tier_a` vs `tier_b`), sandboxed worktree, module scope, and specialized tool bindings.

---

### Living Documentation Autonomous Generation Engine (`workplace/docs/`)

To ensure that living documentation never goes stale, every workflow includes an autonomous documentation generation step executed by `agent_living_doc_architect`. During each workflow run, the documentation engine introspects the codebase AST, wire contracts, and execution traces to produce or update 5 standardized visual documents in `workplace/docs/`:

1. **System Architecture C4 Model (`workplace/docs/<domain>_architecture.md`)**:
   - System context, container, and component breakdown.
   - Rendered using Mermaid `graph TD` / `graph LR` showing module boundaries, ports, and protocol bindings.
2. **Runtime Sequence Flow (`workplace/docs/<domain>_sequence.md`)**:
   - Chronological step-by-step request/response and event messaging flows across subagents, modules, and daemons.
   - Rendered using Mermaid `sequenceDiagram` with numbered transactions.
3. **Data Flow & Contract Exchange DAG (`workplace/docs/<domain>_data_flow.md`)**:
   - Visual map of data pipelines, stream transformations, AST token pruners, and wire contract handoffs.
   - Rendered using Mermaid `flowchart LR` showing data schemas and throughput benchmarks.
4. **Entity-Relationship & State Ontology (`workplace/docs/<domain>_entity_relation.md`)**:
   - Structural data schemas, relational entities, DDL tables, or state transition automata.
   - Rendered using Mermaid `erDiagram` or `stateDiagram-v2`.
5. **Contract & Artifact Registry (`workplace/docs/<domain>_contracts_registry.md`)**:
   - Machine-readable catalog linking all wire contracts (`.nb/context/contracts/`), safety rules (`.nb/context/rules/`), and workflow artifacts with version numbers and validation hashes.

### File Structure (Dual-Mode Comparison)

#### When `project.mode: single_module` (Preserving Simplicity)
```
.
├── .percipience/
│   └── parent_master.nbpack                  # Sealed, obfuscated binary envelope (AES-256-GCM)
├── .nb/                                      # [PLATFORM AGENTIC CI/CD SYSTEM]
│   ├── bin/
│   │   └── percipience                       # Unified Agentic CI/CD CLI & Gatekeeper
│   ├── config/                               # Platform Configurations
│   │   ├── billing_plans.yaml                # Tier definitions & developer seat quotas
│   │   ├── byor_config.json                  # Multi-VCS BYOR Adapter config
│   │   ├── issue_tracker_mcp.yaml            # Jira / Linear MCP binding config
│   │   └── token_compression_rules.yaml      # AST pruning, log slicing & attention budget rules
│   ├── core/                                 # Platform Engines (38 Python Modules)
│   │   ├── ast_optimizer.py                  # Structural AST skeletonizer
│   │   ├── autonomous_cicd.py                # Self-sustaining CI/CD Triad
│   │   ├── living_doc_engine.py              # In-workflow AST living doc generator
│   │   ├── merkle_engine.py                  # SHA-256 Merkle DAG state ledger
│   │   ├── token_tracker.py                  # Real-time token FinOps & 15% rev-share
│   │   └── workflow_orchestrator.py          # Parallel Fan-Out/In DAG engine
│   ├── scripts/
│   │   └── install_git_hook.sh               # Pre-commit hook invoking .nb/bin/percipience
│   ├── tests/                                # Platform CI/CD Verification Suites
│   │   ├── test_agentic_sdlc_suite.py        # Swarm, workflows, and error recovery tests
│   │   ├── test_living_doc_engine.py         # Doc generator & Mermaid syntax tests
│   │   ├── test_request_formalizer.py        # Unstructured input ingestion tests
│   │   ├── test_section_16_1_suite.py        # OTel GenAI telemetry & cache tests
│   │   └── test_section_17_3_suite.py        # Red-team fuzzing & attention budget tests
│   ├── context/                              # [OBFUSCATED / RAM-HYDRATED ENCLAVE - Sealed in .nbpack]
│   │   ├── ledger/
│   │   │   ├── context_ledger.yaml           # Internal Merkle DAG ledger (RAM-enclave)
│   │   │   ├── context_ledger.public.yaml    # Client-facing sanitized status projection
│   │   │   └── token_savings_ledger.yaml     # Real-time AST token FinOps ledger
│   │   ├── schemas/                          # Sealed validation schemas (RAM-enclave)
│   │   └── reports/context_maturity_report_template.md
│   ├── agentic/                              # [OBFUSCATED / RAM-HYDRATED ENCLAVE - Sealed in .nbpack]
│   │   ├── prompts/                          # Serialized & AST-mangled prompt bytecode
│   │   ├── workflows/                        # Serialized orchestration workflows
│   │   ├── methodologies/                    # Proprietary agentic heuristics & playbooks
│   │   └── runtime/                          # Declarative runtime schemas & facades
│   ├── keys/                                 # Cryptographic keys (Ed25519, AES-256)
│   ├── plan/                                 # Governing master & free plans
│   └── tools/                                # Bundle compiler and packaging tools
├── workplace/                                # [PROJECT-SPECIFIC SOURCE & LAYERED PLANS]
│   ├── config/
│   │   └── site_config.yaml                  # Project application configuration
│   ├── docs/                                 # Living documentation & visual models
│   │   ├── README.md                         # Documentation index & guide
│   │   ├── architecture.md                   # System C4 & component diagrams (Mermaid)
│   │   ├── module_catalog.md                 # Public interface catalog & exports
│   │   ├── sequence_flows.md                 # Runtime execution sequence flows (Mermaid)
│   │   ├── data_flow.md                      # Data pipelines & event streams (Mermaid)
│   │   ├── entity_relationship.md            # Schema ER diagrams (Mermaid erDiagram)
│   │   └── domain_extensions.md              # Active layered domain deep-dive docs
│   ├── src/                                  # Project application source code
│   ├── include/                              # Project header files / stubs
│   └── tests/                                # Project-specific test suites
└── user/                                     # [CLIENT-ACCESSIBLE / USER ENCLAVE]
    ├── inputs/                               # MVS specifications & requirements
    ├── hitl/                                 # Human-In-The-Loop logs & quarantines
    └── outputs/                              # Maturity scorecards & visual dashboard
```

#### When `project.mode: multi_module` (Poly-Module Ecosystem)
```
.
├── .percipience/
│   └── parent_master.nbpack                  # Sealed, obfuscated binary envelope (AES-256-GCM)
├── .nb/                                      # [PLATFORM AGENTIC CI/CD SYSTEM]
│   ├── bin/
│   │   └── percipience                       # Unified Agentic CI/CD CLI & Gatekeeper
│   ├── config/                               # Platform Configurations
│   │   ├── billing_plans.yaml                # Free & Paid tier configuration
│   │   ├── byor_config.json                  # Multi-VCS BYOR Adapter config
│   │   ├── issue_tracker_mcp.yaml            # Issue tracker MCP binding config
│   │   └── token_compression_rules.yaml      # AST pruning, log slicing & attention budget rules
│   ├── core/                                 # Platform Engines (38 Python Modules)
│   │   ├── ast_optimizer.py                  # Structural AST skeletonizer
│   │   ├── autonomous_cicd.py                # Self-sustaining CI/CD Triad
│   │   ├── living_doc_engine.py              # In-workflow AST living doc generator
│   │   ├── merkle_engine.py                  # SHA-256 Merkle DAG state ledger
│   │   ├── token_tracker.py                  # Real-time token FinOps & 15% rev-share
│   │   └── workflow_orchestrator.py          # Parallel Fan-Out/In DAG engine
│   ├── scripts/
│   │   └── install_git_hook.sh               # Pre-commit hook invoking .nb/bin/percipience
│   ├── tests/                                # Platform CI/CD Verification Suites
│   │   ├── test_agentic_sdlc_suite.py        # Swarm, workflows, and error recovery tests
│   │   ├── test_living_doc_engine.py         # Doc generator & Mermaid syntax tests
│   │   ├── test_request_formalizer.py        # Unstructured input ingestion tests
│   │   ├── test_section_16_1_suite.py        # OTel GenAI telemetry & cache tests
│   │   └── test_section_17_3_suite.py        # Red-team fuzzing & attention budget tests
│   ├── context/                              # [OBFUSCATED / RAM-HYDRATED ENCLAVE - Sealed in .nbpack]
│   │   ├── ledger/
│   │   │   ├── context_ledger.yaml           # Federated multi-module state DAG (RAM-enclave)
│   │   │   ├── context_ledger.public.yaml    # Client-facing sanitized status projection
│   │   │   ├── token_savings_ledger.yaml     # Real-time AST token FinOps ledger
│   │   │   ├── self_improving_ledger.yaml    # Closed-loop autonomous telemetry ledger
│   │   │   └── archive/                      # Rolling Merkle epoch checkpoint archives
│   │   │       └── epoch_0000_0087.json      # Sealed cryptographic historical epochs
│   │   ├── contracts/                        # Cross-module interface specifications
│   │   │   ├── service_contract.yaml         # Shared API specifications & endpoint contracts
│   │   │   ├── event_stream_spec.yaml        # Async event stream schema (AsyncAPI)
│   │   │   └── common_schema.json            # Shared entity and DTO schemas
│   │   ├── schemas/                          # Sealed validation schemas (RAM-enclave)
│   │   │   ├── context_ledger_schema.yaml
│   │   │   ├── recovery_point_schema.yaml
│   │   │   └── ledger_chain_schema.yaml
│   │   └── reports/context_maturity_report_template.md
│   ├── agentic/                              # [OBFUSCATED / RAM-HYDRATED ENCLAVE - Sealed in .nbpack]
│   │   ├── prompts/                          # Serialized & AST-mangled prompt bytecode
│   │   ├── workflows/                        # Serialized orchestration workflows
│   │   │   ├── cross_module_orchestrator.yaml
│   │   │   ├── pr_gatekeeper.yaml            # 6-Stage PR verification gatekeeper DAG
│   │   │   └── model_tiering_router.yaml
│   │   ├── methodologies/                    # Proprietary agentic heuristics & playbooks
│   │   ├── runtime/                          # Declarative runtime schemas & facades
│   │   └── custom/agents/                    # Autonomous CI/CD Specialist Agent Plugins
│   │       ├── flaky_test_detector.yaml      # Test stabilization & quarantine guard
│   │       ├── contract_compatibility_checker.yaml # SemVer wire contract guard
│   │       ├── dependency_cve_sentinel.yaml  # Supply-chain security sentinel
│   │       ├── doc_drift_synchronizer.yaml   # Blueprint documentation sync guard
│   │       └── agent_living_doc_architect.yaml# In-workflow living doc & Mermaid visualizer
│   ├── keys/                                 # Cryptographic keys (Ed25519, AES-256)
│   ├── plan/                                 # Governing master & free plans
│   └── tools/                                # Verification & bundle compiler tools
├── workplace/                                # [PROJECT-SPECIFIC SOURCE & LAYERED PLANS]
│   ├── config/                               # Project-Specific Configuration
│   │   ├── site_config.yaml                  # SaaS Portal Web configuration
│   │   └── tailwind.config.ts                # Marketing & Portal styling config
│   ├── shared/                               # Cross-boundary protocols and generated types
│   │   ├── protos/
│   │   └── generated/
│   ├── modules/                              # Layered Plan Domain Modules
│   │   ├── mod_service_provider/             # Backend Core Provider Service module
│   │   │   ├── config/                       # Database, service ports, auth configs
│   │   │   ├── src/                          # Service business logic & REST/gRPC handlers
│   │   │   └── tests/                        # Unit & contract test fixtures
│   │   ├── mod_service_consumer/             # Downstream Consumer / Client module
│   │   │   ├── config/                       # Client bundle settings, route config
│   │   │   ├── src/                          # Client interface, API client adapters
│   │   │   └── tests/                        # Component & contract integration tests
│   │   ├── mod_intellij_plugin/              # JetBrains IDE integration module
│   │   └── mod_vscode_extension/             # VSCode LSP & extension module
│   ├── portal/                               # Project Web Portal backend (server.py)
│   ├── src/                                  # Project Web Frontend (components, styles, pages)
│   ├── templates/                            # Project Test Mocks & Bridge Emulators
│   │   ├── packaging/                        # Plan packaging templates
│   │   ├── bridge/                           # Virtual simulation loopback bridge
│   │   ├── concurrency/                      # Worktree templates
│   │   └── recovery/                         # Recovery templates
│   ├── docs/                                 # Living visual documentation
│   │   ├── README.md                         # Documentation index & map
│   │   ├── architecture.md                   # System C4 topologies & component graphs (Mermaid)
│   │   ├── module_catalog.md                 # Poly-module interface & API catalog
│   │   ├── sequence_flows.md                 # Runtime sequence diagrams (Mermaid)
│   │   ├── data_flow.md                      # Data pipeline & event stream DAGs (Mermaid)
│   │   ├── entity_relationship.md            # Schema ER diagrams (Mermaid erDiagram)
│   │   ├── domain_extensions.md              # Active layered domain deep-dive docs
│   │   └── parent_context_engineering_guide.md
│   └── tests/                                # Project-Specific Domain Test Suites
│       ├── test_cross_module_e2e.py          # End-to-end integration tests
│       ├── test_ide_plugins_space.py         # JetBrains & VSCode plugin tests
│       ├── test_play3_suite.py               # Comprehensive subsystem integration
│       └── test_portal_observability_auth.py # Web portal & auth tests
└── user/                                     # [CLIENT-ACCESSIBLE / USER ENCLAVE]
    ├── inputs/
    │   ├── provider_module_mvs_spec.yaml
    │   └── consumer_module_mvs_spec.yaml
    ├── hitl/
    │   ├── clr_sample_request.md
    │   ├── poisoning_quarantine.md
    │   └── flaky_quarantine.yaml             # Isolated intermittent non-blocking tests
    └── outputs/
        ├── context_maturity_report.md
        ├── eval_report.json
        ├── release_manifest.json
        └── dashboard/
            ├── index.html                    # Visual DAG with multi-module node clustering
            ├── app.js
            └── style.css
```

### Architectural Separation: Agentic CI/CD Platform System vs. Project-Specific Layered Plans

A fundamental architectural mandate of the Percipience framework is the complete decoupling between the **Platform Agentic CI/CD System** and **Project-Specific Layered Plans**:

1. **The Platform Agentic CI/CD System (`.nb/`)**:
   - **Scope**: Contains the parent operating system, the 38 Python execution engines (`.nb/core/`), platform configuration files (`.nb/config/`), the unified CLI (`.nb/bin/percipience`), cryptographic Merkle state ledgers (`.nb/context/ledger/`), wire contracts (`.nb/context/contracts/`), prompt and workflow suites (`.nb/agentic/`), CI/CD git hooks (`.nb/scripts/`), and platform verification test suites (`.nb/tests/`).
   - **Invariance**: Contains **zero application-specific business logic**. It provides general-purpose context optimization, AST skeletonization, Merkle integrity verification, token FinOps accounting, autonomous self-healing, and PR gatekeeping for any software codebase.
   - **Canonical Execution**: Invocable from the repository root exclusively via `./.nb/bin/percipience`, with all symbolic links completely eliminated across the workspace to preserve absolute deterministic execution across platforms.

2. **Project-Specific Layered Plans (`workplace/`)**:
   - **Scope**: Strictly houses customer application source code, domain-specific modules (`workplace/modules/`), SaaS web portals (`workplace/portal/`), UI frontends (`workplace/src/`), project configurations (`workplace/config/site_config.yaml`, `workplace/config/tailwind.config.ts`), shared cross-boundary schemas (`workplace/shared/`), living documentation (`workplace/docs/`), and application domain test suites (`workplace/tests/`).
   - **Isolation**: Layered plan files must never import or implement platform engines directly into `workplace/`. Instead, layered applications interact with the platform through standardized contracts (`.nb/context/contracts/`), CLI invocations (`.nb/bin/percipience`), or declarative facade imports.

3. **User Enclave (`user/`)**:
   - Houses developer requirements, unstructured specifications, and Jira inputs (`user/inputs/`), human-in-the-loop audit logs and quarantined tests (`user/hitl/`), and compiled visual artifacts including the HTML DAG dashboard and maturity reports (`user/outputs/`).

### IntelliJ IDEA & PyCharm Plugin Integration & Free Community Tier Bundling

The framework integrates natively with JetBrains IDEs via the `mod_intellij_plugin` module, providing developers with zero-friction onboarding, live execution, and sandbox governance aligned with `.nb/config/billing_plans.yaml`:

1. **Free Community Tier (`plan_free`) Asset Bundling**:
   - The plugin distribution (`.nb/bundles/percipience-intellij-plugin-1.0.0.zip`) directly packages canonical platform templates under its internal JAR resources (`percipience/`):
     - `bin/percipience`: Canonical CLI binary orchestrator and gatekeeper.
     - `config/billing_plans.yaml`: Free Community tier configuration enabling AST token pruning, Merkle chain audit, and basic autonomous CI/CD (1 seat, 1 worktree, 500 PR audits/mo).
     - `config/token_compression_rules.yaml`: AST skeletonization rules preserving function/class signatures while stripping internal implementations.
     - `workflows/basic_autonomous_cicd.yaml`: Free edition self-healing continuous delivery workflow.
     - `plan/claude-context-engineering-parent-master-free_plan.md`: Free community master plan template.
2. **Automated New Workspace Detection & Interactive Startup Prompt**:
   - `PercipienceProjectStartupActivity` (implementing `com.intellij.openapi.startup.ProjectActivity`) runs automatically upon project opening.
   - If the workspace lacks `.nb/bin/percipience`, `.nb/config/billing_plans.yaml`, or `.nb/context/ledger/context_ledger.yaml`, it raises a non-intrusive interactive balloon notification prompting the user: `"🚀 Initialize Free Workspace"`.
   - Bootstrapping unpacks all essential templates, ensures `0755` executable permissions on `.nb/bin/percipience`, scaffolds the standard Quad-Space directories, and initializes the Genesis Merkle block (`RP_GENESIS_000`).
3. **Asynchronous Process Execution Service (`PercipienceExecutionService`)**:
   - Project-level service that automatically locates Python 3 (`.venv`, `venv`, Homebrew, system) and executes `.nb/bin/percipience` CLI subcommands (`gate`, `audit`, `cicd run`, `validate --layered`, `tokens summary`).
   - Streams live output asynchronously, tracks exit codes, and triggers `VirtualFileManager.asyncRefresh()` to sync modified files with the IDE in real time.
4. **Interactive Control Plane & Tools Menu**:
   - The Percipience Tool Window and `Tools -> Percipience OS` menu expose buttons directly invoking the execution service with background progress indicators and desktop notifications.
5. **Zero Symlinks Invariant**:
   - All symbolic links (`bin/percipience`, `workplace/bin/percipience`, etc.) have been removed repository-wide.
   - `./.nb/bin/percipience` serves as the sole, canonical executable platform binary across all tools, scripts, workflows, and IDE actions.

---

### Comprehensive Component Inventory & Production Manifest

To guarantee enterprise rigor and zero ambiguity, every architectural component specified across the 21 core capabilities (`CAP-01`..`CAP-27`) is enumerated below with its intended Quad-Space location. The **Target State** column reflects the planned lifecycle stage for each artifact (`Planned | Scaffolded | Implemented | Verified`); because this is a design document, most artifacts are `Planned` until validated by the benchmark and test harness (see *Benchmark & Metrics Provenance* below). It must not be read as an assertion that the component is already built and verified.

| Space | Subsystem / Component | Path | Format & Engine | Verification Mechanism | Target State |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`context/`** | Master State Ledger | `.nb/context/ledger/context_ledger.yaml` | YAML Merkle DAG | SHA-256 Block Chaining (`ledger_chain_verifier.py`) | **Planned (sealed in .nbpack enclave)** |
| **`context/`** | Public Sanitized Projection | `.nb/context/ledger/context_ledger.public.yaml` | YAML Status View | Masked state projection | **Planned (Public projection)** |
| **`context/`** | Master Ledger Schema | `context/schemas/context_ledger_schema.yaml` | JSON Schema Draft-07 | Syntax & Schema Validation | **Planned (sealed in .nbpack enclave)** |
| **`context/`** | Recovery Point Schema | `context/schemas/recovery_point_schema.yaml` | JSON Schema Draft-07 | Snapshot Contract Validation | **Planned (sealed in .nbpack enclave)** |
| **`context/`** | Ledger Block Chain Schema | `context/schemas/ledger_chain_schema.yaml` | JSON Schema Draft-07 | Merkle Header Conformance | **Planned (sealed in .nbpack enclave)** |
| **`context/`** | Cross-Module Service Contract | `.nb/context/contracts/service_contract.yaml` | YAML OpenAPI Contract | `gate_cross_module_compatibility` | **Planned (sealed in .nbpack enclave)** |
| **`context/`** | Cross-Module Event Spec | `.nb/context/contracts/event_stream_spec.yaml` | AsyncAPI YAML Contract | Payload & Event Validation | **Planned (sealed in .nbpack enclave)** |
| **`context/`** | Cross-Module Entity Schema | `.nb/context/contracts/common_schema.json` | JSON Schema Contract | Schema Compatibility Check | **Planned (sealed in .nbpack enclave)** |
| **`context/`** | Maturity Report Template | `.nb/context/reports/context_maturity_report_template.md`| Markdown Template | 6-Dimensional Score Evaluation | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Master System Prompt | `agentic/prompts/system_prompt.md` | Markdown Prompt | Quad-Space Invariant Assertion | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Bootstrapping Prompt | `agentic/prompts/bootstrapping_prompt.md` | Markdown Prompt | Dual-Mode Folder Scaffolding | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Derivation Metaprompt | `agentic/prompts/derivation_prompt.md` | Markdown Prompt | MVS ASG Synthesizer | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Evaluation & Refinement Prompt | `agentic/prompts/evaluation_refinement_prompt.md` | Markdown Prompt | Scorecard Generator | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Lifecycle Delivery Prompt | `agentic/prompts/lifecycle_delivery_prompt.md` | Markdown Prompt | Release Manifest Sealer | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Worktree Orchestration Prompt | `agentic/prompts/workflow_orchestration_prompt.md` | Markdown Prompt | Ephemeral Subagent Lease Gate | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Cross-Module Orchestrator | `.nb/agentic/workflows/cross_module_orchestrator.yaml` | YAML Workflow DAG | Multi-Module Compatibility Check | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Model Tiering Router | `.nb/agentic/workflows/model_tiering_router.yaml` | YAML Policy | Frontier vs. Fast Model Routing | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Jira / Linear MCP Sync Workflow | `.nb/agentic/workflows/issue_tracker_sync_workflow.yaml`| YAML Workflow | Model Context Protocol Tool Call | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Zero-Drift Engineering Rules | `agentic/methodologies/zero_drift_rules.md` | Markdown Heuristic | AST Spec-to-Code Parity Gate | **Planned (sealed in .nbpack enclave)** |
| **`agentic/`** | Poisoning Defense Playbook | `agentic/methodologies/poisoning_defense_playbook.md`| Markdown Heuristic | 4-Step Remediation Protocol | **Planned (sealed in .nbpack enclave)** |
| **`workplace/`**| Master Project Configuration | `workplace/config/site_config.yaml` | YAML Config | Dual-Mode Module Registry | **Planned** |
| **`.nb/`**     | Token Compression Rules | `.nb/config/token_compression_rules.yaml` | YAML Config | AST Pruner & Cache Alignment | **Planned** |
| **`.nb/`**     | Issue Tracker MCP Config | `.nb/config/issue_tracker_mcp.yaml` | YAML Config | Jira MCP Server Binding | **Planned** |
| **`workplace/`**| Plan Pack Compiler | `workplace/templates/packaging/plan_pack_compiler.py` | Python 3 CLI | Ed25519 / AES-256-GCM Packaging | **Planned** |
| **`workplace/`**| Enclave Runtime Hydrator | `workplace/templates/packaging/envelope_hydrator.py` | Python 3 CLI | RAM-Enclave Memory Hydration | **Planned** |
| **`workplace/`**| Virtual Service Loopback Bridge | `workplace/templates/bridge/virtual_service_bridge.py` | Python 3 Async Socket| Local Virtual Integration Loopback | **Planned** |
| **`workplace/`**| Mock Service Daemon Emulator | `workplace/templates/bridge/mock_service_daemon.py` | Python 3 Daemon | Synthetic Service Telemetry Stream | **Planned** |
| **`workplace/`**| Worktree Lease Manager | `workplace/templates/concurrency/worktree_manager.py`| Python 3 CLI | Ephemeral Worktree Provisioning | **Planned** |
| **`workplace/`**| Atomic Verification Gate Merger | `workplace/templates/concurrency/atomic_gate_merger.py`| Python 3 CLI | Gate Enforcement & Git Atomic Merge| **Planned** |
| **`workplace/`**| Surgical Rollback Manager | `workplace/templates/recovery/surgical_rollback_manager.py`| Python 3 CLI | Module-Scoped State Rewind | **Planned** |
| **`workplace/`**| Ledger Chain Cryptographic Verifier| `workplace/templates/recovery/ledger_chain_verifier.py`| Python 3 CLI | SHA-256 Merkle Block Continuity | **Planned** |
| **`user/`** | MVS Feature Spec Template | `user/inputs/templates/mvs_feature_spec.md` | Markdown + Gherkin | MVS Ingestion Pipeline | **Planned** |
| **`user/`** | MVS OpenAPI Contract Template | `user/inputs/templates/mvs_api_contract.yaml` | OpenAPI 3.1 YAML | Schema Validation & Stub Codegen | **Planned** |
| **`user/`** | MVS Event Stream Template | `user/inputs/templates/mvs_event_stream.yaml` | AsyncAPI 3.0 YAML | Pub/Sub Topic & Payload Linting | **Planned** |
| **`user/`** | MVS ADR Blueprint Template | `user/inputs/templates/mvs_adr_blueprint.md` | Markdown + Mermaid | Architectural Constraint Engine | **Planned** |
| **`user/`** | MVS Jira Story JSON Template | `user/inputs/templates/mvs_jira_story.json` | JSON Schema Interchange | Jira MCP Ingestion Engine | **Planned** |
| **`user/`** | MVS UI Design Tokens Template | `user/inputs/templates/mvs_design_tokens.json` | JSON Design System | WCAG 2.1 AA Contrast Auditing | **Planned** |
| **`user/`** | Context Poisoning Quarantine Log | `user/hitl/poisoning_quarantine.md` | Markdown Quarantine | HITL Inspection Protocol | **Planned** |
| **`user/`** | Clarification Sample Request | `user/hitl/clr_sample_request.md` | Markdown Clarification | Operator Disambiguation Gate | **Planned** |
| **`user/`** | Visual DAG & Time-Travel Console | `user/outputs/dashboard/index.html` | HTML5 / CSS3 / JS | Static Browser Visualization | **Planned** |
| **`user/`** | Visual DAG Frontend Controller | `user/outputs/dashboard/app.js` | Vanilla ES6 JavaScript | Real-time Merkle Node Explorer | **Planned** |
| **`user/`** | Visual DAG Dark-Mode Styling | `user/outputs/dashboard/style.css` | Modern CSS Grid / Flex | Responsive Dashboard Styling | **Planned** |
| **`.nb/`**     | Autonomous CI/CD Triad Engine | `.nb/core/autonomous_cicd.py` | Python 3 Module | Self-Sustaining, Self-Recovering, Self-Improving | **Planned** |
| **`.nb/`**     | Agent Plugin Engine | `.nb/core/agent_plugin_engine.py` | Python 3 Module | Custom Plugin Lifecycle & Merkle Sealing | **Planned** |
| **`.nb/`**     | Token FinOps & Savings Tracker | `.nb/core/token_tracker.py` | Python 3 Module | Real-time AST Token Metering & 15% Rev-Share | **Planned** |
| **`.nb/`**     | Multi-VCS BYOR Remote Adapter | `.nb/core/byor_adapter.py` | Python 3 Module | SSH Key & Webhook Multi-Vendor VCS Bridge | **Planned** |
| **`.nb/`**     | 3-Tier Layered Context Validator | `.nb/core/layered_context_validator.py` | Python 3 Module | Platform Invariant Precedence Enforcement | **Planned** |
| **`workplace/`**| Observability Telemetry Gateway | `workplace/portal/server.py` | Python 3 HTTP Server | Observability REST APIs & Gateway Proxy | **Planned** |
| **`.nb/`**     | Living Documentation Engine | `.nb/core/living_doc_engine.py` | Python 3 Module | AST & Contract living docs & Mermaid visualizer | **Planned** |
| **`agentic/`** | Custom Agent Plugin Template | `agentic/templates/custom_agent_template.yaml` | YAML Specification | Standardized Healthy Plugin Schema | **Planned** |
| **`agentic/`** | Agent Plugin Architecture Guide | `workplace/docs/guides/AGENT_PLUGIN_GUIDE.md` | Markdown Specification | Healthy Integration Pattern Documentation | **Planned** |
| **`context/`** | Token Savings Ledger | `.nb/context/ledger/token_savings_ledger.yaml` | YAML Ledger | 15% Performance Fee & Savings Accounting | **Planned** |
| **`context/`** | Self-Improving Telemetry Ledger | `.nb/context/ledger/self_improving_ledger.yaml` | YAML Ledger | Closed-Loop Optimization History | **Planned** |
| **`.nb/`**     | Multi-Dimensional Token Optimizer Suite | `.nb/core/token_optimizer_suite.py` | Python 3 Module | 6D Token Compression & Slicing Suite | **Verified** |
| **`.nb/`**     | Diagnostic Re-Prompting Engine | `.nb/core/diagnostic_reprompt.py` | Python 3 Module | Tiered SLA Prompt Escalation & Auto-Heal | **Verified** |
| **`.nb/`**     | Cloud WORM Vault Mirror Egress | `.nb/core/worm_egress_manager.py` | Python 3 Module | S3 Object Lock & GCS SEC 17a-4 Compliance | **Verified** |
| **`user/`** | Autonomous CI/CD Strategic Roadmap| `workplace/docs/reports/autonomous_cicd_roadmap.md` | Markdown Blueprint | 4-Phase Autonomous Delivery Roadmap | **Planned** |
| **`user/`** | Benchmark Whitepaper (62% Savings)| `workplace/docs/reports/token_savings_whitepaper.md`| Markdown Document | Empirical FinOps Case Study & Cost Model | **Planned** |
| **`user/`** | Token Savings Scorecard Report | `workplace/docs/reports/token_savings_report.md` | Markdown Scorecard | Real-time Financial Metering Output | **Planned** |
| **`.nb/`**     | Unified CLI Control Plane | `.nb/bin/percipience` | Executable Shell / Python | Unified Subcommand Architecture | **Planned** |
| **`user/`** | Context Maturity Report | `workplace/docs/reports/context_maturity_report.md` | Markdown Scorecard | Quantitative 6-D Evaluation (0.95)| **Planned** |
| **`.nb/`**     | Model Cognitive Router | `.nb/core/cognitive_router.py` | Python 3 Module | Tier A / Tier B Model Dispatcher & FinOps Arbitrage | **Planned** |
| **`.nb/`**     | Flaky Test Isolation Engine | `.nb/core/flaky_test_detector.py` | Python 3 Module | Multi-run Test Stability & Non-blocking Quarantine | **Planned** |
| **`.nb/`**     | Contract Compatibility Checker | `.nb/core/contract_compatibility_checker.py` | Python 3 Module | SemVer & Wire Contract Backward-Compatibility Diff | **Planned** |
| **`.nb/`**     | Dependency CVE Sentinel | `.nb/core/dependency_cve_sentinel.py` | Python 3 Module | Supply-Chain Vulnerability & License Auditor | **Planned** |
| **`.nb/`**     | Doc Drift Synchronizer | `.nb/core/doc_drift_synchronizer.py` | Python 3 Module | AST Export vs Markdown Blueprint Sync | **Planned** |
| **`agentic/`** | Flaky Test Detector Manifest | `.nb/agentic/custom/agents/flaky_test_detector.yaml` | YAML Specification | Autonomous Flaky Test Isolation Guard | **Planned** |
| **`agentic/`** | Contract Checker Manifest | `.nb/agentic/custom/agents/contract_compatibility_checker.yaml` | YAML Specification | Wire Contract Evolution & SemVer Guard | **Planned** |
| **`agentic/`** | Dependency CVE Manifest | `.nb/agentic/custom/agents/dependency_cve_sentinel.yaml` | YAML Specification | Supply-Chain Security & License Sentinel | **Planned** |
| **`agentic/`** | Doc Drift Manifest | `.nb/agentic/custom/agents/doc_drift_synchronizer.yaml` | YAML Specification | Architectural Blueprint & Doc Drift Synchronizer | **Planned** |
| **`agentic/`** | Living Documentation Agent Manifest| `.nb/agentic/custom/agents/agent_living_doc_architect.yaml` | YAML Specification | In-workflow Living Documentation & Mermaid Visualizer | **Planned** |
| **`context/`** | Merkle Epoch Checkpoint Archives | `.nb/context/ledger/archive/epoch_*.json` | JSON Archive | Constant-size Active Window & Cryptographic Rollups | **Planned** |
| **`user/`** | Flaky Test Quarantine Registry | `user/hitl/flaky_quarantine.yaml` | YAML Registry | Non-blocking Flaky Test Isolation Store | **Planned** |
| **`workplace/`**| Living Architecture Document | `workplace/docs/architecture.md` | Markdown + Mermaid | System Topologies, Boundaries & C4 Components | **Planned** |
| **`workplace/`**| Poly-Module Interface Catalog | `workplace/docs/module_catalog.md` | Markdown + Mermaid | Module Inventory, Public APIs & Dependencies | **Planned** |
| **`workplace/`**| Runtime Sequence Flow Document | `workplace/docs/sequence_flows.md` | Markdown + Mermaid | Execution Sequences & Cross-Module Handshakes | **Planned** |
| **`workplace/`**| Data Flow & Pipeline Document | `workplace/docs/data_flow.md` | Markdown + Mermaid | Ingestion DAGs, Event Streams & State Machines | **Planned** |
| **`workplace/`**| Entity-Relationship Document | `workplace/docs/entity_relationship.md` | Markdown + Mermaid | DDL Relations, Data Models & Schema Mappings | **Planned** |
| **`workplace/`**| Domain Layer Extensions Document| `workplace/docs/domain_extensions.md` | Markdown + Mermaid | Active Layered Domain Deep Dive Visuals | **Planned** |
| **`.nb/`**     | Parallel Workflow Orchestrator | `.nb/core/workflow_orchestrator.py` | Python 3 Module | Concurrent Fan-Out & Barrier Sync DAG Engine | **Implemented** |
| **`.nb/`**     | Error Recovery Orchestrator | `.nb/core/error_recovery_orchestrator.py` | Python 3 Module | 4-Pillar Taxonomy & Adaptive Recovery Playbooks | **Implemented** |
| **`.nb/`**     | Prompt Drift Sentinel | `.nb/core/prompt_drift_sentinel.py` | Python 3 Module | SHA-256 Manifest & Prefix Pinning Auditor | **Implemented** |
| **`.nb/`**     | Swarm Governor & Authority Tree | `.nb/core/swarm_governor.py` | Python 3 Module | 4-Tier Authority & Anti-Usurpation Interceptor | **Implemented** |
| **`.nb/`**     | Adversarial Mutation Fuzzer | `.nb/core/adversarial_fuzzer.py` | Python 3 Module | Boundary & Security Injection Red-Team Fuzzer | **Implemented** |
| **`.nb/`**     | Context Attention Budgeter | `.nb/core/attention_budgeter.py` | Python 3 Module | 5-Slice Proportional Context Quota Enforcer | **Implemented** |
| **`.nb/`**     | Trajectory Recorder & Replayer | `.nb/core/trajectory_recorder.py` | Python 3 Module | ReAct Trajectory Serialization & Determinism Replay | **Implemented** |
| **`.nb/`**     | Ambiguity Resolver & RFC Engine | `.nb/core/ambiguity_resolver.py` | Python 3 Module | Requirement Entropy & HITL Clarification RFCs | **Implemented** |
| **`agentic/`** | Prompt SemVer Manifest | `agentic/prompts/prompt_manifest.yaml` | YAML Specification | Cryptographic Hash Baseline for All Prompts | **Implemented** |
| **`agentic/`** | Adversarial Fuzzer Agent Manifest | `.nb/agentic/custom/agents/agent_adversarial_fuzzer.yaml` | YAML Specification | Autonomous Red-Team Fuzzing Sentinel | **Implemented** |
| **`agentic/`** | Ambiguity Resolver Agent Manifest | `.nb/agentic/custom/agents/agent_ambiguity_resolver.yaml` | YAML Specification | Requirement Entropy & Ambiguity Gate Specialist | **Implemented** |
| **`platform`** | Standardized Integration Test Suite | `workplace/tests/test_play3_suite.py` | Python 3 Unittest | 17-Test Comprehensive End-to-End Suite | **Implemented** |
| **`.nb/`**     | Section 17.2 SDLC Test Suite | `.nb/tests/test_agentic_sdlc_suite.py` | Python 3 Unittest | 16-Test Swarm & Workflow Governance Suite | **Implemented** |
| **`.nb/`**     | Section 17.3 Cognitive Test Suite | `.nb/tests/test_section_17_3_suite.py` | Python 3 Unittest | 10-Test Fuzzing & Attention Budget Suite | **Implemented** |

---

# Testing

### Validation Approach
Verification is performed by executing the Parent Master Prompt Suite against synthetic single-module and multi-module MVS packages:
1. **Plan & Proprietary Space Obfuscation Verification Test**: Verify that compiling with `percipience pack --include-spaces context,agentic` produces an Ed25519-signed `.nbpack` bundle. Verify that initializing via `percipience init --parent-plan parent_master.nbpack` decrypts cleanly into RAM enclave without leaving plaintext markdown or YAML files for `context/` and `agentic/` on client disk.
2. **Single-Module Integrity Test**: Verify that initializing a single-module project produces zero nested folder bloat, uses flat `workplace/src/` and `workplace/config/`, and executes the complete lifecycle without multi-module overhead.
3. **Multi-Module Bootstrapping Test**: Initialize a multi-module project (`mode: multi_module`) with Provider Service and Consumer Module specs; verify deterministic creation of `.nb/context/contracts/`, `workplace/shared/`, and `workplace/modules/`.
4. **Cross-Module Contract Compatibility Gate Test**: Intentionally alter an endpoint payload schema in `service_contract.yaml`; verify `gate_cross_module_compatibility` flags the breaking change before merging.
5. **Surgical Rollback Isolation Test**: Introduce a context poisoning hallucination into the Consumer module; verify that only the Consumer module rolls back to its recovery point (`RP_CONS_004`), leaving the Provider Service builds (`RP_PROV_003`) completely untouched.
6. **Virtual Emulation Bridge Test**: Execute automated integration tests in `workplace/tests/integration/` where the client application simulator interacts with the mock service daemon over loopback, confirming request routing, payload rendering, and event streaming.
7. **Living Documentation & Mermaid Visualizer Verification Test**: Run `.nb/core/living_doc_engine.py` across derived multi-module repositories; verify that `workplace/docs/` contains complete, non-empty Markdown files (`architecture.md`, `module_catalog.md`, `sequence_flows.md`, `data_flow.md`, `entity_relationship.md`, `domain_extensions.md`), that all embedded Mermaid blocks pass syntax parsing, and that AST-to-doc hash synchronization avoids unnecessary token burn on unchanged files.
8. **Autonomous SDLC & Swarm Governance Verification Test**: Run `.nb/tests/test_agentic_sdlc_suite.py` to verify declarative Quad-Space facade boundaries, multi-threaded parallel fan-out/fan-in barriers with cycle detection, 4-pillar error recovery playbooks, prompt manifest cryptographic integrity, and 4-tier swarm authority anti-usurpation spawning constraints.
9. **Cognitive Attention, Prefix Pinning, Fuzzing & Ambiguity Verification Test**: Run `.nb/tests/test_section_17_3_suite.py` to verify adversarial red-team fuzzing resilience, 5-slice attention quota enforcement, static prefix pinning KV-cache compliance across all prompts, ReAct trajectory recording & replay determinism, and requirement ambiguity entropy scoring with interactive clarification RFC generation.
10. **All Core Capabilities**: Dynamic model cascading, bounded TDD self-healing, cryptographic Merkle ledger chaining, and visual DAG dashboard rendering.

---

# Delivery Steps

### Step 1: Define Parent Ledger Schema, Dual-Mode & Multi-Module Contracts
Establish the machine-readable YAML schemas for `context_ledger.yaml` supporting `mode: single_module | multi_module`, module registries, cross-module contracts, Merkle hash chaining, plan security parameters, and surgical recovery points.

- Define `context_ledger_schema.yaml` covering every section referenced by the `CAP-01`..`CAP-27` capabilities: `mcp_integrations`, `mode`, `modules`, `contracts`, `ledger_chain`, `plan_security`, `model_tiering_policy`, `token_optimization`, `worktrees`, `semantic_parity`, `quarantined_tests`, `recovery_points`, `poisoning_incidents`, `git_commits`, `remaining_issues`, `standard_issue_checklist`, plus the newer capability sections — `token_savings_ledger`, `self_improving_ledger`, `living_docs`, custom-agent/plugin registry, `layered_context` precedence policy, and forward-compatible `simulations` / `training_runs` blocks. The schema is validated against the `CAP` list in CI to prevent schema drift.
- Formulate cross-module contract specifications in `.nb/context/contracts/` (`service_contract.yaml`, `event_stream_spec.yaml`, `common_schema.json`).

### Step 2: Quad-Space Bootstrapping Metaprompt (Dual-Mode Aware)
Develop system and bootstrapping prompts establishing the Model-Agnostic Agentic Orchestrator's role (with Claude / Gemini / GPT as reference engines) supporting both single-module simplicity and poly-module coordination.

- Formulate `system_prompt.md` with zero-drift constraints, context poisoning defense rules, dual-mode execution rules, and Quad-Space registration rules.
- Draft `bootstrapping_prompt.md` dynamically creating flat folders for `single_module` or modular folder hierarchies for `multi_module`.

### Step 3: Develop Surgical Rollback Manager & Cross-Module Compatibility Gate
Build scripts and prompt handlers for module isolation and contract compatibility.

- Scaffold `surgical_rollback_manager.py` in `workplace/templates/recovery/`.
- Scaffold `gate_cross_module_compatibility` in `.nb/agentic/workflows/cross_module_orchestrator.yaml`.

### Step 4: Develop Cross-Module Simulation Loopback Bridge
Build virtual emulation bridges linking heterogeneous domain components.

- Scaffold `virtual_service_bridge.py` and `mock_service_daemon.py` in `workplace/templates/bridge/`.
- Wire up integration test runners in `workplace/tests/integration/`.

### Step 5: Develop Git Worktree Concurrency & Atomic Gate Merger Templates
Build scripts and prompt handlers for isolated concurrent subagent workflows across multiple modules.

- Scaffold `worktree_manager.py` and `atomic_gate_merger.py` in `workplace/templates/concurrency/`.

### Step 6: Develop Bounded TDD Self-Healing & Semantic Parity Engines
Build tools and prompt directives for bounded healing and anti-drift monitoring.

- Scaffold `bounded_tdd_healer.py` and `semantic_parity_checker.py` in `workplace/templates/healing/`.

### Step 7: Develop Cryptographic Ledger Chaining & Poisoning Recovery Engine
Build verification scripts and recovery handlers for state integrity.

- Scaffold `ledger_chain_verifier.py`, `recovery_point_manager.py`, and `context_poisoning_auditor.py` in `workplace/templates/recovery/`.

### Step 8: Formulate Visual DAG Dashboard Generator (Multi-Module Clustered)
Build the interactive time-travel dashboard engine rendering module clusters.

- Create `index.html`, `app.js`, and `style.css` templates under `user/outputs/dashboard/`.

### Step 9: Formulate Lifecycle Delivery & Multi-Agent Orchestration Metaprompt
Create incremental SDLC orchestration prompts with worktree concurrency, multi-module coordination, verification gates, hooks, and HITL clarification gates.

- Scaffold `git_commit_formatter.py` and `ci_cd_pipeline_template.yml` in `workplace/templates/delivery/`.
- Formulate `lifecycle_delivery_prompt.md` and `workflow_orchestration_prompt.md` linking all 21 capabilities (`CAP-01`..`CAP-27`) into an executable autonomous delivery flow.

### Step 10: Domain Adaptation & Validation Playbook
Produce comprehensive guidance for applying the parent master plan across domain spaces (IoT, GenAI, Web, Mobile, Neural, DB Migration, Robotics, Multi-Module Connected Ecosystems).

- Formulate `workplace/docs/parent_context_engineering_guide.md`, `agentic/methodologies/semantic_parity_guide.md`, and `agentic/methodologies/token_optimization_playbook.md`.
- Run verification tests against synthetic MVS packages to validate zero drift, single-module integrity, multi-module contract compatibility, surgical rollbacks, and simulator loopback bridges.

### Step 11: Proprietary Context & Agentic Space Obfuscation, Compilation & Binary Packaging Engine
Build CLI tools and cryptographic packers (`percipience pack`) for obfuscating and sealing markdown plans, `agentic/` prompt trees, and `context/` governance schemas into `.nbpack` envelopes with Ed25519 signatures and memory-only hydration.

- Scaffold `plan_pack_compiler.py` and `envelope_hydrator.py` in `workplace/templates/packaging/`.
- Wire `percipience pack --include-spaces context,agentic` and `percipience init --parent-plan <file.nbpack>` into the CLI runner to ensure proprietary trade secrets, metaprompts, and architectural blueprints are never exposed in plaintext on the client filesystem.

### Step 12: Enterprise Reliability Hardening (Atomic Writes, PID Probing & Wire Schema Gate)
Implement hardened system-level reliability guarantees across the Quad-Space workspace to eliminate file truncation, orphaned subagent worktrees, and broken wire contracts during high-concurrency or crash events.

- Implement `MerkleEngine.atomic_write_data()` and `TokenTracker.save_ledger()` using temporary file creation, `os.fsync()`, and atomic `os.replace()` to ensure zero corrupt or partial state files.
- Implement active POSIX PID-probing (`os.kill(pid, 0)`) in `WorktreeEngine` and `WorktreeManager` to automatically detect crashed processes and reclaim orphaned worktree directory leases.
- Implement deep JSON Schema Draft-07 wire contract validation and sample payload checking in `LayeredContextValidator.validate_wire_contracts()` and `validate_sample_payload()`.

### Step 13: Scalability Architecture (Content-Addressable AST Caching, Merkle Epoch Checkpointing & Cognitive Tiering Router)
Scale the context engineering platform for high-throughput enterprise repositories with thousands of files and extensive Git commit histories.

- Implement SHA-256 content-addressable AST skeleton caching in `ASTOptimizer`, achieving sub-millisecond retrieval (0.1ms) on unchanged source code.
- Implement rolling Merkle epoch checkpointing (`MerkleEngine.checkpoint_epoch()`) archiving historical blocks to `.nb/context/ledger/archive/epoch_{start}_{end}.json` with sealed `epoch_rollup_hash` references, bounding active ledger sizes to $O(1)$ while preserving tamper-proof cryptographic audit trails.
- Implement the model-agnostic `CognitiveRouter` (`.nb/core/cognitive_router.py`, `.nb/agentic/runtime/cognitive_router.py`), enforcing Tier A (`claude-3-7-sonnet / pro`) for high-reasoning tasks and Tier B (`claude-3-5-haiku / flash`) for routine tasks, realizing a 90% cost reduction on standard subagent tasks.

### Step 14: Autonomous CI/CD Specialist Agent Plugins & 6-Stage Gatekeeper Integration
Build a standardized fleet of specialist agent plugins under `.nb/agentic/custom/agents/` and integrate them into the PR verification gatekeeper.

- Scaffold `agent_flaky_test_detector` (`flaky_test_detector.py`) with non-blocking quarantine in `user/hitl/flaky_quarantine.yaml`.
- Scaffold `agent_contract_compatibility_checker` (`contract_compatibility_checker.py`) enforcing SemVer rules and blocking breaking wire contract removals.
- Scaffold `agent_dependency_cve_sentinel` (`dependency_cve_sentinel.py`) detecting compromised dependencies and restrictive licenses.
- Scaffold `agent_doc_drift_synchronizer` (`doc_drift_synchronizer.py`) auditing exported AST interface coverage against architecture plans.
- Upgrade `.nb/agentic/workflows/pr_gatekeeper.yaml` and `./.nb/bin/percipience gate` into a comprehensive verification pipeline.
- Expand the automated test suite in `workplace/tests/test_play3_suite.py` to end-to-end integration tests, validating all reliability, scalability, and specialist plugin subsystems.

### Step 15: Autonomous Living Documentation Agent & In-Workflow Mermaid Visualizer Integration
Build and integrate the autonomous in-workflow documentation engine and Mermaid visualizer (`agent_living_doc_architect`) to continuously synchronize `workplace/docs/` with zero drift.

- Implement `LivingDocEngine` in `.nb/core/living_doc_engine.py`:
  - *AST Symbol & Contract Parser*: Automatically extracts module hierarchies, exported classes/methods, REST/gRPC endpoints, event stream channels, and DDL entity schemas.
  - *Mermaid Visual Generators*:
    - C4 Architecture & Topologies (`render_architecture_mermaid()`): Renders boundary graphs (`graph TD` / `graph LR`) showing client tiers, API gateways, worker pools, persistence tiers, and virtual simulation bridges.
    - Module Interface Catalog (`render_module_catalog_mermaid()`): Renders module dependency graphs and tabular interface matrices (`workplace/docs/module_catalog.md`).
    - Sequence Flow Engine (`render_sequence_mermaid()`): Generates chronological `sequenceDiagram` models for request lifecycles, auth flows, and cross-module message dispatching (`workplace/docs/sequence_flows.md`).
    - Data Flow & Transformation DAGs (`render_data_flow_mermaid()`): Generates `flowchart TD` pipelines and `stateDiagram-v2` lifecycles (`workplace/docs/data_flow.md`).
    - Entity-Relationship Modeler (`render_erd_mermaid()`): Generates standard `erDiagram` structures with exact field typing and cardinality keys (`workplace/docs/entity_relationship.md`).
    - Active Domain Layer Deep Dives (`render_domain_extensions_mermaid()`): Inspects active domain layer IDs (e.g. `domain_blockchained_audio`, `domain_iot_mobile`, `domain_saas_portal`) and generates layer-specific diagrams (such as P2P swarm mesh topologies, BLE GATT characteristic graphs, or multi-tenant RBAC trees in `workplace/docs/domain_extensions.md`).
  - *Incremental Content-Addressable AST Hashing*: Maintains `.scratch/doc_ast_hashes.json` to skip re-rendering unchanged modules, achieving zero redundant token consumption during continuous workflow runs.
  - *Mermaid Syntax Validator*: Enforces node quotation rules (`id["Label (Details)"]`) and checks syntax validity before persisting Markdown files.
- Scaffold specialist agent manifest `.nb/agentic/custom/agents/agent_living_doc_architect.yaml` (Tier B execution for routine extraction, escalating to Tier A for complex architectural disambiguation).
- Inject `agent_living_doc_architect` and `gate_doc_drift_verification` into `.nb/agentic/workflows/pr_gatekeeper.yaml` and `.nb/agentic/workflows/cross_module_orchestrator.yaml`.
- Implement automated verification test in `.nb/tests/test_living_doc_engine.py` validating that document generation succeeds, all Mermaid blocks are valid, and Merkle ledger entries are sealed under `living_docs`.

---



### Step 16: Autonomous SDLC, Cognitive Strategy & Swarm Governance Suite
Implement the advanced autonomous engineering governance triad spanning execution synchronization, prompt hardening, and cognitive attention controls.

- Implement `WorkflowOrchestrator` (`CAP-28`) and `ErrorRecoveryOrchestrator` (`CAP-29`) in `.nb/core/`.
- Deploy cryptographic prompt manifest `agentic/prompts/prompt_manifest.yaml` and `PromptDriftSentinel` (`CAP-30`) enforcing static prefix pinning for KV-cache reuse.
- Enforce 4-tier authority hierarchy and anti-usurpation spawning interception via `SwarmGovernor` (`CAP-31`).
- Embed proactive resilience hardening with `AdversarialFuzzer` (`CAP-32`) and attention quota budgeting via `AttentionBudgeter` (`CAP-33`).
- Serialize ReAct trajectories via `TrajectoryRecorder` (`CAP-34`) and automate requirement ambiguity gating via `AmbiguityResolver` (`CAP-35`).

### Domain-Specific Layering Architecture
The Parent Master Plan deliberately provides universal, domain-agnostic abstractions (`mod_service_provider`, `mod_service_consumer`, `service_contract.yaml`, `virtual_service_bridge.py`). Domain-specific software systems are decoupled into dedicated **Layerable Context Engineering Plans** that overlay on top of this framework via Tier 2 (Enterprise Domain Rules & Wire Contracts) and Tier 3 (Specialist Subagents & Workflow Plugins):

- **Decentralized Audio Streaming, P2P Swarms & Capability Loans**: Defined in [`.nb/plan/claude-context-engineering-blockchained-audio-streamer-space.md`](./claude-context-engineering-blockchained-audio-streamer-space.md) (encapsulates Web3 EIP-712 capability loans, P2P audio chunks, BitTorrent swarm mesh routing, IPFS content-addressed manifests, tokenized royalty splitters, and dynamic domain extensions in `workplace/docs/domain_extensions.md`).
- **Connected IoT, Embedded Hardware & Mobile Systems**: Encapsulates BLE GATT tables, FreeRTOS/Zephyr C/C++, QEMU emulation, mTLS CSR handshakes, and dual-bank A/B OTA manifests.
- **Enterprise SaaS, Corporate Portals & Web Platforms**: Defined in [`.nb/plan/claude-context-engineering-saas-portal-domain-plan.md`](./claude-context-engineering-saas-portal-domain-plan.md) and [`.nb/plan/CEaasS/play_3_corp_site_saas_portal_plan.md`](./CEaasS/play_3_corp_site_saas_portal_plan.md) (encapsulates Next.js/React frontend portals, Tailwind CSS design tokens, WCAG 2.1 AA accessibility, multi-tenant RBAC policies, and Stripe/Paddle billing webhooks).
- **Standardized Custom Layer Template**: Reusable domain authoring blueprint defined in [`.nb/plan/templates/custom_domain_layer_template.md`](./templates/custom_domain_layer_template.md) and [`.nb/agentic/templates/custom_domain_layer_template.md`](../../.nb/agentic/templates/custom_domain_layer_template.md) for scaffolding domain wire contracts, specialist agents, and virtual simulator bridges.
- **Encrypted Layer Packaging & In-Memory Enclave Consumption (`.nbpack`)**: Proprietary domain layers are compiled and sealed via `./.nb/bin/percipience layer pack` and consumed directly into volatile memory (zero disk plaintext residue) with Merkle state transitions via `./.nb/bin/percipience layer apply`.
