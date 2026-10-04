//! Integration tests for end-to-end orchestrator flow
//!
//! Tests the complete pipeline: request → classification → routing → processor selection

use pos_orchestrator::{
    classifier::{Classification, ClassifierConfig, IntentClassifier, LLMCallConfig, LLMClient},
    registry::ProcessorRegistry,
    router::Router,
    types::*,
};
use std::path::PathBuf;
use std::sync::Arc;

/// Mock LLM client that returns predefined classification responses
struct MockLLMClient {
    response: String,
}

impl MockLLMClient {
    fn new_project_generation() -> Self {
        Self {
            response: r#"{
                "primary_intent": "project_generation",
                "secondary_intents": ["synthesis"],
                "complexity": "moderate",
                "confidence": 0.92,
                "extracted_entities": [
                    {
                        "entity_type": "technology",
                        "value": "Redis",
                        "relevance": 0.95
                    },
                    {
                        "entity_type": "technology",
                        "value": "session store",
                        "relevance": 0.90
                    }
                ],
                "resource_estimates": {
                    "ephemeral_worktrees": true,
                    "git_operations": true,
                    "llm_calls": "high_frequency",
                    "compute_tier": "tier_a",
                    "estimated_duration_seconds": 300
                },
                "suggested_processors": [
                    {
                        "processor_id": "thought_to_project",
                        "confidence": 0.92,
                        "rationale": "Request contains technical specifications for software project"
                    }
                ],
                "warnings": []
            }"#.to_string(),
        }
    }

    fn new_low_confidence() -> Self {
        Self {
            response: r#"{
                "primary_intent": "project_generation",
                "secondary_intents": [],
                "complexity": "moderate",
                "confidence": 0.45,
                "extracted_entities": [],
                "resource_estimates": {
                    "ephemeral_worktrees": false,
                    "git_operations": false,
                    "llm_calls": "none",
                    "compute_tier": "tier_a",
                    "estimated_duration_seconds": 60
                },
                "suggested_processors": [],
                "warnings": [
                    {
                        "warning_type": "ambiguous_request",
                        "message": "Request lacks clear technical specifications",
                        "severity": "high"
                    }
                ]
            }"#.to_string(),
        }
    }

    fn new_data_analysis() -> Self {
        Self {
            response: r#"{
                "primary_intent": "data_analysis",
                "secondary_intents": ["reconciliation"],
                "complexity": "complex",
                "confidence": 0.88,
                "extracted_entities": [
                    {
                        "entity_type": "domain",
                        "value": "finance",
                        "relevance": 0.95
                    },
                    {
                        "entity_type": "data_source",
                        "value": "database",
                        "relevance": 0.90
                    }
                ],
                "resource_estimates": {
                    "ephemeral_worktrees": false,
                    "git_operations": false,
                    "llm_calls": "low_frequency",
                    "compute_tier": "tier_b",
                    "estimated_duration_seconds": 180
                },
                "suggested_processors": [
                    {
                        "processor_id": "financial_analysis",
                        "confidence": 0.88,
                        "rationale": "Financial data analysis with reconciliation needs"
                    }
                ],
                "warnings": []
            }"#.to_string(),
        }
    }
}

impl LLMClient for MockLLMClient {
    fn call_llm(
        &self,
        _prompt: String,
        _config: LLMCallConfig,
    ) -> std::pin::Pin<Box<dyn std::future::Future<Output = pos_orchestrator::error::Result<String>> + Send + '_>>
    {
        let response = self.response.clone();
        Box::pin(async move { Ok(response) })
    }
}

/// Helper function to create a test processor registry with thought_to_project
fn create_test_registry(base_path: &PathBuf) -> ProcessorRegistry {
    use pos_orchestrator::registry::*;

    let mut registry = ProcessorRegistry::new(base_path.clone());

    // Create entry point file for testing
    let entry_path = base_path.join(".nb/plan/extensions/thought_to_project");
    std::fs::create_dir_all(&entry_path).ok();
    std::fs::write(
        entry_path.join("concise.md"),
        "# Thought to Project Test Entry Point",
    )
    .ok();

    let thought_to_project_spec = ProcessorSpec {
        processor_id: "thought_to_project".to_string(),
        processor_name: "Thought to Project".to_string(),
        version: "1.0.0".to_string(),
        processor_type: "project_generation".to_string(),
        status: ProcessorStatus::Active,
        supported_intents: vec![Intent::ProjectGeneration],
        complexity_levels: vec![
            ComplexityLevel::Simple,
            ComplexityLevel::Moderate,
            ComplexityLevel::Complex,
        ],
        min_routing_confidence: 0.75,
        priority: 90,
        entry_point: PathBuf::from(".nb/plan/extensions/thought_to_project/concise.md"),
        entry_type: "domain_plan".to_string(),
        agent_requirements: vec![],
        workflow_requirements: vec![],
        resource_requirements: ProcessorResourceRequirements {
            ephemeral_worktrees: true,
            git_operations: true,
            llm_calls: LlmCallFrequency::HighFrequency,
            compute_tier: ComputeTier::TierA,
            max_memory_mb: 2048,
            max_disk_mb: 5120,
            max_concurrent_instances: 3,
        },
        estimated_duration_seconds: 300,
        timeout_seconds: 600,
        input_schema: serde_json::json!({
            "type": "object",
            "properties": {
                "thought_content": {"type": "string"},
                "domain_hint": {"type": "string"},
                "context_files": {"type": "array"}
            },
            "required": ["thought_content"]
        }),
        output_schema: serde_json::json!({
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "artifacts": {"type": "array"}
            }
        }),
        classification_hints: ClassificationHints {
            strong_indicators: vec![
                "implement".to_string(),
                "build".to_string(),
                "create project".to_string(),
            ],
            weak_indicators: vec!["software".to_string(), "code".to_string()],
            exclusion_indicators: vec!["analyze existing".to_string(), "review".to_string()],
            required_entities: RequiredEntities {
                entity_types: vec!["technology".to_string()],
            },
        },
        fallback_processor_id: None,
        retry_policy: None,
        documentation_url: Some("https://docs.example.com/thought_to_project".to_string()),
        maintainer: "platform-team".to_string(),
        tags: vec!["project_generation".to_string(), "core".to_string()],
    };

    registry
        .register_processor(thought_to_project_spec)
        .expect("Failed to register thought_to_project");

    registry
}

