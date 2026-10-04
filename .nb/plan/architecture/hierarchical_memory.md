---
gap_id: "GAP-012"
name: "Hierarchical Episodic-to-Semantic Memory Compaction"
priority: "P1"
status: "specification"
created: "2026-10-04"
---

# Cognitive Scaling: Hierarchical Memory Horizons with Temporal Decay

## Problem Statement

Current vector search treats all thoughts/notes equally:

```rust
// workplace/modules/pos_memory/src/vector_search.rs
pub async fn search_similar(
    &self,
    query_embedding: &[f32],
    limit: usize,
) -> Result<Vec<SearchResult>, MemoryError> {
    // Flat cosine similarity search across ALL thoughts
    let results = self.vector_store
        .search(query_embedding, limit)
        .await?;
    
    Ok(results)
}
```

### Information Overload Scenario

```
Year 1 (2024):
  - 1,500 daily thoughts (grocery lists, todo items, quick notes)
  - 500 journal entries
  - 200 meeting notes
  Total: 2,200 documents

Year 2 (2025):
  - 2,200 new documents
  Total: 4,400 documents

Year 3 (2026):
  - 2,200 new documents
  Total: 6,600 documents

User Query (2026): "What are my long-term career goals?"

Vector Search Returns:
  1. Thought from 2024: "Buy milk and eggs" (cosine: 0.82) ❌
  2. Thought from 2025: "Schedule dentist appointment" (cosine: 0.79) ❌
  3. Journal from 2024: "I want to become a technical leader..." (cosine: 0.75) ✅
  4. Thought from 2026: "Lunch with Sarah" (cosine: 0.73) ❌
  ...
```

**Impact**:
- **Semantic noise**: Trivial daily notes dilute high-value insights
- **Recency bias**: Vector search doesn't distinguish ephemeral vs evergreen
- **Cognitive bloat**: User must manually filter through thousands of results
- **Lost context**: Important life decisions buried under grocery lists

---

## Solution Architecture: Tiered Memory Horizons

### Memory Hierarchy

