---
gap_id: "GAP-011"
name: "Probabilistic Entity Resolution & Deduplication"
priority: "P1"
status: "specification"
created: "2026-10-04"
---

# Entity Resolution: Fuzzy Matching & Graph Clustering for Contact Deduplication

## Problem Statement

Current contact/project extraction uses exact string matching:

```rust
// workplace/modules/pos_crm/src/contact_extractor.rs
pub async fn extract_contact_from_email(
    &self,
    email: &Email,
) -> Result<Contact, CRMError> {
    let sender_email = email.from.clone();
    let sender_name = email.from_name.clone();
    
    // Exact lookup
    let existing = sqlx::query_as!(
        Contact,
        "SELECT * FROM contacts WHERE email = ?1",
        sender_email,
    )
    .fetch_optional(&self.pool)
    .await?;
    
    if let Some(contact) = existing {
        return Ok(contact);
    }
    
    // Create new contact (duplication!)
    self.create_contact(sender_name, sender_email).await
}
```

### Duplication Scenario

```
Email 1: From: "Robert Smith <robert.smith@acme.com>"
         → Contact: {name: "Robert Smith", email: "robert.smith@acme.com"}

Email 2: From: "Bob Smith <bob@acme.com>"
         → Contact: {name: "Bob Smith", email: "bob@acme.com"}

Calendar: Meeting with "Dr. R. Smith"
         → Contact: {name: "Dr. R. Smith", email: null}

Siri:     "Call Bob from Acme"
         → Contact: {name: "Bob", organization: "Acme", phone: "+1-555-1234"}
```

**Result**: 4 duplicate contact entities for the same person!

**Impact**:
- Fragmented interaction history
- Incorrect relationship graphs
- Low-quality CRM insights
- User confusion ("Who is this contact?")

---

## Solution Architecture: Multi-Stage Entity Resolution

### Resolution Pipeline

```
┌────────────────────────────────────────────────────────────┐
│  Stage 1: Exact Matching (High Confidence)                 │
│  - Email address exact match                                │
│  - Phone number (normalized) exact match                    │
│  - LinkedIn URL exact match                                 │
│  → Confidence: 1.00 (auto-merge)                            │
└────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────┐
│  Stage 2: Fuzzy Name Matching (Medium Confidence)          │
│  - Jaro-Winkler string similarity                           │
│  - Levenshtein distance (edit distance)                     │
│  - Phonetic matching (Soundex, Metaphone)                   │
│  → Confidence: 0.70-0.95 (HITL suggestion)                  │
└────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────┐
│  Stage 3: Graph Clustering (Context-Based)                  │
│  - Email domain co-occurrence                               │
│  - Calendar event co-attendance                             │
│  - Project/task co-mentions                                 │
│  → Confidence: 0.60-0.90 (HITL suggestion)                  │
└────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────┐
│  Stage 4: Human-in-the-Loop (Low Confidence)               │
│  - Present merge candidates to user                         │
│  - User confirms or rejects                                 │
│  - Learn from user feedback (ML model update)               │
└────────────────────────────────────────────────────────────┘
```

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│              Entity Resolution Graph                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   Robert Smith <robert.smith@acme.com>                       │
│   ┌────────────────────────────┐                            │
│   │ Canonical Entity ID: E-001  │                            │
│   │ Confidence: 1.00             │                            │
│   └────────────────────────────┘                            │
│          │                                                    │
│          ├─ Variant: "Bob Smith" (similarity: 0.85)         │
│          ├─ Variant: "Dr. R. Smith" (similarity: 0.72)      │
│          └─ Alias Email: bob@acme.com                        │
│                                                               │
│   Evidence Links:                                             │
│   - Same domain: acme.com                                    │
│   - Co-attended: 5 calendar events                           │
│   - Email thread participants                                │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│           SQLite Schema: Entity Resolution                    │
├──────────────────────────────────────────────────────────────┤
│  CREATE TABLE canonical_entities (                            │
│    entity_id TEXT PRIMARY KEY,                               │
│    entity_type TEXT NOT NULL,  -- 'person', 'organization'   │
│    canonical_name TEXT NOT NULL,                             │
│    created_at DATETIME,                                       │
│    confidence REAL DEFAULT 1.0                               │
│  );                                                           │
│                                                               │
│  CREATE TABLE entity_variants (                               │
│    variant_id TEXT PRIMARY KEY,                              │
│    canonical_entity_id TEXT REFERENCES canonical_entities,   │
│    variant_name TEXT NOT NULL,                               │
│    variant_email TEXT,                                        │
│    variant_phone TEXT,                                        │
│    similarity_score REAL NOT NULL,                           │
│    source TEXT NOT NULL,  -- 'email', 'calendar', 'siri'     │
│    merged_at DATETIME                                         │
│  );                                                           │
│                                                               │
│  CREATE TABLE merge_suggestions (                             │
│    suggestion_id TEXT PRIMARY KEY,                           │
│    entity_a TEXT REFERENCES canonical_entities,              │
│    entity_b TEXT REFERENCES canonical_entities,              │
│    confidence REAL NOT NULL,                                 │
│    evidence_json TEXT,  -- JSON array of evidence            │
│    status TEXT DEFAULT 'pending',  -- 'pending', 'accepted', │
│                                    -- 'rejected'              │
│    suggested_at DATETIME,                                     │
│    resolved_at DATETIME                                       │
│  );                                                           │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Specification

