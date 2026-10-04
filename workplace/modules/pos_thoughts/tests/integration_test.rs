//! Integration tests for pos_thoughts evaluation pipeline.

use pos_thoughts::actionability::ActionabilityEvaluator;
use pos_thoughts::ambiguity::AmbiguityEvaluator;
use pos_thoughts::LLMClient;
use async_trait::async_trait;
use std::error::Error as StdError;
use std::sync::{Arc, Mutex};

/// Mock LLM client that returns predefined responses for testing.
#[derive(Clone)]
struct MockLLMClient {
    responses: Arc<Vec<String>>,
    call_count: Arc<Mutex<usize>>,
}

impl MockLLMClient {
    fn new(responses: Vec<String>) -> Self {
        Self {
            responses: Arc::new(responses),
            call_count: Arc::new(Mutex::new(0)),
        }
    }
}

#[async_trait]
impl LLMClient for MockLLMClient {
    async fn call(&self, _prompt: &str) -> Result<String, Box<dyn StdError>> {
        let mut count = self.call_count.lock().unwrap();
        let response = self.responses.get(*count).ok_or("No more mock responses")?;
        *count += 1;
        Ok(response.clone())
    }
}

#[tokio::test]
async fn test_actionable_thought_passes_both_checks() {
    // High-quality thought with clear goals, technical details, and bounded scope
    let thought = r#"
Implement an LRU cache with the following requirements:

**Goal**: Create a thread-safe LRU cache for storing embedding vectors.

**Technical Details**:
- Use `HashMap<String, CachedEntry>` for O(1) lookups
- Use `LinkedList` for LRU ordering
- Capacity: 1000 entries
- Entry eviction: Least Recently Used (LRU)

**Success Criteria**:
- Cache hit retrieves entry in <1ms
- Cache miss adds entry and evicts LRU if at capacity
- All operations are thread-safe (use `Arc<Mutex<>>`)

**Dependencies**:
- Requires existing `EmbeddingVector` type
- No external crate dependencies

**Scope**:
- Single module: `workplace/modules/pos_storage/src/vector_cache.rs`
- Estimated: 200-300 lines of code
"#;

    let mock_actionability_response = r#"{
        "score": 0.88,
        "dimensions": {
            "clear_goal": 0.95,
            "technical_details": 0.90,
            "success_criteria": 0.85,
            "dependencies": 0.85,
            "bounded_scope": 0.90
        },
        "missing_elements": [],
        "confidence": 0.95
    }"#;

    let mock_ambiguity_response = r#"{
        "score": 0.12,
        "vague_elements": [],
        "questions_to_ask": [],
        "confidence": 0.93
    }"#;

    let mock_client = Box::new(MockLLMClient::new(vec![
        mock_actionability_response.to_string(),
        mock_ambiguity_response.to_string(),
    ]));

    let actionability = ActionabilityEvaluator::new(mock_client.clone());
    let ambiguity = AmbiguityEvaluator::new(mock_client);

    let action_report = actionability.evaluate(thought).await.unwrap();
    let ambig_report = ambiguity.evaluate(thought).await.unwrap();

    // Assertions
    assert!(action_report.is_actionable(), "High-quality thought should be actionable");
    assert!(ambig_report.is_clear(), "High-quality thought should be clear");

    assert!(action_report.score >= 0.80, "Actionability score should be high");
    assert!(ambig_report.score <= 0.30, "Ambiguity score should be low");

    assert_eq!(action_report.missing_elements.len(), 0);
    assert_eq!(ambig_report.vague_elements.len(), 0);
}