```
┌───────────────────────────────────────────────────────────────┐
│              Episodic Tier (0-30 Days)                         │
│  - Raw thoughts, daily notes, todo items                       │
│  - High granularity, unfiltered                                │
│  - Optimized for: "What did I do yesterday?"                   │
│  Storage: Full vector embeddings + full text                   │
│  Retention: 30 days, then synthesized or archived              │
└───────────────────────────────────────────────────────────────┘
              │
              │ Weekly Synthesis (LLM)
              ▼
┌───────────────────────────────────────────────────────────────┐
│            Short-Term Memory (1-12 Months)                     │
│  - Weekly digests, monthly retrospectives                      │
│  - Automated summaries of episodic content                     │
│  - Optimized for: "What happened in Q2?"                       │
│  Storage: Synthesized embeddings + summaries                   │
│  Retention: 12 months, then compacted to semantic core         │
└───────────────────────────────────────────────────────────────┘
              │
              │ Yearly Compaction (LLM + HITL)
              ▼
┌───────────────────────────────────────────────────────────────┐
│            Semantic Core (> 1 Year)                            │
│  - Life principles, long-term goals, key milestones            │
│  - Evergreen knowledge, personal values                        │
│  - Optimized for: "What are my core values?"                   │
│  Storage: Curated high-value nodes only                        │
│  Retention: Permanent (until user explicitly deletes)          │
└───────────────────────────────────────────────────────────────┘
```

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│           Temporal Decay in Vector Search                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   Query: "What are my long-term career goals?"               │
│                                                               │
│   1. Raw Vector Search (cosine similarity)                   │
│      ┌─────────────────────────────────────┐                │
│      │ 1. "Buy milk and eggs" (0.82)       │                │
│      │ 2. "Dentist appointment" (0.79)     │                │
│      │ 3. "Technical leader..." (0.75)     │  ← Buried!     │
│      └─────────────────────────────────────┘                │
│                                                               │
│   2. Temporal Decay Applied (exponential half-life)          │
│      ┌─────────────────────────────────────┐                │
│      │ Decay Formula:                       │                │
│      │ score_final = cosine × (0.5)^(age/90)│                │
│      │                                       │                │
│      │ "Buy milk" (2 days old):             │                │
│      │   0.82 × (0.5)^(2/90) = 0.81        │                │
│      │                                       │                │
│      │ "Technical leader" (400 days old):   │                │
│      │   0.75 × (0.5)^(400/90) = 0.03      │  ← Decayed     │
│      └─────────────────────────────────────┘                │
│                                                               │
│   3. Tier Boosting (amplify semantic core)                   │
│      ┌─────────────────────────────────────┐                │
│      │ Tier Multipliers:                    │                │
│      │ - Episodic (0-30d): 1.0x             │                │
│      │ - Short-term (1-12m): 1.2x           │                │
│      │ - Semantic Core (>1y): 2.0x          │                │
│      │                                       │                │
│      │ "Technical leader" (Semantic Core):  │                │
│      │   0.03 × 2.0 = 0.06                 │                │
│      └─────────────────────────────────────┘                │
│                                                               │
│   4. Final Ranking (RRF + Temporal + Tier)                   │
│      ┌─────────────────────────────────────┐                │
│      │ 1. "Technical leader..." (0.90)     │  ✅ Surfaced!  │
│      │ 2. "Career retrospective" (0.85)    │                │
│      │ 3. "Buy milk and eggs" (0.81)       │                │
│      └─────────────────────────────────────┘                │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                 SQLite Schema: Memory Tiers                   │
├──────────────────────────────────────────────────────────────┤
│  CREATE TABLE memory_nodes (                                  │
│    node_id TEXT PRIMARY KEY,                                 │
│    tier TEXT NOT NULL,  -- 'episodic', 'short_term',         │
│                         -- 'semantic_core'                    │
│    content TEXT NOT NULL,                                     │
│    embedding_id TEXT REFERENCES embeddings,                  │
│    created_at DATETIME NOT NULL,                             │
│    last_accessed_at DATETIME,                                │
│    synthesis_source TEXT,  -- 'weekly_digest_2024_10_w2'    │
│    importance_score REAL DEFAULT 0.5,  -- 0.0-1.0            │
│    promoted_at DATETIME                                       │
│  );                                                           │
│                                                               │
│  CREATE INDEX idx_memory_tier ON memory_nodes(tier);         │
│  CREATE INDEX idx_memory_created ON memory_nodes(created_at);│
│                                                               │
│  CREATE TABLE synthesis_jobs (                                │
│    job_id TEXT PRIMARY KEY,                                  │
│    synthesis_type TEXT NOT NULL,  -- 'weekly', 'monthly',    │
│                                   -- 'yearly'                 │
│    start_date DATE NOT NULL,                                 │
│    end_date DATE NOT NULL,                                   │
│    input_node_ids TEXT,  -- JSON array                       │
│    output_node_id TEXT REFERENCES memory_nodes,              │
│    status TEXT DEFAULT 'pending',                            │
│    created_at DATETIME                                        │
│  );                                                           │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Specification

### 1. Temporal Decay Scoring