#[tokio::test]
async fn test_end_to_end_project_generation_routing() {
    // Setup
    let base_path = PathBuf::from("/tmp/test_orchestrator");
    let llm_client = Arc::new(MockLLMClient::new_project_generation());
    let config = ClassifierConfig::default();
    let classifier = IntentClassifier::new(llm_client, config);
    let registry = create_test_registry(&base_path);
    let router = Router::new(classifier, registry, base_path.clone());

    // Test request
    let request = "Implement a Redis-backed session store with TTL support and connection pooling";
    let context = RequestContext {
        user_id: Some("test_user".to_string()),
        session_id: Some("test_session".to_string()),
        urgency: Some("normal".to_string()),
        available_context: vec![],
        data_sensitivity: None,
    };

    // Execute classification and routing
    let result = router.classify_and_route(request, &context).await;

    // Assertions
    if result.is_err() {
        eprintln!("Routing failed with error: {:?}", result.as_ref().unwrap_err());
    }
    assert!(result.is_ok(), "Routing should succeed");
    let plan = result.unwrap();

    assert_eq!(plan.processors.len(), 1, "Should have exactly one processor");
    assert_eq!(
        plan.processors[0].processor_id, "thought_to_project",
        "Should route to thought_to_project"
    );
    assert_eq!(
        plan.processors[0].execution_order, 0,
        "Should be first in execution order"
    );
    assert!(
        plan.processors[0].dependencies.is_empty(),
        "Should have no dependencies for single processor"
    );
    assert!(
        plan.resource_allocation.ephemeral_worktrees.len() > 0,
        "Should allocate ephemeral worktree"
    );
    assert_eq!(
        plan.resource_allocation.compute_allocations[0].compute_tier,
        ComputeTier::TierA,
        "Should allocate tier A compute"
    );
}

#[tokio::test]
async fn test_low_confidence_classification_rejected() {
    // Setup
    let base_path = PathBuf::from("/tmp/test_orchestrator");
    let llm_client = Arc::new(MockLLMClient::new_low_confidence());
    let config = ClassifierConfig::default();
    let classifier = IntentClassifier::new(llm_client, config);
    let registry = create_test_registry(&base_path);
    let router = Router::new(classifier, registry, base_path.clone());

    // Test ambiguous request
    let request = "Do something with the thing";
    let context = RequestContext {
        user_id: Some("test_user".to_string()),
        session_id: None,
        urgency: None,
        available_context: vec![],
        data_sensitivity: None,
    };

    // Execute classification and routing
    let result = router.classify_and_route(request, &context).await;

    // Assertions
    assert!(result.is_err(), "Should reject low confidence classification");
    let error = result.unwrap_err();
    match error {
        pos_orchestrator::error::OrchestratorError::LowConfidence { confidence } => {
            assert!(
                confidence < 0.60,
                "Confidence should be below threshold: {}",
                confidence
            );
        }
        _ => panic!("Expected LowConfidence error, got: {:?}", error),
    }
}

#[tokio::test]
async fn test_no_matching_processor() {
    // Setup - registry without financial_analysis processor
    let base_path = PathBuf::from("/tmp/test_orchestrator");
    let llm_client = Arc::new(MockLLMClient::new_data_analysis());
    let config = ClassifierConfig::default();
    let classifier = IntentClassifier::new(llm_client, config);
    let registry = create_test_registry(&base_path); // Only has thought_to_project
    let router = Router::new(classifier, registry, base_path.clone());

    // Test financial analysis request
    let request = "Analyze Q4 revenue report and reconcile with database transactions";
    let context = RequestContext {
        user_id: Some("test_user".to_string()),
        session_id: None,
        urgency: None,
        available_context: vec![],
        data_sensitivity: Some("high".to_string()),
    };

    // Execute classification and routing
    let result = router.classify_and_route(request, &context).await;

    // Assertions
    assert!(result.is_err(), "Should fail when no matching processor");
    let error = result.unwrap_err();
    match error {
        pos_orchestrator::error::OrchestratorError::NoMatchingProcessor(intent) => {
            assert_eq!(intent, "data_analysis", "Should report correct intent");
        }
        _ => panic!("Expected NoMatchingProcessor error, got: {:?}", error),
    }
}

