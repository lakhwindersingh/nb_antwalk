//! Email classifier implementation
//!
//! Defined in Section 2.2 and Section 4 of `.nb/plan/extensions/email_triage/detailed.md`.

use crate::error::Result;
use crate::features::{EmailFeatures, FeatureExtractor};
use async_trait::async_trait;
use pos_email::{Email, EmailCategory};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

/// Structured classification output
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Classification {
    pub category: EmailCategory,
    pub confidence: f32,
    pub reasoning: String,
}

/// Interface for LLM completions
#[async_trait]
pub trait LlmClient: Send + Sync {
    async fn complete(&self, prompt: &str) -> Result<String>;
}

/// Mock LLM Client returning canned classification or parsing responses
pub struct MockLlmClient {
    default_response: String,
}

impl MockLlmClient {
    pub fn new(default_response: &str) -> Self {
        Self {
            default_response: default_response.to_string(),
        }
    }
}

#[async_trait]
impl LlmClient for MockLlmClient {
    async fn complete(&self, _prompt: &str) -> Result<String> {
        Ok(self.default_response.clone())
    }
}

pub struct EmailClassifier {
    llm_client: Option<Arc<dyn LlmClient>>,
    feature_extractor: FeatureExtractor,
}

impl Default for EmailClassifier {
    fn default() -> Self {
        Self::new(None)
    }
}

impl EmailClassifier {
    pub fn new(llm_client: Option<Arc<dyn LlmClient>>) -> Self {
        Self {
            llm_client,
            feature_extractor: FeatureExtractor::new(),
        }
    }

    /// Classify an email using LLM with deterministic rule-based fallback
    pub async fn classify(&self, email: &Email, user_email: Option<&str>) -> Result<Classification> {
        let features = self.feature_extractor.extract(email, user_email);

        // If an LLM client is available, attempt structured LLM completion
        if let Some(ref llm) = self.llm_client {
            let prompt = format!(
                "Classify this email into one of: action_required, fyi, newsletter, receipt, spam\n\
                 Subject: {}\n\
                 From: {} <{}>\n\
                 Snippet: {}\n\
                 Features: {:#?}\n\n\
                 Return valid JSON only in format: {{\"category\": \"...\", \"confidence\": 0.0-1.0, \"reasoning\": \"...\"}}",
                email.subject,
                email.from.name.as_deref().unwrap_or(""),
                email.from.email,
                email.body_snippet,
                features
            );

            if let Ok(response) = llm.complete(&prompt).await {
                if let Ok(parsed) = serde_json::from_str::<Classification>(&response) {
                    return Ok(parsed);
                }
            }
        }

        // Fallback: Rule-based heuristic classifier (offline, fast, private)
        Ok(self.classify_rule_based(&features, email))
    }

    /// Deterministic rule-based classifier based on Section 4 guidelines
    pub fn classify_rule_based(&self, features: &EmailFeatures, email: &Email) -> Classification {
        let subject_lower = email.subject.to_lowercase();
        let from_email_lower = email.from.email.to_lowercase();

        // 1. Receipt / Financial
        if features.has_price_pattern
            && (subject_lower.contains("receipt")
                || subject_lower.contains("invoice")
                || subject_lower.contains("order")
                || subject_lower.contains("payment")
                || subject_lower.contains("paid")
                || from_email_lower.contains("stripe")
                || from_email_lower.contains("paypal")
                || from_email_lower.contains("billing"))
        {
            return Classification {
                category: EmailCategory::Receipt,
                confidence: 0.95,
                reasoning: format!(
                    "Receipt detected with price: ${:.2}",
                    features.extracted_price.unwrap_or(0.0)
                ),
            };
        }

        // 2. Newsletter / Marketing
        if features.has_unsubscribe_link
            || from_email_lower.contains("no-reply")
            || from_email_lower.contains("noreply")
            || from_email_lower.contains("newsletter")
        {
            return Classification {
                category: EmailCategory::Newsletter,
                confidence: 0.92,
                reasoning: "Contains unsubscribe indicators or bulk sender address".to_string(),
            };
        }

        // 3. Action Required
        if features.has_deadline_words
            || (features.has_question_mark && !features.is_cc_recipient)
            || subject_lower.contains("urgent")
            || subject_lower.contains("review")
        {
            return Classification {
                category: EmailCategory::ActionRequired,
                confidence: 0.88,
                reasoning: "Direct inquiry or deadline-driven request addressed to user"
                    .to_string(),
            };
        }

        // 4. Spam check
        if subject_lower.contains("crypto")
            || subject_lower.contains("win money")
            || subject_lower.contains("lottery")
            || subject_lower.contains("exclusive prize")
        {
            return Classification {
                category: EmailCategory::Spam,
                confidence: 0.96,
                reasoning: "Phishing / spam keyword indicators detected".to_string(),
            };
        }

        // 5. FYI (Informational / Notifications)
        Classification {
            category: EmailCategory::Fyi,
            confidence: 0.75,
            reasoning: "Informational notification with no urgent action required".to_string(),
        }
    }
}
