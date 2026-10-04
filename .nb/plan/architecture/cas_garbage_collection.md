---
gap_id: "GAP-009"
name: "Content-Addressed Storage Lifecycle & Garbage Collection"
priority: "P1"
status: "specification"
created: "2026-10-04"
---

# CAS Storage Lifecycle: Mark-and-Sweep Garbage Collection with Tiered Compression

## Problem Statement

Current CAS (Content-Addressed Storage) implementation in `pos_storage`:

```rust
// workplace/modules/pos_storage/src/cas.rs
pub async fn store_blob(
    &self,
    content: &[u8],
) -> Result<String, StorageError> {
    let hash = blake3::hash(content);
    let hash_hex = hash.to_hex();
    
    let blob_path = self.blob_path(&hash_hex);
    fs::write(blob_path, content).await?;
    
    Ok(hash_hex.to_string())
}
```

### Storage Bloat Scenario

```
Day 1:  User uploads 20 email attachments (50 MB total)
        → CAS stores 20 blobs

Day 30: User deletes all emails
        → SQLite references removed
        → CAS blobs remain on disk (50 MB orphaned)

Month 6: User has processed 5000 emails, 500 receipts, 200 audio memos
        → CAS accumulates 15 GB of data
        → 40% is orphaned (6 GB wasted)
        → No automatic reclamation
```

**Impact**:
- Unbounded disk growth (exponential over years)
- Backup bloat (orphaned blobs backed up to Time Machine/cloud)
- No storage quotas or alerts
- Performance degradation (large directory listings)

---

## Solution Architecture: Two-Phase Mark-and-Sweep GC

### Overview

Implement **generational garbage collection** with three tiers:

1. **Hot Tier** (0-30 days): Uncompressed, frequently accessed
2. **Warm Tier** (30-90 days): Zstd level 9 compression
3. **Cold Tier** (90+ days): Zstd level 19 compression, archival

**Garbage Collection Flow**:
```
┌────────────────────────────────────────────┐
│  Phase 1: Mark (Identify Live Blobs)      │
│  - Scan all SQLite foreign keys            │
│  - Mark referenced blobs as "live"         │
└────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────┐
│  Phase 2: Sweep (Delete Orphaned Blobs)   │
│  - Find blobs not marked "live"            │
│  - Grace period: 14 days since last access │
│  - Move to trash or delete permanently     │
└────────────────────────────────────────────┘
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CAS Storage Layout                        │
├─────────────────────────────────────────────────────────────┤
│  ~/.pos/cas/                                                 │
│    ├── hot/              (uncompressed, 0-30 days)          │
│    │   ├── a3/f2/a3f2b9c1e4d6...  (BLAKE3 hash)            │
│    │   └── b7/8a/b78a3c2f1e9d...                            │
│    ├── warm/             (zstd level 9, 30-90 days)         │
│    │   ├── c2/3e/c23e9f7b1a4d....zst                        │
│    │   └── d5/1c/d51c8a6f3b2e....zst                        │
│    └── cold/             (zstd level 19, 90+ days)          │
│        ├── e8/4f/e84f2c1d9a7b....zst                        │
│        └── f9/a2/f9a27e5c3d1f....zst                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              SQLite Reference Tracking                       │
├─────────────────────────────────────────────────────────────┤
│  CREATE TABLE cas_references (                               │
│    blob_hash TEXT NOT NULL,                                  │
│    referrer_table TEXT NOT NULL,  -- 'email_attachments'    │
│    referrer_id TEXT NOT NULL,     -- email UUID             │
│    created_at DATETIME,                                      │
│    PRIMARY KEY (blob_hash, referrer_table, referrer_id)     │
│  );                                                           │
│                                                               │
│  CREATE INDEX idx_cas_blob_hash ON cas_references(blob_hash);│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Garbage Collection Workflow                     │
├─────────────────────────────────────────────────────────────┤
│  1. Daily: Tier Promotion                                    │
│     - Find blobs older than 30 days in hot/ → warm/          │
│     - Find blobs older than 90 days in warm/ → cold/         │
│                                                               │
│  2. Weekly: Mark-and-Sweep GC                                │
│     - Mark Phase: Scan cas_references table                  │
│     - Sweep Phase: Delete blobs with zero references         │
│       + Grace period: 14 days since last access              │
│                                                               │
│  3. Monthly: Quota Enforcement                               │
│     - Calculate total CAS size                               │
│     - Alert if > 80% of user-defined quota                   │
│     - Suggest cleanup candidates                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Specification

### 1. Reference Tracking Schema

```sql
-- workplace/modules/pos_storage/migrations/009_cas_references.sql