### 1. String Similarity Metrics

```rust
// workplace/modules/pos_crm/src/entity_resolution/similarity.rs

use strsim::{jaro_winkler, levenshtein};

pub struct SimilarityCalculator;

impl SimilarityCalculator {
    /// Jaro-Winkler similarity (0.0 - 1.0)
    /// Best for short strings with transpositions
    pub fn jaro_winkler(s1: &str, s2: &str) -> f64 {
        jaro_winkler(s1, s2)
    }
    
    /// Normalized Levenshtein distance
    /// Best for typos and spelling variations
    pub fn levenshtein_similarity(s1: &str, s2: &str) -> f64 {
        let distance = levenshtein(s1, s2) as f64;
        let max_len = s1.len().max(s2.len()) as f64;
        
        if max_len == 0.0 {
            return 1.0;
        }
        
        1.0 - (distance / max_len)
    }
    
    /// Combined similarity score (weighted average)
    pub fn combined_similarity(name1: &str, name2: &str) -> f64 {
        let name1_norm = Self::normalize_name(name1);
        let name2_norm = Self::normalize_name(name2);
        
        let jw_score = Self::jaro_winkler(&name1_norm, &name2_norm);
        let lev_score = Self::levenshtein_similarity(&name1_norm, &name2_norm);
        
        // Weighted average (Jaro-Winkler more reliable for names)
        (jw_score * 0.7) + (lev_score * 0.3)
    }
    
    /// Normalize name for comparison
    fn normalize_name(name: &str) -> String {
        name.to_lowercase()
            .trim()
            .replace("dr. ", "")
            .replace("mr. ", "")
            .replace("mrs. ", "")
            .replace("ms. ", "")
            .replace("  ", " ")
    }
    
    /// Phonetic similarity (Soundex algorithm)
    pub fn phonetic_match(name1: &str, name2: &str) -> bool {
        let soundex1 = Self::soundex(name1);
        let soundex2 = Self::soundex(name2);
        
        soundex1 == soundex2
    }
    
    /// Simplified Soundex implementation
    fn soundex(name: &str) -> String {
        if name.is_empty() {
            return String::new();
        }
        
        let name_upper = name.to_uppercase();
        let first_char = name_upper.chars().next().unwrap();
        
        let mut code = first_char.to_string();
        let mut prev_code = Self::soundex_code(first_char);
        
        for ch in name_upper.chars().skip(1) {
            let ch_code = Self::soundex_code(ch);
            
            if ch_code != '0' && ch_code != prev_code {
                code.push(ch_code);
                
                if code.len() == 4 {
                    break;
                }
            }
            
            prev_code = ch_code;
        }
        
        // Pad with zeros
        while code.len() < 4 {
            code.push('0');
        }
        
        code
    }
    
    fn soundex_code(ch: char) -> char {
        match ch {
            'B' | 'F' | 'P' | 'V' => '1',
            'C' | 'G' | 'J' | 'K' | 'Q' | 'S' | 'X' | 'Z' => '2',
            'D' | 'T' => '3',
            'L' => '4',
            'M' | 'N' => '5',
            'R' => '6',
            _ => '0',
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_jaro_winkler() {
        // "Robert" vs "Bob" (nickname)
        let score = SimilarityCalculator::jaro_winkler("Robert", "Bob");
        assert!(score > 0.5);  // Somewhat similar
        
        // "Robert Smith" vs "Robert Smyth" (typo)
        let score = SimilarityCalculator::jaro_winkler("Robert Smith", "Robert Smyth");
        assert!(score > 0.9);  // Very similar
    }
    
    #[test]
    fn test_phonetic_match() {
        // "Smith" and "Smyth" sound the same
        assert!(SimilarityCalculator::phonetic_match("Smith", "Smyth"));
        
        // "Robert" and "Bob" do NOT sound the same (nickname, not phonetic)
        assert!(!SimilarityCalculator::phonetic_match("Robert", "Bob"));
    }
}
```

