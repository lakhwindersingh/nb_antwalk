//! Actionability evaluation for thoughts using LLM-based semantic analysis.
//!
//! Determines if a thought is ready to become a software project by evaluating
//! five dimensions: goal clarity, technical details, success criteria,
//! dependencies, and scope boundedness.

use serde::{Deserialize, Serialize};
use std::error::Error as StdError;
use crate::LLMClient;

/// Evaluation dimensions for actionability scoring.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionabilityDimensions {
    /// 0.0-1.0: Is the desired outcome explicitly stated?
    pub clear_goal: f64,

    /// 0.0-1.0: Are APIs, data structures, or algorithms mentioned?
    pub technical_details: f64,

    /// 0.0-1.0: Are acceptance criteria or metrics defined?
    pub success_criteria: f64,

    /// 0.0-1.0: Are constraints or prerequisites identified?
    pub dependencies: f64,

    /// 0.0-1.0: Is the scope well-defined (not too vague/large)?
    pub bounded_scope: f64,
}

impl ActionabilityDimensions {
    /// Calculate aggregate score as weighted average.
    pub fn aggregate_score(&self) -> f64 {
        const WEIGHTS: [f64; 5] = [0.25, 0.20, 0.20, 0.15, 0.20];

        let scores = [
            self.clear_goal,
            self.technical_details,
            self.success_criteria,
            self.dependencies,
            self.bounded_scope,
        ];

        scores.iter()
            .zip(WEIGHTS.iter())
            .map(|(score, weight)| score * weight)
            .sum()
    }
}

/// Missing elements identified during evaluation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissingElement {
    /// Dimension this element relates to.
    pub dimension: String,

    /// Human-readable description of what's missing.
    pub description: String,

    /// Suggested question to ask the user to clarify.
    pub suggested_question: Option<String>,
}

/// Result of actionability evaluation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionabilityReport {
    /// Overall actionability score (0.0-1.0).
    pub score: f64,

    /// Breakdown by dimension.
    pub dimensions: ActionabilityDimensions,

    /// Elements missing or unclear.
    pub missing_elements: Vec<MissingElement>,

    /// Confidence in the evaluation (0.0-1.0).
    pub confidence: f64,
}

impl ActionabilityReport {
    /// Is the thought ready to synthesize into an MVS?
    pub fn is_actionable(&self) -> bool {
        const THRESHOLD: f64 = 0.70;
        self.score >= THRESHOLD
    }

    /// Get dimensions below threshold for targeted improvement.
    pub fn weak_dimensions(&self) -> Vec<(&str, f64)> {
        const WEAK_THRESHOLD: f64 = 0.60;

        let mut weak = Vec::new();

        if self.dimensions.clear_goal < WEAK_THRESHOLD {
            weak.push(("clear_goal", self.dimensions.clear_goal));
        }
        if self.dimensions.technical_details < WEAK_THRESHOLD {
            weak.push(("technical_details", self.dimensions.technical_details));
        }
        if self.dimensions.success_criteria < WEAK_THRESHOLD {
            weak.push(("success_criteria", self.dimensions.success_criteria));
        }
        if self.dimensions.dependencies < WEAK_THRESHOLD {
            weak.push(("dependencies", self.dimensions.dependencies));
        }
        if self.dimensions.bounded_scope < WEAK_THRESHOLD {
            weak.push(("bounded_scope", self.dimensions.bounded_scope));
        }

        weak
    }
}

/// LLM prompt template for actionability evaluation.
pub const ACTIONABILITY_PROMPT_TEMPLATE: &str = r#"Evaluate if this thought is ready to become a software project.

Thought content:
{content}

Rate 0.0-1.0 on these dimensions:
1. **Clear Goal**: Is the desired outcome explicitly stated? Look for action verbs, concrete deliverables, and stated purpose.
2. **Technical Details**: Are APIs, data structures, algorithms, or implementation approaches mentioned? Look for code blocks, library names, architectural patterns.
3. **Success Criteria**: Are acceptance criteria, test cases, or success metrics defined? Look for "Given-When-Then", performance targets, or quality gates.
4. **Dependencies**: Are constraints, prerequisites, or blocking factors identified? Look for required infrastructure, external services, or data dependencies.
5. **Bounded Scope**: Is the scope well-defined (not too vague like "make it better", not too large like "rewrite entire system")?