CREATE TABLE IF NOT EXISTS cas_references (
    blob_hash TEXT NOT NULL,
    referrer_table TEXT NOT NULL,
    referrer_id TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (blob_hash, referrer_table, referrer_id)
) WITHOUT ROWID;

CREATE INDEX idx_cas_blob_hash ON cas_references(blob_hash);
CREATE INDEX idx_cas_referrer ON cas_references(referrer_table, referrer_id);
CREATE INDEX idx_cas_last_accessed ON cas_references(last_accessed_at);

-- Metadata for GC runs
CREATE TABLE IF NOT EXISTS cas_gc_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    blobs_scanned INTEGER NOT NULL DEFAULT 0,
    blobs_deleted INTEGER NOT NULL DEFAULT 0,
    bytes_reclaimed INTEGER NOT NULL DEFAULT 0,
    errors TEXT
);

-- Storage tier tracking
CREATE TABLE IF NOT EXISTS cas_blob_metadata (
    blob_hash TEXT PRIMARY KEY,
    tier TEXT NOT NULL CHECK (tier IN ('hot', 'warm', 'cold')),
    original_size_bytes INTEGER NOT NULL,
    compressed_size_bytes INTEGER,
    compression_algo TEXT,  -- 'none', 'zstd-9', 'zstd-19'
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    promoted_to_tier_at DATETIME
) WITHOUT ROWID;

CREATE INDEX idx_cas_tier ON cas_blob_metadata(tier);
CREATE INDEX idx_cas_promoted_at ON cas_blob_metadata(promoted_to_tier_at);
```

### 2. Reference Counting Coordinator

```rust
// workplace/modules/pos_storage/src/cas_refcount.rs

use sqlx::SqlitePool;
use std::sync::Arc;

pub struct CASReferenceTracker {
    pool: SqlitePool,
}

impl CASReferenceTracker {
    pub fn new(pool: SqlitePool) -> Self {
        Self { pool }
    }
    
    /// Register a new reference to a CAS blob
    pub async fn add_reference(
        &self,
        blob_hash: &str,
        referrer_table: &str,
        referrer_id: &str,
    ) -> Result<(), StorageError> {
        sqlx::query!(
            r#"
            INSERT INTO cas_references (blob_hash, referrer_table, referrer_id)
            VALUES (?1, ?2, ?3)
            ON CONFLICT (blob_hash, referrer_table, referrer_id) DO UPDATE
            SET last_accessed_at = CURRENT_TIMESTAMP
            "#,
            blob_hash,
            referrer_table,
            referrer_id,
        )
        .execute(&self.pool)
        .await?;
        
        Ok(())
    }
    
    /// Remove a reference (when entity is deleted)
    pub async fn remove_reference(
        &self,
        blob_hash: &str,
        referrer_table: &str,
        referrer_id: &str,
    ) -> Result<(), StorageError> {
        sqlx::query!(
            r#"
            DELETE FROM cas_references
            WHERE blob_hash = ?1 AND referrer_table = ?2 AND referrer_id = ?3
            "#,
            blob_hash,
            referrer_table,
            referrer_id,
        )
        .execute(&self.pool)
        .await?;
        
        Ok(())
    }
    
    /// Get reference count for a blob
    pub async fn get_reference_count(
        &self,
        blob_hash: &str,
    ) -> Result<i64, StorageError> {
        let row = sqlx::query!(
            r#"
            SELECT COUNT(*) as count
            FROM cas_references
            WHERE blob_hash = ?1
            "#,
            blob_hash,
        )
        .fetch_one(&self.pool)
        .await?;
        
        Ok(row.count)
    }
    