### 2. Entity Resolution Engine

```rust
// workplace/modules/pos_crm/src/entity_resolution/resolver.rs

pub struct EntityResolver {
    pool: SqlitePool,
    similarity_threshold: f64,
    auto_merge_threshold: f64,
}

impl EntityResolver {
    pub fn new(pool: SqlitePool) -> Self {
        Self {
            pool,
            similarity_threshold: 0.70,   // Suggest merge if >= 0.70
            auto_merge_threshold: 0.95,   // Auto-merge if >= 0.95
        }
    }
    
    /// Find or create canonical entity for a contact
    pub async fn resolve_contact(
        &self,
        name: &str,
        email: Option<&str>,
        phone: Option<&str>,
    ) -> Result<String, ResolutionError> {
        // Stage 1: Exact email/phone match
        if let Some(email) = email {
            if let Some(entity_id) = self.exact_match_email(email).await? {
                return Ok(entity_id);
            }
        }
        
        if let Some(phone) = phone {
            let normalized_phone = Self::normalize_phone(phone);
            if let Some(entity_id) = self.exact_match_phone(&normalized_phone).await? {
                return Ok(entity_id);
            }
        }
        
        // Stage 2: Fuzzy name matching
        let candidates = self.fuzzy_name_match(name).await?;
        
        for candidate in candidates {
            if candidate.similarity_score >= self.auto_merge_threshold {
                // High confidence: auto-merge
                self.merge_into_entity(&candidate.entity_id, name, email, phone).await?;
                return Ok(candidate.entity_id);
            } else if candidate.similarity_score >= self.similarity_threshold {
                // Medium confidence: create HITL suggestion
                self.create_merge_suggestion(&candidate.entity_id, name, email, phone, candidate.similarity_score).await?;
            }
        }
        
        // No match: create new canonical entity
        let entity_id = self.create_canonical_entity(name, email, phone).await?;
        
        Ok(entity_id)
    }
    
    async fn exact_match_email(&self, email: &str) -> Result<Option<String>, ResolutionError> {
        let row = sqlx::query!(
            r#"
            SELECT canonical_entity_id
            FROM entity_variants
            WHERE variant_email = ?1
            LIMIT 1
            "#,
            email,
        )
        .fetch_optional(&self.pool)
        .await?;
        
        Ok(row.map(|r| r.canonical_entity_id))
    }
    
    async fn exact_match_phone(&self, phone: &str) -> Result<Option<String>, ResolutionError> {
        let row = sqlx::query!(
            r#"
            SELECT canonical_entity_id
            FROM entity_variants
            WHERE variant_phone = ?1
            LIMIT 1
            "#,
            phone,
        )
        .fetch_optional(&self.pool)
        .await?;
        
        Ok(row.map(|r| r.canonical_entity_id))
    }
    
    async fn fuzzy_name_match(&self, name: &str) -> Result<Vec<NameCandidate>, ResolutionError> {
        // Fetch all existing canonical entities
        let entities = sqlx::query!(
            r#"
            SELECT entity_id, canonical_name
            FROM canonical_entities
            WHERE entity_type = 'person'
            "#
        )
        .fetch_all(&self.pool)
        .await?;
        
        let mut candidates = Vec::new();
        
        for entity in entities {
            let similarity = SimilarityCalculator::combined_similarity(
                name,
                &entity.canonical_name,
            );
            
            if similarity >= self.similarity_threshold {
                candidates.push(NameCandidate {
                    entity_id: entity.entity_id,
                    canonical_name: entity.canonical_name,
                    similarity_score: similarity,
                });
            }
        }
        
        // Sort by similarity (descending)
        candidates.sort_by(|a, b| b.similarity_score.partial_cmp(&a.similarity_score).unwrap());
        
        Ok(candidates)
    }
    
    async fn create_canonical_entity(
        &self,
        name: &str,
        email: Option<&str>,
        phone: Option<&str>,
    ) -> Result<String, ResolutionError> {
        let entity_id = format!("E-{}", uuid::Uuid::new_v4());
        
        sqlx::query!(
            r#"
            INSERT INTO canonical_entities (entity_id, entity_type, canonical_name)
            VALUES (?1, 'person', ?2)
            "#,
            entity_id,
            name,
        )
        .execute(&self.pool)
        .await?;
        
        // Create initial variant
        self.add_variant(&entity_id, name, email, phone, 1.0, "initial").await?;
        
        info!("Created canonical entity: {} ({})", entity_id, name);
        
        Ok(entity_id)
    }
    
    async fn merge_into_entity(
        &self,
        entity_id: &str,
        name: &str,
        email: Option<&str>,
        phone: Option<&str>,
    ) -> Result<(), ResolutionError> {
        // Calculate similarity with canonical name
        let canonical = sqlx::query!(
            r#"
            SELECT canonical_name
            FROM canonical_entities
            WHERE entity_id = ?1
            "#,
            entity_id,
        )
        .fetch_one(&self.pool)
        .await?;
        
        let similarity = SimilarityCalculator::combined_similarity(
            name,
            &canonical.canonical_name,
        );
        
        // Add as variant
        self.add_variant(entity_id, name, email, phone, similarity, "merged").await?;
        
        info!("Merged '{}' into entity {}", name, entity_id);
        
        Ok(())
    }
    
    async fn add_variant(
        &self,
        entity_id: &str,
        name: &str,
        email: Option<&str>,
        phone: Option<&str>,
        similarity: f64,
        source: &str,
    ) -> Result<(), ResolutionError> {
        let variant_id = format!("V-{}", uuid::Uuid::new_v4());
        
        sqlx::query!(
            r#"
            INSERT INTO entity_variants (
                variant_id,
                canonical_entity_id,
                variant_name,
                variant_email,
                variant_phone,
                similarity_score,
                source
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)
            "#,
            variant_id,
            entity_id,
            name,
            email,
            phone,
            similarity,
            source,
        )
        .execute(&self.pool)
        .await?;
        
        Ok(())
    }
    
    async fn create_merge_suggestion(
        &self,
        entity_id: &str,
        name: &str,
        email: Option<&str>,
        phone: Option<&str>,
        confidence: f64,
    ) -> Result<(), ResolutionError> {
        let suggestion_id = format!("S-{}", uuid::Uuid::new_v4());
        
        let evidence = serde_json::json!({
            "proposed_name": name,
            "proposed_email": email,
            "proposed_phone": phone,
            "similarity_score": confidence,
        });
        
        sqlx::query!(
            r#"
            INSERT INTO merge_suggestions (
                suggestion_id,
                entity_a,
                entity_b,
                confidence,
                evidence_json,
                status
            ) VALUES (?1, ?2, NULL, ?3, ?4, 'pending')
            "#,
            suggestion_id,
            entity_id,
            confidence,
            evidence.to_string(),
        )
        .execute(&self.pool)
        .await?;
        
        info!("Created merge suggestion {} (confidence: {:.2})", suggestion_id, confidence);
        
        Ok(())
    }
    
    fn normalize_phone(phone: &str) -> String {
        phone.chars()
            .filter(|c| c.is_numeric())
            .collect()
    }
}

#[derive(Debug)]
struct NameCandidate {
    entity_id: String,
    canonical_name: String,
    similarity_score: f64,
}
```

