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
//! - **AST Parsing**: Extracts structured information from markdown thoughts
//!   (headings, code blocks, wikilinks, metadata) using pulldown-cmark.
//!
//! - **Entity Extraction**: Identifies named entities, concepts, and domain
//!   terms for knowledge graph integration.
//!
//! - **Storage**: Persists thoughts and evaluation results in SQLite with
//!   bidirectional traceability to generated plans.
//!
//! ## Usage Example
//!
//! ```rust,no_run
//! use pos_thoughts::actionability::ActionabilityEvaluator;
//! use pos_thoughts::ambiguity::AmbiguityEvaluator;
//! use pos_thoughts::LLMClient;
//! use async_trait::async_trait;
//! use std::error::Error as StdError;
//!
//! // Example mock client for demonstration
//! struct MyLLMClient;
//!
//! #[async_trait]
//! impl LLMClient for MyLLMClient {
//!     async fn call(&self, _prompt: &str) -> Result<String, Box<dyn StdError>> {
//!         Ok(r#"{"score": 0.85, "dimensions": {...}, "missing_elements": [], "confidence": 0.95}"#.to_string())
//!     }
//! }
//!
//! async fn evaluate_thought(content: &str) {
//!     let llm_client = Box::new(MyLLMClient);
//!
//!     let actionability = ActionabilityEvaluator::new(llm_client);
//!     let action_report = actionability.evaluate(content).await.unwrap();
//!
//!     if action_report.is_actionable() {
//!         println!("Thought is ready for MVS synthesis!");
//!     }
//! }
//! ```
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

/// Trait for LLM client abstraction (shared across modules).
#[async_trait]
pub trait LLMClient: Send + Sync {
    /// Call LLM with prompt, return response text.
    async fn call(&self, prompt: &str) -> Result<String, Box<dyn StdError>>;
}

// Future modules (blocked by Phase 1 core dependencies):
// pub mod ast_parser;       // Requires pulldown-cmark
// pub mod entity_extractor; // Requires NLP tokenization
// pub mod storage;          // Requires SQLite + sqlx

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
