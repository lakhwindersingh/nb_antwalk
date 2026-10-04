//! Feature extraction for email classification
//!
//! Defined in Section 2.2 of `.nb/plan/extensions/email_triage/detailed.md`.

use pos_email::Email;
use regex::Regex;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EmailFeatures {
    pub has_question_mark: bool,
    pub has_deadline_words: bool,
    pub has_unsubscribe_link: bool,
    pub has_price_pattern: bool,
    pub extracted_price: Option<f64>,
    pub sender_in_contacts: bool,
    pub is_cc_recipient: bool,
    pub word_count: usize,
}

pub struct FeatureExtractor {
    price_regex: Regex,
}

impl Default for FeatureExtractor {
    fn default() -> Self {
        Self::new()
    }
}

impl FeatureExtractor {
    pub fn new() -> Self {
        let price_regex = Regex::new(r"(?:\$|USD\s*|EUR\s*|€)(\d+(?:\.\d{2})?)").unwrap();
        Self { price_regex }
    }

    /// Extract feature vector from an email metadata snippet
    pub fn extract(&self, email: &Email, user_email: Option<&str>) -> EmailFeatures {
        let snippet_lower = email.body_snippet.to_lowercase();
        let subject_lower = email.subject.to_lowercase();

        let has_question_mark = email.subject.contains('?') || email.body_snippet.contains('?');
        let has_deadline_words = self.contains_deadline_words(&subject_lower)
            || self.contains_deadline_words(&snippet_lower);
        let has_unsubscribe_link = snippet_lower.contains("unsubscribe")
            || snippet_lower.contains("opt out")
            || snippet_lower.contains("manage preferences");

        let extracted_price = self.extract_price(&email.body_snippet);
        let has_price_pattern = extracted_price.is_some();

        let is_cc_recipient = user_email
            .map(|u| email.cc.iter().any(|addr| addr.email.eq_ignore_ascii_case(u)))
            .unwrap_or(false);

        let word_count = email.body_snippet.split_whitespace().count();

        EmailFeatures {
            has_question_mark,
            has_deadline_words,
            has_unsubscribe_link,
            has_price_pattern,
            extracted_price,
            sender_in_contacts: false, // Updated when integrated with contacts CRM
            is_cc_recipient,
            word_count,
        }
    }

    fn contains_deadline_words(&self, text: &str) -> bool {
        let deadline_keywords = [
            "deadline",
            "due",
            "by tomorrow",
            "asap",
            "urgent",
            "action required",
            "please review",
            "waiting for your",
            "follow up",
        ];
        deadline_keywords.iter().any(|kw| text.contains(kw))
    }

    fn extract_price(&self, text: &str) -> Option<f64> {
        self.price_regex
            .captures(text)
            .and_then(|cap| cap.get(1))
            .and_then(|m| m.as_str().parse::<f64>().ok())
    }
}
