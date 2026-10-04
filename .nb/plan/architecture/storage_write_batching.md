---
gap_id: "GAP-002"
name: "SQLite Write Lock Contention Mitigation"
priority: "P0"
status: "specification"
created: "2026-10-04"
---

# SQLite Write Lock Contention Under Continuous Sensing

## Problem Statement

Personal OS features continuous sensing across multiple concurrent sources:
- **File watcher** (`pos_files`): High-frequency inotify events for file modifications
- **Activity tracker** (`pos_activities`): Focus session telemetry every 30 seconds
- **Email sync** (`pos_interactions`): Periodic IMAP polling and entity extraction
- **Habit logger** (`pos_activities`): User-triggered habit completions
- **Voice capture** (`pos_thoughts`): Real-time transcription results
- **Background workflows**: Scheduled tasks updating state every 15-60 minutes

**Current Architecture Issue**: Each subsystem opens independent SQLite write transactions, causing serialization at the WAL lock. While SQLite WAL mode allows concurrent readers, **only one writer can hold the lock at a time**. Under high load:
- Write transactions queue and timeout
- User-facing operations (habit logging, thought capture) experience latency spikes
- Background tasks compete with interactive commands
- No write priority differentiation

**Measured Impact** (projected):
- P95 latency for habit logging: 200ms → 800ms under file scanning
- Thought capture during email sync: 50ms → 400ms
- Failed writes under concurrent load: 2-5% transaction rollback rate

---

## Solution Architecture: MPSC Write Batching Channel

Introduce a **centralized write coordinator** in `pos_storage` that:
1. Accepts write requests via `tokio::sync::mpsc` unbounded channel
2. Batches requests into discrete transactions (time-based or size-based windows)
3. Executes batches sequentially with a single dedicated writer task
4. Returns results to callers via `oneshot` response channels
5. Implements priority lanes for interactive vs. background operations

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  pos_files │ pos_thoughts │ pos_activities │ pos_interactions │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                  pos_storage::WriteCoordinator                │
│                                                                │
│  ┌────────────────────────────────────────┐                  │
│  │  MPSC Unbounded Channel (Write Queue)  │                  │
│  │  - Priority Lane: Interactive (P0)     │                  │
│  │  - Standard Lane: Background (P1)      │                  │
│  └────────────────────────────────────────┘                  │
│                     │                                         │
│                     ▼                                         │
│  ┌────────────────────────────────────────┐                  │
│  │  Batching Window (10ms or 50 writes)   │                  │
│  │  - Accumulate writes                   │                  │
│  │  - Group by table for optimization     │                  │
│  └────────────────────────────────────────┘                  │
│                     │                                         │
│                     ▼                                         │
│  ┌────────────────────────────────────────┐                  │
│  │  Single Writer Task (Tokio Task)       │                  │
│  │  - BEGIN IMMEDIATE transaction         │                  │
│  │  - Execute batch of prepared stmts     │                  │
│  │  - COMMIT                               │                  │
│  │  - Send responses via oneshot channels │                  │
│  └────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│               SQLite Database (WAL Mode)                      │
│  - Single active writer at a time                             │
│  - Concurrent readers unaffected                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Specification

### 1. Write Request Types

```rust
// workplace/modules/pos_storage/src/write_coordinator.rs

use tokio::sync::{mpsc, oneshot};
use sqlx::SqlitePool;

#[derive(Debug)]
pub enum WriteRequest {
    InsertThought {
        id: String,
        title: String,
        content: String,
        tags: Vec<String>,
        respond_to: oneshot::Sender<Result<(), StorageError>>,
    },
    LogHabit {
        habit_id: String,
        completed_at: DateTime<Utc>,
        respond_to: oneshot::Sender<Result<(), StorageError>>,
    },
    UpdateFile {
        id: String,
        blake3_hash: String,
        extracted_text: Option<String>,
        respond_to: oneshot::Sender<Result<(), StorageError>>,
    },
    InsertInteraction {
        contact_id: Option<String>,
        summary: String,
        occurred_at: DateTime<Utc>,
        respond_to: oneshot::Sender<Result<String, StorageError>>,
    },
    // ... other write operations
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum WritePriority {
    Interactive = 0,  // User-facing: habit logs, thought capture
    Background = 1,   // Background: file indexing, email sync
}

#[derive(Debug)]
pub struct PrioritizedWrite {
    priority: WritePriority,
    request: WriteRequest,
}
```

