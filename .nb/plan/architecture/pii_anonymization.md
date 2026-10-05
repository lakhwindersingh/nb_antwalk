---
gap_id: "GAP-004"
name: "PII/Sensitive Entity Anonymization Prior to Frontier LLM Egress"
priority: "P1"
status: "specification"
created: "2026-10-04"
---

# PII/Sensitive Entity Anonymization Before LLM Egress

## Problem Statement

Personal OS currently redacts **vault secrets** (API keys, tokens) via `RedactionSentinel` before sending context to LLMs, but lacks comprehensive **PII (Personally Identifiable Information) protection**:

```rust
// Current implementation (insufficient)
RedactionSentinel::scan_for_api_keys(text);
RedactionSentinel::scan_for_tokens(text);
```

**Missing Protection**:
1. **Personal Names**: "John Smith called me", "Meeting with Sarah Johnson"
2. **Email Addresses**: "contact me at john@example.com"
3. **Phone Numbers**: "+1-555-123-4567", "(650) 555-0100"
4. **Physical Addresses**: "123 Main St, San Francisco, CA 94102"
5. **SSN/Tax IDs**: "123-45-6789", "EIN 12-3456789"
6. **Financial Details**: "Credit card ending in 1234", "Account #9876543210"
7. **Medical Info**: "diagnosed with diabetes", "prescription for Lipitor"
8. **Usernames/IDs**: "@johndoe", "employee ID 12345"

**Risk Scenarios**:
- User captures thought: "Remind me to call Dr. Smith (555-1234) about Mom's lab results for diabetes"
- Agent queries: "Summarize my recent medical interactions"
- LLM receives unredacted: Real doctor name, phone, medical condition → **HIPAA/Privacy violation**
- LLM provider logs/trains on data → **Permanent PII leakage**

**Current Gaps**:
- No Named Entity Recognition (NER) before LLM egress
- No contextual anonymization (preserve semantic meaning)
- No reversible de-identification (for user-facing results)
- No privacy-level classification (public vs. confidential thoughts)

---

## Solution Architecture: Dual-Pass Privacy Pipeline

Implement **layered privacy protection** with NER-based entity detection, reversible anonymization, and privacy-aware routing.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                  User Input / Data Source                     │
│   "Meeting with Sarah Johnson (sarah@acme.com) about Q2      │
│    revenue. She mentioned 15% growth target."                 │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              Stage 1: Vault Secret Redaction                  │
│  - API keys (regex: sk-[a-zA-Z0-9]{48})                      │
│  - Tokens (Bearer, OAuth)                                     │
│  - Passwords (context-aware patterns)                         │
│  → Immediate replacement with [REDACTED_API_KEY]              │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│          Stage 2: NER Entity Extraction (Local BERT)          │
│  - Candle pure-Rust NER pipeline (zero LibTorch) [GAP-007]   │
│  - Detected entities:                                         │
│    • PER: "Sarah Johnson" → [PERSON_1]                        │
│    • EMAIL: "sarah@acme.com" → [EMAIL_1]                      │
│    • ORG: "Acme" → [ORG_1]                                    │
│    • PERCENT: "15%" → [PERCENT_1] (optional)                  │
│  - Entity map stored: {PERSON_1: "Sarah Johnson", ...}        │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│        Stage 3: Anonymized Text Generation                    │
│  "Meeting with [PERSON_1] ([EMAIL_1]) about Q2 revenue.      │
│   She mentioned [PERCENT_1] growth target."                   │
│                                                                │
│  - Semantic structure preserved for LLM reasoning             │
│  - PII fully removed, reversible via entity map               │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│            Stage 4: LLM Processing (Frontier Models)          │
│  - Claude/GPT receives anonymized text only                   │
│  - Response: "You should follow up with [PERSON_1] on the    │
│    [PERCENT_1] target by end of quarter."                     │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│      Stage 5: De-Anonymization (User-Facing Output)          │
│  - Reverse entity map: [PERSON_1] → "Sarah Johnson"          │
│  - Final output: "You should follow up with Sarah Johnson    │
│    on the 15% target by end of quarter."                      │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Specification

### 1. NER Model Setup (Candle Pure Rust - GAP-007)

