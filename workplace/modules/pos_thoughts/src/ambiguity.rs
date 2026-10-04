//! Ambiguity detection for thoughts using LLM-based semantic evaluation.
//!
//! Identifies vague, unclear, or underspecified elements in thought content
//! using four key checks: undefined terms, missing specifics, unclear scope,
//! and unspecified implementation details.

use serde::{Deserialize, Serialize};
use std::error::Error as StdError;
use crate::LLMClient;

/// Element identified as vague or ambiguous.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VagueElement {
    /// Category: undefined_terms, missing_specifics, unclear_scope, unspecified_details
    pub category: String,

    /// The vague text fragment identified.
    pub text: String,

    /// Why this is problematic.
    pub reason: String,

    /// Suggested clarifying question to ask.
    pub suggested_question: String,
}

/// Result of ambiguity evaluation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AmbiguityReport {
    /// Overall ambiguity score (0.0-1.0, higher = more ambiguous).
    pub score: f64,

    /// Vague or ambiguous elements identified.
    pub vague_elements: Vec<VagueElement>,

    /// Questions to ask user for clarification.
    pub questions_to_ask: Vec<String>,

    /// Confidence in the evaluation (0.0-1.0).
    pub confidence: f64,
}

impl AmbiguityReport {
    /// Is the thought clear enough to proceed with MVS synthesis?
    pub fn is_clear(&self) -> bool {
        const MAX_ACCEPTABLE_AMBIGUITY: f64 = 0.30;
        self.score <= MAX_ACCEPTABLE_AMBIGUITY
    }

    /// Get count of vague elements by category.
    pub fn vague_by_category(&self) -> std::collections::HashMap<String, usize> {
        let mut counts = std::collections::HashMap::new();

        for element in &self.vague_elements {
            *counts.entry(element.category.clone()).or_insert(0) += 1;
        }

        counts
    }

    /// Get highest priority clarifying questions (limit to top N).
    pub fn priority_questions(&self, limit: usize) -> Vec<String> {
        self.questions_to_ask
            .iter()
            .take(limit)
            .cloned()
            .collect()
    }
}

/// LLM prompt template for ambiguity detection.
pub const AMBIGUITY_PROMPT_TEMPLATE: &str = r#"Identify vague or ambiguous elements in this thought.

Thought content:
{content}

Check for these categories of ambiguity:

1. **Undefined Terms**: Are key concepts explained or referenced? Look for jargon, acronyms, or domain terms used without definition.

2. **Missing Specifics**: Are there weasel words that lack concrete meaning?
   - "better", "faster", "improved", "optimized"
   - "some", "various", "several", "multiple"
   - "should", "might", "could", "probably"
   Look for claims without quantifiable metrics.

3. **Unclear Scope**: Is it clear what's in/out of scope?
   - Is the work bounded (e.g., "refactor auth module" vs. "improve codebase")?
   - Are edge cases or boundary conditions mentioned?
   - Is it clear when the work is "done"?

4. **Unspecified Details**: Are implementation details mentioned?
   - Data structures (struct, enum, trait definitions)
   - APIs (function signatures, HTTP endpoints)
   - Interfaces (trait bounds, generic constraints)
   - Algorithms (search strategy, caching policy)

For each vague element found:
- Extract the vague text fragment
- Explain why it's problematic
- Suggest a clarifying question to ask

Calculate score:
- 0.0-0.2: Very clear, ready to implement
- 0.3-0.5: Some ambiguity, minor clarifications needed
- 0.6-0.8: Significant ambiguity, major clarifications needed
- 0.9-1.0: Extremely vague, not actionable

Return ONLY valid JSON (no markdown fences):
{
  "score": 0.0,
  "vague_elements": [
    {
      "category": "missing_specifics",
      "text": "make it faster",
      "reason": "No baseline performance metric or target improvement specified",
      "suggested_question": "What is the current performance and what's the target?"
    }
  ],
  "questions_to_ask": [
    "What is the current performance baseline?",
    "What's the target performance improvement?"
  ],
  "confidence": 0.0
}
"#;

/// Evaluates ambiguity of thought content using LLM.
pub struct AmbiguityEvaluator {
    llm_client: Box<dyn LLMClient>,
}

