---
gap_id: "GAP-003"
name: "Embedding Model Version Drift & Re-Indexing Strategy"
priority: "P1"
status: "specification"
created: "2026-10-04"
---

# Embedding Model Version Drift & Re-Indexing Invalidation

## Problem Statement

Personal OS uses vector embeddings for semantic search across thoughts, files, and interactions:
```yaml
# From hybrid_search_contract.json
embedding_model: "all-MiniLM-L6-v2 (384d) or text-embedding-3-small (1536d)"
```

**Critical Issues**:
1. **No Version Tracking**: SQLite schema has `embedding BLOB` with no model version metadata
   ```sql
   CREATE TABLE thoughts (
       ...
       embedding BLOB,  -- 384d or 1536d? Which model? When generated?
       ...
   );
   ```
2. **Incompatible Upgrades**: Switching models breaks existing embeddings
   - Upgrading 384d → 1536d: Dimension mismatch, all searches fail
   - Changing models (MiniLM → OpenAI): Different vector spaces, search quality degrades
3. **No Incremental Re-Index**: Must re-embed entire corpus at once (hours for 100K+ docs)
4. **Stale Embeddings**: Content updated but embedding not regenerated
5. **Multi-Model Support**: Cannot A/B test models or run hybrid retrieval

**Impact Scenarios**:
- User has 50,000 thoughts embedded with MiniLM (384d)
- Upgrade to OpenAI text-embedding-3-small (1536d) for better quality
- Options: (A) Re-embed all 50K thoughts (4+ hours), blocking system, or (B) Discard all embeddings, search broken until re-index complete

---

## Solution Architecture: Versioned Embedding Lifecycle

Implement **multi-version embedding coexistence** with incremental background re-indexing and graceful fallback.

### Key Components

1. **Embedding Version Registry**: Track model metadata (name, dimension, creation date)
2. **Versioned Vector Storage**: Store multiple embedding versions per document
3. **Incremental Re-Indexing**: Background workflow progressively migrates embeddings
4. **Hybrid Search Fallback**: Search uses latest available version per document
5. **Garbage Collection**: Purge old embeddings after migration complete

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                   Application Layer                           │
│         pos_thoughts │ pos_files │ pos_search                 │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│            pos_storage::EmbeddingCoordinator                  │
│                                                                │
│  ┌────────────────────────────────────────┐                  │
│  │  Embedding Version Registry            │                  │
│  │  - Model name, dimension, tokenizer    │                  │
│  │  - Creation timestamp, deprecation     │                  │
│  │  - Active version pointer              │                  │
│  └────────────────────────────────────────┘                  │
│                     │                                         │
│                     ▼                                         │
│  ┌────────────────────────────────────────┐                  │
│  │  Multi-Version Embedding Store         │                  │
│  │  - Document ID → [Version → Vector]    │                  │
│  │  - Stale embeddings marked for purge   │                  │
│  └────────────────────────────────────────┘                  │
│                     │                                         │
│                     ▼                                         │
│  ┌────────────────────────────────────────┐                  │
│  │  Incremental Re-Indexer (Background)   │                  │
│  │  - Priority queue: recent docs first   │                  │
│  │  - Rate limiting: 100 docs/min         │                  │
│  │  - Progress tracking & ETA             │                  │
│  └────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              SQLite + sqlite-vec Storage                      │
│  - embedding_versions table                                   │
│  - document_embeddings table (versioned)                      │
│  - re_index_queue table (work queue)                          │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Specification

### 1. SQLite Schema Extensions

