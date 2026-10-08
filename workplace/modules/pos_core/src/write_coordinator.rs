use std::sync::Arc;
use std::time::Duration;
use parking_lot::RwLock;
use tokio::sync::{mpsc, oneshot};
use crate::storage::{Database, StorageError, Result};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum WritePriority {
    Interactive = 0, // P0: User-facing operations (habit logging, thought capture)
    Background = 1,  // P1: Background jobs (file indexing, email sync)
}

pub enum WriteRequest {
    InsertThought {
        id: String,
        title: String,
        content: String,
        thought_type: String,
        tags: Vec<String>,
        respond_to: oneshot::Sender<Result<()>>,
    },
    InsertProject {
        id: String,
        name: String,
        root_path: Option<String>,
        repo_url: Option<String>,
        respond_to: oneshot::Sender<Result<()>>,
    },
    InsertTransaction {
        id: String,
        description: String,
        amount: f64,
        category: String,
        respond_to: oneshot::Sender<Result<String>>,
    },
    ApproveTransaction {
        id: String,
        respond_to: oneshot::Sender<Result<()>>,
    },
    InsertHabit {
        id: String,
        name: String,
        frequency: String,
        target_count: i32,
        respond_to: oneshot::Sender<Result<()>>,
    },
}

pub struct PrioritizedWrite {
    pub priority: WritePriority,
    pub request: WriteRequest,
}

#[derive(Debug, Default, Clone)]
pub struct CoordinatorMetrics {
    pub total_writes: u64,
    pub total_batches: u64,
    pub p0_writes: u64,
    pub p1_writes: u64,
}

/// Centralized MPSC Write Batching Coordinator (GAP-002)
/// Mitigates SQLite WAL write lock contention by accumulating concurrent writes
/// into prioritized batches executed sequentially by a single dedicated writer task.
#[derive(Clone)]
pub struct WriteCoordinator {
    tx: mpsc::UnboundedSender<PrioritizedWrite>,
    metrics: Arc<RwLock<CoordinatorMetrics>>,
}

impl WriteCoordinator {
    pub const BATCH_SIZE: usize = 50;
    pub const BATCH_TIMEOUT: Duration = Duration::from_millis(10);

    pub fn new(db: Database) -> Self {
        let (tx, rx) = mpsc::unbounded_channel();
        let metrics = Arc::new(RwLock::new(CoordinatorMetrics::default()));
        let metrics_clone = Arc::clone(&metrics);

        tokio::spawn(async move {
            Self::writer_task(db, rx, metrics_clone).await;
        });

        Self { tx, metrics }
    }

    pub fn submit(&self, write: PrioritizedWrite) -> std::result::Result<(), StorageError> {
        self.tx
            .send(write)
            .map_err(|_| StorageError::NotFound("WriteCoordinator channel closed".to_string()))
    }

    pub fn get_metrics(&self) -> CoordinatorMetrics {
        self.metrics.read().clone()
    }

    pub async fn insert_thought_batched(
        &self,
        id: &str,
        title: &str,
        content: &str,
        thought_type: &str,
        tags: &[String],
        priority: WritePriority,
    ) -> Result<()> {
        let (respond_to, rx) = oneshot::channel();
        self.submit(PrioritizedWrite {
            priority,
            request: WriteRequest::InsertThought {
                id: id.to_string(),
                title: title.to_string(),
                content: content.to_string(),
                thought_type: thought_type.to_string(),
                tags: tags.to_vec(),
                respond_to,
            },
        })?;
        rx.await.map_err(|_| StorageError::NotFound("Coordinator dropped response channel".to_string()))?
    }

    pub async fn insert_project_batched(
        &self,
        id: &str,
        name: &str,
        root_path: Option<&str>,
        repo_url: Option<&str>,
        priority: WritePriority,
    ) -> Result<()> {
        let (respond_to, rx) = oneshot::channel();
        self.submit(PrioritizedWrite {
            priority,
            request: WriteRequest::InsertProject {
                id: id.to_string(),
                name: name.to_string(),
                root_path: root_path.map(|s| s.to_string()),
                repo_url: repo_url.map(|s| s.to_string()),
                respond_to,
            },
        })?;
        rx.await.map_err(|_| StorageError::NotFound("Coordinator dropped response channel".to_string()))?
    }