```rust
// workplace/modules/pos_privacy/src/ner_engine.rs

use rust_bert::pipelines::ner::{NERModel, Entity};
use rust_bert::pipelines::common::ModelType;
use std::sync::Arc;

pub struct NEREngine {
    model: Arc<NERModel>,
}

impl NEREngine {
    pub fn new() -> Result<Self, PrivacyError> {
        // Use local BERT-NER model (no API calls)
        let model = NERModel::new(Default::default())?;
        Ok(Self {
            model: Arc::new(model),
        })
    }
    
    pub fn extract_entities(&self, text: &str) -> Result<Vec<DetectedEntity>, PrivacyError> {
        let predictions = self.model.predict(&[text]);
        
        let mut entities = Vec::new();
        for batch in predictions {
            for entity in batch {
                entities.push(DetectedEntity {
                    text: entity.word.clone(),
                    entity_type: Self::map_entity_type(&entity.label),
                    start_pos: entity.offset.begin,
                    end_pos: entity.offset.end,
                    confidence: entity.score,
                });
            }
        }
        
        Ok(entities)
    }
    
    fn map_entity_type(label: &str) -> EntityType {
        match label {
            "PER" | "PERSON" => EntityType::Person,
            "ORG" | "ORGANIZATION" => EntityType::Organization,
            "LOC" | "LOCATION" | "GPE" => EntityType::Location,
            "EMAIL" => EntityType::Email,
            "PHONE" => EntityType::Phone,
            "DATE" => EntityType::Date,
            "MONEY" => EntityType::Financial,
            "PERCENT" => EntityType::Percentage,
            _ => EntityType::Other,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetectedEntity {
    pub text: String,
    pub entity_type: EntityType,
    pub start_pos: usize,
    pub end_pos: usize,
    pub confidence: f32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EntityType {
    Person,
    Organization,
    Location,
    Email,
    Phone,
    SSN,
    CreditCard,
    BankAccount,
    Address,
    Date,
    Financial,
    Medical,
    Username,
    Percentage,
    Other,
}
```

### 2. Pattern-Based PII Detectors (Complement to NER)

```rust
// workplace/modules/pos_privacy/src/pattern_detectors.rs

use regex::Regex;
use once_cell::sync::Lazy;

static EMAIL_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b").unwrap()
});

static PHONE_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})").unwrap()
});

static SSN_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"\b\d{3}-\d{2}-\d{4}\b").unwrap()
});

static CREDIT_CARD_REGEX: Lazy<Regex> = Lazy::new(|| {
    // Visa, MasterCard, Amex, Discover
    Regex::new(r"\b(?:\d{4}[-\s]?){3}\d{4}\b").unwrap()
});

static IP_ADDRESS_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b").unwrap()
});

static ADDRESS_REGEX: Lazy<Regex> = Lazy::new(|| {
    // US addresses: "123 Main St, City, ST 12345"
    Regex::new(r"\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct),?\s+[\w\s]+,?\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?").unwrap()
});

pub struct PatternDetector;

impl PatternDetector {
    pub fn detect_all(text: &str) -> Vec<DetectedEntity> {
        let mut entities = Vec::new();
        
        // Email
        for capture in EMAIL_REGEX.captures_iter(text) {
            entities.push(DetectedEntity {
                text: capture[0].to_string(),
                entity_type: EntityType::Email,
                start_pos: capture.get(0).unwrap().start(),
                end_pos: capture.get(0).unwrap().end(),
                confidence: 1.0,
            });
        }
        
        // Phone
        for capture in PHONE_REGEX.captures_iter(text) {
            entities.push(DetectedEntity {
                text: capture[0].to_string(),
                entity_type: EntityType::Phone,
                start_pos: capture.get(0).unwrap().start(),
                end_pos: capture.get(0).unwrap().end(),
                confidence: 1.0,
            });
        }
        
        // SSN
        for capture in SSN_REGEX.captures_iter(text) {
            entities.push(DetectedEntity {
                text: capture[0].to_string(),
                entity_type: EntityType::SSN,
                start_pos: capture.get(0).unwrap().start(),
                end_pos: capture.get(0).unwrap().end(),
                confidence: 1.0,
            });
        }
        
        // Credit Card (use Luhn algorithm to validate)
        for capture in CREDIT_CARD_REGEX.captures_iter(text) {
            let digits: String = capture[0].chars().filter(|c| c.is_digit(10)).collect();
            if Self::luhn_check(&digits) {
                entities.push(DetectedEntity {
                    text: capture[0].to_string(),
                    entity_type: EntityType::CreditCard,
                    start_pos: capture.get(0).unwrap().start(),
                    end_pos: capture.get(0).unwrap().end(),
                    confidence: 1.0,
                });
            }
        }
        
        entities
    }
    
    fn luhn_check(card_number: &str) -> bool {
        let digits: Vec<u32> = card_number.chars()
            .filter_map(|c| c.to_digit(10))
            .collect();
        
        if digits.len() < 13 || digits.len() > 19 {
            return false;
        }
        
        let checksum: u32 = digits.iter().rev().enumerate()
            .map(|(i, &d)| {
                if i % 2 == 1 {
                    let doubled = d * 2;
                    if doubled > 9 { doubled - 9 } else { doubled }
                } else {
                    d
                }
            })
            .sum();
        
        checksum % 10 == 0
    }
}
```