```sql
-- Embedding model version registry
CREATE TABLE IF NOT EXISTS embedding_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL UNIQUE,  -- "all-MiniLM-L6-v2"
    model_provider TEXT NOT NULL,     -- "sentence-transformers", "openai", "local"
    dimension INTEGER NOT NULL,       -- 384, 1536, etc.
    tokenizer_config TEXT,            -- JSON config if needed
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deprecated_at DATETIME,           -- NULL if active
    is_active BOOLEAN NOT NULL DEFAULT 1,
    notes TEXT                        -- "Upgraded for better quality"
);

-- Multi-version embedding storage (replaces single embedding BLOB)
CREATE TABLE IF NOT EXISTS document_embeddings (
    document_id TEXT NOT NULL,
    document_type TEXT NOT NULL CHECK (document_type IN ('thought', 'file', 'interaction')),
    version_id INTEGER NOT NULL REFERENCES embedding_versions(version_id),
    embedding_vector BLOB NOT NULL,   -- sqlite-vec virtual table compatible
    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT NOT NULL,       -- BLAKE3 of embedded content (detect staleness)
    PRIMARY KEY (document_id, document_type, version_id)
);
CREATE INDEX idx_doc_embeddings_version ON document_embeddings(version_id, document_type);
CREATE INDEX idx_doc_embeddings_document ON document_embeddings(document_id, document_type);

-- Re-indexing work queue
CREATE TABLE IF NOT EXISTS re_index_queue (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    from_version_id INTEGER REFERENCES embedding_versions(version_id),
    to_version_id INTEGER NOT NULL REFERENCES embedding_versions(version_id),
    priority INTEGER NOT NULL DEFAULT 5,  -- 1=urgent (recent docs), 10=low (old docs)
    content_preview TEXT,                 -- First 200 chars for deduplication
    enqueued_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_started_at DATETIME,
    completed_at DATETIME,
    error_message TEXT,
    UNIQUE(document_id, document_type, to_version_id)
);
CREATE INDEX idx_re_index_priority ON re_index_queue(priority, enqueued_at) WHERE completed_at IS NULL;
CREATE INDEX idx_re_index_status ON re_index_queue(completed_at, processing_started_at);

-- sqlite-vec virtual table (per version)
CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings_v1 USING vec0(
    document_id TEXT PRIMARY KEY,
    embedding FLOAT[384]  -- Dimension for version 1
);

CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings_v2 USING vec0(
    document_id TEXT PRIMARY KEY,
    embedding FLOAT[1536]  -- Dimension for version 2
);

-- Migration tracking
CREATE TABLE IF NOT EXISTS embedding_migrations (
    migration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_version_id INTEGER REFERENCES embedding_versions(version_id),
    to_version_id INTEGER NOT NULL REFERENCES embedding_versions(version_id),
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    total_documents INTEGER NOT NULL,
    documents_completed INTEGER NOT NULL DEFAULT 0,
    documents_failed INTEGER NOT NULL DEFAULT 0,
    estimated_completion_at DATETIME
);

-- Remove single embedding column from existing tables (migration)
-- ALTER TABLE thoughts DROP COLUMN embedding;  -- Will be in document_embeddings
-- ALTER TABLE files DROP COLUMN embedding;
```

### 2. Embedding Coordinator

