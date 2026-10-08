//! # pos_thoughts
//!
//! Core library for thought capture, evaluation, and readiness scoring in the
//! thought-to-project pipeline.
//!
//! ## Overview
//!
//! This crate provides the foundation for transforming unstructured thoughts
//! (captured in markdown) into actionable software project specifications (MVS).
//!
//! ## Key Components
//!
//! - **Actionability Evaluation**: Determines if a thought is ready to become
//!   a software project by evaluating goal clarity, technical details, success
//!   criteria, dependencies, and scope boundedness.
//!
//! - **Ambiguity Detection**: Identifies vague or underspecified elements using
//!   LLM-based semantic analysis across four categories: undefined terms,
//!   missing specifics, unclear scope, and unspecified implementation details.
//!
//! - **MVS Synthesis (E-THOUGHT-02)**: Normalizes unstructured thoughts into structured
//!   Minimum Viable Set specifications.
//!
//! - **Domain Layer Plan Generator (E-THOUGHT-04)**: Generates layerable domain
//!   plans complying with `custom_domain_layer_template.md`.
//!
//! - **Petgraph Task DAG (E-THOUGHT-05)**: Compiles plans into directed acyclic
//!   task dependency graphs with cycle detection and parallel wave scheduling.
//!
//! - **Autonomous Pipeline Bridge (E-THOUGHT-07 & E-THOUGHT-08)**: End-to-end
//!   orchestration connecting thoughts to ephemeral worktrees with knowledge loop closure.
//!
//! ## Architecture Integration
//!
//! This crate implements components required by:
//! - `.nb/agentic/custom/agents/agent_thought_synthesizer.yaml`
//! - `.nb/plan/extensions/thought_to_project/concise.md`
//!
//! See `REMEDIATION_STATUS.md` for implementation progress.

use async_trait::async_trait;
use std::error::Error as StdError;

pub mod actionability;
pub mod ambiguity;
pub mod mvs_synthesis;
pub mod plan_compiler;
pub mod task_dag;
pub mod pipeline_bridge;

pub use mvs_synthesis::{MvsComponent, MvsConstraint, MvsSpecification, MvsSynthesisError, MvsSynthesizer};
pub use plan_compiler::{CompiledPlan, PlanCompiler};
pub use task_dag::{PipelineTask, TaskDag, TaskDagError};
pub use pipeline_bridge::{PipelineBridgeError, PipelineExecutionResult, ThoughtToProjectBridge};

/// Trait for LLM client abstraction (shared across modules).
#[async_trait]
pub trait LLMClient: Send + Sync {
    /// Call LLM with prompt, return response text.
    async fn call(&self, prompt: &str) -> Result<String, Box<dyn StdError>>;
}

#[cfg(test)]
mod integration_tests {
    use super::*;
    use actionability::ActionabilityEvaluator;
    use ambiguity::AmbiguityEvaluator;
    use std::sync::{Arc, Mutex};

    /// Mock LLM client for testing without actual API calls.
    #[derive(Clone)]
    struct MockLLMClient {
        actionability_response: Arc<String>,
        ambiguity_response: Arc<String>,
        call_count: Arc<Mutex<usize>>,
    }

    #[async_trait]
    impl LLMClient for MockLLMClient {
        async fn call(&self, prompt: &str) -> Result<String, Box<dyn StdError>> {
            let mut count = self.call_count.lock().unwrap();
            *count += 1;

            if prompt.contains("Evaluate if this thought is ready") {
                Ok((*self.actionability_response).clone())
            } else if prompt.contains("Identify vague or ambiguous") {
                Ok((*self.ambiguity_response).clone())
            } else {
                Err("Unknown prompt type".into())
            }
        }
    }

    #[tokio::test]
    async fn test_high_quality_thought_evaluation() {
        let mock_client = Box::new(MockLLMClient {
            actionability_response: Arc::new(r#"{
                "score": 0.85,
                "dimensions": {
                    "clear_goal": 0.9,
                    "technical_details": 0.8,
                    "success_criteria": 0.9,
                    "dependencies": 0.8,
                    "bounded_scope": 0.9
                },
                "missing_elements": [],
                "confidence": 0.95
            }"#.to_string()),
            ambiguity_response: Arc::new(r#"{
                "score": 0.15,
                "vague_elements": [],
                "questions_to_ask": [],
                "confidence": 0.95
            }"#.to_string()),
            call_count: Arc::new(Mutex::new(0)),
        });

        let actionability = ActionabilityEvaluator::new(mock_client.clone());
        let ambiguity = AmbiguityEvaluator::new(mock_client);

        let thought_content = "Implement LRU cache with 1000 entry capacity...";

        let action_report = actionability.evaluate(thought_content).await.unwrap();
        let ambig_report = ambiguity.evaluate(thought_content).await.unwrap();

        assert!(action_report.is_actionable());
        assert!(ambig_report.is_clear());
        assert!(action_report.score >= 0.80);
        assert!(ambig_report.score <= 0.30);
    }

    #[tokio::test]
    async fn test_low_quality_thought_blocks_mvs() {
        let mock_client = Box::new(MockLLMClient {
            actionability_response: Arc::new(r#"{
                "score": 0.45,
                "dimensions": {
                    "clear_goal": 0.6,
                    "technical_details": 0.3,
                    "success_criteria": 0.2,
                    "dependencies": 0.5,
                    "bounded_scope": 0.7
                },
                "missing_elements": [
                    {
                        "dimension": "technical_details",
                        "description": "No data structures specified",
                        "suggested_question": "What data structure should be used?"
                    }
                ],
                "confidence": 0.85
            }"#.to_string()),
            ambiguity_response: Arc::new(r#"{
                "score": 0.65,
                "vague_elements": [
                    {
                        "category": "missing_specifics",
                        "text": "make it better",
                        "reason": "No concrete metric defined",
                        "suggested_question": "Better in what way?"
                    }
                ],
                "questions_to_ask": ["Better in what way?"],
                "confidence": 0.80
            }"#.to_string()),
            call_count: Arc::new(Mutex::new(0)),
        });

        let actionability = ActionabilityEvaluator::new(mock_client.clone());
        let ambiguity = AmbiguityEvaluator::new(mock_client);

        let thought_content = "Make the cache better...";

        let action_report = actionability.evaluate(thought_content).await.unwrap();
        let ambig_report = ambiguity.evaluate(thought_content).await.unwrap();

        assert!(!action_report.is_actionable());
        assert!(!ambig_report.is_clear());
        assert!(ambig_report.questions_to_ask.len() > 0);
    }
}