### 3. Privacy Coordinator (Orchestrates Pipeline)

```rust
// workplace/modules/pos_privacy/src/coordinator.rs

use std::collections::HashMap;

pub struct PrivacyCoordinator {
    ner_engine: NEREngine,
    entity_cache: Arc<RwLock<HashMap<String, EntityMap>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityMap {
    pub entities: HashMap<String, String>,  // Placeholder → Original
    pub reverse: HashMap<String, String>,   // Original → Placeholder
}

impl PrivacyCoordinator {
    pub fn new() -> Result<Self, PrivacyError> {
        Ok(Self {
            ner_engine: NEREngine::new()?,
            entity_cache: Arc::new(RwLock::new(HashMap::new())),
        })
    }
    
    /// Anonymize text before LLM egress
    pub async fn anonymize(
        &self,
        text: &str,
        context_id: &str,  // Unique ID for this anonymization context
        sensitivity: PrivacyLevel,
    ) -> Result<AnonymizedText, PrivacyError> {
        // Stage 1: Vault secret redaction
        let text = RedactionSentinel::redact_secrets(text);
        
        // Stage 2: NER entity extraction
        let ner_entities = self.ner_engine.extract_entities(&text)?;
        
        // Stage 3: Pattern-based entity detection
        let pattern_entities = PatternDetector::detect_all(&text);
        
        // Merge and deduplicate entities
        let all_entities = Self::merge_entities(ner_entities, pattern_entities);
        
        // Stage 4: Filter by sensitivity level
        let entities_to_redact = Self::filter_by_sensitivity(all_entities, sensitivity);
        
        // Stage 5: Generate anonymized text
        let (anonymized_text, entity_map) = Self::generate_anonymized_text(
            &text,
            &entities_to_redact,
        )?;
        
        // Cache entity map for de-anonymization
        self.entity_cache.write().await.insert(
            context_id.to_string(),
            entity_map.clone(),
        );
        
        Ok(AnonymizedText {
            text: anonymized_text,
            context_id: context_id.to_string(),
            redacted_count: entities_to_redact.len(),
            entity_types: entities_to_redact.iter()
                .map(|e| e.entity_type)
                .collect(),
        })
    }
    
    /// De-anonymize LLM response
    pub async fn de_anonymize(
        &self,
        text: &str,
        context_id: &str,
    ) -> Result<String, PrivacyError> {
        let cache = self.entity_cache.read().await;
        let entity_map = cache.get(context_id)
            .ok_or(PrivacyError::ContextNotFound(context_id.to_string()))?;
        
        let mut result = text.to_string();
        
        // Replace placeholders with original entities
        for (placeholder, original) in &entity_map.entities {
            result = result.replace(placeholder, original);
        }
        
        Ok(result)
    }
    
    fn generate_anonymized_text(
        text: &str,
        entities: &[DetectedEntity],
    ) -> Result<(String, EntityMap), PrivacyError> {
        let mut result = text.to_string();
        let mut entity_map = EntityMap {
            entities: HashMap::new(),
            reverse: HashMap::new(),
        };
        
        // Sort entities by position (descending) to replace from end to start
        let mut sorted_entities = entities.to_vec();
        sorted_entities.sort_by(|a, b| b.start_pos.cmp(&a.start_pos));
        
        let mut type_counters: HashMap<EntityType, usize> = HashMap::new();
        
        for entity in sorted_entities {
            let counter = type_counters.entry(entity.entity_type).or_insert(0);
            *counter += 1;
            
            let placeholder = format!("[{}_{:02}]", 
                Self::entity_type_prefix(entity.entity_type), 
                counter
            );
            
            // Replace in text
            result.replace_range(entity.start_pos..entity.end_pos, &placeholder);
            
            // Store mapping
            entity_map.entities.insert(placeholder.clone(), entity.text.clone());
            entity_map.reverse.insert(entity.text.clone(), placeholder);
        }
        
        Ok((result, entity_map))
    }
    
    fn entity_type_prefix(entity_type: EntityType) -> &'static str {
        match entity_type {
            EntityType::Person => "PERSON",
            EntityType::Email => "EMAIL",
            EntityType::Phone => "PHONE",
            EntityType::SSN => "SSN",
            EntityType::CreditCard => "CARD",
            EntityType::Address => "ADDRESS",
            EntityType::Organization => "ORG",
            EntityType::Location => "LOC",
            EntityType::Financial => "AMOUNT",
            EntityType::Medical => "MEDICAL",
            _ => "REDACTED",
        }
    }
    
    fn filter_by_sensitivity(
        entities: Vec<DetectedEntity>,
        level: PrivacyLevel,
    ) -> Vec<DetectedEntity> {
        entities.into_iter().filter(|e| {
            match level {
                PrivacyLevel::Maximum => true,  // Redact everything
                PrivacyLevel::High => matches!(e.entity_type, 
                    EntityType::Person | EntityType::Email | EntityType::Phone |
                    EntityType::SSN | EntityType::CreditCard | EntityType::Address |
                    EntityType::Medical
                ),
                PrivacyLevel::Medium => matches!(e.entity_type,
                    EntityType::Email | EntityType::Phone | EntityType::SSN |
                    EntityType::CreditCard | EntityType::Medical
                ),
                PrivacyLevel::Low => matches!(e.entity_type,
                    EntityType::SSN | EntityType::CreditCard | EntityType::Medical
                ),
                PrivacyLevel::None => false,  // No redaction
            }
        }).collect()
    }
    
    fn merge_entities(
        ner_entities: Vec<DetectedEntity>,
        pattern_entities: Vec<DetectedEntity>,
    ) -> Vec<DetectedEntity> {
        let mut merged = ner_entities;
        
        // Add pattern entities that don't overlap with NER entities
        'outer: for pattern_entity in pattern_entities {
            for ner_entity in &merged {
                // Check for overlap
                if Self::ranges_overlap(
                    (pattern_entity.start_pos, pattern_entity.end_pos),
                    (ner_entity.start_pos, ner_entity.end_pos),
                ) {
                    continue 'outer;  // Skip overlapping pattern entity
                }
            }
            merged.push(pattern_entity);
        }
        
        merged
    }
    
    fn ranges_overlap(r1: (usize, usize), r2: (usize, usize)) -> bool {
        r1.0 < r2.1 && r2.0 < r1.1
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PrivacyLevel {
    None,      // No redaction (trusted local operations)
    Low,       // Only critical PII (SSN, credit cards, medical)
    Medium,    // + contact info (email, phone)
    High,      // + personal identifiers (names, addresses)
    Maximum,   // Redact all entities (paranoid mode)
}

#[derive(Debug)]
pub struct AnonymizedText {
    pub text: String,
    pub context_id: String,
    pub redacted_count: usize,
    pub entity_types: Vec<EntityType>,
}
```