### 3. Graph Clustering (Domain Co-occurrence)

```rust
// workplace/modules/pos_crm/src/entity_resolution/graph_clustering.rs

pub struct GraphClusterer {
    pool: SqlitePool,
}

impl GraphClusterer {
    /// Find contacts likely to be the same person based on shared context
    pub async fn find_domain_clusters(&self) -> Result<Vec<ClusterCandidate>, ClusterError> {
        // Find contacts sharing email domain
        let clusters = sqlx::query_as!(
            DomainCluster,
            r#"
            SELECT 
                ev.canonical_entity_id,
                SUBSTR(ev.variant_email, INSTR(ev.variant_email, '@') + 1) as domain,
                COUNT(*) as contact_count
            FROM entity_variants ev
            WHERE ev.variant_email IS NOT NULL
            GROUP BY domain
            HAVING contact_count > 1
            "#
        )
        .fetch_all(&self.pool)
        .await?;
        
        let mut candidates = Vec::new();
        
        for cluster in clusters {
            // Get all contacts in this domain
            let contacts = self.get_contacts_by_domain(&cluster.domain).await?;
            
            // Check for name similarity between domain contacts
            for i in 0..contacts.len() {
                for j in (i + 1)..contacts.len() {
                    let similarity = SimilarityCalculator::combined_similarity(
                        &contacts[i].name,
                        &contacts[j].name,
                    );
                    
                    if similarity >= 0.60 {
                        candidates.push(ClusterCandidate {
                            entity_a: contacts[i].entity_id.clone(),
                            entity_b: contacts[j].entity_id.clone(),
                            confidence: similarity,
                            evidence: format!("Same domain: {}", cluster.domain),
                        });
                    }
                }
            }
        }
        
        Ok(candidates)
    }
    
    /// Find contacts who frequently appear together in calendar events
    pub async fn find_calendar_coattendees(&self) -> Result<Vec<ClusterCandidate>, ClusterError> {
        // Query calendar events with multiple attendees
        let coattendees = sqlx::query!(
            r#"
            SELECT 
                a1.contact_id as contact_a,
                a2.contact_id as contact_b,
                COUNT(*) as coattendance_count
            FROM calendar_attendees a1
            JOIN calendar_attendees a2 ON a1.event_id = a2.event_id
            WHERE a1.contact_id < a2.contact_id
            GROUP BY a1.contact_id, a2.contact_id
            HAVING coattendance_count >= 3
            "#
        )
        .fetch_all(&self.pool)
        .await?;
        
        let mut candidates = Vec::new();
        
        for row in coattendees {
            // Calculate confidence based on coattendance frequency
            let confidence = (row.coattendance_count as f64 / 10.0).min(0.90);
            
            candidates.push(ClusterCandidate {
                entity_a: row.contact_a,
                entity_b: row.contact_b,
                confidence,
                evidence: format!("Co-attended {} events", row.coattendance_count),
            });
        }
        
        Ok(candidates)
    }
    
    async fn get_contacts_by_domain(&self, domain: &str) -> Result<Vec<ContactInfo>, ClusterError> {
        let domain_pattern = format!("%@{}", domain);
        
        let contacts = sqlx::query_as!(
            ContactInfo,
            r#"
            SELECT 
                ce.entity_id,
                ce.canonical_name as name,
                ev.variant_email as email
            FROM canonical_entities ce
            JOIN entity_variants ev ON ce.entity_id = ev.canonical_entity_id
            WHERE ev.variant_email LIKE ?1
            "#,
            domain_pattern,
        )
        .fetch_all(&self.pool)
        .await?;
        
        Ok(contacts)
    }
}

#[derive(Debug)]
struct DomainCluster {
    canonical_entity_id: String,
    domain: String,
    contact_count: i64,
}

#[derive(Debug)]
struct ContactInfo {
    entity_id: String,
    name: String,
    email: Option<String>,
}

#[derive(Debug)]
pub struct ClusterCandidate {
    pub entity_a: String,
    pub entity_b: String,
    pub confidence: f64,
    pub evidence: String,
}
```

