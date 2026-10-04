//! Structured entity extraction from emails
//!
//! Defined in Section 2.2 of `.nb/plan/extensions/email_triage/detailed.md`.

use crate::classifier::LlmClient;
use crate::error::Result;
use chrono::Utc;
use pos_email::Email;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::sync::Arc;

/// Extracted task entity for Personal OS Projects pillar
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExtractedTask {
    pub title: String,
    pub description: String,
    pub due_date: Option<String>,
    pub priority: u8, // 1 (low) to 4 (critical)
}

/// Extracted calendar event for Personal OS Activities pillar
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExtractedEvent {
    pub title: String,
    pub start: String,
    pub end: Option<String>,
    pub location: Option<String>,
    pub attendees: Vec<String>,
}

/// Extracted contact for Personal OS Interactions / CRM pillar
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExtractedContact {
    pub name: String,
    pub email: String,
    pub organization: Option<String>,
    pub phone: Option<String>,
    pub title: Option<String>,
}

/// Extracted receipt for Personal OS Purchases pillar
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExtractedReceipt {
    pub vendor: String,
    pub amount_cents: i64,
    pub currency: String,
    pub date: String,
    pub items: Vec<String>,
}

pub struct EntityExtractor {
    llm_client: Option<Arc<dyn LlmClient>>,
    price_regex: Regex,
}

impl Default for EntityExtractor {
    fn default() -> Self {
        Self::new(None)
    }
}

impl EntityExtractor {
    pub fn new(llm_client: Option<Arc<dyn LlmClient>>) -> Self {
        Self {
            llm_client,
            price_regex: Regex::new(r"\$(\d+(?:\.\d{2})?)").unwrap(),
        }
    }

    /// Extract action items and tasks
    pub async fn extract_tasks(&self, email: &Email) -> Result<Vec<ExtractedTask>> {
        if let Some(ref llm) = self.llm_client {
            let prompt = format!(
                "Extract action items from this email. Return JSON array.\n\n\
                 Subject: {}\n\
                 Body: {}\n\n\
                 Format: [{{\"title\": \"...\", \"description\": \"...\", \"due_date\": \"YYYY-MM-DD or null\", \"priority\": 1-4}}]",
                email.subject, email.body_snippet
            );

            if let Ok(response) = llm.complete(&prompt).await {
                if let Ok(tasks) = serde_json::from_str::<Vec<ExtractedTask>>(&response) {
                    return Ok(tasks);
                }
            }
        }

        // Rule-based task extraction fallback
        let title = format!("Follow up on: {}", email.subject);
        let task = ExtractedTask {
            title,
            description: email.body_snippet.clone(),
            due_date: None,
            priority: 2,
        };
        Ok(vec![task])
    }

    /// Extract calendar events
    pub async fn extract_events(&self, email: &Email) -> Result<Vec<ExtractedEvent>> {
        if let Some(ref llm) = self.llm_client {
            let prompt = format!(
                "Extract meeting/event details from this email. Return JSON array.\n\n\
                 Subject: {}\n\
                 Body: {}\n\n\
                 Format: [{{\"title\": \"...\", \"start\": \"ISO8601\", \"end\": \"ISO8601\", \"location\": \"...\", \"attendees\": [...]}}]",
                email.subject, email.body_snippet
            );

            if let Ok(response) = llm.complete(&prompt).await {
                if let Ok(events) = serde_json::from_str::<Vec<ExtractedEvent>>(&response) {
                    return Ok(events);
                }
            }
        }

        // Rule-based fallback if meeting invitation detected
        let mut attendees = Vec::new();
        if let Some(from_name) = &email.from.name {
            attendees.push(format!("{} <{}>", from_name, email.from.email));
        } else {
            attendees.push(email.from.email.clone());
        }

        let event = ExtractedEvent {
            title: email.subject.clone(),
            start: Utc::now().to_rfc3339(),
            end: None,
            location: None,
            attendees,
        };
        Ok(vec![event])
    }

    /// Extract contact from sender and signature
    pub async fn extract_contacts(&self, email: &Email) -> Result<Vec<ExtractedContact>> {
        let name = email
            .from
            .name
            .clone()
            .unwrap_or_else(|| email.from.email.split('@').next().unwrap_or("").to_string());

        let mut organization = None;
        if let Some(domain) = email.from.email.split('@').nth(1) {
            let org = domain.split('.').next().unwrap_or("");
            if !org.is_empty() && org != "gmail" && org != "yahoo" && org != "hotmail" && org != "outlook" {
                organization = Some(org.to_string());
            }
        }

        let contact = ExtractedContact {
            name,
            email: email.from.email.clone(),
            organization,
            phone: None,
            title: None,
        };
        Ok(vec![contact])
    }

    /// Extract receipt details from purchase confirmations
    pub async fn extract_receipt(&self, email: &Email) -> Result<ExtractedReceipt> {
        if let Some(ref llm) = self.llm_client {
            let prompt = format!(
                "Extract receipt details from this email. Return JSON.\n\n\
                 Subject: {}\n\
                 Body: {}\n\n\
                 Format: {{\"vendor\": \"...\", \"amount_cents\": 0, \"currency\": \"USD\", \"date\": \"YYYY-MM-DD\", \"items\": [...]}}",
                email.subject, email.body_snippet
            );

            if let Ok(response) = llm.complete(&prompt).await {
                if let Ok(receipt) = serde_json::from_str::<ExtractedReceipt>(&response) {
                    return Ok(receipt);
                }
            }
        }

        // Rule-based fallback
        let amount = self
            .price_regex
            .captures(&email.body_snippet)
            .and_then(|cap| cap.get(1))
            .and_then(|m| m.as_str().parse::<f64>().ok())
            .unwrap_or(0.0);

        let vendor = email
            .from
            .name
            .clone()
            .unwrap_or_else(|| email.from.email.clone());

        let receipt = ExtractedReceipt {
            vendor,
            amount_cents: (amount * 100.0) as i64,
            currency: "USD".to_string(),
            date: email.date.format("%Y-%m-%d").to_string(),
            items: vec![email.subject.clone()],
        };
        Ok(receipt)
    }
}