    /// Update last accessed timestamp (for LRU eviction)
    pub async fn touch_blob(
        &self,
        blob_hash: &str,
    ) -> Result<(), StorageError> {
        sqlx::query!(
            r#"
            UPDATE cas_references
            SET last_accessed_at = CURRENT_TIMESTAMP
            WHERE blob_hash = ?1
            "#,
            blob_hash,
        )
        .execute(&self.pool)
        .await?;
        
        Ok(())
    }
}
```

### 3. Mark-and-Sweep Garbage Collector

```rust
// workplace/modules/pos_storage/src/cas_gc.rs

use std::collections::HashSet;
use std::path::{Path, PathBuf};
use tokio::fs;

pub struct CASGarbageCollector {
    pool: SqlitePool,
    cas_root: PathBuf,
    grace_period_days: i64,
}

impl CASGarbageCollector {
    pub fn new(pool: SqlitePool, cas_root: PathBuf) -> Self {
        Self {
            pool,
            cas_root,
            grace_period_days: 14,
        }
    }
    
    /// Run full mark-and-sweep GC
    pub async fn run(&self) -> Result<GCStats, StorageError> {
        let run_id = self.start_gc_run().await?;
        
        info!("Starting GC run {}", run_id);
        
        // Phase 1: Mark (identify live blobs)
        let live_blobs = self.mark_phase().await?;
        
        info!("Mark phase complete: {} live blobs", live_blobs.len());
        
        // Phase 2: Sweep (delete unreferenced blobs)
        let stats = self.sweep_phase(&live_blobs).await?;
        
        self.complete_gc_run(run_id, &stats).await?;
        
        info!("GC run {} complete: deleted {} blobs, reclaimed {} bytes",
            run_id, stats.blobs_deleted, stats.bytes_reclaimed);
        
        Ok(stats)
    }
    
    /// Mark Phase: Scan all references to identify live blobs
    async fn mark_phase(&self) -> Result<HashSet<String>, StorageError> {
        let mut live_blobs = HashSet::new();
        
        // Scan cas_references table
        let mut rows = sqlx::query!(
            r#"
            SELECT DISTINCT blob_hash
            FROM cas_references
            "#
        )
        .fetch(&self.pool);
        
        while let Some(row) = rows.try_next().await? {
            live_blobs.insert(row.blob_hash);
        }
        
        Ok(live_blobs)
    }
    
    /// Sweep Phase: Delete unreferenced blobs (with grace period)
    async fn sweep_phase(
        &self,
        live_blobs: &HashSet<String>,
    ) -> Result<GCStats, StorageError> {
        let mut stats = GCStats::default();
        
        // Scan all tiers
        for tier in &["hot", "warm", "cold"] {
            let tier_stats = self.sweep_tier(tier, live_blobs).await?;
            stats.blobs_scanned += tier_stats.blobs_scanned;
            stats.blobs_deleted += tier_stats.blobs_deleted;
            stats.bytes_reclaimed += tier_stats.bytes_reclaimed;
        }
        
        Ok(stats)
    }
    
    async fn sweep_tier(
        &self,
        tier: &str,
        live_blobs: &HashSet<String>,
    ) -> Result<GCStats, StorageError> {
        let mut stats = GCStats::default();
        let tier_path = self.cas_root.join(tier);
        
        // Recursively scan tier directory
        let mut entries = fs::read_dir(&tier_path).await?;
        
        while let Some(entry) = entries.next_entry().await? {
            let path = entry.path();
            
            if path.is_dir() {
                // Recurse into subdirectory (hash prefix)
                continue;
            }
            
            stats.blobs_scanned += 1;
            
            // Extract blob hash from filename
            let blob_hash = self.extract_blob_hash(&path)?;
            
            // Check if blob is live
            if live_blobs.contains(&blob_hash) {
                continue;  // Keep this blob
            }
            
            // Check grace period
            let metadata = fs::metadata(&path).await?;
            let last_accessed = metadata.accessed()?;
            let age_days = (SystemTime::now().duration_since(last_accessed)?).as_secs() / 86400;
            
            if age_days < self.grace_period_days as u64 {
                continue;  // Too recent, skip for now
            }
            
            // Delete orphaned blob
            let size = metadata.len();
            fs::remove_file(&path).await?;
            
            stats.blobs_deleted += 1;
            stats.bytes_reclaimed += size;
            
            info!("Deleted orphaned blob: {} (age: {} days, size: {} bytes)",
                blob_hash, age_days, size);
        }
        
        Ok(stats)
    }
    