```rust
// workplace/modules/pos_memory/src/temporal_decay.rs

use chrono::{Utc, Duration};

pub struct TemporalScorer {
    half_life_days: i64,
}

impl TemporalScorer {
    pub fn new(half_life_days: i64) -> Self {
        Self { half_life_days }
    }
    
    pub fn default() -> Self {
        Self::new(90)  // 90-day half-life (3 months)
    }
    
    /// Apply exponential decay based on document age
    pub fn apply_decay(&self, cosine_score: f64, created_at: &chrono::DateTime<Utc>) -> f64 {
        let age_days = (Utc::now() - *created_at).num_days();
        
        if age_days < 0 {
            return cosine_score;  // Future date (shouldn't happen)
        }
        
        // Exponential decay: score × (0.5)^(age / half_life)
        let decay_factor = 0.5_f64.powf(age_days as f64 / self.half_life_days as f64);
        
        cosine_score * decay_factor
    }
    
    /// Apply tier-based boosting
    pub fn apply_tier_boost(&self, score: f64, tier: &MemoryTier) -> f64 {
        let multiplier = match tier {
            MemoryTier::Episodic => 1.0,       // No boost
            MemoryTier::ShortTerm => 1.2,      // Slight boost
            MemoryTier::SemanticCore => 2.0,   // Strong boost
        };
        
        score * multiplier
    }
    
    /// Combined scoring: cosine × decay × tier_boost
    pub fn combined_score(
        &self,
        cosine_score: f64,
        created_at: &chrono::DateTime<Utc>,
        tier: &MemoryTier,
    ) -> f64 {
        let decayed = self.apply_decay(cosine_score, created_at);
        self.apply_tier_boost(decayed, tier)
    }
}

#[derive(Debug, Clone, PartialEq)]
pub enum MemoryTier {
    Episodic,       // 0-30 days
    ShortTerm,      // 1-12 months
    SemanticCore,   // > 1 year
}

impl MemoryTier {
    pub fn from_age(age_days: i64) -> Self {
        if age_days <= 30 {
            MemoryTier::Episodic
        } else if age_days <= 365 {
            MemoryTier::ShortTerm
        } else {
            MemoryTier::SemanticCore
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_temporal_decay() {
        let scorer = TemporalScorer::default();
        
        // Fresh thought (2 days old)
        let recent = Utc::now() - Duration::days(2);
        let decayed = scorer.apply_decay(0.80, &recent);
        assert!(decayed > 0.78);  // Minimal decay
        
        // Old thought (400 days old)
        let old = Utc::now() - Duration::days(400);
        let decayed = scorer.apply_decay(0.80, &old);
        assert!(decayed < 0.10);  // Heavy decay
    }
    
    #[test]
    fn test_tier_boost() {
        let scorer = TemporalScorer::default();
        
        let base_score = 0.50;
        
        let episodic = scorer.apply_tier_boost(base_score, &MemoryTier::Episodic);
        assert_eq!(episodic, 0.50);  // No boost
        
        let semantic = scorer.apply_tier_boost(base_score, &MemoryTier::SemanticCore);
        assert_eq!(semantic, 1.00);  // 2x boost
    }
}
```

### 2. Enhanced Vector Search with Temporal Ranking