### 4. Human-in-the-Loop (HITL) Workflow

```rust
// workplace/modules/pos_crm/src/entity_resolution/hitl.rs

pub struct HITLWorkflow {
    pool: SqlitePool,
}

impl HITLWorkflow {
    /// Get pending merge suggestions for user review
    pub async fn get_pending_suggestions(&self) -> Result<Vec<MergeSuggestion>, HITLError> {
        let suggestions = sqlx::query_as!(
            MergeSuggestion,
            r#"
            SELECT 
                ms.suggestion_id,
                ms.entity_a,
                ms.entity_b,
                ms.confidence,
                ms.evidence_json,
                ce_a.canonical_name as name_a,
                ce_b.canonical_name as name_b
            FROM merge_suggestions ms
            JOIN canonical_entities ce_a ON ms.entity_a = ce_a.entity_id
            LEFT JOIN canonical_entities ce_b ON ms.entity_b = ce_b.entity_id
            WHERE ms.status = 'pending'
            ORDER BY ms.confidence DESC
            LIMIT 10
            "#
        )
        .fetch_all(&self.pool)
        .await?;
        
        Ok(suggestions)
    }
    
    /// User accepts merge suggestion
    pub async fn accept_merge(&self, suggestion_id: &str) -> Result<(), HITLError> {
        // Get suggestion details
        let suggestion = sqlx::query!(
            r#"
            SELECT entity_a, entity_b, evidence_json
            FROM merge_suggestions
            WHERE suggestion_id = ?1
            "#,
            suggestion_id,
        )
        .fetch_one(&self.pool)
        .await?;
        
        // Parse proposed variant from evidence
        let evidence: serde_json::Value = serde_json::from_str(&suggestion.evidence_json)?;
        
        // Merge entities
        if let Some(entity_b) = suggestion.entity_b {
            self.merge_entities(&suggestion.entity_a, &entity_b).await?;
        } else {
            // Add as variant
            let resolver = EntityResolver::new(self.pool.clone());
            resolver.merge_into_entity(
                &suggestion.entity_a,
                evidence["proposed_name"].as_str().unwrap(),
                evidence["proposed_email"].as_str(),
                evidence["proposed_phone"].as_str(),
            ).await?;
        }
        
        // Mark suggestion as accepted
        sqlx::query!(
            r#"
            UPDATE merge_suggestions
            SET status = 'accepted', resolved_at = CURRENT_TIMESTAMP
            WHERE suggestion_id = ?1
            "#,
            suggestion_id,
        )
        .execute(&self.pool)
        .await?;
        
        info!("Accepted merge suggestion: {}", suggestion_id);
        
        Ok(())
    }
    
    /// User rejects merge suggestion
    pub async fn reject_merge(&self, suggestion_id: &str) -> Result<(), HITLError> {
        sqlx::query!(
            r#"
            UPDATE merge_suggestions
            SET status = 'rejected', resolved_at = CURRENT_TIMESTAMP
            WHERE suggestion_id = ?1
            "#,
            suggestion_id,
        )
        .execute(&self.pool)
        .await?;
        
        info!("Rejected merge suggestion: {}", suggestion_id);
        
        Ok(())
    }
    
    async fn merge_entities(&self, entity_a: &str, entity_b: &str) -> Result<(), HITLError> {
        // Move all variants from entity_b to entity_a
        sqlx::query!(
            r#"
            UPDATE entity_variants
            SET canonical_entity_id = ?1
            WHERE canonical_entity_id = ?2
            "#,
            entity_a,
            entity_b,
        )
        .execute(&self.pool)
        .await?;
        
        // Delete entity_b
        sqlx::query!(
            r#"
            DELETE FROM canonical_entities
            WHERE entity_id = ?1
            "#,
            entity_b,
        )
        .execute(&self.pool)
        .await?;
        
        info!("Merged entity {} into {}", entity_b, entity_a);
        
        Ok(())
    }
}

#[derive(Debug)]
pub struct MergeSuggestion {
    pub suggestion_id: String,
    pub entity_a: String,
    pub entity_b: Option<String>,
    pub confidence: f64,
    pub evidence_json: String,
    pub name_a: String,
    pub name_b: Option<String>,
}
```

