---
gap_id: "GAP-001"
name: "CRDT-Based Multi-Device Conflict Resolution"
priority: "P0"
status: "specification"
created: "2026-10-04"
---

# Multi-Device Conflict Resolution with CRDTs

## Problem Statement

Personal OS currently uses a **last-write-wins (LWW)** conflict resolution strategy for multi-device sync:
```yaml
# From wf_background_sync.yaml
conflict_strategy: "last_write_wins"
```

**Critical Issues with LWW**:
1. **Silent Data Loss**: Later timestamp overwrites earlier changes, losing work
   - User edits thought on laptop at 10:00 AM
   - User adds tags to same thought on phone at 10:05 AM (offline)
   - Sync at 10:10 AM: Phone timestamp wins, laptop edits lost
2. **No Semantic Merging**: Cannot merge concurrent non-conflicting edits
   - Device A adds tag "work" to thought
   - Device B adds tag "urgent" to same thought
   - Result: Only one tag survives (whichever device synced last)
3. **Causality Violations**: No happened-before relationship tracking
4. **User Frustration**: Unpredictable which device "wins", work lost without warning

**Frequency** (projected for multi-device users):
- Conflicting writes: 5-10% of sync operations
- Data loss incidents: 2-3 per week per active user
- User-reported "disappearing changes": Critical UX failure

---

## Solution Architecture: CRDT Layer with Operational Transformation

Replace LWW with **Conflict-Free Replicated Data Types (CRDTs)** that guarantee eventual consistency without coordination. Use **Yrs** (Yjs Rust port) for text documents and custom **LWW-Element-Set** for metadata.

### CRDT Selection Matrix

| Data Type | CRDT Type | Implementation | Use Case |
|-----------|-----------|----------------|----------|
| Thought content (text) | **Yjs Text CRDT** | `yrs` crate | Rich text with concurrent edits |
| Thought tags | **LWW-Element-Set** | Custom | Set merge with add-wins semantics |
| Task status | **LWW-Register** | Custom | Single-value state with timestamp |
| Habit logs | **G-Counter** | Custom | Append-only (never conflicts) |
| File metadata | **Multi-Value Register** | Custom | Show conflicts to user |

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                      Application Layer                        │
│              pos_thoughts │ pos_activities                    │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              pos_storage::CRDTCoordinator                     │
│                                                                │
│  ┌────────────────────────────────────────┐                  │
│  │  CRDT Document Store (per entity)      │                  │
│  │  - Entity ID → Yrs Doc mapping         │                  │
│  │  - Vector Clock per device             │                  │
│  │  - Update log for sync                 │                  │
│  └────────────────────────────────────────┘                  │
│                     │                                         │
│                     ▼                                         │
│  ┌────────────────────────────────────────┐                  │
│  │  Merge Engine                          │                  │
│  │  - Apply remote updates                │                  │
│  │  - Generate local updates              │                  │
│  │  - Detect true conflicts (MVR only)    │                  │
│  └────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    SQLite Storage Layer                       │
│  - crdt_updates table (update log per entity)                 │
│  - device_clocks table (vector clock state)                   │
│  - thoughts table (materialized view from CRDT)               │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Specification

### 1. SQLite Schema Extensions

```sql
-- Vector Clock tracking per device
CREATE TABLE IF NOT EXISTS device_clocks (
    device_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('thought', 'task', 'habit', 'file')),
    clock_value INTEGER NOT NULL DEFAULT 0,
    last_updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (device_id, entity_id, entity_type)
);

-- CRDT update log (append-only)
CREATE TABLE IF NOT EXISTS crdt_updates (
    update_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    device_id TEXT NOT NULL,
    vector_clock TEXT NOT NULL, -- JSON: {"device_a": 5, "device_b": 3}
    update_payload BLOB NOT NULL, -- Yrs binary update or custom CRDT op
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    synced_to_backend BOOLEAN NOT NULL DEFAULT 0
);
CREATE INDEX idx_crdt_updates_entity ON crdt_updates(entity_id, entity_type);
CREATE INDEX idx_crdt_updates_device ON crdt_updates(device_id, applied_at);
CREATE INDEX idx_crdt_updates_pending_sync ON crdt_updates(synced_to_backend, applied_at);

-- Materialized view metadata (track CRDT → SQL projection version)
CREATE TABLE IF NOT EXISTS crdt_materializations (
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    last_snapshot_clock TEXT NOT NULL, -- JSON vector clock
    last_materialized_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entity_id, entity_type)
);
```

### 2. Yrs Integration for Thought Content