```rust
// workplace/modules/pos_memory/src/hierarchical_search.rs

pub struct HierarchicalSearch {
    vector_store: Arc<VectorStore>,
    temporal_scorer: TemporalScorer,
    pool: SqlitePool,
}

impl HierarchicalSearch {
    pub async fn search(
        &self,
        query_embedding: &[f32],
        limit: usize,
        filters: SearchFilters,
    ) -> Result<Vec<ScoredNode>, MemoryError> {
        // Step 1: Raw vector search (no filters)
        let raw_results = self.vector_store
            .search(query_embedding, limit * 3)  // Over-fetch for re-ranking
            .await?;
        
        // Step 2: Fetch metadata (tier, created_at, importance)
        let mut scored_nodes = Vec::new();
        
        for result in raw_results {
            let metadata = self.fetch_node_metadata(&result.node_id).await?;
            
            // Skip if doesn't match user filters
            if !filters.matches(&metadata) {
                continue;
            }
            
            // Apply temporal decay and tier boosting
            let final_score = self.temporal_scorer.combined_score(
                result.cosine_score,
                &metadata.created_at,
                &metadata.tier,
            );
            
            // Apply importance weighting
            let importance_weighted = final_score * (0.5 + metadata.importance_score * 0.5);
            
            scored_nodes.push(ScoredNode {
                node_id: result.node_id,
                content: metadata.content,
                tier: metadata.tier,
                created_at: metadata.created_at,
                cosine_score: result.cosine_score,
                final_score: importance_weighted,
            });
        }
        
        // Step 3: Re-rank by final_score
        scored_nodes.sort_by(|a, b| b.final_score.partial_cmp(&a.final_score).unwrap());
        
        // Step 4: Truncate to limit
        scored_nodes.truncate(limit);
        
        Ok(scored_nodes)
    }
    
    async fn fetch_node_metadata(&self, node_id: &str) -> Result<NodeMetadata, MemoryError> {
        let row = sqlx::query!(
            r#"
            SELECT 
                tier,
                content,
                created_at,
                importance_score
            FROM memory_nodes
            WHERE node_id = ?1
            "#,
            node_id,
        )
        .fetch_one(&self.pool)
        .await?;
        
        Ok(NodeMetadata {
            node_id: node_id.to_string(),
            tier: match row.tier.as_str() {
                "episodic" => MemoryTier::Episodic,
                "short_term" => MemoryTier::ShortTerm,
                "semantic_core" => MemoryTier::SemanticCore,
                _ => MemoryTier::Episodic,
            },
            content: row.content,
            created_at: chrono::DateTime::parse_from_rfc3339(&row.created_at)
                .unwrap()
                .with_timezone(&Utc),
            importance_score: row.importance_score,
        })
    }
}

#[derive(Debug, Clone)]
pub struct SearchFilters {
    pub tier: Option<MemoryTier>,
    pub min_date: Option<chrono::DateTime<Utc>>,
    pub max_date: Option<chrono::DateTime<Utc>>,
    pub include_trivial: bool,  // importance_score < 0.3
}

impl SearchFilters {
    pub fn matches(&self, metadata: &NodeMetadata) -> bool {
        if let Some(ref tier) = self.tier {
            if metadata.tier != *tier {
                return false;
            }
        }
        
        if let Some(min_date) = self.min_date {
            if metadata.created_at < min_date {
                return false;
            }
        }
        
        if let Some(max_date) = self.max_date {
            if metadata.created_at > max_date {
                return false;
            }
        }
        
        if !self.include_trivial && metadata.importance_score < 0.3 {
            return false;
        }
        
        true
    }
}

#[derive(Debug)]
pub struct NodeMetadata {
    pub node_id: String,
    pub tier: MemoryTier,
    pub content: String,
    pub created_at: chrono::DateTime<Utc>,
    pub importance_score: f64,
}

#[derive(Debug)]
pub struct ScoredNode {
    pub node_id: String,
    pub content: String,
    pub tier: MemoryTier,
    pub created_at: chrono::DateTime<Utc>,
    pub cosine_score: f64,
    pub final_score: f64,
}
```

### 3. Weekly Synthesis Engine