impl AmbiguityEvaluator {
    /// Create new evaluator with specified LLM client.
    pub fn new(llm_client: Box<dyn LLMClient>) -> Self {
        Self { llm_client }
    }

    /// Evaluate ambiguity of thought content.
    pub async fn evaluate(&self, content: &str) -> Result<AmbiguityReport, Box<dyn StdError>> {
        let prompt = AMBIGUITY_PROMPT_TEMPLATE.replace("{content}", content);

        let response = self.llm_client
            .call(&prompt)
            .await
            .map_err(|e| format!("LLM call failed: {}", e))?;

        let report: AmbiguityReport = serde_json::from_str(&response)
            .map_err(|e| format!("Failed to parse LLM response: {}", e))?;

        // Validate score is in valid range
        if !(0.0..=1.0).contains(&report.score) {
            return Err(format!(
                "Invalid ambiguity score: {} (must be 0.0-1.0)",
                report.score
            ).into());
        }

        // Validate confidence is in valid range
        if !(0.0..=1.0).contains(&report.confidence) {
            return Err(format!(
                "Invalid confidence: {} (must be 0.0-1.0)",
                report.confidence
            ).into());
        }

        Ok(report)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ambiguity_threshold() {
        let report = AmbiguityReport {
            score: 0.25,
            vague_elements: vec![VagueElement {
                category: "missing_specifics".to_string(),
                text: "make it better".to_string(),
                reason: "No concrete metric defined".to_string(),
                suggested_question: "What metric should improve?".to_string(),
            }],
            questions_to_ask: vec!["What metric should improve?".to_string()],
            confidence: 0.9,
        };

        assert!(report.is_clear());
    }

    #[test]
    fn test_high_ambiguity_blocks_mvs() {
        let report = AmbiguityReport {
            score: 0.75,
            vague_elements: vec![
                VagueElement {
                    category: "unclear_scope".to_string(),
                    text: "improve the system".to_string(),
                    reason: "Scope unbounded".to_string(),
                    suggested_question: "Which part of the system?".to_string(),
                },
                VagueElement {
                    category: "unspecified_details".to_string(),
                    text: "use caching".to_string(),
                    reason: "No cache strategy specified".to_string(),
                    suggested_question: "What caching strategy (LRU, LFU, TTL)?".to_string(),
                },
            ],
            questions_to_ask: vec![
                "Which part of the system?".to_string(),
                "What caching strategy?".to_string(),
            ],
            confidence: 0.85,
        };

        assert!(!report.is_clear());
        assert_eq!(report.vague_elements.len(), 2);
    }

    #[test]
    fn test_vague_elements_by_category() {
        let report = AmbiguityReport {
            score: 0.60,
            vague_elements: vec![
                VagueElement {
                    category: "missing_specifics".to_string(),
                    text: "faster".to_string(),
                    reason: "No metric".to_string(),
                    suggested_question: "How much faster?".to_string(),
                },
                VagueElement {
                    category: "missing_specifics".to_string(),
                    text: "better".to_string(),
                    reason: "No metric".to_string(),
                    suggested_question: "Better how?".to_string(),
                },
                VagueElement {
                    category: "undefined_terms".to_string(),
                    text: "RLHF".to_string(),
                    reason: "Acronym not defined".to_string(),
                    suggested_question: "What is RLHF?".to_string(),
                },
            ],
            questions_to_ask: vec![],
            confidence: 0.8,
        };

        let counts = report.vague_by_category();

        assert_eq!(*counts.get("missing_specifics").unwrap(), 2);
        assert_eq!(*counts.get("undefined_terms").unwrap(), 1);
    }

    #[test]
    fn test_priority_questions_limit() {
        let report = AmbiguityReport {
            score: 0.50,
            vague_elements: vec![],
            questions_to_ask: vec![
                "Question 1".to_string(),
                "Question 2".to_string(),
                "Question 3".to_string(),
                "Question 4".to_string(),
            ],
            confidence: 0.9,
        };

        let priority = report.priority_questions(2);

        assert_eq!(priority.len(), 2);
        assert_eq!(priority[0], "Question 1");
        assert_eq!(priority[1], "Question 2");
    }
}