```rust
// workplace/modules/pos_storage/src/crdt/thought_crdt.rs

use yrs::{Doc, Text, Transact, Update};
use yrs::updates::encoder::{Encode, Encoder};
use yrs::updates::decoder::{Decode, Decoder};

pub struct ThoughtCRDT {
    doc: Doc,
    content: Text,
}

impl ThoughtCRDT {
    pub fn new(thought_id: &str) -> Self {
        let doc = Doc::with_client_id(Self::device_id_to_client_id());
        let content = doc.get_or_insert_text("content");
        Self { doc, content }
    }
    
    /// Apply local edit (insert text at position)
    pub fn insert(&mut self, index: u32, text: &str) -> Vec<u8> {
        let mut txn = self.doc.transact_mut();
        self.content.insert(&mut txn, index, text);
        
        // Generate update encoding
        let update = txn.encode_update_v1();
        update
    }
    
    /// Apply local delete (remove range)
    pub fn delete(&mut self, index: u32, len: u32) -> Vec<u8> {
        let mut txn = self.doc.transact_mut();
        self.content.remove_range(&mut txn, index, len);
        
        let update = txn.encode_update_v1();
        update
    }
    
    /// Apply remote update from another device
    pub fn apply_remote_update(&mut self, update_bytes: &[u8]) -> Result<(), CRDTError> {
        let update = Update::decode_v1(update_bytes)?;
        let mut txn = self.doc.transact_mut();
        txn.apply_update(update);
        Ok(())
    }
    
    /// Get current text content (materialized view)
    pub fn get_text(&self) -> String {
        let txn = self.doc.transact();
        self.content.get_string(&txn)
    }
    
    /// Get state vector (for efficient sync: only send missing updates)
    pub fn get_state_vector(&self) -> Vec<u8> {
        let txn = self.doc.transact();
        txn.state_vector().encode_v1()
    }
    
    /// Get diff since remote state vector
    pub fn get_diff_update(&self, remote_state_vector: &[u8]) -> Result<Vec<u8>, CRDTError> {
        let state_vec = yrs::updates::decoder::DecoderV1::from(remote_state_vector)
            .read_state_vector()?;
        let txn = self.doc.transact();
        let update = txn.encode_diff_v1(&state_vec);
        Ok(update)
    }
    
    fn device_id_to_client_id() -> u64 {
        // Hash device UUID to u64 for Yrs client ID
        let device_id = std::env::var("DEVICE_ID").unwrap_or_default();
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        let mut hasher = DefaultHasher::new();
        device_id.hash(&mut hasher);
        hasher.finish()
    }
}
```

### 3. LWW-Element-Set for Tags

```rust
// workplace/modules/pos_storage/src/crdt/lww_set.rs

use chrono::{DateTime, Utc};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LWWElementSet<T: Eq + Hash + Clone> {
    adds: HashMap<T, DateTime<Utc>>,    // Element → timestamp when added
    removes: HashMap<T, DateTime<Utc>>, // Element → timestamp when removed
}

impl<T: Eq + Hash + Clone> LWWElementSet<T> {
    pub fn new() -> Self {
        Self {
            adds: HashMap::new(),
            removes: HashMap::new(),
        }
    }
    
    /// Add element with current timestamp
    pub fn add(&mut self, element: T) {
        let now = Utc::now();
        self.adds.insert(element, now);
    }
    
    /// Remove element with current timestamp
    pub fn remove(&mut self, element: &T) {
        let now = Utc::now();
        if let Some(element) = element.clone() {
            self.removes.insert(element, now);
        }
    }
    
    /// Check if element is in the set (add wins if timestamps equal)
    pub fn contains(&self, element: &T) -> bool {
        let add_time = self.adds.get(element);
        let remove_time = self.removes.get(element);
        
        match (add_time, remove_time) {
            (Some(add_ts), Some(rm_ts)) => add_ts >= rm_ts, // Add-wins bias
            (Some(_), None) => true,
            _ => false,
        }
    }
    
    /// Get all elements in the set
    pub fn elements(&self) -> Vec<T> {
        self.adds.keys()
            .filter(|elem| self.contains(elem))
            .cloned()
            .collect()
    }
    
    /// Merge with another LWW-Element-Set (commutative, associative, idempotent)
    pub fn merge(&mut self, other: &Self) {
        for (elem, ts) in &other.adds {
            self.adds.entry(elem.clone())
                .and_modify(|existing| {
                    if ts > existing {
                        *existing = *ts;
                    }
                })
                .or_insert(*ts);
        }
        
        for (elem, ts) in &other.removes {
            self.removes.entry(elem.clone())
                .and_modify(|existing| {
                    if ts > existing {
                        *existing = *ts;
                    }
                })
                .or_insert(*ts);
        }
    }
}
```