    fn extract_blob_hash(&self, path: &Path) -> Result<String, StorageError> {
        let filename = path.file_name().unwrap().to_str().unwrap();
        
        // Remove .zst extension if compressed
        let hash = filename.strip_suffix(".zst").unwrap_or(filename);
        
        Ok(hash.to_string())
    }
    
    async fn start_gc_run(&self) -> Result<i64, StorageError> {
        let row = sqlx::query!(
            r#"
            INSERT INTO cas_gc_runs (started_at)
            VALUES (CURRENT_TIMESTAMP)
            RETURNING run_id
            "#
        )
        .fetch_one(&self.pool)
        .await?;
        
        Ok(row.run_id)
    }
    
    async fn complete_gc_run(
        &self,
        run_id: i64,
        stats: &GCStats,
    ) -> Result<(), StorageError> {
        sqlx::query!(
            r#"
            UPDATE cas_gc_runs
            SET completed_at = CURRENT_TIMESTAMP,
                blobs_scanned = ?2,
                blobs_deleted = ?3,
                bytes_reclaimed = ?4
            WHERE run_id = ?1
            "#,
            run_id,
            stats.blobs_scanned,
            stats.blobs_deleted,
            stats.bytes_reclaimed as i64,
        )
        .execute(&self.pool)
        .await?;
        
        Ok(())
    }
}

#[derive(Debug, Default)]
pub struct GCStats {
    pub blobs_scanned: i64,
    pub blobs_deleted: i64,
    pub bytes_reclaimed: u64,
}
```

### 4. Tier Promotion (Compression)

```rust
// workplace/modules/pos_storage/src/cas_tier_promotion.rs

use zstd::Encoder;

pub struct TierPromoter {
    pool: SqlitePool,
    cas_root: PathBuf,
}

impl TierPromoter {
    pub async fn promote_hot_to_warm(&self) -> Result<PromotionStats, StorageError> {
        let cutoff_date = (Utc::now() - Duration::days(30)).to_rfc3339();
        
        let blobs = sqlx::query!(
            r#"
            SELECT blob_hash, original_size_bytes
            FROM cas_blob_metadata
            WHERE tier = 'hot'
              AND created_at < ?1
            "#,
            cutoff_date,
        )
        .fetch_all(&self.pool)
        .await?;
        
        let mut stats = PromotionStats::default();
        
        for blob in blobs {
            self.compress_and_move(
                &blob.blob_hash,
                "hot",
                "warm",
                9,  // Zstd level 9
            ).await?;
            
            stats.blobs_promoted += 1;
        }
        
        Ok(stats)
    }
    
    pub async fn promote_warm_to_cold(&self) -> Result<PromotionStats, StorageError> {
        let cutoff_date = (Utc::now() - Duration::days(90)).to_rfc3339();
        
        let blobs = sqlx::query!(
            r#"
            SELECT blob_hash
            FROM cas_blob_metadata
            WHERE tier = 'warm'
              AND promoted_to_tier_at < ?1
            "#,
            cutoff_date,
        )
        .fetch_all(&self.pool)
        .await?;
        
        let mut stats = PromotionStats::default();
        
        for blob in blobs {
            self.compress_and_move(
                &blob.blob_hash,
                "warm",
                "cold",
                19,  // Zstd level 19 (maximum compression)
            ).await?;
            
            stats.blobs_promoted += 1;
        }
        
        Ok(stats)
    }
    
