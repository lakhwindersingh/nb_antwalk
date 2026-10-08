use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, thiserror::Error, PartialEq)]
pub enum MvsSynthesisError {
    #[error("E_MVS_LOW_CONFIDENCE: Synthesized MVS confidence score {confidence:.2} is below required threshold {threshold:.2}")]
    LowConfidence { confidence: f64, threshold: f64 },

    #[error("E_MVS_EMPTY_COMPONENTS: MVS specification must contain at least one concrete component")]
    EmptyComponents,

    #[error("E_MVS_PARSING_FAILED: Failed to parse MVS specification: {0}")]
    ParsingFailed(String),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MvsComponent {
    pub name: String,
    pub description: String,
    pub interface_spec: String,
    pub target_tests: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MvsConstraint {
    pub constraint_type: String, // e.g., "Performance", "Security", "ZeroLeakage"
    pub description: String,
    pub severity: String,        // "MustHave", "ShouldHave"
}

/// Minimum Viable Set (MVS) Specification (E-THOUGHT-02 / CAP-01)
/// Standardized structured specification derived from unstructured thoughts.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MvsSpecification {
    pub mvs_id: String,
    pub thought_id: String,
    pub title: String,
    pub domain_slug: String,
    pub components: Vec<MvsComponent>,
    pub constraints: Vec<MvsConstraint>,
    pub confidence_score: f64,
    pub created_at: DateTime<Utc>,
}

pub struct MvsSynthesizer {
    pub confidence_threshold: f64,
}

impl Default for MvsSynthesizer {
    fn default() -> Self {
        Self {
            confidence_threshold: 0.80,
        }
    }
}

impl MvsSynthesizer {
    pub fn new(confidence_threshold: f64) -> Self {
        Self {
            confidence_threshold,
        }
    }

    /// Derives formal MVS specification from evaluated thought content
    pub fn derive_mvs(
        &self,
        thought_id: &str,
        title: &str,
        domain_slug: &str,
        raw_content: &str,
        actionability_score: f64,
    ) -> Result<MvsSpecification, MvsSynthesisError> {
        if actionability_score < 0.65 {
            return Err(MvsSynthesisError::LowConfidence {
                confidence: actionability_score,
                threshold: self.confidence_threshold,
            });
        }

        // Deterministic extraction of components from headers and code blocks
        let mut components = Vec::new();
        let mut constraints = Vec::new();

        for line in raw_content.lines() {
            let trimmed = line.trim();
            if trimmed.starts_with("## Component:") || trimmed.starts_with("### Component:") {
                let comp_name = trimmed.replace("## Component:", "").replace("### Component:", "").trim().to_string();
                components.push(MvsComponent {
                    name: comp_name.clone(),
                    description: format!("Autonomous component derived for {}", comp_name),
                    interface_spec: format!("pub trait {}Engine", comp_name),
                    target_tests: vec![format!("test_{}_lifecycle", comp_name.to_lowercase())],
                });
            } else if trimmed.starts_with("Constraint:") || trimmed.starts_with("- Constraint:") {
                let c_text = trimmed.replace("- Constraint:", "").replace("Constraint:", "").trim().to_string();
                constraints.push(MvsConstraint {
                    constraint_type: "Invariant".to_string(),
                    description: c_text,
                    severity: "MustHave".to_string(),
                });
            }
        }

        // Fallback default component if general actionable thought
        if components.is_empty() {
            components.push(MvsComponent {
                name: format!("{}_core", domain_slug),
                description: format!("Core domain implementation for {}", title),
                interface_spec: "pub struct CoreEngine;".to_string(),
                target_tests: vec!["test_core_execution".to_string()],
            });
        }

        let mvs_id = format!("mvs_{}_{}", domain_slug, Utc::now().timestamp());

        Ok(MvsSpecification {
            mvs_id,
            thought_id: thought_id.to_string(),
            title: title.to_string(),
            domain_slug: domain_slug.to_string(),
            components,
            constraints,
            confidence_score: actionability_score,
            created_at: Utc::now(),
        })
    }

    pub fn serialize_spec(&self, spec: &MvsSpecification) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(spec)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mvs_derivation_success() {
        let synthesizer = MvsSynthesizer::default();
        let thought = r#"
        # Real-Time Vector Cache
        ## Component: CacheEngine
        High performance in-memory LRU vector store
        - Constraint: P95 latency must be sub-1ms
        "#;

        let res = synthesizer.derive_mvs("t-001", "Vector Cache", "vector_cache", thought, 0.88);
        assert!(res.is_ok());
        let spec = res.unwrap();
        assert_eq!(spec.thought_id, "t-001");
        assert_eq!(spec.components.len(), 1);
        assert_eq!(spec.components[0].name, "CacheEngine");
        assert_eq!(spec.constraints.len(), 1);
    }

    #[test]
    fn test_mvs_derivation_low_confidence_rejected() {
        let synthesizer = MvsSynthesizer::new(0.80);
        let res = synthesizer.derive_mvs("t-002", "Vague Note", "vague", "some vague text", 0.50);
        assert!(matches!(res, Err(MvsSynthesisError::LowConfidence { .. })));
    }
}