---

## CLI Commands

```bash
# Run entity resolution scan
pos crm resolve

# Output:
# 🔍 Scanning for duplicate entities...
# Found 12 merge candidates:
# 1. "Robert Smith" <robert.smith@acme.com> ≈ "Bob Smith" (confidence: 0.85)
# 2. "Dr. R. Smith" ≈ "Bob Smith" (confidence: 0.72)
# ...
# ✅ Created 12 merge suggestions

# Review pending merge suggestions
pos crm merges --pending

# Output:
# Pending Merge Suggestions:
# 1. [S-a3f2b9c1] "Robert Smith" → "Bob Smith" (0.85)
#    Evidence: Same domain (acme.com), co-attended 3 events
#    Accept? (y/n)

# Accept merge
pos crm merge accept S-a3f2b9c1

# Output:
# ✅ Merged "Bob Smith" into "Robert Smith"
```

---

## Performance Targets

- **Fuzzy Matching**: <50ms per contact (Jaro-Winkler)
- **Graph Clustering**: <5 seconds for 10,000 contacts
- **HITL Suggestion Generation**: <10 seconds for full corpus
- **Auto-Merge**: Real-time (synchronous with contact creation)

---

## Benefits

1. **Unified Contact View**: Single entity for each person across sources
2. **Accurate Relationship Graphs**: No duplicate nodes in interaction graph
3. **Improved CRM Quality**: Complete interaction history per person
4. **User Control**: HITL workflow for low-confidence merges
5. **Continuous Learning**: User feedback improves resolution accuracy

---

## Related Gaps

- **GAP-002** (Write Batching): Resolution runs as background batch job
- **GAP-004** (PII Anonymization): Entity IDs used for anonymization mapping
- **GAP-012** (Cognitive Scaling): Canonical entities used for memory graph

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Implement `EntityResolver` with Jaro-Winkler and create HITL UI