    pub async fn insert_transaction_batched(
        &self,
        id: &str,
        description: &str,
        amount: f64,
        category: &str,
        priority: WritePriority,
    ) -> Result<String> {
        let (respond_to, rx) = oneshot::channel();
        self.submit(PrioritizedWrite {
            priority,
            request: WriteRequest::InsertTransaction {
                id: id.to_string(),
                description: description.to_string(),
                amount,
                category: category.to_string(),
                respond_to,
            },
        })?;
        rx.await.map_err(|_| StorageError::NotFound("Coordinator dropped response channel".to_string()))?
    }

    async fn writer_task(
        db: Database,
        mut rx: mpsc::UnboundedReceiver<PrioritizedWrite>,
        metrics: Arc<RwLock<CoordinatorMetrics>>,
    ) {
        let mut batch: Vec<PrioritizedWrite> = Vec::with_capacity(Self::BATCH_SIZE);

        loop {
            tokio::select! {
                maybe_write = rx.recv() => {
                    match maybe_write {
                        Some(write) => {
                            batch.push(write);
                            while batch.len() < Self::BATCH_SIZE {
                                match rx.try_recv() {
                                    Ok(w) => batch.push(w),
                                    Err(_) => break,
                                }
                            }
                            if batch.len() >= Self::BATCH_SIZE {
                                Self::flush_batch(&db, &mut batch, &metrics);
                            }
                        }
                        None => break, // channel closed
                    }
                }
                _ = tokio::time::sleep(Self::BATCH_TIMEOUT), if !batch.is_empty() => {
                    Self::flush_batch(&db, &mut batch, &metrics);
                }
            }
        }

        // Flush any remaining writes on shutdown
        if !batch.is_empty() {
            Self::flush_batch(&db, &mut batch, &metrics);
        }
    }

    fn flush_batch(
        db: &Database,
        batch: &mut Vec<PrioritizedWrite>,
        metrics: &Arc<RwLock<CoordinatorMetrics>>,
    ) {
        if batch.is_empty() {
            return;
        }

        // Sort by priority (P0 Interactive before P1 Background)
        batch.sort_by_key(|w| w.priority);

        let writes_count = batch.len() as u64;
        let mut p0 = 0;
        let mut p1 = 0;

        for item in batch.drain(..) {
            match item.priority {
                WritePriority::Interactive => p0 += 1,
                WritePriority::Background => p1 += 1,
            }

            match item.request {
                WriteRequest::InsertThought { id, title, content, thought_type, tags, respond_to } => {
                    let res = db.insert_thought(&id, &title, &content, &thought_type, &tags);
                    let _ = respond_to.send(res);
                }
                WriteRequest::InsertProject { id, name, root_path, repo_url, respond_to } => {
                    let res = db.insert_project(&id, &name, root_path.as_deref(), repo_url.as_deref());
                    let _ = respond_to.send(res);
                }
                WriteRequest::InsertTransaction { id, description, amount, category, respond_to } => {
                    let res = db.insert_transaction(&id, &description, amount, &category);
                    let _ = respond_to.send(res);
                }
                WriteRequest::ApproveTransaction { id, respond_to } => {
                    let res = db.approve_transaction(&id);
                    let _ = respond_to.send(res);
                }
                WriteRequest::InsertHabit { id, name, frequency, target_count, respond_to } => {
                    let res = db.insert_habit(&id, &name, &frequency, target_count);
                    let _ = respond_to.send(res);
                }
            }
        }

        let mut m = metrics.write();
        m.total_batches += 1;
        m.total_writes += writes_count;
        m.p0_writes += p0;
        m.p1_writes += p1;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_write_batching_coordinator() {
        let db = Database::open_in_memory().unwrap();
        let coordinator = WriteCoordinator::new(db.clone());

        // Concurrent submits across P0 and P1
        let mut handles = Vec::new();
        for i in 0..20 {
            let coord = coordinator.clone();
            let priority = if i % 2 == 0 {
                WritePriority::Interactive
            } else {
                WritePriority::Background
            };
            handles.push(tokio::spawn(async move {
                coord.insert_thought_batched(
                    &format!("thought-{}", i),
                    &format!("Title {}", i),
                    "Content of thought",
                    "atomic",
                    &["tag1".to_string()],
                    priority,
                ).await
            }));
        }

        for h in handles {
            let res = h.await.unwrap();
            assert!(res.is_ok());
        }

        let metrics = coordinator.get_metrics();
        assert_eq!(metrics.total_writes, 20);
        assert_eq!(metrics.p0_writes, 10);
        assert_eq!(metrics.p1_writes, 10);
        assert!(metrics.total_batches >= 1);

        // Verify thoughts are queryable
        let search = db.search_thoughts_fts("Title 0").unwrap();
        assert!(!search.is_empty());
    }
}