    async fn compress_and_move(
        &self,
        blob_hash: &str,
        from_tier: &str,
        to_tier: &str,
        compression_level: i32,
    ) -> Result<(), StorageError> {
        let from_path = self.blob_path(from_tier, blob_hash);
        let to_path = self.blob_path(to_tier, &format!("{}.zst", blob_hash));
        
        // Read original blob
        let data = fs::read(&from_path).await?;
        let original_size = data.len();
        
        // Compress with Zstd
        let mut encoder = Encoder::new(Vec::new(), compression_level)?;
        encoder.write_all(&data)?;
        let compressed_data = encoder.finish()?;
        let compressed_size = compressed_data.len();
        
        // Write to new tier
        fs::create_dir_all(to_path.parent().unwrap()).await?;
        fs::write(&to_path, compressed_data).await?;
        
        // Delete original
        fs::remove_file(&from_path).await?;
        
        // Update metadata
        sqlx::query!(
            r#"
            UPDATE cas_blob_metadata
            SET tier = ?1,
                compressed_size_bytes = ?2,
                compression_algo = ?3,
                promoted_to_tier_at = CURRENT_TIMESTAMP
            WHERE blob_hash = ?4
            "#,
            to_tier,
            compressed_size as i64,
            format!("zstd-{}", compression_level),
            blob_hash,
        )
        .execute(&self.pool)
        .await?;
        
        info!("Promoted blob {} from {} to {} (compression ratio: {:.2}x)",
            blob_hash, from_tier, to_tier,
            original_size as f64 / compressed_size as f64);
        
        Ok(())
    }
    
    fn blob_path(&self, tier: &str, blob_hash: &str) -> PathBuf {
        // Split hash into directory structure: a3f2b9c1 → a3/f2/a3f2b9c1
        let prefix1 = &blob_hash[0..2];
        let prefix2 = &blob_hash[2..4];
        
        self.cas_root
            .join(tier)
            .join(prefix1)
            .join(prefix2)
            .join(blob_hash)
    }
}

#[derive(Debug, Default)]
pub struct PromotionStats {
    pub blobs_promoted: i64,
}
```

### 5. Quota Enforcement

```rust
// workplace/modules/pos_storage/src/cas_quota.rs

pub struct QuotaSentinel {
    pool: SqlitePool,
    cas_root: PathBuf,
    quota_bytes: u64,
}

impl QuotaSentinel {
    pub fn new(pool: SqlitePool, cas_root: PathBuf, quota_gb: u64) -> Self {
        Self {
            pool,
            cas_root,
            quota_bytes: quota_gb * 1024 * 1024 * 1024,
        }
    }
    
    pub async fn check_quota(&self) -> Result<QuotaStatus, StorageError> {
        let total_bytes = self.calculate_total_size().await?;
        let usage_percent = (total_bytes as f64 / self.quota_bytes as f64) * 100.0;
        
        let status = if usage_percent >= 95.0 {
            QuotaStatus::Critical
        } else if usage_percent >= 80.0 {
            QuotaStatus::Warning
        } else {
            QuotaStatus::OK
        };
        
        info!("CAS storage: {} / {} GB ({:.1}% used)",
            total_bytes / (1024 * 1024 * 1024),
            self.quota_bytes / (1024 * 1024 * 1024),
            usage_percent);
        
        Ok(status)
    }
    
    async fn calculate_total_size(&self) -> Result<u64, StorageError> {
        let mut total = 0u64;
        
        for tier in &["hot", "warm", "cold"] {
            let tier_path = self.cas_root.join(tier);
            total += Self::dir_size(&tier_path).await?;
        }
        
        Ok(total)
    }
    
    async fn dir_size(path: &Path) -> Result<u64, StorageError> {
        let mut total = 0u64;
        let mut entries = fs::read_dir(path).await?;
        
        while let Some(entry) = entries.next_entry().await? {
            let metadata = entry.metadata().await?;
            
            if metadata.is_dir() {
                total += Self::dir_size(&entry.path()).await?;
            } else {
                total += metadata.len();
            }
        }
        
        Ok(total)
    }
    
