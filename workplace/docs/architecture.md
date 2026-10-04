# Personal OS: System Architecture & C4 Topology

**Document Version**: 7.5.0  
**Living Doc Status**: Synchronized & Verified  
**Engine**: `LivingDocEngine` / `agent_living_doc_architect`  

---

## 1. System Context & Quad-Space Isolation

Personal OS operates under strict Quad-Space architectural isolation, separating untrusted user data, customer business logic, platform governance, and autonomous multi-agent swarms.

```mermaid
flowchart TD
    subgraph UserSpace["User Enclave (user/)"]
        UI["User Inputs & RFC Specs"]
        HITL["HITL Quarantine & Review"]
        Dash["Observability Dashboard"]
    end

    subgraph WorkplaceSpace["Customer Modules (workplace/)"]
        Orch["pos_orchestrator"]
        Thoughts["pos_thoughts"]
        Email["pos_email"]
        Triage["pos_triage"]
    end

    subgraph NBContext["Platform Governance (.nb/context/)"]
        Invariants["Tier 1 Invariants"]
        Contracts["Wire Contracts"]
        Ledger["Merkle DAG Ledger"]
    end

    subgraph NBAgentic["Multi-Agent Swarms (.nb/agentic/)"]
        Gatekeeper["PR Gatekeeper Swarm"]
        LivingDoc["Living Doc Architect"]
        Healer["Bounded TDD Healer"]
    end

    UI -->|Ingestion| Thoughts
    Thoughts -->|Task Graphs| Orch
    Email -->|Raw Messages| Triage
    Triage -->|Action Items| Orch
    Orch -->|State Diffs| Ledger
    NBAgentic -->|Enforces Security| WorkplaceSpace
    Invariants -->|Precedence Control| NBAgentic
    Ledger -->|Telemetry Metrics| Dash
```

---

## 2. Microservice Module Topology

```mermaid
graph LR
    subgraph Ingestion["Ingestion Layer"]
        M1["pos_thoughts: Unstructured Thought Parsing"]
        M2["pos_email: IMAP & OAuth2 Synchronization"]
    end

    subgraph Processing["Processing & Reasoning Layer"]
        M3["pos_triage: Zero-Shot Classification & Entity Extraction"]
    end

    subgraph Orchestration["Control & Execution Layer"]
        M4["pos_orchestrator: Intent Router & Action Dispatcher"]
    end

    M1 -->|PlanSynthesisTask| M4
    M2 -->|NormalizedMessage| M3
    M3 -->|TriageResult| M4
```

---

## 3. Layered Governance Precedence

```mermaid
flowchart TB
    T1["Tier 1: Base Platform Invariants (.nb/context/invariants/)"]
    T2["Tier 2: Enterprise Global Rules & Wire Contracts (.nb/context/rules/)"]
    T3["Tier 3: Domain Custom Context & Team Agents (.nb/agentic/custom/)"]

    T1 -->|Overrides| T2
    T2 -->|Overrides| T3
```
