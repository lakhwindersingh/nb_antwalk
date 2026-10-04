---
plan_id: plan_lineage_and_index
name: Personal OS & Percipience Plan Lineage and Dependency Index
version: 1.0.0
status: authoritative_reference
created: 2026-10-04
last_updated: 2026-10-04
reference_framework: .nb/plan/master/parent-master-plan/detailed.md
reference_core_plan: .nb/plan/personal_os/detailed.md
reference_invariants: .nb/context/rules/personal_os_invariants.md
---

# Personal OS & Percipience Plan Lineage, Hierarchy & Dependency Index

### Executive Overview & Strategic Purpose
The **Percipience Context Engineering Framework** structures complex agentic software development into a strictly governed, multi-tiered hierarchy of plans. These plans range from domain-agnostic master framework governance down to low-level cryptographic wire contracts and specialized AI subagent extensions.

This document serves as the **authoritative master lineage and dependency index** for all plans across [`.nb/plan/`](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/README.md). It defines:
1. **The Architectural Lineage Graph**: How parent frameworks derive domain plans, how domain plans branch into architectural gap resolutions and domain extensions, and how contracts govern execution.
2. **Topological Implementation Order**: Strict dependency-ordered execution sequences for both the **Pragmatic Lean MVP Track (8 Weeks)** and the **Full Enterprise Track (24 Weeks)**.
3. **The Master Plan Catalog**: An exhaustive, searchable reference matrix of every plan document, specifying its type, version, prerequisites, and downstream consumers.
4. **Invariant Governance Traceability**: Direct mapping between platform security invariants (Invariants 1–10) and their enforcing plan files.

---

## 1. Master Plan Lineage Topology

To maximize readability and eliminate diagram clutter, the overall plan lineage is divided into three focused, vertically oriented architectural diagrams:
- **Diagram 1A: Master Governance & Core Plan Derivation Hierarchy**
- **Diagram 1B: Architecture Gaps & Hardening Specifications**
- **Diagram 1C: Modular Extensions & Commercialization Lineage**

---

### Diagram 1A: Master Governance & Core Plan Derivation Hierarchy

To ensure crystal-clear readability and eliminate visual crowding across the governance and domain tiers, Diagram 1A is divided into two focused, progressive diagrams:
- **Diagram 1A-1: Strategic Framework Governance & Wire Contract Pipeline** (Parent framework to platform invariants and validated wire contracts)
- **Diagram 1A-2: Core Domain Plan Suite & Operational Artifact Derivation** (Validated contracts and blueprints to the full Personal OS plan suite and Merkle audit ledger)

---

#### Diagram 1A-1: Strategic Framework Governance & Wire Contract Pipeline

This vertical pipeline illustrates how the root **Parent Master Plan (v7.5.0)** establishes the 10 platform security invariants and commercial billing matrices, which directly parameterize the JSON Schema Draft-07 wire contracts:

```mermaid
flowchart TD
    subgraph Tier0["Tier 0: Parent Master Framework Foundation"]
        P_Master["Parent Master Plan (v7.5.0)<br/>.nb/plan/master/parent-master-plan/<br/>(CAP-01 to CAP-36 Foundation Architecture)"]
        P_Free["Parent Master Free Plan<br/>.nb/plan/master/parent-master-free-plan/<br/>(Community Open-Source Baseline)"]
        T_Custom["Custom Domain Layer Template<br/>.nb/plan/templates/custom_domain_layer_template.md<br/>(Scaffolding Standard for Layerable Domains)"]
        P_Master -.->|Open-Source Subset| P_Free
        P_Master -->|Derivation Standard| T_Custom
    end

    subgraph Tier1["Tier 1: Platform Invariants, Safety Rules & Economics"]
        R_Invariants["10 Non-Negotiable Invariants<br/>.nb/context/rules/personal_os_invariants.md<br/>(Zero-Knowledge, Offline-First, Memory Hygiene)"]
        R_Financial["Financial Safety Rules<br/>.nb/context/rules/financial_safety_rules.md<br/>(Mandatory HITL Approvals for Tx > $0.00)"]
        Cfg_Billing["Commercial Billing Matrix<br/>.nb/config/billing_plans.yaml<br/>(Free, Team, Business, Enterprise Ceilings)"]
    end

    subgraph Tier2["Tier 2: Enterprise Wire Contracts (JSON Schema Draft-07)"]
        C_Core["Primary Domain Wire Contract<br/>personal_os_wire_contracts.yaml (v1.2.0)<br/>(8-Pillar RPC & 12 Consolidated MCP Tools)"]
        C_Security["Security & Storage Contracts<br/>vault_security_contract.json & hybrid_search_contract.json<br/>(Zeroize RAM Leases & Sub-15ms FTS5/Vector)"]
        C_Specialized["Subsystem Integration Contracts<br/>thought_to_project, native_siri & plan_synthesis<br/>(Zettelkasten AST, AppIntents & MVS Generation)"]
    end

    %% GOVERNANCE & ENFORCEMENT FLOWS
    P_Master --> R_Invariants
    P_Master --> R_Financial
    P_Master --> Cfg_Billing
    R_Invariants -->|Enforces Schema & Zeroize| C_Core
    R_Invariants -->|Enforces RAM Scrubbing & Latency| C_Security
    R_Financial -->|Enforces HITL Approval Queue| C_Core
    R_Invariants -->|Enforces Boundary Contracts| C_Specialized
```