### 4. CRDT Coordinator

```rust
// workplace/modules/pos_storage/src/crdt/coordinator.rs

use sqlx::{SqlitePool, Transaction};
use std::collections::HashMap;

pub struct CRDTCoordinator {
    pool: SqlitePool,
    device_id: String,
    // In-memory cache of active CRDT documents
    thought_docs: Arc<RwLock<HashMap<String, ThoughtCRDT>>>,
}

impl CRDTCoordinator {
    pub fn new(pool: SqlitePool, device_id: String) -> Self {
        Self {
            pool,
            device_id,
            thought_docs: Arc::new(RwLock::new(HashMap::new())),
        }
    }
    
    /// Apply local thought edit and persist update
    pub async fn edit_thought(
        &self,
        thought_id: &str,
        edit_op: EditOperation,
    ) -> Result<(), CRDTError> {
        // Get or create CRDT doc
        let mut docs = self.thought_docs.write().await;
        let crdt = docs.entry(thought_id.to_string())
            .or_insert_with(|| self.load_thought_crdt(thought_id)?);
        
        // Apply local edit and generate update
        let update_bytes = match edit_op {
            EditOperation::Insert { index, text } => crdt.insert(index, &text),
            EditOperation::Delete { index, len } => crdt.delete(index, len),
        };
        
        // Persist update to log
        let vector_clock = self.increment_vector_clock(thought_id, "thought").await?;
        
        sqlx::query!(
            "INSERT INTO crdt_updates (update_id, entity_id, entity_type, device_id, vector_clock, update_payload)
             VALUES (?, ?, 'thought', ?, ?, ?)",
            ulid::Ulid::new().to_string(),
            thought_id,
            self.device_id,
            serde_json::to_string(&vector_clock)?,
            update_bytes
        )
        .execute(&self.pool)
        .await?;
        
        // Update materialized view in thoughts table
        self.materialize_thought(thought_id, crdt).await?;
        
        Ok(())
    }
    
    /// Apply remote updates from sync
    pub async fn apply_remote_updates(
        &self,
        updates: Vec<CRDTUpdate>,
    ) -> Result<(), CRDTError> {
        for update in updates {
            match update.entity_type.as_str() {
                "thought" => {
                    let mut docs = self.thought_docs.write().await;
                    let crdt = docs.entry(update.entity_id.clone())
                        .or_insert_with(|| self.load_thought_crdt(&update.entity_id)?);
                    
                    crdt.apply_remote_update(&update.payload)?;
                    
                    // Persist update log
                    sqlx::query!(
                        "INSERT INTO crdt_updates (update_id, entity_id, entity_type, device_id, vector_clock, update_payload, synced_to_backend)
                         VALUES (?, ?, ?, ?, ?, ?, 1)",
                        ulid::Ulid::new().to_string(),
                        update.entity_id,
                        update.entity_type,
                        update.device_id,
                        serde_json::to_string(&update.vector_clock)?,
                        update.payload
                    )
                    .execute(&self.pool)
                    .await?;
                    
                    // Re-materialize
                    self.materialize_thought(&update.entity_id, crdt).await?;
                }
                _ => {} // Handle other entity types
            }
        }
        
        Ok(())
    }
    
    /// Get pending local updates for sync
    pub async fn get_pending_updates(&self) -> Result<Vec<CRDTUpdate>, CRDTError> {
        let rows = sqlx::query!(
            "SELECT update_id, entity_id, entity_type, device_id, vector_clock, update_payload
             FROM crdt_updates
             WHERE synced_to_backend = 0
             ORDER BY applied_at ASC"
        )
        .fetch_all(&self.pool)
        .await?;
        
        Ok(rows.into_iter().map(|row| CRDTUpdate {
            update_id: row.update_id,
            entity_id: row.entity_id,
            entity_type: row.entity_type,
            device_id: row.device_id,
            vector_clock: serde_json::from_str(&row.vector_clock).unwrap(),
            payload: row.update_payload,
        }).collect())
    }
    
    async fn materialize_thought(
        &self,
        thought_id: &str,
        crdt: &ThoughtCRDT,
    ) -> Result<(), CRDTError> {
        let content = crdt.get_text();
        
        sqlx::query!(
            "UPDATE thoughts SET content_raw = ?, updated_at = CURRENT_TIMESTAMP
             WHERE id = ?",
            content,
            thought_id
        )
        .execute(&self.pool)
        .await?;
        
        Ok(())
    }
    
    async fn increment_vector_clock(
        &self,
        entity_id: &str,
        entity_type: &str,
    ) -> Result<HashMap<String, u64>, CRDTError> {
        // Increment local clock and return full vector clock
        sqlx::query!(
            "INSERT INTO device_clocks (device_id, entity_id, entity_type, clock_value)
             VALUES (?, ?, ?, 1)
             ON CONFLICT(device_id, entity_id, entity_type)
             DO UPDATE SET clock_value = clock_value + 1, last_updated_at = CURRENT_TIMESTAMP",
            self.device_id,
            entity_id,
            entity_type
        )
        .execute(&self.pool)
        .await?;
        
        // Fetch full vector clock for this entity
        let rows = sqlx::query!(
            "SELECT device_id, clock_value FROM device_clocks
             WHERE entity_id = ? AND entity_type = ?",
            entity_id,
            entity_type
        )
        .fetch_all(&self.pool)
        .await?;
        
        Ok(rows.into_iter()
            .map(|row| (row.device_id, row.clock_value as u64))
            .collect())
    }
}
```

