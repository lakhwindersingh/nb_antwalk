//! Routing engine
//!
//! Generates routing plans from classifications and orchestrates processor execution.

use crate::classifier::{Classification, IntentClassifier};
use crate::error::{OrchestratorError, Result};
use crate::registry::{ProcessorRegistry, ProcessorSpec};
use crate::types::*;
use petgraph::graph::{DiGraph, NodeIndex};
use petgraph::Direction;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use uuid::Uuid;

/// Router for classifying requests and generating execution plans
pub struct Router {
    classifier: IntentClassifier,
    registry: ProcessorRegistry,
    base_path: PathBuf,
}

/// Complete routing plan for execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoutingPlan {
    pub execution_id: Uuid,
    pub processors: Vec<ProcessorStep>,
    pub resource_allocation: ResourceAllocation,
    pub estimated_duration_seconds: u64,
}

impl Router {
    /// Create a new router
    pub fn new(
        classifier: IntentClassifier,
        registry: ProcessorRegistry,
        base_path: PathBuf,
    ) -> Self {
        Self {
            classifier,
            registry,
            base_path,
        }
    }

    /// Classify a request and generate routing plan
    pub async fn classify_and_route(
        &self,
        request_text: &str,
        context: &RequestContext,
    ) -> Result<RoutingPlan> {
        // Step 1: Classify the request
        let classification = self.classifier.classify(request_text, context).await?;

        // Step 2: Find matching processors
        let matches = self
            .registry
            .match_processors(&classification, &self.base_path);

        if matches.is_empty() {
            return Err(OrchestratorError::NoMatchingProcessor(
                classification.primary_intent.as_str().to_string(),
            ));
        }

        // Step 3: Select primary processor (highest score)
        let primary_match = &matches[0];

        if !primary_match.requirements_met {
            return Err(OrchestratorError::ProcessorValidationFailed {
                processor_id: primary_match.processor_id.clone(),
                missing: primary_match.missing_requirements.clone(),
            });
        }

        // Step 4: Generate routing plan
        let execution_id = Uuid::new_v4();
        let processor = self
            .registry
            .get(&primary_match.processor_id)
            .ok_or_else(|| {
                OrchestratorError::ProcessorNotFound(primary_match.processor_id.clone())
            })?;

        // For now, simple single-processor routing
        // Phase 2 will add multi-processor coordination
        let routing_plan = self.build_single_processor_plan(
            execution_id,
            processor,
            &classification,
            context,
        )?;

        Ok(routing_plan)
    }

    /// Build a routing plan for a single processor
    fn build_single_processor_plan(
        &self,
        execution_id: Uuid,
        processor: &ProcessorSpec,
        classification: &Classification,
        context: &RequestContext,
    ) -> Result<RoutingPlan> {
        // Build input mapping from classification
        let input_mapping = self.build_input_mapping(processor, classification, context)?;

        // Allocate resources
        let resource_allocation = self.allocate_resources(processor)?;

        // Create processor step
        let step = ProcessorStep {
            processor_id: processor.processor_id.clone(),
            execution_order: 0,
            dependencies: vec![],
            input_mapping,
            resource_allocation: resource_allocation.clone(),
            fallback_processor_id: processor.fallback_processor_id.clone(),
        };

        Ok(RoutingPlan {
            execution_id,
            processors: vec![step],
            resource_allocation,
            estimated_duration_seconds: processor.estimated_duration_seconds,
        })
    }

    /// Build input mapping for processor from classification
    fn build_input_mapping(
        &self,
        processor: &ProcessorSpec,
        classification: &Classification,
        context: &RequestContext,
    ) -> Result<serde_json::Value> {
        // This would validate against processor.input_schema
        // and map classification data to expected input format

        // For thought_to_project, build the expected input
        if processor.processor_id == "thought_to_project" {
            return Ok(serde_json::json!({
                "thought_content": "", // Would need original request text
                "domain_hint": self.infer_domain_hint(&classification.extracted_entities),
                "context_files": context.available_context,
            }));
        }

        // Generic fallback
        Ok(serde_json::json!({
            "classification": classification,
            "context": context,
        }))
    }

    /// Infer domain hint from extracted entities
    fn infer_domain_hint(&self, entities: &[Entity]) -> String {
        for entity in entities {
            if entity.entity_type == "domain" {
                return entity.value.clone();
            }
        }
        "general".to_string()
    }

    /// Allocate resources for processor execution
    fn allocate_resources(&self, processor: &ProcessorSpec) -> Result<ResourceAllocation> {
        let mut ephemeral_worktrees = Vec::new();
        let mut compute_allocations = Vec::new();

        // Allocate worktree if needed
        if processor.resource_requirements.ephemeral_worktrees {
            let worktree_id = format!("worktree_{}", Uuid::new_v4());
            ephemeral_worktrees.push(worktree_id);
        }

        // Allocate compute resources
        let allocation = ComputeAllocation {
            allocation_id: format!("compute_{}", Uuid::new_v4()),
            compute_tier: processor.resource_requirements.compute_tier,
            max_memory_mb: processor.resource_requirements.max_memory_mb,
            max_disk_mb: processor.resource_requirements.max_disk_mb,
        };
        compute_allocations.push(allocation);

        Ok(ResourceAllocation {
            ephemeral_worktrees,
            compute_allocations,
            estimated_total_duration_seconds: processor.estimated_duration_seconds,
        })
    }