---

#### Diagram 1A-2: Core Domain Plan Suite & Operational Artifact Derivation

This vertical sequence illustrates how upstream validated wire contracts and the domain layer template synthesize the **Personal OS Detailed Blueprint**, which subsequently derives the concise spec, capability manifest, and immutable Merkle ledger:

```mermaid
flowchart TD
    subgraph Upstream["1. Upstream Blueprints & Validated Contracts"]
        T_CustomInput["Custom Domain Layer Template<br/>.nb/plan/templates/custom_domain_layer_template.md"]
        C_Validated["Tier 2 Validated Wire Contracts<br/>.nb/context/contracts/*.yaml & *.json<br/>(100% JSON Schema Draft-07 Compliant)"]
    end

    subgraph CoreBlueprint["2. Core Single Source of Truth"]
        POS_Detailed["Personal OS Detailed Blueprint (v1.2.0)<br/>.nb/plan/personal_os/detailed.md<br/>(System Topology, SQLite DDL, MCP Catalog & Section 8 Lean Plan)"]
    end

    subgraph DerivedArtifacts["3. Derived Specifications & Operational Artifacts"]
        POS_Concise["Personal OS Concise Spec (v1.2.0)<br/>.nb/plan/personal_os/concise.md<br/>(Quad-Space Mapping, Agent Manifests & Lean 3-Crate Option)"]
        POS_Manifest["Personal OS Manifest (v1.2.0)<br/>.nb/plan/personal_os/MANIFEST.yaml<br/>(Machine-Readable Capabilities P-OS-01..17 & Phase Tracks)"]
        POS_Summary["Improvements Summary (v1.2.0)<br/>.nb/plan/personal_os/IMPROVEMENTS_SUMMARY.md<br/>(Release History v1.0.0..1.2.0 & Cross-Sync Matrix)"]
    end

    subgraph AuditLedger["4. Cryptographic State Attestation"]
        Merkle_Ledger["Percipience Merkle DAG Ledger<br/>context_ledger.yaml (Blocks 0–10 Verified)<br/>(Immutable Audit Trail of Plan Mutations & Hash Chains)"]
    end

    %% DERIVATION FLOWS
    T_CustomInput --> POS_Detailed
    C_Validated --> POS_Detailed
    POS_Detailed --> POS_Concise
    POS_Detailed --> POS_Manifest
    POS_Detailed --> POS_Summary
    POS_Detailed --> Merkle_Ledger
    POS_Manifest --> Merkle_Ledger
```

---

### Diagram 1B: Architecture Gaps & Hardening Lineage

The core Personal OS architecture anchors 12 critical engineering gap specifications ([`GAPS_COMPLETE.md`](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/GAPS_COMPLETE.md)), categorized into three functional pillars:

```mermaid
flowchart TD
    POS_Core["Personal OS Core Architecture<br/>.nb/plan/personal_os/detailed.md"]
    GAP_Master["Master Gap Resolution Matrix<br/>.nb/plan/architecture/GAPS_COMPLETE.md"]

    subgraph G_Storage["1. Storage, Concurrency & Sync Gaps"]
        GAP_01["GAP-001: Yrs CRDT Multi-Device Sync<br/>.nb/plan/architecture/crdt_conflict_resolution.md"]
        GAP_02["GAP-002: Storage Write Batching Coordinator<br/>.nb/plan/architecture/storage_write_batching.md"]
        GAP_03["GAP-003: Multi-Version Embedding Migration<br/>.nb/plan/architecture/embedding_versioning.md"]
        GAP_09["GAP-009: CAS Garbage Collection & Zstd Tiers<br/>.nb/plan/architecture/cas_garbage_collection.md"]
        GAP_10["GAP-010: mDNS Local Peer Discovery<br/>.nb/plan/architecture/mobile_peer_discovery.md"]
    end

    subgraph G_Security["2. Security, Privacy & Memory Gaps"]
        GAP_04["GAP-004: Dual-Pass NER PII Redaction<br/>.nb/plan/architecture/pii_anonymization.md"]
        GAP_06["GAP-006: BIP-39 Vault Recovery & Shamir SSS<br/>.nb/plan/architecture/vault_disaster_recovery.md"]
        GAP_08["GAP-008: Subagent Bubblewrap/Seatbelt Sandbox<br/>.nb/plan/architecture/subagent_sandboxing.md"]
        GAP_11["GAP-011: Contact Entity Resolution<br/>.nb/plan/architecture/entity_resolution.md"]
        GAP_12["GAP-012: Hierarchical 3-Tier Memory<br/>.nb/plan/architecture/hierarchical_memory.md"]
    end

    subgraph G_Execution["3. Workflow & Inference Gaps"]
        GAP_05["GAP-005: Durable Saga Workflow State Machine<br/>.nb/plan/architecture/saga_workflow_durability.md"]
        GAP_07["GAP-007: Local Quantized Inference Optimization<br/>.nb/plan/architecture/inference_engine_optimization.md"]
    end

    %% LINKAGES
    POS_Core --> GAP_Master
    GAP_Master --> G_Storage
    GAP_Master --> G_Security
    GAP_Master --> G_Execution
```

---

### Diagram 1C: Modular Extensions & Commercialization Lineage

The core Personal OS architecture directly drives modular subsystem extensions and maps to cross-cutting interaction topologies and commercial monetization models:

```mermaid
flowchart TD
    POS_Core["Personal OS Core Architecture<br/>.nb/plan/personal_os/detailed.md"]

    subgraph Ext_P0["Core Tier 1 Subsystem Extensions (P0)"]
        Ext_Orch["Meta-Orchestrator Extension<br/>.nb/plan/extensions/meta_orchestrator/<br/>(Semantic Intent Classifier & Router)"]
        Ext_T2P["Thought-to-Project Triad<br/>.nb/plan/extensions/thought_to_project/<br/>(Autonomous Zettelkasten to CI/CD)"]
        Ext_Siri["Native Apple SiriKit Extension<br/>.nb/plan/extensions/native_apple_siri/<br/>(App Intents & Dynamic Island)"]
        Ext_Voice["Voice Interface Extension<br/>.nb/plan/extensions/voice_interface/<br/>(Whisper.cpp & 'Hey Kiro' Audio Ingestion)"]
        Ext_Email["Email Triage Extension<br/>.nb/plan/extensions/email_triage/<br/>(IMAP/OAuth2 & Invoice Parser)"]
    end

    subgraph Ext_P1["Intelligence Extensions (P1)"]
        Ext_Meet["Meeting Intelligence Extension<br/>.nb/plan/extensions/meeting_intelligence/<br/>(Audio Diarization & Action Extraction)"]
        Ext_Proact["Proactive Intelligence Extension<br/>.nb/plan/extensions/proactive_intelligence/<br/>(Circadian Rhythm & Habit Optimizer)"]
    end

    subgraph Topologies["Cross-Cutting Topologies & Commercialization"]
        Top_Interactions["Master Interaction Points Topology<br/>.nb/plan/INTERACTION_POINTS.md"]
        Top_Market["Use Cases & Market Valuation ($194B TAM)<br/>.nb/plan/USE_CASES_AND_MARKET_VALUE.md"]
        Top_Summary["Complete Documentation Summary<br/>.nb/plan/COMPLETE_SUMMARY.md"]
    end

    %% LINKAGES
    POS_Core --> Ext_P0
    POS_Core --> Ext_P1
    Ext_Orch --> Top_Interactions
    Ext_T2P --> Top_Interactions
    POS_Core --> Top_Interactions
    POS_Core --> Top_Market
    POS_Core --> Top_Summary
```

---

## 2. Topological Implementation Order

To prevent circular dependencies and blocking states, implementation must follow a strictly ordered DAG sequence. Personal OS provides two execution pathways:

---

### Track A: Pragmatic Lean MVP Track (Recommended: 6–8 Weeks)
*Consolidates codebase into a 3-crate modular monolith (`pos_core`, `pos_server`, `pos_cli`), reducing compile times by 7x and lines of code by 68%.*

