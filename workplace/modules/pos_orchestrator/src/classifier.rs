//! Intent classification module
//!
//! Uses LLM-based semantic analysis to classify incoming requests
//! and determine appropriate processor routing.

use crate::error::{OrchestratorError, Result};
use crate::types::*;
use lru::LruCache;
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use std::num::NonZeroUsize;
use std::sync::Arc;

/// Classification result from LLM analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Classification {
    pub primary_intent: Intent,
    pub secondary_intents: Vec<Intent>,
    pub complexity: ComplexityLevel,
    pub confidence: f64,
    pub extracted_entities: Vec<Entity>,
    pub resource_estimates: ResourceEstimates,
    pub suggested_processors: Vec<ProcessorSuggestion>,
    pub warnings: Vec<Warning>,
}

/// Processor suggestion with confidence and rationale
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessorSuggestion {
    pub processor_id: String,
    pub confidence: f64,
    pub rationale: String,
}

/// Intent classifier using LLM-based semantic analysis
pub struct IntentClassifier {
    llm_client: Arc<dyn LLMClient>,
    classification_cache: Arc<RwLock<LruCache<String, Classification>>>,
    config: ClassifierConfig,
}

/// Configuration for the classifier
#[derive(Debug, Clone)]
pub struct ClassifierConfig {
    pub confidence_threshold: f64,
    pub cache_ttl_seconds: u64,
    pub cache_size: usize,
    pub model_name: String,
    pub temperature: f32,
}

impl Default for ClassifierConfig {
    fn default() -> Self {
        Self {
            confidence_threshold: 0.60,
            cache_ttl_seconds: 300, // 5 minutes
            cache_size: 1000,
            model_name: "claude-3-7-sonnet".to_string(),
            temperature: 0.2,
        }
    }
}

/// Trait for LLM clients (to be implemented by pos_thoughts or similar)
pub trait LLMClient: Send + Sync {
    fn call_llm(
        &self,
        prompt: String,
        config: LLMCallConfig,
    ) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<String>> + Send + '_>>;
}

#[derive(Debug, Clone)]
pub struct LLMCallConfig {
    pub model: String,
    pub temperature: f32,
    pub max_tokens: u32,
}

impl IntentClassifier {
    /// Create a new intent classifier
    pub fn new(llm_client: Arc<dyn LLMClient>, config: ClassifierConfig) -> Self {
        let cache_size = NonZeroUsize::new(config.cache_size).unwrap();
        Self {
            llm_client,
            classification_cache: Arc::new(RwLock::new(LruCache::new(cache_size))),
            config,
        }
    }

    /// Classify a request and return the classification result
    pub async fn classify(
        &self,
        request_text: &str,
        context: &RequestContext,
    ) -> Result<Classification> {
        // Generate cache key
        let cache_key = self.generate_cache_key(request_text, context);

        // Check cache
        {
            let mut cache = self.classification_cache.write();
            if let Some(cached) = cache.get(&cache_key) {
                return Ok(cached.clone());
            }
        }

        // Build classification prompt
        let prompt = self.build_classification_prompt(request_text, context);

        // Call LLM
        let llm_config = LLMCallConfig {
            model: self.config.model_name.clone(),
            temperature: self.config.temperature,
            max_tokens: 2048,
        };

        let response = self
            .llm_client
            .call_llm(prompt, llm_config)
            .await
            .map_err(|e| OrchestratorError::LlmCallFailed(e.to_string()))?;

        // Parse response as JSON
        let classification: Classification = serde_json::from_str(&response)
            .map_err(|e| OrchestratorError::ClassificationFailed(format!("Invalid JSON: {}", e)))?;

        // Validate confidence threshold
        if classification.confidence < self.config.confidence_threshold {
            return Err(OrchestratorError::LowConfidence {
                confidence: classification.confidence,
            });
        }

        // Cache result
        {
            let mut cache = self.classification_cache.write();
            cache.put(cache_key, classification.clone());
        }

        Ok(classification)
    }