```rust
// workplace/modules/pos_memory/src/synthesis.rs

pub struct SynthesisEngine {
    pool: SqlitePool,
    llm_client: Arc<LLMClient>,
    embedding_coordinator: Arc<EmbeddingCoordinator>,
}

impl SynthesisEngine {
    /// Generate weekly digest from episodic thoughts
    pub async fn synthesize_weekly(&self, week_start: chrono::NaiveDate) -> Result<String, SynthesisError> {
        let week_end = week_start + Duration::days(7);
        
        // Fetch all episodic nodes from this week
        let nodes = self.fetch_nodes_in_range(week_start, week_end).await?;
        
        if nodes.is_empty() {
            return Err(SynthesisError::NoContent);
        }
        
        // Filter out trivial content (importance_score < 0.3)
        let meaningful_nodes: Vec<_> = nodes.into_iter()
            .filter(|n| n.importance_score >= 0.3)
            .collect();
        
        // Create synthesis prompt
        let prompt = self.create_synthesis_prompt(&meaningful_nodes, "weekly");
        
        // Call LLM to generate digest
        let digest = self.llm_client
            .complete(&prompt, CompletionParams {
                max_tokens: 1000,
                temperature: 0.3,
                ..Default::default()
            })
            .await?;
        
        // Store digest as short-term memory node
        let digest_node_id = self.create_digest_node(
            &digest,
            MemoryTier::ShortTerm,
            &meaningful_nodes.iter().map(|n| n.node_id.as_str()).collect::<Vec<_>>(),
        ).await?;
        
        // Mark synthesis job as complete
        self.mark_synthesis_complete(&digest_node_id, &meaningful_nodes).await?;
        
        info!("Weekly synthesis complete: {}", digest_node_id);
        
        Ok(digest_node_id)
    }
    
    /// Generate yearly semantic core summary
    pub async fn synthesize_yearly(&self, year: i32) -> Result<String, SynthesisError> {
        let year_start = chrono::NaiveDate::from_ymd_opt(year, 1, 1).unwrap();
        let year_end = chrono::NaiveDate::from_ymd_opt(year, 12, 31).unwrap();
        
        // Fetch short-term memory nodes (monthly digests) from this year
        let nodes = self.fetch_nodes_in_range(year_start, year_end).await?;
        
        // Create synthesis prompt with focus on patterns and insights
        let prompt = format!(
            "Review the following summaries from {} and extract:\n\
             1. Key life events and milestones\n\
             2. Recurring patterns and themes\n\
             3. Long-term goals and values\n\
             4. Important lessons learned\n\n\
             Keep the summary concise (< 500 words) and focus on evergreen insights.\n\n\
             Content:\n{}",
            year,
            nodes.iter()
                .map(|n| format!("- {}", n.content))
                .collect::<Vec<_>>()
                .join("\n")
        );
        
        // Call LLM
        let summary = self.llm_client
            .complete(&prompt, CompletionParams {
                max_tokens: 800,
                temperature: 0.2,  // Low temperature for factual synthesis
                ..Default::default()
            })
            .await?;
        
        // Store as semantic core node (permanent)
        let core_node_id = self.create_digest_node(
            &summary,
            MemoryTier::SemanticCore,
            &nodes.iter().map(|n| n.node_id.as_str()).collect::<Vec<_>>(),
        ).await?;
        
        info!("Yearly synthesis complete: {}", core_node_id);
        
        Ok(core_node_id)
    }
    
    fn create_synthesis_prompt(&self, nodes: &[MemoryNode], synthesis_type: &str) -> String {
        let content = nodes.iter()
            .map(|n| format!("- {}", n.content))
            .collect::<Vec<_>>()
            .join("\n");
        
        format!(
            "Synthesize the following {} notes into a concise summary:\n\n{}\n\n\
             Summary (2-3 paragraphs):",
            synthesis_type,
            content
        )
    }
    
    async fn create_digest_node(
        &self,
        content: &str,
        tier: MemoryTier,
        source_node_ids: &[&str],
    ) -> Result<String, SynthesisError> {
        let node_id = format!("N-{}", uuid::Uuid::new_v4());
        
        // Generate embedding for digest
        let embedding_id = self.embedding_coordinator
            .embed_text(content)
            .await?;
        
        // Store node
        sqlx::query!(
            r#"
            INSERT INTO memory_nodes (
                node_id,
                tier,
                content,
                embedding_id,
                synthesis_source,
                importance_score
            ) VALUES (?1, ?2, ?3, ?4, ?5, 0.8)
            "#,
            node_id,
            tier.to_string(),
            content,
            embedding_id,
            serde_json::to_string(source_node_ids).unwrap(),
        )
        .execute(&self.pool)
        .await?;
        
        Ok(node_id)
    }
    
    async fn fetch_nodes_in_range(
        &self,
        start: chrono::NaiveDate,
        end: chrono::NaiveDate,
    ) -> Result<Vec<MemoryNode>, SynthesisError> {
        let start_str = start.format("%Y-%m-%d").to_string();
        let end_str = end.format("%Y-%m-%d").to_string();
        
        let nodes = sqlx::query_as!(
            MemoryNode,
            r#"
            SELECT node_id, tier, content, importance_score, created_at
            FROM memory_nodes
            WHERE DATE(created_at) BETWEEN ?1 AND ?2
            ORDER BY created_at ASC
            "#,
            start_str,
            end_str,
        )
        .fetch_all(&self.pool)
        .await?;
        
        Ok(nodes)
    }
    
    async fn mark_synthesis_complete(
        &self,
        output_node_id: &str,
        source_nodes: &[MemoryNode],
    ) -> Result<(), SynthesisError> {
        let job_id = format!("J-{}", uuid::Uuid::new_v4());
        let source_ids = source_nodes.iter()
            .map(|n| n.node_id.as_str())
            .collect::<Vec<_>>();
        
        sqlx::query!(
            r#"
            INSERT INTO synthesis_jobs (
                job_id,
                synthesis_type,
                start_date,
                end_date,
                input_node_ids,
                output_node_id,
                status
            ) VALUES (?1, 'weekly', ?2, ?3, ?4, ?5, 'complete')
            "#,
            job_id,
            source_nodes.first().unwrap().created_at,
            source_nodes.last().unwrap().created_at,
            serde_json::to_string(&source_ids).unwrap(),
            output_node_id,
        )
        .execute(&self.pool)
        .await?;
        
        Ok(())
    }
}

#[derive(Debug)]
struct MemoryNode {
    node_id: String,
    tier: String,
    content: String,
    importance_score: f64,
    created_at: String,
}

impl MemoryTier {
    fn to_string(&self) -> &'static str {
        match self {
            MemoryTier::Episodic => "episodic",
            MemoryTier::ShortTerm => "short_term",
            MemoryTier::SemanticCore => "semantic_core",
        }
    }
}
```

