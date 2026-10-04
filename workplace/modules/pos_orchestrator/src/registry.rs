//! Processor registry management
//!
//! Loads, validates, and queries registered processors from YAML configuration files.

use crate::error::{OrchestratorError, Result};
use crate::types::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};

/// Processor registry managing all registered processors
pub struct ProcessorRegistry {
    processors: HashMap<String, ProcessorSpec>,
    intent_index: HashMap<Intent, Vec<String>>,
    registry_path: PathBuf,
}

/// Full processor specification loaded from YAML
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessorSpec {
    pub processor_id: String,
    pub processor_name: String,
    pub version: String,
    pub processor_type: String,
    pub status: ProcessorStatus,

    // Intent & capability mapping
    pub supported_intents: Vec<Intent>,
    pub complexity_levels: Vec<ComplexityLevel>,
    pub min_routing_confidence: f64,
    pub priority: u8,

    // Entry points & dependencies
    pub entry_point: PathBuf,
    pub entry_type: String,
    pub agent_requirements: Vec<String>,
    pub workflow_requirements: Vec<String>,

    // Resource requirements
    pub resource_requirements: ProcessorResourceRequirements,
    pub estimated_duration_seconds: u64,
    pub timeout_seconds: u64,

    // Schemas
    pub input_schema: serde_json::Value,
    pub output_schema: serde_json::Value,

    // Classification hints
    pub classification_hints: ClassificationHints,

    // Fallback & error handling
    pub fallback_processor_id: Option<String>,
    pub retry_policy: Option<RetryPolicy>,

    // Metadata
    pub documentation_url: Option<String>,
    pub maintainer: String,
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProcessorStatus {
    Active,
    Planned,
    Deprecated,
    Disabled,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessorResourceRequirements {
    pub ephemeral_worktrees: bool,
    pub git_operations: bool,
    pub llm_calls: LlmCallFrequency,
    pub compute_tier: ComputeTier,
    pub max_memory_mb: u64,
    pub max_disk_mb: u64,
    pub max_concurrent_instances: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClassificationHints {
    pub strong_indicators: Vec<String>,
    pub weak_indicators: Vec<String>,
    pub exclusion_indicators: Vec<String>,
    #[serde(default)]
    pub required_entities: RequiredEntities,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct RequiredEntities {
    #[serde(default)]
    pub entity_types: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetryPolicy {
    pub max_attempts: u32,
    pub backoff_strategy: String,
    pub backoff_base_ms: u64,
}

/// Query filters for processor lookup
#[derive(Debug, Clone, Default)]
pub struct ProcessorQuery {
    pub intent: Option<Intent>,
    pub complexity: Option<ComplexityLevel>,
    pub tags: Vec<String>,
    pub status: Option<ProcessorStatus>,
}

/// Processor match result with score
#[derive(Debug, Clone)]
pub struct ProcessorMatch {
    pub processor_id: String,
    pub score: f64,
    pub requirements_met: bool,
    pub missing_requirements: Vec<String>,
}

impl ProcessorRegistry {
    /// Create a new processor registry
    pub fn new(registry_path: PathBuf) -> Self {
        Self {
            processors: HashMap::new(),
            intent_index: HashMap::new(),
            registry_path,
        }
    }

    /// Load all processor registrations from the registry directory
    pub fn load(&mut self) -> Result<()> {
        let processors_dir = self.registry_path.join("processors");

        if !processors_dir.exists() {
            return Err(OrchestratorError::RegistryLoadFailed(format!(
                "Processors directory not found: {:?}",
                processors_dir
            )));
        }

        // Read all YAML files in processors directory
        for entry in std::fs::read_dir(&processors_dir)
            .map_err(|e| OrchestratorError::RegistryLoadFailed(e.to_string()))?
        {
            let entry = entry.map_err(|e| OrchestratorError::RegistryLoadFailed(e.to_string()))?;
            let path = entry.path();

            if path.extension().and_then(|s| s.to_str()) == Some("yaml") {
                match self.load_processor_spec(&path) {
                    Ok(spec) => {
                        self.register_processor(spec)?;
                    }
                    Err(e) => {
                        eprintln!("Warning: Failed to load processor from {:?}: {}", path, e);
                    }
                }
            }
        }

        Ok(())
    }

    /// Load a single processor spec from YAML file
    fn load_processor_spec(&self, path: &Path) -> Result<ProcessorSpec> {
        let content = std::fs::read_to_string(path)?;
        let spec: ProcessorSpec = serde_yaml::from_str(&content)?;
        Ok(spec)
    }

    /// Register a processor and update indices
    pub fn register_processor(&mut self, spec: ProcessorSpec) -> Result<()> {
        let processor_id = spec.processor_id.clone();

        // Update intent index
        for intent in &spec.supported_intents {
            self.intent_index
                .entry(*intent)
                .or_insert_with(Vec::new)
                .push(processor_id.clone());
        }

        // Store processor spec
        self.processors.insert(processor_id, spec);

        Ok(())
    }

    /// Query processors matching the given filters
    pub fn query(&self, query: &ProcessorQuery) -> Vec<&ProcessorSpec> {
        let mut results: Vec<&ProcessorSpec> = Vec::new();

        // Start with all processors or filter by intent
        let candidates: Vec<&ProcessorSpec> = if let Some(intent) = query.intent {
            self.intent_index
                .get(&intent)
                .map(|ids| {
                    ids.iter()
                        .filter_map(|id| self.processors.get(id))
                        .collect()
                })
                .unwrap_or_default()
        } else {
            self.processors.values().collect()
        };

        // Apply additional filters
        for spec in candidates {
            // Filter by status
            if let Some(status) = query.status {
                if spec.status != status {
                    continue;
                }
            }

            // Filter by complexity
            if let Some(complexity) = query.complexity {
                if !spec.complexity_levels.contains(&complexity) {
                    continue;
                }
            }

            // Filter by tags
            if !query.tags.is_empty() {
                let has_all_tags = query.tags.iter().all(|tag| spec.tags.contains(tag));
                if !has_all_tags {
                    continue;
                }
            }

            results.push(spec);
        }

        results
    }

    /// Find processors matching a classification and rank by score
    pub fn match_processors(
        &self,
        classification: &crate::classifier::Classification,
        base_path: &Path,
    ) -> Vec<ProcessorMatch> {
        let mut matches = Vec::new();

        let query = ProcessorQuery {
            intent: Some(classification.primary_intent),
            complexity: Some(classification.complexity),
            tags: vec![],
            status: Some(ProcessorStatus::Active),
        };

        for spec in self.query(&query) {
            // Calculate match score
            let score = self.calculate_match_score(spec, classification);

            // Skip if below minimum confidence
            if score < spec.min_routing_confidence {
                continue;
            }

            // Validate requirements
            let (requirements_met, missing) = self.validate_requirements(spec, base_path);

            matches.push(ProcessorMatch {
                processor_id: spec.processor_id.clone(),
                score,
                requirements_met,
                missing_requirements: missing,
            });
        }

        // Sort by score descending
        matches.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());

        matches
    }

    /// Calculate match score for a processor
    fn calculate_match_score(
        &self,
        spec: &ProcessorSpec,
        classification: &crate::classifier::Classification,
    ) -> f64 {
        // Base score from classification confidence
        let mut score = classification.confidence;

        // Boost by processor priority (normalize to 0.0-1.0)
        let priority_boost = (spec.priority as f64) / 100.0 * 0.2;
        score += priority_boost;

        // Check for strong indicator matches in classification
        // (Would need access to original request text for full implementation)

        // Cap at 1.0
        score.min(1.0)
    }

    /// Validate that processor requirements are met
    fn validate_requirements(&self, spec: &ProcessorSpec, base_path: &Path) -> (bool, Vec<String>) {
        let mut missing = Vec::new();

        // Check if entry point exists
        let entry_point = base_path.join(&spec.entry_point);
        if !entry_point.exists() {
            missing.push(format!("Entry point not found: {:?}", spec.entry_point));
        }

        // Check required agents exist
        let agents_dir = base_path.join(".nb/agentic/custom/agents");
        for agent in &spec.agent_requirements {
            let agent_path = agents_dir.join(format!("{}.yaml", agent));
            if !agent_path.exists() {
                missing.push(format!("Required agent not found: {}", agent));
            }
        }

        // Check required workflows exist
        let workflows_dir = base_path.join(".nb/agentic/custom/workflows");
        for workflow in &spec.workflow_requirements {
            let workflow_path = workflows_dir.join(format!("{}.yaml", workflow));
            if !workflow_path.exists() {
                missing.push(format!("Required workflow not found: {}", workflow));
            }
        }

        let requirements_met = missing.is_empty();
        (requirements_met, missing)
    }

    /// Get a processor by ID
    pub fn get(&self, processor_id: &str) -> Option<&ProcessorSpec> {
        self.processors.get(processor_id)
    }

    /// Get all registered processor IDs
    pub fn list_processor_ids(&self) -> Vec<String> {
        self.processors.keys().cloned().collect()
    }

    /// Get count of registered processors
    pub fn count(&self) -> usize {
        self.processors.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_processor_query() {
        let mut registry = ProcessorRegistry::new(PathBuf::from("/tmp"));

        let spec = ProcessorSpec {
            processor_id: "test_processor".to_string(),
            processor_name: "Test Processor".to_string(),
            version: "1.0.0".to_string(),
            processor_type: "test".to_string(),
            status: ProcessorStatus::Active,
            supported_intents: vec![Intent::ProjectGeneration],
            complexity_levels: vec![ComplexityLevel::Simple],
            min_routing_confidence: 0.75,
            priority: 90,
            entry_point: PathBuf::from("test.md"),
            entry_type: "test".to_string(),
            agent_requirements: vec![],
            workflow_requirements: vec![],
            resource_requirements: ProcessorResourceRequirements {
                ephemeral_worktrees: false,
                git_operations: false,
                llm_calls: LlmCallFrequency::None,
                compute_tier: ComputeTier::TierA,
                max_memory_mb: 1024,
                max_disk_mb: 2048,
                max_concurrent_instances: 1,
            },
            estimated_duration_seconds: 60,
            timeout_seconds: 120,
            input_schema: serde_json::json!({}),
            output_schema: serde_json::json!({}),
            classification_hints: ClassificationHints {
                strong_indicators: vec![],
                weak_indicators: vec![],
                exclusion_indicators: vec![],
                required_entities: RequiredEntities::default(),
            },
            fallback_processor_id: None,
            retry_policy: None,
            documentation_url: None,
            maintainer: "test".to_string(),
            tags: vec![],
        };

        registry.register_processor(spec).unwrap();

        let query = ProcessorQuery {
            intent: Some(Intent::ProjectGeneration),
            complexity: None,
            tags: vec![],
            status: Some(ProcessorStatus::Active),
        };

        let results = registry.query(&query);
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].processor_id, "test_processor");
    }
}