#[tokio::test]
async fn test_classification_caching() {
    // Setup
    let _base_path = PathBuf::from("/tmp/test_orchestrator");
    let llm_client = Arc::new(MockLLMClient::new_project_generation());
    let config = ClassifierConfig {
        cache_size: 10,
        cache_ttl_seconds: 300,
        ..Default::default()
    };
    let classifier = IntentClassifier::new(llm_client, config);

    let request = "Implement a Redis-backed session store";
    let context = RequestContext {
        user_id: Some("test_user".to_string()),
        session_id: None,
        urgency: None,
        available_context: vec![],
        data_sensitivity: None,
    };

    // First call - should hit LLM
    let result1 = classifier.classify(request, &context).await;
    assert!(result1.is_ok(), "First classification should succeed");

    // Second call - should hit cache
    let result2 = classifier.classify(request, &context).await;
    assert!(result2.is_ok(), "Second classification should succeed");

    // Results should be identical
    let classification1 = result1.unwrap();
    let classification2 = result2.unwrap();
    assert_eq!(
        classification1.primary_intent, classification2.primary_intent,
        "Cached classification should match"
    );
    assert_eq!(
        classification1.confidence, classification2.confidence,
        "Cached confidence should match"
    );
}

#[tokio::test]
async fn test_processor_requirement_validation() {
    use pos_orchestrator::registry::*;

    // Setup registry with processor requiring missing agents
    let base_path = PathBuf::from("/tmp/test_orchestrator_validation");
    let mut registry = ProcessorRegistry::new(base_path.clone());

    let spec_with_requirements = ProcessorSpec {
        processor_id: "test_processor_with_deps".to_string(),
        processor_name: "Test Processor".to_string(),
        version: "1.0.0".to_string(),
        processor_type: "test".to_string(),
        status: ProcessorStatus::Active,
        supported_intents: vec![Intent::ProjectGeneration],
        complexity_levels: vec![ComplexityLevel::Simple],
        min_routing_confidence: 0.60,
        priority: 50,
        entry_point: PathBuf::from("nonexistent/entry.md"),
        entry_type: "domain_plan".to_string(),
        agent_requirements: vec!["missing_agent".to_string()],
        workflow_requirements: vec!["missing_workflow".to_string()],
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

    registry
        .register_processor(spec_with_requirements)
        .expect("Registration should succeed");

    // Test matching with validation
    let classification = Classification {
        primary_intent: Intent::ProjectGeneration,
        secondary_intents: vec![],
        complexity: ComplexityLevel::Simple,
        confidence: 0.85,
        extracted_entities: vec![],
        resource_estimates: ResourceEstimates {
            ephemeral_worktrees: false,
            git_operations: false,
            llm_calls: LlmCallFrequency::None,
            compute_tier: ComputeTier::TierA,
            estimated_duration_seconds: 60,
        },
        suggested_processors: vec![],
        warnings: vec![],
    };

    let matches = registry.match_processors(&classification, &base_path);

    // Should find processor but requirements not met
    assert_eq!(matches.len(), 1, "Should find one matching processor");
    assert!(
        !matches[0].requirements_met,
        "Requirements should not be met"
    );
    assert!(
        matches[0].missing_requirements.len() > 0,
        "Should report missing requirements"
    );
}

#[test]
fn test_routing_plan_circular_dependency_detection() {
    use pos_orchestrator::router::RoutingPlan;

    let base_path = PathBuf::from("/tmp/test_orchestrator");
    let llm_client = Arc::new(MockLLMClient::new_project_generation());
    let config = ClassifierConfig::default();
    let classifier = IntentClassifier::new(llm_client, config);
    let registry = create_test_registry(&base_path);
    let router = Router::new(classifier, registry, base_path.clone());

    // Create plan with circular dependency: A → B → A
    let plan_with_cycle = RoutingPlan {
        execution_id: uuid::Uuid::new_v4(),
        processors: vec![
            ProcessorStep {
                processor_id: "processor_a".to_string(),
                execution_order: 0,
                dependencies: vec!["processor_b".to_string()],
                input_mapping: serde_json::json!({}),
                resource_allocation: ResourceAllocation {
                    ephemeral_worktrees: vec![],
                    compute_allocations: vec![],
                    estimated_total_duration_seconds: 60,
                },
                fallback_processor_id: None,
            },
            ProcessorStep {
                processor_id: "processor_b".to_string(),
                execution_order: 1,
                dependencies: vec!["processor_a".to_string()],
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

    let result = router.validate_routing_plan(&plan_with_cycle);
    assert!(result.is_err(), "Should detect circular dependency");
    match result.unwrap_err() {
        pos_orchestrator::error::OrchestratorError::CircularDependency => {
            // Expected
        }
        _ => panic!("Expected CircularDependency error"),
    }
}