    /// Validate routing plan for circular dependencies
    pub fn validate_routing_plan(&self, plan: &RoutingPlan) -> Result<()> {
        if plan.processors.len() <= 1 {
            return Ok(());
        }

        // Build dependency graph
        let mut graph = DiGraph::<String, ()>::new();
        let mut node_map = HashMap::new();

        // Add nodes
        for step in &plan.processors {
            let node = graph.add_node(step.processor_id.clone());
            node_map.insert(step.processor_id.clone(), node);
        }

        // Add edges for dependencies
        for step in &plan.processors {
            let target_node = node_map[&step.processor_id];
            for dep in &step.dependencies {
                if let Some(&source_node) = node_map.get(dep) {
                    graph.add_edge(source_node, target_node, ());
                }
            }
        }

        // Check for cycles using DFS
        if self.has_cycle(&graph) {
            return Err(OrchestratorError::CircularDependency);
        }

        Ok(())
    }

    /// Check if a directed graph has cycles
    fn has_cycle(&self, graph: &DiGraph<String, ()>) -> bool {
        let mut visited = vec![false; graph.node_count()];
        let mut rec_stack = vec![false; graph.node_count()];

        for node in graph.node_indices() {
            if self.has_cycle_util(graph, node, &mut visited, &mut rec_stack) {
                return true;
            }
        }

        false
    }

    /// DFS utility for cycle detection
    fn has_cycle_util(
        &self,
        graph: &DiGraph<String, ()>,
        node: NodeIndex,
        visited: &mut [bool],
        rec_stack: &mut [bool],
    ) -> bool {
        let idx = node.index();

        if rec_stack[idx] {
            return true;
        }

        if visited[idx] {
            return false;
        }

        visited[idx] = true;
        rec_stack[idx] = true;

        for neighbor in graph.neighbors_directed(node, Direction::Outgoing) {
            if self.has_cycle_util(graph, neighbor, visited, rec_stack) {
                return true;
            }
        }

        rec_stack[idx] = false;
        false
    }

    /// Get reference to the classifier
    pub fn classifier(&self) -> &IntentClassifier {
        &self.classifier
    }

    /// Get reference to the registry
    pub fn registry(&self) -> &ProcessorRegistry {
        &self.registry
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::classifier::{ClassifierConfig, LLMCallConfig, LLMClient};
    use std::sync::Arc;

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
                    "suggested_processors": [{
                        "processor_id": "thought_to_project",
                        "confidence": 0.92,
                        "rationale": "Test"
                    }],
                    "warnings": []
                }"#
                .to_string())
            })
        }
    }

    #[test]
    fn test_validate_routing_plan_no_cycle() {
        let client = Arc::new(MockLLMClient);
        let config = ClassifierConfig::default();
        let classifier = IntentClassifier::new(client, config);
        let registry = ProcessorRegistry::new(PathBuf::from("/tmp"));
        let router = Router::new(classifier, registry, PathBuf::from("/tmp"));

        let plan = RoutingPlan {
            execution_id: Uuid::new_v4(),
            processors: vec![
                ProcessorStep {
                    processor_id: "proc1".to_string(),
                    execution_order: 0,
                    dependencies: vec![],
                    input_mapping: serde_json::json!({}),
                    resource_allocation: ResourceAllocation {
                        ephemeral_worktrees: vec![],
                        compute_allocations: vec![],
                        estimated_total_duration_seconds: 60,
                    },
                    fallback_processor_id: None,
                },
                ProcessorStep {
                    processor_id: "proc2".to_string(),
                    execution_order: 1,
                    dependencies: vec!["proc1".to_string()],
                    input_mapping: serde_json::json!({}),
                    resource_allocation: ResourceAllocation {
                        ephemeral_worktrees: vec![],
                        compute_allocations: vec![],
                        estimated_total_duration_seconds: 60,
                    },
                    fallback_processor_id: None,
                },
            ],
            resource_allocation: ResourceAllocation {
                ephemeral_worktrees: vec![],
                compute_allocations: vec![],
                estimated_total_duration_seconds: 120,
            },
            estimated_duration_seconds: 120,
        };

        let result = router.validate_routing_plan(&plan);
        assert!(result.is_ok());
    }

    #[test]
    fn test_validate_routing_plan_with_cycle() {
        let client = Arc::new(MockLLMClient);
        let config = ClassifierConfig::default();
        let classifier = IntentClassifier::new(client, config);
        let registry = ProcessorRegistry::new(PathBuf::from("/tmp"));
        let router = Router::new(classifier, registry, PathBuf::from("/tmp"));

        let plan = RoutingPlan {
            execution_id: Uuid::new_v4(),
            processors: vec![
                ProcessorStep {
                    processor_id: "proc1".to_string(),
                    execution_order: 0,
                    dependencies: vec!["proc2".to_string()],
                    input_mapping: serde_json::json!({}),
                    resource_allocation: ResourceAllocation {
                        ephemeral_worktrees: vec![],
                        compute_allocations: vec![],
                        estimated_total_duration_seconds: 60,
                    },
                    fallback_processor_id: None,
                },
                ProcessorStep {
                    processor_id: "proc2".to_string(),
                    execution_order: 1,
                    dependencies: vec!["proc1".to_string()],
                    input_mapping: serde_json::json!({}),
                    resource_allocation: ResourceAllocation {
                        ephemeral_worktrees: vec![],
                        compute_allocations: vec![],
                        estimated_total_duration_seconds: 60,
                    },
                    fallback_processor_id: None,
                },
            ],
            resource_allocation: ResourceAllocation {
                ephemeral_worktrees: vec![],
                compute_allocations: vec![],
                estimated_total_duration_seconds: 120,
            },
            estimated_duration_seconds: 120,
        };

        let result = router.validate_routing_plan(&plan);
        assert!(result.is_err());
        assert!(matches!(
            result.unwrap_err(),
            OrchestratorError::CircularDependency
        ));
    }
}