For each dimension:
- Score 1.0 if clearly and completely addressed
- Score 0.5-0.8 if partially addressed or somewhat vague
- Score 0.0-0.4 if missing or very unclear

Also identify missing elements with suggested clarifying questions.

Return ONLY valid JSON (no markdown fences):
{
  "score": 0.0,
  "dimensions": {
    "clear_goal": 0.0,
    "technical_details": 0.0,
    "success_criteria": 0.0,
    "dependencies": 0.0,
    "bounded_scope": 0.0
  },
  "missing_elements": [
    {
      "dimension": "success_criteria",
      "description": "No test cases or acceptance criteria defined",
      "suggested_question": "What would confirm this feature works correctly?"
    }
  ],
  "confidence": 0.0
}
"#;

/// Evaluates actionability of thought content using LLM.
pub struct ActionabilityEvaluator {
    llm_client: Box<dyn LLMClient>,
}

impl ActionabilityEvaluator {
    /// Create new evaluator with specified LLM client.
    pub fn new(llm_client: Box<dyn LLMClient>) -> Self {
        Self { llm_client }
    }

    /// Evaluate actionability of thought content.
    pub async fn evaluate(&self, content: &str) -> Result<ActionabilityReport, Box<dyn StdError>> {
        let prompt = ACTIONABILITY_PROMPT_TEMPLATE.replace("{content}", content);

        let response = self.llm_client
            .call(&prompt)
            .await
            .map_err(|e| format!("LLM call failed: {}", e))?;

        let report: ActionabilityReport = serde_json::from_str(&response)
            .map_err(|e| format!("Failed to parse LLM response: {}", e))?;

        // Validate score consistency
        let calculated_score = report.dimensions.aggregate_score();
        if (calculated_score - report.score).abs() > 0.05 {
            return Err(format!(
                "Score mismatch: reported {} but calculated {}",
                report.score, calculated_score
            ).into());
        }

        Ok(report)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_aggregate_score_calculation() {
        let dimensions = ActionabilityDimensions {
            clear_goal: 1.0,
            technical_details: 0.8,
            success_criteria: 0.6,
            dependencies: 0.4,
            bounded_scope: 0.9,
        };

        let score = dimensions.aggregate_score();

        // Expected: 0.25*1.0 + 0.20*0.8 + 0.20*0.6 + 0.15*0.4 + 0.20*0.9
        //         = 0.25 + 0.16 + 0.12 + 0.06 + 0.18 = 0.77
        assert!((score - 0.77).abs() < 0.01);
    }

    #[test]
    fn test_actionability_threshold() {
        let report = ActionabilityReport {
            score: 0.75,
            dimensions: ActionabilityDimensions {
                clear_goal: 0.8,
                technical_details: 0.7,
                success_criteria: 0.7,
                dependencies: 0.8,
                bounded_scope: 0.7,
            },
            missing_elements: vec![],
            confidence: 0.9,
        };

        assert!(report.is_actionable());
    }

    #[test]
    fn test_weak_dimensions_identification() {
        let report = ActionabilityReport {
            score: 0.65,
            dimensions: ActionabilityDimensions {
                clear_goal: 0.9,
                technical_details: 0.5,  // Below 0.60 threshold
                success_criteria: 0.4,   // Below 0.60 threshold
                dependencies: 0.7,
                bounded_scope: 0.8,
            },
            missing_elements: vec![],
            confidence: 0.8,
        };

        let weak = report.weak_dimensions();

        assert_eq!(weak.len(), 2);
        assert!(weak.iter().any(|(dim, _)| *dim == "technical_details"));
        assert!(weak.iter().any(|(dim, _)| *dim == "success_criteria"));
    }
}