```mermaid
flowchart TD
    subgraph Stage1["Stage 1: Core Foundation & Data Engine (Weeks 1–2)"]
        S1_1["3-Crate Monolith Scaffolding<br/>pos_core, pos_server, pos_cli"]
        S1_2["SQLite WAL Mode + Native FTS5<br/>BM25 Full-Text Indexing & Plain File Store"]
        S1_3["OS Keyring (keyring-rs) & Vault<br/>zeroize::ZeroizeOnDrop Memory Hygiene"]
        S1_4["Append-Only Merkle DAG Ledger<br/>Cryptographic State Sealing in context_ledger.yaml"]
        S1_1 --> S1_2 --> S1_3 --> S1_4
    end

    subgraph Stage2["Stage 2: Core Domain Engines & Git Worktrees (Weeks 3–5)"]
        S2_1["Markdown Thought Ingestion<br/>CommonMark AST & Bidirectional Wikilink Graph"]
        S2_2["pos_projects & Git Worktrees<br/>Ephemeral .worktrees/agentic-* for Atomic Rollback"]
        S2_3["Flat Expense Ledger & Subscriptions<br/>Strict HITL Gate & hledger Export"]
        S2_4["Activity & Habit Streak Tracker<br/>iCalendar Agenda Parsing & Focus Telemetry"]
        S2_1 --> S2_2 --> S2_3 --> S2_4
    end

    subgraph Stage3["Stage 3: Consolidated MCP Tools & Delivery (Weeks 6–8)"]
        S3_1["12 Consolidated Action-Based MCP Tools<br/>pos_server Stdio + SSE Transports"]
        S3_2["Local Ollama / llama.cpp HTTP Client<br/>Standard OpenAI-Compatible REST Endpoints"]
        S3_3["Canonical Terminal CLI ('pos')<br/>Interactive Clap v4 Command-Line Binary"]
        S3_4["End-to-End Loopback Verification<br/>Percipience Audit & Invariant Compliance"]
        S3_1 --> S3_2 --> S3_3 --> S3_4
    end

    %% STAGE DEPENDENCY CHAIN
    Stage1 --> Stage2
    Stage2 --> Stage3
```

#### Stage Deliverables Breakdown:
1. **Stage 1 (Weeks 1–2): Scaffolding, Data & Cryptographic Security**:
   - **Prerequisites**: [`.nb/context/rules/personal_os_invariants.md`](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/context/rules/personal_os_invariants.md), [`.nb/context/contracts/personal_os_wire_contracts.yaml`](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/context/contracts/personal_os_wire_contracts.yaml).
   - **Outputs**: `pos_core` scaffold, SQLite WAL mode with FTS5 lexical full-text index. Configure OS Keyring via `keyring-rs` and `zeroize::ZeroizeOnDrop` memory hygiene. Implement Merkle block appending to `context_ledger.yaml`.
2. **Stage 2 (Weeks 3–5): Core Domain Engines & Git Worktrees**:
   - **Prerequisites**: Stage 1 SQLite and Vault foundation.
   - **Outputs**: Markdown thought parser with bidirectional wikilink indexing. Implement `pos_projects` with Git2 worktree provisioning (`.worktrees/agentic-*`) for atomic agent rollback. Build flat transactional expense table with HITL gate. Build habit streak calculation and iCal agenda parsing.
3. **Stage 3 (Weeks 6–8): 12 Consolidated MCP Tools, Local LLM & CLI**:
   - **Prerequisites**: Stage 2 Domain Engines.
   - **Outputs**: Implement the 12 consolidated MCP tools in `pos_server` using standard `action` parameters. Wire local Ollama / llama.cpp HTTP inference endpoint. Build the canonical interactive `pos` CLI binary.

---

### Track B: Full Enterprise Track (24 Weeks)
*Deploys the full 14-crate workspace with custom distributed sagas, Tantivy, BLAKE3 CAS, and native mobile mesh synchronization.*

