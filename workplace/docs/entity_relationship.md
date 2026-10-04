# Entity-Relationship Models & Schema Mappings

**Document Version**: 7.5.0  
**Living Doc Status**: Synchronized & Verified  
**Engine**: `LivingDocEngine` / `agent_living_doc_architect`  

---

## 1. Domain Entities & Contract Relationships

```mermaid
erDiagram
    EMAIL_ACCOUNT ||--o{ EMAIL_MESSAGE : synchronizes
    EMAIL_MESSAGE ||--o{ ACTION_ITEM : extracts
    EMAIL_MESSAGE ||--|| TRIAGE_RESULT : produces
    THOUGHT_ITEM ||--|| TASK_GRAPH : decomposes
    TASK_GRAPH ||--o{ GRAPH_TASK : contains
    GRAPH_TASK ||--o{ ACTION_ITEM : correlates
    TRIAGE_RESULT ||--o{ ROUTE_RECORD : triggers
    ROUTE_RECORD ||--|| MERKLE_BLOCK : seals

    EMAIL_MESSAGE {
        string message_id PK
        string account_id FK
        string sender
        string subject
        datetime received_at
        string status
    }

    ACTION_ITEM {
        string item_id PK
        string message_id FK
        string description
        string priority
        datetime due_date
    }

    TRIAGE_RESULT {
        string triage_id PK
        string message_id FK
        string primary_category
        float confidence
        boolean requires_hitl
    }

    TASK_GRAPH {
        string graph_id PK
        string thought_id FK
        int node_count
        string root_goal
    }

    MERKLE_BLOCK {
        int block_id PK
        string prev_hash
        string current_hash
        string merkle_root
        datetime timestamp
    }
```