    pub async fn suggest_cleanup_candidates(&self) -> Result<Vec<CleanupCandidate>, StorageError> {
        // Find largest unreferenced blobs (grace period expired)
        let candidates = sqlx::query_as!(
            CleanupCandidate,
            r#"
            SELECT bm.blob_hash, bm.original_size_bytes, bm.last_accessed_at
            FROM cas_blob_metadata bm
            LEFT JOIN cas_references cr ON bm.blob_hash = cr.blob_hash
            WHERE cr.blob_hash IS NULL
              AND julianday('now') - julianday(bm.last_accessed_at) > 14
            ORDER BY bm.original_size_bytes DESC
            LIMIT 100
            "#
        )
        .fetch_all(&self.pool)
        .await?;
        
        Ok(candidates)
    }
}

#[derive(Debug)]
pub enum QuotaStatus {
    OK,
    Warning,   // 80-95% full
    Critical,  // 95%+ full
}

#[derive(Debug)]
pub struct CleanupCandidate {
    pub blob_hash: String,
    pub original_size_bytes: i64,
    pub last_accessed_at: String,
}
```

---

## Background Workflow

```yaml
# workplace/config/workflows/wf_cas_maintenance.yaml

name: "cas_maintenance"
description: "Daily CAS maintenance: tier promotion, garbage collection, quota checks"
trigger:
  cron: "0 2 * * *"  # Run at 2 AM daily

steps:
  - name: "promote_hot_to_warm"
    tool: "cas_tier_promote"
    input:
      from_tier: "hot"
      to_tier: "warm"
      age_days: 30
    
  - name: "promote_warm_to_cold"
    tool: "cas_tier_promote"
    input:
      from_tier: "warm"
      to_tier: "cold"
      age_days: 90
  
  - name: "run_garbage_collection"
    tool: "cas_gc_run"
    input:
      grace_period_days: 14
  
  - name: "check_quota"
    tool: "cas_quota_check"
    input:
      quota_gb: 50
    
  - name: "send_quota_alert"
    tool: "notification_send"
    condition: "{{check_quota.status}} == 'Warning' OR {{check_quota.status}} == 'Critical'"
    input:
      message: "⚠️ CAS storage at {{check_quota.usage_percent}}% of quota"
```

---

## CLI Commands

```bash
# Run manual GC
pos storage gc

# Output:
# 🧹 Running garbage collection...
# Mark phase: found 4,521 live blobs
# Sweep phase: deleted 327 orphaned blobs (1.2 GB reclaimed)
# ✅ GC complete

# Check storage quota
pos storage quota

# Output:
# 📊 CAS Storage Usage:
# Hot:   2.4 GB (12,450 blobs)
# Warm:  8.1 GB (32,100 blobs) [compressed]
# Cold:  4.8 GB (18,000 blobs) [highly compressed]
# Total: 15.3 GB / 50.0 GB (30.6% used)
# Status: ✅ OK

# List largest blobs
pos storage top --size

# Output:
# Top 10 Largest Blobs:
# 1. a3f2b9c1e4d6... (450 MB) - video memo from 2024-08-15
# 2. b78a3c2f1e9d... (320 MB) - email attachment (PDF)
# ...
```

---

## Performance Targets

- **GC Throughput**: 10,000 blobs/minute (mark phase)
- **Sweep Latency**: <5ms per blob deletion
- **Compression Ratio**: 3-5x for text/JSON, 1.2-2x for images
- **Tier Promotion**: 100 blobs/minute (warm→cold)

---

## Benefits

1. **Bounded Disk Growth**: Automatic orphan reclamation prevents unbounded bloat
2. **Cost Savings**: Compression reduces storage by 60-80% in cold tier
3. **Performance**: Smaller hot tier improves directory listing speed
4. **User Control**: Quota alerts and cleanup suggestions
5. **Auditability**: GC run history tracked in SQLite

---

## Related Gaps

- **GAP-002** (Write Batching): GC operations use WriteCoordinator
- **GAP-003** (Embedding Versioning): Embedding vectors stored in CAS
- **GAP-006** (Vault Recovery): Encrypted CAS blobs backed up

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Implement `CASGarbageCollector` and schedule daily maintenance workflow
