# Poly-Module Interface Catalog

**Document Version**: 7.5.0  
**Living Doc Status**: Synchronized & Verified  
**Engine**: `LivingDocEngine` / `agent_living_doc_architect`  

---

## 1. Module Inventory & Public API Surfaces

| Module ID | Domain & Responsibility | Public API Surface / Types | Dependencies |
| :--- | :--- | :--- | :--- |
| `pos_orchestrator` | Core Intent Routing, Subagent Leases & Pipeline Dispatch | `Router`, `RouteTarget`, `IntentClassifier`, `ActionItemDispatcher` | `tokio`, `async-channel`, `serde` |
| `pos_thoughts` | Thought Ingestion, Task Graph Decomposition & Project Synthesis | `ThoughtParser`, `TaskGraph`, `PlanSynthesisTask`, `DependencyEdge` | `serde`, `serde_json`, `uuid` |
| `pos_email` | Multi-Account Ingestion, IMAP/OAuth2 Bridge & Account Management | `EmailClient`, `EmailMessage`, `SyncConfig`, `ImapBridge` | `async_trait`, `chrono`, `uuid` |
| `pos_triage` | Zero-Shot Classification, Action Item Extraction & Threat Scanning | `TriageEngine`, `EmailCategory`, `ActionItem`, `TriageResult` | `pos_email`, `regex`, `chrono` |

---

## 2. Cross-Module Contract Bindings

```mermaid
flowchart LR
    E["pos_email"] -->|"NormalizedMessage (email_triage_contract)"| T["pos_triage"]
    T -->|"TriageResult (email_triage_contract)"| O["pos_orchestrator"]
    TH["pos_thoughts"] -->|"PlanSynthesisTask (thought_to_project_contract)"| O
```

---

## 3. Module Recovery Points & Verification

- `pos_orchestrator`: Current Verified Recovery Point `RP_ORCH_001`
- `pos_thoughts`: Current Verified Recovery Point `RP_THOUGHT_001`
- `pos_email`: Current Verified Recovery Point `RP_EMAIL_001`
- `pos_triage`: Current Verified Recovery Point `RP_TRIAGE_001`