### 2. Write Coordinator Core

```rust
pub struct WriteCoordinator {
    tx: mpsc::UnboundedSender<PrioritizedWrite>,
    writer_handle: JoinHandle<()>,
}

impl WriteCoordinator {
    pub fn new(pool: SqlitePool) -> Self {
        let (tx, rx) = mpsc::unbounded_channel();
        
        let writer_handle = tokio::spawn(async move {
            Self::writer_task(pool, rx).await
        });
        
        Self { tx, writer_handle }
    }
    
    pub fn submit(
        &self,
        request: WriteRequest,
        priority: WritePriority,
    ) -> Result<(), SendError<PrioritizedWrite>> {
        self.tx.send(PrioritizedWrite { priority, request })
    }
    
    async fn writer_task(
        pool: SqlitePool,
        mut rx: mpsc::UnboundedReceiver<PrioritizedWrite>,
    ) {
        const BATCH_SIZE: usize = 50;
        const BATCH_TIMEOUT: Duration = Duration::from_millis(10);
        
        let mut batch: Vec<PrioritizedWrite> = Vec::with_capacity(BATCH_SIZE);
        
        loop {
            tokio::select! {
                Some(write) = rx.recv() => {
                    batch.push(write);
                    
                    // Drain immediate queue until batch full or empty
                    while batch.len() < BATCH_SIZE {
                        match rx.try_recv() {
                            Ok(write) => batch.push(write),
                            Err(_) => break,
                        }
                    }
                    
                    if batch.len() >= BATCH_SIZE {
                        Self::execute_batch(&pool, &mut batch).await;
                    }
                }
                _ = tokio::time::sleep(BATCH_TIMEOUT), if !batch.is_empty() => {
                    Self::execute_batch(&pool, &mut batch).await;
                }
            }
        }
    }
    
    async fn execute_batch(
        pool: &SqlitePool,
        batch: &mut Vec<PrioritizedWrite>,
    ) {
        if batch.is_empty() {
            return;
        }
        
        // Sort by priority: Interactive first
        batch.sort_by_key(|w| w.priority);
        
        let mut tx = match pool.begin().await {
            Ok(tx) => tx,
            Err(e) => {
                error!("Failed to begin transaction: {}", e);
                Self::respond_all_error(batch, e.into());
                return;
            }
        };
        
        for write in batch.drain(..) {
            let result = Self::execute_write(&mut tx, write.request).await;
            // Response already sent inside execute_write
        }
        
        if let Err(e) = tx.commit().await {
            error!("Failed to commit batch transaction: {}", e);
        }
    }
    
    async fn execute_write(
        tx: &mut Transaction<'_, Sqlite>,
        request: WriteRequest,
    ) -> Result<(), StorageError> {
        match request {
            WriteRequest::InsertThought { id, title, content, tags, respond_to } => {
                let result = sqlx::query!(
                    "INSERT INTO thoughts (id, title, content_raw, tags) VALUES (?, ?, ?, ?)",
                    id, title, content, serde_json::to_string(&tags)?
                )
                .execute(&mut **tx)
                .await
                .map(|_| ())
                .map_err(StorageError::from);
                
                let _ = respond_to.send(result);
                result
            }
            WriteRequest::LogHabit { habit_id, completed_at, respond_to } => {
                let result = sqlx::query!(
                    "INSERT INTO habit_logs (id, habit_id, completed_at) VALUES (?, ?, ?)",
                    ulid::Ulid::new().to_string(), habit_id, completed_at
                )
                .execute(&mut **tx)
                .await
                .map(|_| ())
                .map_err(StorageError::from);
                
                let _ = respond_to.send(result);
                result
            }
            // ... handle other write types
            _ => Ok(())
        }
    }
    
    fn respond_all_error(batch: &mut Vec<PrioritizedWrite>, error: StorageError) {
        for write in batch.drain(..) {
            // Send error to all oneshot channels
            // (implementation varies by WriteRequest enum variant)
        }
    }
}
```

### 3. Public API Surface