### 4. Integration with Agent System

```rust
// workplace/modules/pos_agents/src/llm_client.rs

impl LLMClient {
    pub async fn query_with_privacy(
        &self,
        prompt: &str,
        privacy_level: PrivacyLevel,
    ) -> Result<String, AgentError> {
        let context_id = ulid::Ulid::new().to_string();
        
        // Anonymize before sending to frontier LLM
        let anonymized = self.privacy_coordinator
            .anonymize(prompt, &context_id, privacy_level)
            .await?;
        
        info!(
            "Anonymized {} entities before LLM egress: {:?}",
            anonymized.redacted_count,
            anonymized.entity_types
        );
        
        // Send anonymized text to LLM
        let response = self.call_llm_api(&anonymized.text).await?;
        
        // De-anonymize response
        let de_anonymized = self.privacy_coordinator
            .de_anonymize(&response, &context_id)
            .await?;
        
        Ok(de_anonymized)
    }
}
```

### 5. CLI Privacy Controls

```bash
# Set default privacy level
pos config set privacy.default_level high

# Override for specific operations
pos agent query "Summarize my medical notes" --privacy maximum

# Disable privacy (local-only operations)
pos search "John Smith" --privacy none
```

---

## SQLite Schema Extensions

```sql
-- Privacy audit log
CREATE TABLE IF NOT EXISTS privacy_audit_log (
    audit_id TEXT PRIMARY KEY,
    operation TEXT NOT NULL,  -- 'anonymize', 'de_anonymize', 'llm_egress'
    context_id TEXT NOT NULL,
    privacy_level TEXT NOT NULL,
    entity_count INTEGER NOT NULL,
    entity_types TEXT NOT NULL,  -- JSON array
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    agent_id TEXT,
    user_approved BOOLEAN DEFAULT 0
);
CREATE INDEX idx_privacy_audit_timestamp ON privacy_audit_log(timestamp);
CREATE INDEX idx_privacy_audit_context ON privacy_audit_log(context_id);

-- User privacy preferences per data type
CREATE TABLE IF NOT EXISTS privacy_preferences (
    preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_source TEXT NOT NULL,  -- 'thoughts', 'emails', 'meetings', etc.
    default_privacy_level TEXT NOT NULL CHECK (default_privacy_level IN ('none', 'low', 'medium', 'high', 'maximum')),
    auto_anonymize_entities TEXT,  -- JSON array: ['Person', 'Email', ...]
    require_approval_for_egress BOOLEAN NOT NULL DEFAULT 0,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## Performance Targets

| Metric | Target | Max |
|--------|--------|-----|
| NER entity extraction (per 1000 chars) | 50ms | 200ms |
| Pattern matching (per 1000 chars) | 10ms | 50ms |
| Anonymization pipeline (total) | 100ms | 300ms |
| De-anonymization (per response) | 5ms | 20ms |
| Memory overhead (cached entity maps) | <10MB | <50MB |

---

## Privacy Rule Enforcement

```yaml
# .nb/context/rules/pii_protection_rules.md