```rust
// workplace/modules/pos_storage/src/embedding/coordinator.rs

use sqlx::SqlitePool;
use std::sync::Arc;

pub struct EmbeddingCoordinator {
    pool: SqlitePool,
    active_version_id: Arc<RwLock<i32>>,
    embedder_registry: HashMap<i32, Box<dyn Embedder>>,
}

impl EmbeddingCoordinator {
    pub async fn new(pool: SqlitePool) -> Result<Self, EmbeddingError> {
        let active_version_id = Self::get_active_version(&pool).await?;
        
        let mut embedder_registry = HashMap::new();
        // Load all registered embedding models
        let versions = Self::load_all_versions(&pool).await?;
        for version in versions {
            let embedder = Self::create_embedder(&version)?;
            embedder_registry.insert(version.version_id, embedder);
        }
        
        Ok(Self {
            pool,
            active_version_id: Arc::new(RwLock::new(active_version_id)),
            embedder_registry,
        })
    }
    
    /// Register new embedding model version
    pub async fn register_version(
        &mut self,
        model_name: &str,
        model_provider: &str,
        dimension: usize,
    ) -> Result<i32, EmbeddingError> {
        let version_id = sqlx::query_scalar!(
            "INSERT INTO embedding_versions (model_name, model_provider, dimension, is_active)
             VALUES (?, ?, ?, 0)
             RETURNING version_id",
            model_name,
            model_provider,
            dimension as i32
        )
        .fetch_one(&self.pool)
        .await?;
        
        // Create sqlite-vec virtual table for new version
        sqlx::query(&format!(
            "CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings_v{} USING vec0(
                document_id TEXT PRIMARY KEY,
                embedding FLOAT[{}]
            )",
            version_id, dimension
        ))
        .execute(&self.pool)
        .await?;
        
        // Register embedder
        let embedder = Self::create_embedder_by_name(model_name, model_provider)?;
        self.embedder_registry.insert(version_id, embedder);
        
        Ok(version_id)
    }
    
    /// Activate new version and trigger migration
    pub async fn activate_version(
        &self,
        new_version_id: i32,
    ) -> Result<MigrationHandle, EmbeddingError> {
        let old_version_id = *self.active_version_id.read().await;
        
        // Start migration
        let migration_id = sqlx::query_scalar!(
            "INSERT INTO embedding_migrations (from_version_id, to_version_id, total_documents)
             VALUES (?, ?, (SELECT COUNT(DISTINCT document_id) FROM document_embeddings WHERE version_id = ?))
             RETURNING migration_id",
            old_version_id,
            new_version_id,
            old_version_id
        )
        .fetch_one(&self.pool)
        .await?;
        
        // Enqueue all documents for re-indexing
        sqlx::query!(
            "INSERT INTO re_index_queue (document_id, document_type, from_version_id, to_version_id, priority)
             SELECT 
                 de.document_id,
                 de.document_type,
                 ?,
                 ?,
                 CASE 
                     WHEN t.updated_at > datetime('now', '-7 days') THEN 1  -- Recent docs first
                     WHEN t.updated_at > datetime('now', '-30 days') THEN 5
                     ELSE 10
                 END as priority
             FROM document_embeddings de
             LEFT JOIN thoughts t ON de.document_id = t.id AND de.document_type = 'thought'
             WHERE de.version_id = ?",
            old_version_id,
            new_version_id,
            old_version_id
        )
        .execute(&self.pool)
        .await?;
        
        // Update active version
        sqlx::query!(
            "UPDATE embedding_versions SET is_active = 0 WHERE version_id = ?;
             UPDATE embedding_versions SET is_active = 1 WHERE version_id = ?;",
            old_version_id,
            new_version_id
        )
        .execute(&self.pool)
        .await?;
        
        *self.active_version_id.write().await = new_version_id;
        
        Ok(MigrationHandle { migration_id })
    }
    
    /// Embed document with active version
    pub async fn embed_document(
        &self,
        document_id: &str,
        document_type: &str,
        content: &str,
    ) -> Result<(), EmbeddingError> {
        let version_id = *self.active_version_id.read().await;
        let embedder = self.embedder_registry.get(&version_id)
            .ok_or(EmbeddingError::EmbedderNotFound(version_id))?;
        
        let vector = embedder.encode(content).await?;
        let content_hash = blake3::hash(content.as_bytes()).to_hex();
        
        // Store in document_embeddings
        sqlx::query!(
            "INSERT INTO document_embeddings (document_id, document_type, version_id, embedding_vector, content_hash)
             VALUES (?, ?, ?, ?, ?)
             ON CONFLICT(document_id, document_type, version_id)
             DO UPDATE SET embedding_vector = excluded.embedding_vector,
                          content_hash = excluded.content_hash,
                          generated_at = CURRENT_TIMESTAMP",
            document_id,
            document_type,
            version_id,
            vector.as_bytes(),
            content_hash.as_str()
        )
        .execute(&self.pool)
        .await?;
        
        // Store in sqlite-vec virtual table
        sqlx::query(&format!(
            "INSERT INTO vec_embeddings_v{} (document_id, embedding) VALUES (?, ?)
             ON CONFLICT(document_id) DO UPDATE SET embedding = excluded.embedding",
            version_id
        ))
        .bind(document_id)
        .bind(vector.as_bytes())
        .execute(&self.pool)
        .await?;
        
        Ok(())
    }
    
    /// Get best available embedding for document (fallback to older version if new not ready)
    pub async fn get_embedding(
        &self,
        document_id: &str,
        document_type: &str,
    ) -> Result<Option<(i32, Vec<f32>)>, EmbeddingError> {
        let result = sqlx::query!(
            "SELECT version_id, embedding_vector
             FROM document_embeddings
             WHERE document_id = ? AND document_type = ?
             ORDER BY version_id DESC
             LIMIT 1",
            document_id,
            document_type
        )
        .fetch_optional(&self.pool)
        .await?;
        
        match result {
            Some(row) => {
                let vector = Self::deserialize_vector(&row.embedding_vector)?;
                Ok(Some((row.version_id, vector)))
            }
            None => Ok(None),
        }
    }
    
    /// Check if document embedding is stale (content changed)
    pub async fn is_stale(
        &self,
        document_id: &str,
        document_type: &str,
        current_content: &str,
    ) -> Result<bool, EmbeddingError> {
        let current_hash = blake3::hash(current_content.as_bytes()).to_hex();
        
        let stored_hash = sqlx::query_scalar!(
            "SELECT content_hash FROM document_embeddings
             WHERE document_id = ? AND document_type = ? AND version_id = ?",
            document_id,
            document_type,
            *self.active_version_id.read().await
        )
        .fetch_optional(&self.pool)
        .await?;
        
        Ok(stored_hash.map(|h| h != current_hash.as_str()).unwrap_or(true))
    }
}
```