```mermaid
flowchart TD
    subgraph Phase1["Phase 1: Foundation & High-Throughput Storage (Weeks 1–4)"]
        P1_1["14-Crate Workspace Scaffolding<br/>pos_core, pos_storage, pos_orchestrator"]
        P1_2["SQLite WAL + Tantivy BM25 + BLAKE3 CAS<br/>Dual Lexical & Vector Indexing"]
        P1_3["Tokio MPSC Storage Write Batcher (GAP-002)<br/>Priority P0/P1 Queues & 10ms Flush Window"]
        P1_1 --> P1_2 --> P1_3
    end

    subgraph Phase2["Phase 2: Security Enclave Vault & Privacy (Weeks 5–6)"]
        P2_1["pos_vault with Argon2id & ChaCha20-Poly1305<br/>Zero-Knowledge Root Key Hygiene"]
        P2_2["BIP-39 Seed Recovery & Shamir SSS (GAP-006)<br/>24-Word Paper Escrow & M-of-N Quorum"]
        P2_3["Dual-Pass NER Redaction Sentinel (GAP-004)<br/>PII Token Vault & Cryptographic Surrogates"]
        P2_1 --> P2_2 --> P2_3
    end

    subgraph Phase3["Phase 3: The 8 Domain Pillar Engines (Weeks 7–14)"]
        P3_1["pos_projects, pos_files, pos_thoughts<br/>Git2 Worktrees, Notify Watcher & Wikilinks"]
        P3_2["Thought-to-Project Triad & Task Petgraph<br/>Autonomous SpecGen -> CodeGen -> Verifier"]
        P3_3["pos_activities, pos_interactions, pos_purchases<br/>CalDAV Sync, Diarization & Double-Entry FinOps"]
        P3_1 --> P3_2 --> P3_3
    end

    subgraph Phase4["Phase 4: Agent Runtime, Sagas & Local Inference (Weeks 15–18)"]
        P4_1["Durable Saga State Machine (GAP-005)<br/>Forward Actions, Compensations & SQLite Journals"]
        P4_2["Subagent Container Sandboxing (GAP-008)<br/>Bubblewrap Namespaces & Seatbelt Profiles"]
        P4_3["Quantized ONNX Runtime & vLLM (GAP-007)<br/>In-Process Sub-35MB RAM Model Execution"]
        P4_1 --> P4_2 --> P4_3
    end

    subgraph Phase5["Phase 5: Client Surfaces, Mesh Sync & Launch (Weeks 19–24)"]
        P5_1["Canonical Clap v4 CLI ('pos') & Axum Web Portal<br/>Subcommand Hierarchy & Browser Dashboard"]
        P5_2["Native MCP Server (Stdio + WebSocket/SSE Transports)<br/>Full 28-Tool Catalog & Resource Subscriptions"]
        P5_3["Yrs CRDT Sync (GAP-001) & mDNS Mesh (GAP-010)<br/>Multi-Device State Vector Synchronization"]
        P5_4["Swift UniFFI SiriKit & Live Activities Bridge<br/>Dynamic Island & Voice Intent Handlers"]
        P5_1 --> P5_2 --> P5_3 --> P5_4
    end

    %% PHASE DEPENDENCY CHAIN
    Phase1 --> Phase2
    Phase2 --> Phase3
    Phase3 --> Phase4
    Phase4 --> Phase5
```

#### Enterprise Phase Matrix:

| **Phase 1: Storage & Foundation** | Weeks 1–4 | `pos_core`, `pos_storage`, `pos_orchestrator` | Platform Invariants, Base Contracts | [detailed.md § 7.1](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-002](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/storage_write_batching.md), [GAP-003](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/embedding_versioning.md) |
| **Phase 2: Security & Vault Enclave** | Weeks 5–6 | `pos_vault` | Phase 1 Storage Engine | [detailed.md § 7.2](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-004](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/pii_anonymization.md), [GAP-006](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/vault_disaster_recovery.md) |
| **Phase 3: The 8 Domain Pillar Engines** | Weeks 7–14 | `pos_projects`, `pos_files`, `pos_thoughts`, `pos_activities`, `pos_workflows`, `pos_interactions`, `pos_purchases` | Phase 2 Vault & Security Enclave | [detailed.md § 7.3](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-009](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/cas_garbage_collection.md), [GAP-011](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/entity_resolution.md), [thought_to_project](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/extensions/thought_to_project/detailed.md) |
| **Phase 4: Agent Runtime & Durable Sagas** | Weeks 15–18 | `pos_agents`, `pos_workflows` (Saga Engine) | Phase 3 Domain Engines | [detailed.md § 7.4](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-005](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/saga_workflow_durability.md), [GAP-007](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/inference_engine_optimization.md), [GAP-008](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/subagent_sandboxing.md) |
| **Phase 5: Client Surfaces & Mesh Sync** | Weeks 19–24 | `pos_cli`, `pos_server`, Swift SiriKit FFI | Phase 4 Agent Runtime | [detailed.md § 7.5](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-001](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/crdt_conflict_resolution.md), [GAP-010](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/mobile_peer_discovery.md), [native_apple_siri](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/extensions/native_apple_siri/concise.md) |