    /// Build the classification prompt from template
    fn build_classification_prompt(&self, request_text: &str, context: &RequestContext) -> String {
        let context_summary = self.format_context(context);

        format!(
            r#"Classify the following user request to determine routing strategy.

Request:
{request_text}

Available Context:
{context_summary}

Analyze the request across these dimensions:

1. **Primary Intent**: What is the main objective?
   - project_generation: Convert idea/thought into executable software project
   - data_analysis: Analyze structured or unstructured data
   - reconciliation: Compare and align data from multiple sources
   - computation: Perform heavy computational work
   - information_extraction: Extract structured data from unstructured sources
   - synthesis: Combine multiple inputs into unified output
   - monitoring: Track and alert on system state
   - optimization: Improve performance or efficiency

2. **Complexity Level**: How complex is this task?
   - simple: Single-step, single-processor
   - moderate: Multi-step within single processor
   - complex: Multi-processor coordination
   - exploratory: Iterative refinement required

3. **Key Entities**: What are the named entities?
   - Technologies (languages, frameworks, libraries)
   - Data sources (databases, files, APIs)
   - Metrics (performance targets, thresholds)
   - Domains (finance, healthcare, infrastructure)

4. **Resource Requirements**: What resources are needed?
   - Ephemeral worktrees (code generation)
   - Git operations (version control)
   - LLM calls frequency (none/low_frequency/high_frequency)
   - Compute tier (tier_a/tier_b/tier_c)
   - Estimated duration

Return ONLY valid JSON (no markdown fences):
{{
  "primary_intent": "project_generation",
  "secondary_intents": ["specification_synthesis"],
  "complexity": "moderate",
  "confidence": 0.92,
  "extracted_entities": [
    {{
      "entity_type": "technology",
      "value": "LRU cache",
      "relevance": 0.95
    }},
    {{
      "entity_type": "metric",
      "value": "1000 entry capacity",
      "relevance": 0.85
    }}
  ],
  "resource_estimates": {{
    "ephemeral_worktrees": true,
    "git_operations": true,
    "llm_calls": "high_frequency",
    "compute_tier": "tier_a",
    "estimated_duration_seconds": 300
  }},
  "suggested_processors": [
    {{
      "processor_id": "thought_to_project",
      "confidence": 0.92,
      "rationale": "Request contains technical specifications and bounded scope"
    }}
  ],
  "warnings": []
}}"#,
            request_text = request_text,
            context_summary = context_summary
        )
    }

    /// Format request context for prompt
    fn format_context(&self, context: &RequestContext) -> String {
        let mut parts = Vec::new();

        if let Some(user_id) = &context.user_id {
            parts.push(format!("User: {}", user_id));
        }
        if let Some(session_id) = &context.session_id {
            parts.push(format!("Session: {}", session_id));
        }
        if let Some(urgency) = &context.urgency {
            parts.push(format!("Urgency: {}", urgency));
        }
        if !context.available_context.is_empty() {
            parts.push(format!(
                "Available files: {}",
                context.available_context.join(", ")
            ));
        }
        if let Some(sensitivity) = &context.data_sensitivity {
            parts.push(format!("Data sensitivity: {}", sensitivity));
        }

        if parts.is_empty() {
            "No additional context provided".to_string()
        } else {
            parts.join("\n")
        }
    }

    /// Generate cache key for request
    fn generate_cache_key(&self, request_text: &str, _context: &RequestContext) -> String {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut hasher = DefaultHasher::new();
        request_text.hash(&mut hasher);
        format!("{:x}", hasher.finish())
    }

    /// Clear the classification cache
    pub fn clear_cache(&self) {
        let mut cache = self.classification_cache.write();
        cache.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct MockLLMClient;

    impl LLMClient for MockLLMClient {
        fn call_llm(
            &self,
            _prompt: String,
            _config: LLMCallConfig,
        ) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<String>> + Send + '_>>
        {
            Box::pin(async {
                Ok(r#"{
                    "primary_intent": "project_generation",
                    "secondary_intents": [],
                    "complexity": "moderate",
                    "confidence": 0.92,
                    "extracted_entities": [],
                    "resource_estimates": {
                        "ephemeral_worktrees": true,
                        "git_operations": true,
                        "llm_calls": "high_frequency",
                        "compute_tier": "tier_a",
                        "estimated_duration_seconds": 300
                    },
                    "suggested_processors": [],
                    "warnings": []
                }"#
                .to_string())
            })
        }
    }

    #[tokio::test]
    async fn test_classify_request() {
        let client = Arc::new(MockLLMClient);
        let config = ClassifierConfig::default();
        let classifier = IntentClassifier::new(client, config);

        let context = RequestContext {
            user_id: Some("test_user".to_string()),
            session_id: None,
            urgency: None,
            available_context: vec![],
            data_sensitivity: None,
        };

        let result = classifier
            .classify("Implement an LRU cache in Rust", &context)
            .await;

        assert!(result.is_ok());
        let classification = result.unwrap();
        assert_eq!(classification.primary_intent, Intent::ProjectGeneration);
        assert!(classification.confidence >= 0.60);
    }
}