### 3. Background Re-Indexing Workflow

```yaml
---
workflow_id: "wf_embedding_migration"
name: "Incremental Embedding Re-Indexing"
version: "1.0.0"
status: "specification"

metadata:
  description: "Background task to progressively re-index documents with new embedding model"
  category: "system"
  priority: "low"
  estimated_duration: "hours to days (depends on corpus size)"

trigger:
  type: "on_demand"  # Triggered by EmbeddingCoordinator.activate_version()
  conditions:
    - "re_index_queue has pending items"

inputs:
  migration_id:
    type: "integer"
    description: "Migration tracking ID"
  batch_size:
    type: "integer"
    default: 100
    description: "Documents to process per iteration"
  rate_limit_delay_ms:
    type: "integer"
    default: 600
    description: "Delay between batches (600ms = 100 docs/min)"

steps:
  # Step 1: Check queue depth
  - id: "check_queue"
    name: "Get Pending Work Count"
    action: "query_database"
    input:
      query: |
        SELECT COUNT(*) as pending_count
        FROM re_index_queue
        WHERE completed_at IS NULL
    output_binding: "queue_status"
    timeout: 1000

  # Step 2: Fetch batch (priority order)
  - id: "fetch_batch"
    name: "Get Next Batch of Documents"
    action: "query_database"
    input:
      query: |
        SELECT queue_id, document_id, document_type, to_version_id
        FROM re_index_queue
        WHERE completed_at IS NULL AND processing_started_at IS NULL
        ORDER BY priority ASC, enqueued_at ASC
        LIMIT ?
      params: ["${inputs.batch_size}"]
    output_binding: "batch"
    timeout: 2000

  # Step 3: Mark batch as processing
  - id: "mark_processing"
    name: "Update Processing Status"
    action: "execute_update"
    input:
      query: |
        UPDATE re_index_queue
        SET processing_started_at = CURRENT_TIMESTAMP
        WHERE queue_id IN (${batch.queue_ids})
    timeout: 1000

  # Step 4: Generate embeddings
  - id: "generate_embeddings"
    name: "Re-Embed Documents"
    agent: "agent_embedding_worker"
    tool: "batch_embed"
    input:
      documents: "${batch}"
    output_binding: "embedding_results"
    timeout: 60000  # 1 minute for batch
    retry_policy:
      max_retries: 2
      backoff: "exponential"

  # Step 5: Update migration progress
  - id: "update_progress"
    name: "Update Migration Tracking"
    action: "execute_update"
    input:
      query: |
        UPDATE embedding_migrations
        SET documents_completed = documents_completed + ?,
            documents_failed = documents_failed + ?,
            estimated_completion_at = datetime('now', '+' || 
              CAST((total_documents - documents_completed - ?) * ? / 1000 / 60 AS TEXT) || ' minutes')
        WHERE migration_id = ?
      params:
        - "${embedding_results.success_count}"
        - "${embedding_results.failed_count}"
        - "${embedding_results.success_count}"
        - "${inputs.rate_limit_delay_ms}"
        - "${inputs.migration_id}"
    timeout: 1000

  # Step 6: Mark completed
  - id: "mark_completed"
    name: "Mark Batch Complete"
    action: "execute_update"
    input:
      query: |
        UPDATE re_index_queue
        SET completed_at = CURRENT_TIMESTAMP,
            error_message = CASE WHEN queue_id IN (${embedding_results.failed_ids}) THEN 'Embedding generation failed' ELSE NULL END
        WHERE queue_id IN (${batch.queue_ids})
    timeout: 1000

  # Step 7: Rate limiting delay
  - id: "rate_limit_delay"
    name: "Throttle Next Iteration"
    action: "sleep"
    input:
      duration_ms: "${inputs.rate_limit_delay_ms}"

  # Step 8: Check if migration complete
  - id: "check_completion"
    name: "Check Migration Status"
    action: "query_database"
    input:
      query: |
        SELECT 
          (SELECT COUNT(*) FROM re_index_queue WHERE completed_at IS NULL) as remaining,
          (SELECT documents_completed FROM embedding_migrations WHERE migration_id = ?) as completed
      params: ["${inputs.migration_id}"]
    output_binding: "completion_status"
    timeout: 1000

  # Step 9: Self-trigger if more work
  - id: "continue_migration"
    name: "Schedule Next Batch"
    action: "trigger_workflow"
    input:
      workflow_id: "wf_embedding_migration"
      inputs:
        migration_id: "${inputs.migration_id}"
        batch_size: "${inputs.batch_size}"
        rate_limit_delay_ms: "${inputs.rate_limit_delay_ms}"
    condition: "${completion_status.remaining > 0}"

  # Step 10: Finalize migration
  - id: "finalize"
    name: "Mark Migration Complete"
    action: "execute_update"
    input:
      query: |
        UPDATE embedding_migrations
        SET completed_at = CURRENT_TIMESTAMP
        WHERE migration_id = ? AND (SELECT COUNT(*) FROM re_index_queue WHERE completed_at IS NULL) = 0
      params: ["${inputs.migration_id}"]
    condition: "${completion_status.remaining == 0}"
    timeout: 1000

performance_targets:
  batch_duration: "< 60 seconds"
  throughput: "~100 documents per minute"
  system_impact: "< 10% CPU usage"

monitoring:
  metrics:
    - name: "embedding_migration_progress"
      type: "gauge"
      query: "SELECT documents_completed * 100.0 / total_documents FROM embedding_migrations WHERE completed_at IS NULL"
    
    - name: "embedding_migration_eta"
      type: "gauge"
      query: "SELECT CAST(strftime('%s', estimated_completion_at) - strftime('%s', 'now') AS INTEGER) FROM embedding_migrations WHERE completed_at IS NULL"
```