### 4. Importance Scoring (Automatic)

```rust
// workplace/modules/pos_memory/src/importance.rs

pub struct ImportanceScorer {
    llm_client: Arc<LLMClient>,
}

impl ImportanceScorer {
    /// Calculate importance score for a thought/note (0.0-1.0)
    pub async fn score_importance(&self, content: &str) -> Result<f64, ScoringError> {
        // Heuristic-based scoring (fast, no LLM)
        let heuristic_score = self.heuristic_score(content);
        
        // For borderline cases (0.3-0.7), use LLM
        if heuristic_score >= 0.3 && heuristic_score <= 0.7 {
            return self.llm_score(content).await;
        }
        
        Ok(heuristic_score)
    }
    
    fn heuristic_score(&self, content: &str) -> f64 {
        let mut score = 0.5;  // Baseline
        
        // Indicators of low importance (trivial)
        if content.len() < 20 {
            score -= 0.3;
        }
        
        if self.contains_trivial_keywords(content) {
            score -= 0.2;
        }
        
        // Indicators of high importance
        if self.contains_goal_keywords(content) {
            score += 0.3;
        }
        
        if self.contains_reflection_keywords(content) {
            score += 0.2;
        }
        
        if content.len() > 500 {
            score += 0.1;  // Longer content often more thoughtful
        }
        
        score.clamp(0.0, 1.0)
    }
    
    fn contains_trivial_keywords(&self, content: &str) -> bool {
        let trivial = ["buy", "grocery", "shopping", "todo", "lunch", "dinner"];
        let content_lower = content.to_lowercase();
        
        trivial.iter().any(|&kw| content_lower.contains(kw))
    }
    
    fn contains_goal_keywords(&self, content: &str) -> bool {
        let goals = ["goal", "achieve", "aspire", "vision", "dream", "long-term", "career"];
        let content_lower = content.to_lowercase();
        
        goals.iter().any(|&kw| content_lower.contains(kw))
    }
    
    fn contains_reflection_keywords(&self, content: &str) -> bool {
        let reflection = ["learned", "realized", "understand", "insight", "principle", "value"];
        let content_lower = content.to_lowercase();
        
        reflection.iter().any(|&kw| content_lower.contains(kw))
    }
    
    async fn llm_score(&self, content: &str) -> Result<f64, ScoringError> {
        let prompt = format!(
            "Rate the importance of the following note on a scale of 0.0 (trivial) to 1.0 (life-changing):\n\n\
             Note: {}\n\n\
             Importance score (number only):",
            content
        );
        
        let response = self.llm_client
            .complete(&prompt, CompletionParams {
                max_tokens: 10,
                temperature: 0.0,
                ..Default::default()
            })
            .await?;
        
        let score: f64 = response.trim().parse()
            .unwrap_or(0.5);
        
        Ok(score.clamp(0.0, 1.0))
    }
}
```