```rust
// workplace/modules/pos_storage/src/lib.rs

pub struct StorageEngine {
    pool: SqlitePool,
    write_coordinator: WriteCoordinator,
}

impl StorageEngine {
    pub async fn insert_thought(
        &self,
        thought: NewThought,
        priority: WritePriority,
    ) -> Result<(), StorageError> {
        let (tx, rx) = oneshot::channel();
        
        self.write_coordinator.submit(
            WriteRequest::InsertThought {
                id: thought.id,
                title: thought.title,
                content: thought.content,
                tags: thought.tags,
                respond_to: tx,
            },
            priority,
        )?;
        
        rx.await.map_err(|_| StorageError::ChannelClosed)?
    }
    
    pub async fn log_habit(
        &self,
        habit_id: String,
        completed_at: DateTime<Utc>,
    ) -> Result<(), StorageError> {
        let (tx, rx) = oneshot::channel();
        
        self.write_coordinator.submit(
            WriteRequest::LogHabit {
                habit_id,
                completed_at,
                respond_to: tx,
            },
            WritePriority::Interactive, // Always high priority
        )?;
        
        rx.await.map_err(|_| StorageError::ChannelClosed)?
    }
}
```

---

## Performance Targets

| Metric | Current (Projected) | Target | Max |
|--------|---------------------|--------|-----|
| Habit log latency (P50) | 200ms | 30ms | 100ms |
| Thought capture (P95) | 400ms | 50ms | 150ms |
| Batch commit duration | N/A | 5ms | 20ms |
| Write throughput | ~50/sec | 500/sec | 1000/sec |
| Failed write rate | 2-5% | <0.1% | <0.5% |
| Queue depth (P95) | N/A | <50 | <200 |

---

## Migration Strategy

### Phase 1: Infrastructure (Week 1)
- Implement `WriteCoordinator` core with basic batching
- Add `WritePriority` enum
- Create `WriteRequest` enum for top 5 operations

### Phase 2: Integration (Week 2)
- Migrate `pos_thoughts::insert_thought()` to batched writes
- Migrate `pos_activities::log_habit()` to batched writes
- Add telemetry for batch sizes and commit durations

### Phase 3: Rollout (Week 3)
- Migrate remaining write operations (files, interactions, purchases)
- Load testing under simulated concurrent sensing
- Tune batch size and timeout parameters

### Phase 4: Optimization (Week 4)
- Add grouped writes by table for bulk insert optimization
- Implement write coalescing (deduplicate identical writes in queue)
- Add backpressure monitoring and adaptive batching

---

## Monitoring & Observability

### Metrics
```rust
pub struct WriteCoordinatorMetrics {
    pub queue_depth: AtomicUsize,
    pub batch_size_histogram: Histogram,
    pub commit_duration_histogram: Histogram,
    pub writes_per_second: Counter,
    pub failed_writes: Counter,
    pub priority_p0_count: Counter,
    pub priority_p1_count: Counter,
}
```

### Health Checks
- Alert if queue depth > 500 for >30 seconds
- Alert if commit duration P95 > 50ms
- Alert if failed write rate > 1% over 5 minutes

---

## Benefits

1. **Eliminates write lock contention**: Single writer, no serialization delays
2. **Predictable latency**: Interactive writes complete in <100ms even under load
3. **Higher throughput**: Batch commits ~10x more efficient than individual writes
4. **Priority differentiation**: User-facing operations never wait behind background tasks
5. **Graceful degradation**: Queue absorbs load spikes without dropping writes
6. **Simplified error handling**: Centralized retry and rollback logic

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Channel unbounded growth | OOM under sustained overload | Add bounded channel with backpressure |
| Writer task panic | All writes stall | Add panic handler with task restart |
| Batch commit failure | Entire batch fails | Individual write fallback for failed batches |
| Priority starvation | Background writes never execute | Time-based fairness (max P0 consecutive) |

---

## Related Gaps

- **GAP-001** (CRDT Multi-Device Sync): Write coordinator must handle merge operations
- **GAP-005** (Saga Pattern): Workflow state transitions use write coordinator for durability

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Implement `WriteCoordinator` in `workplace/modules/pos_storage/src/write_coordinator.rs`
