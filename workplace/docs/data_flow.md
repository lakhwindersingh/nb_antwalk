# Data Flow Pipelines & State Machines

**Document Version**: 7.5.0  
**Living Doc Status**: Synchronized & Verified  
**Engine**: `LivingDocEngine` / `agent_living_doc_architect`  

---

## 1. Unified Event Ingestion Pipeline

```mermaid
flowchart LR
    subgraph Inputs["Multi-Modal Inputs"]
        In1["IMAP / OAuth2 Mail"]
        In2["Unstructured Notes / Voice"]
        In3["Siri / Android Intents"]
    end

    subgraph Sanitization["Ingestion & Sanitization"]
        S1["Header Extraction & Memory Scrubbing"]
        S2["Token Normalization & Pruning"]
    end

    subgraph Classification["Reasoning & Classification"]
        C1["Zero-Shot Triage Engine"]
        C2["Task Graph Synthesizer"]
    end

    subgraph Routing["Dispatch & Storage"]
        R1["Orchestration Event Router"]
        R2["Merkle Ledger Chain"]
        R3["User Dashboard Sync"]
    end

    In1 --> S1
    In2 --> S2
    In3 --> S2
    S1 --> C1
    S2 --> C2
    C1 --> R1
    C2 --> R1
    R1 --> R2
    R1 --> R3
```

---

## 2. Email Triage State Machine

```mermaid
stateDiagram-v2
    [*] --> Ingested
    Ingested --> Sanitized: Header Validation
    Sanitized --> Quarantined: Poison / Injection Detected
    Sanitized --> Classified: Clean Content
    Classified --> ActionExtracted: Actionable Items Found
    Classified --> DirectRouted: Informational / Newsletter
    ActionExtracted --> OrchestratorDispatched: Valid Contract DTO
    DirectRouted --> OrchestratorDispatched: Read-Only Archive
    OrchestratorDispatched --> MerkleSealed: Block Appended
    MerkleSealed --> [*]
```