---

## Background Workflow

```yaml
# workplace/config/workflows/wf_memory_synthesis.yaml

name: "memory_synthesis"
description: "Weekly memory digests and yearly semantic core compaction"
trigger:
  cron: "0 3 * * 1"  # Monday 3 AM

steps:
  - name: "synthesize_last_week"
    tool: "memory_synthesize"
    input:
      synthesis_type: "weekly"
      week_offset: -1  # Last week
  
  - name: "check_yearly_synthesis"
    tool: "memory_check_yearly"
    input:
      current_year: "{{now.year}}"
    condition: "{{now.month}} == 1 AND {{now.day}} <= 7"  # First week of year
  
  - name: "synthesize_last_year"
    tool: "memory_synthesize"
    condition: "{{check_yearly_synthesis.needed}}"
    input:
      synthesis_type: "yearly"
      year: "{{now.year - 1}}"
  
  - name: "archive_old_episodic"
    tool: "memory_archive"
    input:
      tier: "episodic"
      older_than_days: 30
```

---

## CLI Commands

```bash
# Search with temporal decay (default)
pos memory search "career goals"

# Output:
# 🔍 Search Results (temporally ranked):
# 1. [Semantic Core] "Long-term vision: technical leadership..." (2024-03-15)
# 2. [Short-term] Weekly digest: "Focus on system design..." (2025-10-01)
# 3. [Episodic] "Meeting with Sarah about promotion" (2025-10-02)

# Search specific tier only
pos memory search "career goals" --tier semantic_core

# Force raw vector search (no decay)
pos memory search "career goals" --raw

# Generate weekly digest
pos memory synthesize --weekly

# Output:
# 📝 Synthesizing last week (2025-09-30 to 2025-10-06)...
# Processed 43 thoughts
# Generated digest: N-a3f2b9c1 (320 words)
# ✅ Synthesis complete

# View memory tiers
pos memory stats

# Output:
# Memory Statistics:
# Episodic (0-30d):    1,200 nodes (15 MB)
# Short-term (1-12m):    52 nodes (weekly digests)
# Semantic Core (>1y):   12 nodes (yearly summaries)
# Total: 1,264 nodes
```

---

## Performance Targets

- **Temporal Scoring**: <1ms per node (pure math)
- **Weekly Synthesis**: <30 seconds for 500 thoughts
- **Yearly Synthesis**: <2 minutes for 12 monthly digests
- **Search Latency**: <200ms with temporal re-ranking

---

## Benefits

1. **Noise Reduction**: Trivial daily notes don't pollute long-term queries
2. **Contextual Relevance**: Recent queries favor fresh content, historical queries favor semantic core
3. **Cognitive Scalability**: System remains fast and useful after 5+ years
4. **Automatic Curation**: LLM-powered synthesis extracts insights
5. **User Control**: Explicit tier filtering for specific use cases

---

## Related Gaps

- **GAP-002** (Write Batching): Synthesis jobs batched weekly
- **GAP-003** (Embedding Versioning): Digests re-embedded when model updates
- **GAP-004** (PII Anonymization): Synthesis preserves anonymization
- **GAP-011** (Entity Resolution): Canonical entities used in digests

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Implement `TemporalScorer` and integrate with vector search