---

## 3. Exhaustive Master Plan Catalog & Index

The following table indexes all plans, contracts, gap specifications, extensions, and topologies across `.nb/plan/`:

| Path & Link | Plan Title | Category | Ver / Status | Direct Prerequisites | Downstream Consumers | Key Deliverables |
|:---|:---|:---|:---|:---|:---|:---|
| [master/parent-master-plan/detailed.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/master/parent-master-plan/detailed.md) | Parent Master Plan | Framework Foundation | `7.5.0` Active | None (Root Architecture) | All domain plans & extensions | 36 Capabilities (CAP-01 to CAP-36), quad-space architecture, AST pruning |
| [master/parent-master-free-plan/detailed.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/master/parent-master-free-plan/detailed.md) | Community Edition Framework | Framework Foundation | `1.0.0` Active | None (Open Source Subset) | Community users | Free tier specifications and developer tools |
| [templates/custom_domain_layer_template.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/templates/custom_domain_layer_template.md) | Domain Layer Template | Scaffolding Template | `1.0.0` Template | Parent Master Plan | All custom domain plans | Standard scaffolding structure for new agentic domain layers |
| [personal_os/detailed.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md) | Personal OS Detailed Blueprint | Core Domain Plan | `1.2.0` Active | Parent Master, Platform Invariants, Wire Contracts | All extensions, CLI, server, daemons | Complete architectural blueprint, SQLite schema, 28 MCP tools, Section 8 Lean Plan |
| [personal_os/concise.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/concise.md) | Personal OS Concise Plan | Core Domain Plan | `1.2.0` Active | Parent Master Plan | Subagent system prompts, context loaders | Quad-space mapping, wire contract summaries, agent manifests, 3-crate lean option |
| [personal_os/MANIFEST.yaml](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/MANIFEST.yaml) | Personal OS Manifest | Plan Metadata | `1.2.0` Active | Detailed Plan | Percipience build & packaging toolchain | Machine-readable capability ledger (P-OS-01 to P-OS-17), hashes, phase tracks |
| [personal_os/README.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/README.md) | Personal OS Quick Guide | Quick Navigation | `1.2.0` Active | Detailed Plan | Onboarding engineers, human users | Executive summary, 13-crate table, lean architecture callouts |
| [personal_os/IMPROVEMENTS_SUMMARY.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/IMPROVEMENTS_SUMMARY.md) | Improvements Summary | Historical Changelog | `1.2.0` Active | Detailed Plan | Governance & audit review | Evolution history (v1.0.0 to v1.2.0) and sync verification matrix |
| [architecture/GAPS_COMPLETE.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/GAPS_COMPLETE.md) | Master Gap Resolution Matrix | Architecture Hardening | `1.0.0` Complete | Core Detailed Plan | All 12 GAP specifications | Gap matrix linking GAP-001 through GAP-012 |
| [architecture/crdt_conflict_resolution.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/crdt_conflict_resolution.md) | GAP-001: CRDT Conflict Resolution | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 3.2 | Phase 5 Multi-Device Sync | Yrs CRDT integration, vector clocks, LWW element-set conflict resolution |
| [architecture/storage_write_batching.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/storage_write_batching.md) | GAP-002: Storage Write Batching | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 4 | `pos_storage` Crate | Tokio MPSC write batch coordinator, priority lanes, 10ms commit window |
| [architecture/embedding_versioning.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/embedding_versioning.md) | GAP-003: Embedding Versioning | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 4 | `pos_storage`, `pos_thoughts` | Multi-version embedding tables, migration queue, vector re-indexing pipeline |
| [architecture/pii_anonymization.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/pii_anonymization.md) | GAP-004: PII Anonymization | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 5.2 | `pos_agents`, Egress filter | Dual-pass NER scrubber, PII token vault, cryptographic surrogates |
| [architecture/saga_workflow_durability.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/saga_workflow_durability.md) | GAP-005: Saga Workflow Durability | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 3.5 | `pos_workflows` Crate | Orchestrated Saga engine, forward/compensating transactions, SQLite step checkpoints |
| [architecture/vault_disaster_recovery.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/vault_disaster_recovery.md) | GAP-006: Vault Disaster Recovery | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 3.6 | `pos_vault` Crate | BIP-39 24-word paper seed derivation, Shamir Secret Sharing (M-of-N quorum) |
| [architecture/inference_engine_optimization.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/inference_engine_optimization.md) | GAP-007: Inference Engine Optimization | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 3.3 | `pos_agents`, Inference engine | Quantized local models (4-bit MiniLM / Candle / ONNX), sub-35MB RAM footprint |
| [architecture/subagent_sandboxing.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/subagent_sandboxing.md) | GAP-008: Subagent Sandboxing | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 5 | `pos_agents` Crate | Bubblewrap / Landlock namespaces, filesystem chroot, network domain allowlisting |
| [architecture/cas_garbage_collection.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/cas_garbage_collection.md) | GAP-009: CAS Garbage Collection | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 3.2 | `pos_files`, `pos_storage` | Two-phase Mark & Sweep GC, `cas_references` tracking, Zstd compression tiers |
| [architecture/mobile_peer_discovery.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/mobile_peer_discovery.md) | GAP-010: Mobile Peer Discovery | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 1 | `pos_server`, iOS Sync | mDNS / Bonjour local mesh discovery over TLS 1.3, silent APNs triggers |
| [architecture/entity_resolution.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/entity_resolution.md) | GAP-011: Entity Resolution | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 3.7 | `pos_interactions` Crate | TF-IDF, Jaro-Winkler string similarity, contact and alias deduplication |
| [architecture/hierarchical_memory.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/hierarchical_memory.md) | GAP-012: Hierarchical Memory | Architecture Hardening | `1.0.0` Complete | Detailed Plan § 3.3 | `pos_thoughts`, `pos_agents` | 3-tier memory consolidation (working RAM, episodic SQLite, semantic vector graphs) |
| [extensions/meta_orchestrator/README.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/extensions/meta_orchestrator/README.md) | Meta-Orchestrator Extension | Subsystem Extension | `1.0.0` Complete | Detailed Plan § 3.9 | All cross-domain workflows | Semantic intent classifier (<2ms LRU cache), dynamic processor registry, router |
| [extensions/thought_to_project/detailed.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/extensions/thought_to_project/detailed.md) | Thought-to-Project Triad | Subsystem Extension | `1.0.0` Complete | `pos_thoughts`, `pos_projects` | Autonomous CI/CD pipeline | Multi-agent conversion from raw thought to verifiable Git task DAG and worktrees |
| [extensions/native_apple_siri/concise.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/extensions/native_apple_siri/concise.md) | Native Apple SiriKit Extension | Subsystem Extension | `1.0.0` Complete | Detailed Plan § 6.4 | iOS / macOS App Client | Swift-Rust UniFFI bindings, SiriKit App Intents, Dynamic Island Live Activities |
| [extensions/voice_interface/concise.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/extensions/voice_interface/concise.md) | Voice Interface Extension | Subsystem Extension | `1.0.0` Planned | `pos_files`, `pos_thoughts` | Audio input daemon | Local Whisper.cpp audio ingestion, wake word ("Hey Kiro"), 3s thought capture |
| [extensions/email_triage/concise.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/extensions/email_triage/concise.md) | Email Triage Extension | Subsystem Extension | `1.0.0` Planned | `pos_files`, `pos_purchases` | Communication pipeline | IMAP/Gmail OAuth2 sync, 5-category classification, receipt attachment parser |
| [extensions/meeting_intelligence/concise.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/extensions/meeting_intelligence/concise.md) | Meeting Intelligence Extension | Subsystem Extension | `1.0.0` Planned | `pos_activities`, `pos_interactions` | Meeting debrief pipeline | Calendar auto-join, multi-speaker diarization, decision & commitment extraction |
| [extensions/proactive_intelligence/concise.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/extensions/proactive_intelligence/concise.md) | Proactive Intelligence Extension | Subsystem Extension | `1.0.0` Planned | `pos_activities`, `pos_projects` | Schedule optimizer | Baseline habit learning, focus rhythm telemetry, circadian load balancer |
| [INTERACTION_POINTS.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/INTERACTION_POINTS.md) | Master Interaction Points Topology | Cross-Cutting Blueprint | `1.0.0` Complete | All Domain Plans & Extensions | Frontend, IDEs, API clients | Decoupled vertical interaction diagrams (Client/Ingestion, Domain/Storage, Audit) |
| [USE_CASES_AND_MARKET_VALUE.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/USE_CASES_AND_MARKET_VALUE.md) | Use Cases & Market Valuation | Commercial Strategy | `1.0.0` Complete | Core Detailed Plan, Billing Plans | Commercial Packager & Provisioner | 5 operational use cases, $194B TAM analysis, SaaS pricing tiers & unit economics |
| [COMPLETE_SUMMARY.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/COMPLETE_SUMMARY.md) | Complete Documentation Summary | Comprehensive Summary | `1.0.0` Complete | All Plan Documents | Project stakeholders | Architectural overview, component inventories, and end-to-end dataflow diagrams |

