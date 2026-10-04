# Domain Plan: Personal OS (Rust-Based Agentic Life Operating System)

**Plan ID**: `domain_personal_os`  
**Capability Rating**: `Domain Specialist (P-OS-01 to P-OS-17)`  
**Parent Plan**: [Parent Master Plan](../master/parent-master-plan/concise.md)  
**Version**: `1.2.0`  
**Runtime Core**: Safe Rust (2021 Edition, `tokio`, `sqlx`, `tantivy`, `axum`)

---

## 1. Executive Summary

**Personal OS** is a unified, offline-first, privacy-preserving, high-performance agentic operating system written in Rust. It serves as your personal cognitive co-pilot, orchestrating eight core dimensions of personal and professional life coordinated by an autonomous meta-orchestration layer:

```mermaid
graph TD
    POS["Rust Personal OS Core (pos_daemon)"]
    POS --> PO["Meta-Orchestrator (pos_orchestrator)"]
    PO --> P1["1. Projects (Workspaces, Git, Worktrees, Tasks)"]
    PO --> P2["2. Files (CAS Blob Store, FTS, Semantic Index)"]
    PO --> P3["3. Thoughts (Zettelkasten, Capture, Knowledge Graph)"]
    PO --> P4["4. Activities (Calendar, Habits, Telemetry)"]
    PO --> P5["5. Workflows (Async DAGs, Durable Sagas, Cron)"]
    PO --> P6["6. Credentials (Zero-Knowledge Encrypted Vault)"]
    PO --> P7["7. Interactions (CRM, Meeting Debriefs, Comms)"]
    PO --> P8["8. Purchases (Expenses, Subscriptions, Receipts)"]
```

The system is designed on top of the **Neutron Binary Percipience Parent Master Context Framework**, inheriting cryptographic Merkle audit ledgers, AST token compression, and surgical rollback guarantees.

---

## 2. Quick Links

- **[concise.md](./concise.md)**: Concise layerable domain specification (~220 lines), frontmatter, wire contracts, and agent manifests.
- **[detailed.md](./detailed.md)**: Comprehensive architectural blueprint, Rust crate decomposition, database schemas, cryptographic invariants, verification harnesses, and **Section 8: Pragmatic Lean Alternatives**.
- **[MANIFEST.yaml](./MANIFEST.yaml)**: Machine-readable plan metadata, version hash ledger, and phase roadmap.
- **[Architecture Gaps & Resolutions](../architecture/GAPS_COMPLETE.md)**: Specifications for GAP-001 through GAP-012 (CRDT sync, write batching, NER redaction, durable sagas, BIP-39 recovery).
- **[Interaction Points Topology](../INTERACTION_POINTS.md)**: Comprehensive interaction mechanisms across ingestion, domain execution, and storage/audit pipelines.
- **[Use Cases & Market Valuation](../USE_CASES_AND_MARKET_VALUE.md)**: Operational commercial use cases, unit economics, and ROI models.
- **[Parent Master Plan](../master/parent-master-plan/README.md)**: Master orchestration framework standard.

---

## 3. The Core Subsystem Crates

| # | Domain Pillar | Primary Responsibility | Key Rust Crates |
|---|---|---|---|
| 0 | **Orchestrator** | Request classification, priority routing, processor registry | `pos_orchestrator` (`lru`, `jsonschema`, `petgraph`) |
| 1 | **Projects** | Workspaces, Git repositories, worktrees, sprint tasks, issues | `pos_projects` (`git2`, `petgraph`, `ignore`) |
| 2 | **Files** | Universal file ingestion, BLAKE3 CAS, semantic chunking, watcher | `pos_files` (`notify`, `tantivy`, `blake3`, `infer`) |
| 3 | **Thoughts** | Quick capture, second brain, atomic notes, bidirectional links | `pos_thoughts` (`pulldown-cmark`, `sqlite-vec`, `petgraph`) |
| 4 | **Activities** | Calendar sync, time tracking, habit logs, health/focus telemetry | `pos_activities` (`chrono`, `icalendar`, `rrule`) |
| 5 | **Workflows** | Declarative async task DAGs, durable sagas, cron routines | `pos_workflows` (`tokio`, `async-trait`, `cron`) |
| 6 | **Credentials** | Encrypted vault, OS keychain, zero-knowledge master key, leases | `pos_vault` (`ring`, `argon2`, `keyring`, `zeroize`) |
| 7 | **Interactions** | Personal CRM, contacts, communication logs, meeting debriefs | `pos_interactions` (`sqlx`, `vcard4`, `serde_json`) |
| 8 | **Purchases** | Financial ledger, receipt OCR/parser, subscription renewal alerts | `pos_purchases` (`rust_decimal`, `tesseract` / OCR bridge) |
| 9 | **Storage** | SQLite WAL, Tantivy BM25, BLAKE3 CAS & Tokio MPSC Write Batcher | `pos_storage` (`sqlx`, `tantivy`, `blake3`) |
| 10 | **Agents** | Multi-agent actor runtime, sandbox executor (Bubblewrap/Seatbelt) | `pos_agents` (`tokio`, `async-trait`) |
| 11 | **Server** | Axum HTTP/WebSocket API daemon, native MCP server bridge | `pos_server` (`axum`, `tower`, `tokio-tungstenite`) |
| 12 | **CLI** | Production terminal command-line tool | `pos_cli` (`clap` v4) |

> [!TIP]
> **Pragmatic Lean Architecture Option**: An alternative 3-crate modular architecture (`pos_core`, `pos_server`, `pos_cli`) is fully specified in [`detailed.md#8-pragmatic-reassessment-simpler-easier-architecture--lean-alternatives`](./detailed.md). It delivers 90%+ of capabilities while cutting compile times by 7x, reducing LOC by 68%, and accelerating MVP delivery from 24 weeks down to 6–8 weeks.

---

## 4. Architectural Invariants

1. **Local-First & Zero-Knowledge**: All databases, vectors, and blobs reside on local NVMe storage. Cloud sync is end-to-end encrypted; credentials never leave the local vault in plaintext.
2. **Memory Scrubbing**: Sensitive secrets in RAM implement `zeroize::ZeroizeOnDrop` to prevent cold-boot or heap-dump exfiltration.
3. **Sub-15ms Hybrid Search**: Queries across thoughts, files, and projects execute simultaneously via Tantivy BM25 and vector embeddings with reciprocal rank fusion (RRF).
4. **Sandboxed Subagent Execution**: Agent operations run with least-privilege capability tokens, with human-in-the-loop (HITL) approval required for external mutation, credential export, or financial transactions.

---

## 5. Getting Started & CLI Usage

```bash
# Verify the plan within the Percipience framework
./.nb/bin/percipience audit

# Build the Rust Personal OS daemon and CLI
cargo build --workspace --release

# Initialize personal data vault
pos vault init --keychain

# Start local agentic daemon & web dashboard
pos daemon start --port 8080
```