### 4. Hybrid Search with Version Fallback

```rust
// workplace/modules/pos_storage/src/search/hybrid_search.rs

impl HybridSearch {
    pub async fn search_with_fallback(
        &self,
        query: &str,
        limit: usize,
    ) -> Result<Vec<SearchResult>, SearchError> {
        let active_version_id = *self.embedding_coordinator.active_version_id.read().await;
        
        // Try search with active version
        let results = self.vector_search(query, active_version_id, limit).await?;
        
        // If not enough results (migration in progress), fall back to previous version
        if results.len() < limit / 2 {
            let previous_version_id = self.get_previous_version(active_version_id).await?;
            if let Some(prev_id) = previous_version_id {
                let fallback_results = self.vector_search(query, prev_id, limit).await?;
                // Merge and deduplicate results
                return Ok(Self::merge_results(results, fallback_results, limit));
            }
        }
        
        Ok(results)
    }
}
```

---

## Performance Targets

| Metric | Target | Max |
|--------|--------|-----|
| Re-indexing throughput | 100 docs/min | 200 docs/min |
| Migration duration (10K docs) | 2 hours | 4 hours |
| Migration duration (100K docs) | 20 hours | 48 hours |
| Search latency during migration | +10ms | +50ms |
| Storage overhead (multiple versions) | +30% | +100% |

---

## Migration Strategy

### Phase 1: Schema Update (Week 1)
- Add `embedding_versions`, `document_embeddings`, `re_index_queue` tables
- Migrate existing embeddings to versioned storage (version 1 = current model)
- Remove single `embedding BLOB` columns from `thoughts` and `files`

### Phase 2: Coordinator Implementation (Week 2)
- Implement `EmbeddingCoordinator`
- Multi-version storage and retrieval
- Version activation workflow

### Phase 3: Background Re-Indexer (Week 3)
- Implement `wf_embedding_migration` workflow
- Priority queue processing
- Progress tracking and ETA calculation

### Phase 4: Validation (Week 4)
- Test model upgrade scenario (384d → 1536d)
- Validate incremental migration (no service disruption)
- Performance benchmarking

---

## Benefits

1. **Zero Downtime Upgrades**: Migrate embeddings incrementally without blocking searches
2. **Multi-Model Support**: Run A/B tests, hybrid retrieval strategies
3. **Staleness Detection**: Automatically re-embed when content changes
4. **Graceful Degradation**: Search works during migration using older embeddings
5. **Audit Trail**: Track which model generated each embedding

---

## Crate Dependencies

```toml
[dependencies]
sqlx = { version = "0.7", features = ["sqlite"] }
blake3 = "1.5"
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["full"] }
```

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Implement `EmbeddingCoordinator` with version registry