---

## 4. Invariant Governance & Traceability Matrix

Every plan in Personal OS must strictly conform to the 10 platform security invariants established in [`.nb/context/rules/personal_os_invariants.md`](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/context/rules/personal_os_invariants.md):

| Invariant # | Invariant Rule Name | Governing Plan / Gap Specification | Implementation Mechanism | Enforcing Wire Contract |
|:---|:---|:---|:---|:---|
| **Invariant 1** | **Zero-Knowledge Memory** | [detailed.md § 5.1](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-006](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/vault_disaster_recovery.md) | `zeroize::ZeroizeOnDrop` wrapper; root secrets never written to logs or prompts | [vault_security_contract.json](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/context/contracts/vault_security_contract.json) |
| **Invariant 2** | **HITL Financial & Secret Gate** | [detailed.md § 5.3](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [financial_safety_rules.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/context/rules/financial_safety_rules.md) | Mandatory human authorization queue (`user/hitl/`) for transactions > $0.00 and key exports | [personal_os_wire_contracts.yaml](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/context/contracts/personal_os_wire_contracts.yaml) (`pos_finance`) |
| **Invariant 3** | **Local-First Offline Resilience** | [detailed.md § 1](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-007](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/inference_engine_optimization.md) | Local SQLite WAL + FTS5 / LanceDB; local quantized inference (Ollama / Candle) | All contracts (fail-safe local mode) |
| **Invariant 4** | **Tamper Evidence** | [detailed.md § 5](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [parent-master-plan § CAP-08](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/master/parent-master-plan/detailed.md) | Cryptographic SHA-256 Merkle block append-only ledger (`context_ledger.yaml`) | [personal_os_wire_contracts.yaml](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/context/contracts/personal_os_wire_contracts.yaml) (`pos_ledger`) |
| **Invariant 5** | **Memory Safety** | [detailed.md § 2](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md) | 100% safe Rust (zero `unsafe` blocks in application crates, `cargo geiger` verified) | Rust compiler + CI/CD Gate |
| **Invariant 6** | **Least-Privilege Execution** | [detailed.md § 5](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-008](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/subagent_sandboxing.md) | Capability tokens, Git worktree filesystem isolation, stripped subagent env | [personal_os_wire_contracts.yaml](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/context/contracts/personal_os_wire_contracts.yaml) (`pos_agent`) |
| **Invariant 7** | **Privacy Boundaries** | [detailed.md § 3.2](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-009](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/cas_garbage_collection.md) | 30-day soft-delete, automated CAS garbage collection, zero remote telemetry | `pos_files`, `cas_references` |
| **Invariant 8** | **Idempotency & Crash Safety** | [detailed.md § 3.5](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-005](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/saga_workflow_durability.md) | SQLite WAL mode, atomic database transactions, Git worktree rollbacks | [personal_os_wire_contracts.yaml](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/context/contracts/personal_os_wire_contracts.yaml) (`pos_workflow`) |
| **Invariant 9** | **Rate Limiting & Quotas** | [detailed.md § 3.2](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md) | Token-bucket rate limiters on file ingestion watchers and external API calls | `pos_files`, `pos_server` |
| **Invariant 10** | **Dual-Pass Egress Filter** | [detailed.md § 5.2](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/personal_os/detailed.md), [GAP-004](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/pii_anonymization.md) | Regex patterns + Shannon entropy scan replacing secrets/PII with surrogates (`[REDACTED_SECRET]`) | `RedactionSentinel`, `PrivacyCoordinator` |

---

## 5. Verification & Context Ledger Audit

The entire plan lineage, contracts, and invariants are continuously validated by the Percipience CLI:

```bash
# 1. Audit context maturity and cryptographic Merkle chain continuity
./.nb/bin/percipience audit

# 2. Validate 3-tier layered context hierarchy and JSON Schema Draft-07 wire contracts
./.nb/bin/percipience validate --layered

# 3. Verify autonomous CI/CD triad health
./.nb/bin/percipience cicd status
```