### 5. Modified Background Sync Workflow

```yaml
# .nb/agentic/custom/workflows/wf_background_sync.yaml (updated)

# Step 4: Upload Changes (CRDT-aware)
- id: "upload_changes"
  name: "Push CRDT Updates to Backend"
  agent: "agent_ios_sync_coordinator"
  tool: "push_crdt_updates"  # Changed from push_to_backend
  input:
    updates: "${pending_uploads.crdt_updates}"  # Now CRDT updates, not full entities
    device_id: "${device_id}"
  output_binding: "upload_result"
  timeout: 20000

# Step 5: Handle Upload Conflicts (NOW OBSOLETE - CRDTs never conflict)
# REMOVED: resolve_upload_conflicts step

# Step 7: Pull Remote Changes (CRDT updates)
- id: "pull_remote_updates"
  name: "Download CRDT Updates"
  agent: "agent_ios_sync_coordinator"
  tool: "pull_crdt_updates"  # Changed
  input:
    device_id: "${device_id}"
    last_sync_state_vector: "${last_sync_state_vector}"  # Changed
  output_binding: "remote_updates"

# Step 8: Apply Remote Updates (CRDT merge)
- id: "apply_remote_updates"
  name: "Merge Remote CRDT Updates"
  action: "apply_crdt_updates"  # Changed
  input:
    updates: "${remote_updates.updates}"
  output_binding: "apply_result"

# REMOVED: resolve_download_conflicts (CRDTs auto-merge)
```

---

## Performance Targets

| Metric | LWW Baseline | CRDT Target | Max |
|--------|--------------|-------------|-----|
| Merge operation latency | 5ms | 15ms | 50ms |
| Update log size (per thought) | N/A | <100KB | <1MB |
| Sync payload increase | Baseline | +30% | +100% |
| Conflict resolution success | 0% (data loss) | 100% | 100% |
| False positive conflicts | N/A | 0% | 0% |

---

## Migration Strategy

### Phase 1: Infrastructure (Week 1-2)
- Implement CRDT schema extensions (tables, indexes)
- Integrate `yrs` crate for text CRDTs
- Implement LWW-Element-Set for tags
- Create `CRDTCoordinator`

### Phase 2: Thought Entity Migration (Week 3)
- Migrate `pos_thoughts` to use CRDT layer
- Add CRDT update generation on local edits
- Test concurrent edit scenarios (offline + sync)

### Phase 3: Sync Protocol Update (Week 4)
- Update `wf_background_sync` to exchange CRDT updates
- Implement state vector-based incremental sync
- Remove LWW conflict resolution code

### Phase 4: Validation (Week 5)
- Multi-device concurrent edit testing
- Performance benchmarking (update log growth, merge latency)
- User acceptance testing (verify no data loss)

---

## Benefits

1. **Zero Data Loss**: All concurrent edits preserved and merged
2. **Deterministic**: Same updates applied in any order produce same result
3. **Partition Tolerant**: Devices can work offline indefinitely and sync later
4. **User Trust**: Predictable behavior, no "disappeared changes"
5. **Scalability**: Efficient incremental sync (state vectors reduce payload)

---

## Crate Dependencies

```toml
[dependencies]
yrs = "0.18"              # Yjs CRDT for collaborative text
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
chrono = "0.4"
sqlx = { version = "0.7", features = ["sqlite", "runtime-tokio-native-tls"] }
ulid = "1.0"
```

---

## Related Gaps

- **GAP-002** (Write Batching): CRDT updates use write coordinator for persistence
- **GAP-005** (Saga Pattern): CRDT update log serves as durable event log

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Implement `CRDTCoordinator` and integrate `yrs` crate
