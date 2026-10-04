# Runtime Execution & Cross-Module Sequence Flows

**Document Version**: 7.5.0  
**Living Doc Status**: Synchronized & Verified  
**Engine**: `LivingDocEngine` / `agent_living_doc_architect`  

---

## 1. End-to-End Email Ingestion, Triage & Task Dispatch Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Mail Provider
    participant Email as pos_email
    participant Triage as pos_triage
    participant Orch as pos_orchestrator
    participant Ledger as Percipience Merkle Ledger

    User->>Email: Ingest Raw Email / IMAP Sync
    Email->>Email: Sanitize Headers & Ephemeral Zeroize Body
    Email->>Triage: Forward NormalizedMessage
    Triage->>Triage: Zero-Shot Multi-Category Classification
    Triage->>Triage: Extract Action Items, Deadlines & Priority
    Triage->>Orch: Dispatch TriageResult DTO
    Orch->>Orch: Match RouteTarget (Tasks / Calendar / HITL)
    Orch->>Ledger: Append State Transition Block
    Ledger-->>Orch: Sealed SHA-256 Merkle Receipt
    Orch-->>User: Execution Confirmation / Dashboard Update
```

---

## 2. Thought Ingestion & Task Decomposition Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as User Voice / Text Input
    participant Thoughts as pos_thoughts
    participant Orch as pos_orchestrator
    participant Ledger as Percipience Merkle Ledger

    User->>Thoughts: Ingest Raw Unstructured Thought
    Thoughts->>Thoughts: Parse Syntax & Extract Semantic Intent
    Thoughts->>Thoughts: Construct Directed Acyclic Task Graph
    Thoughts->>Orch: Submit PlanSynthesisTask
    Orch->>Orch: Route to Autonomous Project Pipeline
    Orch->>Ledger: Seal Task Graph in Merkle Chain
    Ledger-->>Orch: Cryptographic Proof Block
```