## Rule 1: Mandatory Anonymization Before Frontier LLM
- All text sent to Claude/GPT/Gemini MUST pass through PrivacyCoordinator
- Default privacy level: HIGH (names, emails, phones redacted)
- Override only with explicit user consent

## Rule 2: Local NER Processing
- NER model runs locally via Candle pure-Rust runtime (no API calls, zero C++ LibTorch)
- No PII sent to external services for entity detection
- Model weights bundled with application

## Rule 3: Entity Map Expiration
- Cached entity maps expire after 1 hour
- Maps cleared on application restart
- No entity maps persisted to disk

## Rule 4: Audit Logging
- All LLM egress events logged with entity counts
- Privacy audit log stored in SQLite
- User can review redaction history

## Rule 5: Opt-Out for Local Operations
- Search, file indexing, local agents: privacy level = NONE
- No anonymization for purely local operations
- Only egress to external LLM APIs triggers anonymization

## Rule 6: Medical/Financial Data Special Handling
- Medical entities always redacted (HIPAA compliance)
- Financial data (SSN, credit cards) always redacted
- Cannot be overridden by user preference
```

---

## Benefits

1. **HIPAA/GDPR Compliance**: Medical and personal data never leaves device unredacted
2. **LLM Provider Protection**: Prevents accidental PII in training data or logs
3. **Reversible Anonymization**: User-facing responses maintain natural language
4. **Contextual Privacy**: Different sensitivity levels for different data sources
5. **Audit Trail**: Complete record of what was redacted and when

---

## Crate Dependencies

```toml
[dependencies]
# Pure-Rust ML stack (replaces legacy rust-bert per GAP-007)
candle-core = { version = "0.8", default-features = false }
candle-nn = "0.8"
candle-transformers = "0.8"
tokenizers = { version = "0.21", default-features = false, features = ["onig"] }
regex = "1.10"
once_cell = "1.19"
serde = { version = "1.0", features = ["derive"] }
ulid = "1.0"
```

---

## Migration Strategy

### Phase 1: Infrastructure (Week 1)
- Implement NER engine and pattern detectors
- Create PrivacyCoordinator with anonymization pipeline
- Add privacy audit log schema

### Phase 2: Integration (Week 2)
- Integrate with LLM client (all frontier model calls)
- Add CLI privacy level controls
- Test anonymization/de-anonymization round-trip

### Phase 3: Rule Enforcement (Week 3)
- Enforce mandatory anonymization for external LLM APIs
- Add privacy preference storage
- Implement entity map caching and expiration

### Phase 4: Validation (Week 4)
- Security audit of anonymization coverage
- Performance benchmarking
- User acceptance testing

---

## Related Gaps

- **GAP-002** (Write Batching): Privacy audit log uses write coordinator
- **Redaction Sentinel**: Extended to include PII (not just vault secrets)

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Implement `NEREngineCandle` using quantized Safetensors per [GAP-007](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/architecture/inference_engine_optimization.md)