#[tokio::test]
async fn test_vague_thought_fails_ambiguity_check() {
    // Low-quality thought with vague requirements
    let thought = "Make the cache faster and better. Optimize performance.";

    let mock_actionability_response = r#"{
        "score": 0.35,
        "dimensions": {
            "clear_goal": 0.40,
            "technical_details": 0.20,
            "success_criteria": 0.15,
            "dependencies": 0.50,
            "bounded_scope": 0.50
        },
        "missing_elements": [
            {
                "dimension": "success_criteria",
                "description": "No measurable performance targets",
                "suggested_question": "What is the current performance and target?"
            }
        ],
        "confidence": 0.80
    }"#;

    let mock_ambiguity_response = r#"{
        "score": 0.78,
        "vague_elements": [
            {
                "category": "missing_specifics",
                "text": "faster",
                "reason": "No baseline or target performance metric",
                "suggested_question": "How much faster? What's the current latency?"
            },
            {
                "category": "missing_specifics",
                "text": "better",
                "reason": "Subjective term without measurable criterion",
                "suggested_question": "Better in what dimension? Accuracy? Throughput?"
            },
            {
                "category": "unspecified_details",
                "text": "optimize performance",
                "reason": "No specific optimization strategy mentioned",
                "suggested_question": "Which optimization approach? Caching? Indexing?"
            }
        ],
        "questions_to_ask": [
            "How much faster? What's the current latency?",
            "Better in what dimension? Accuracy? Throughput?",
            "Which optimization approach? Caching? Indexing?"
        ],
        "confidence": 0.88
    }"#;

    let mock_client = Box::new(MockLLMClient::new(vec![
        mock_actionability_response.to_string(),
        mock_ambiguity_response.to_string(),
    ]));

    let actionability = ActionabilityEvaluator::new(mock_client.clone());
    let ambiguity = AmbiguityEvaluator::new(mock_client);

    let action_report = actionability.evaluate(thought).await.unwrap();
    let ambig_report = ambiguity.evaluate(thought).await.unwrap();

    // Assertions
    assert!(!action_report.is_actionable(), "Vague thought should not be actionable");
    assert!(!ambig_report.is_clear(), "Vague thought should not be clear");

    assert!(action_report.score < 0.50);
    assert!(ambig_report.score > 0.50);

    assert!(ambig_report.vague_elements.len() >= 2, "Should identify multiple vague elements");
    assert!(ambig_report.questions_to_ask.len() >= 2, "Should suggest clarifying questions");
}

#[tokio::test]
async fn test_weak_dimensions_identification() {
    let thought = "Create a new feature for user authentication.";

    let mock_response = r#"{
        "score": 0.58,
        "dimensions": {
            "clear_goal": 0.75,
            "technical_details": 0.40,
            "success_criteria": 0.30,
            "dependencies": 0.65,
            "bounded_scope": 0.80
        },
        "missing_elements": [
            {
                "dimension": "technical_details",
                "description": "No authentication method specified (OAuth, JWT, session-based?)",
                "suggested_question": "Which authentication method should be used?"
            },
            {
                "dimension": "success_criteria",
                "description": "No test cases or acceptance criteria defined",
                "suggested_question": "What confirms the feature works correctly?"
            }
        ],
        "confidence": 0.82
    }"#;

    let mock_client = Box::new(MockLLMClient::new(vec![mock_response.to_string()]));
    let actionability = ActionabilityEvaluator::new(mock_client);

    let report = actionability.evaluate(thought).await.unwrap();

    let weak = report.weak_dimensions();

    assert!(weak.len() >= 2, "Should identify weak dimensions");
    assert!(
        weak.iter().any(|(dim, _)| *dim == "technical_details"),
        "technical_details should be weak"
    );
    assert!(
        weak.iter().any(|(dim, _)| *dim == "success_criteria"),
        "success_criteria should be weak"
    );
}

#[tokio::test]
async fn test_ambiguity_category_distribution() {
    let thought = "Use RLHF to make the model better and faster.";

    let mock_response = r#"{
        "score": 0.82,
        "vague_elements": [
            {
                "category": "undefined_terms",
                "text": "RLHF",
                "reason": "Acronym used without definition",
                "suggested_question": "What does RLHF stand for?"
            },
            {
                "category": "missing_specifics",
                "text": "better",
                "reason": "No measurable improvement criterion",
                "suggested_question": "Better how? Accuracy? Consistency?"
            },
            {
                "category": "missing_specifics",
                "text": "faster",
                "reason": "No baseline or target latency",
                "suggested_question": "How much faster? Current vs target latency?"
            }
        ],
        "questions_to_ask": [
            "What does RLHF stand for?",
            "Better how? Accuracy? Consistency?",
            "How much faster? Current vs target latency?"
        ],
        "confidence": 0.91
    }"#;

    let mock_client = Box::new(MockLLMClient::new(vec![mock_response.to_string()]));
    let ambiguity = AmbiguityEvaluator::new(mock_client);

    let report = ambiguity.evaluate(thought).await.unwrap();

    let counts = report.vague_by_category();

    assert_eq!(*counts.get("undefined_terms").unwrap_or(&0), 1);
    assert_eq!(*counts.get("missing_specifics").unwrap_or(&0), 2);

    let priority = report.priority_questions(2);
    assert_eq!(priority.len(), 2);
}
