//! Data models for `pos_email`
//!
//! Follows Section 2.1 of `.nb/plan/extensions/email_triage/detailed.md`.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Reference to a credential stored in the secure vault
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CredentialRef {
    pub vault_item_id: String,
    pub secret_key_alias: String,
}

/// Email provider configuration
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum EmailProvider {
    Gmail {
        project_id: String,
        client_id: String,
    },
    Imap {
        host: String,
        port: u16,
        tls: bool,
    },
    Exchange {
        server_url: String,
    },
}

/// Sync state tracking timestamp, cursor, and sync tokens
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyncState {
    pub last_sync: DateTime<Utc>,
    pub last_message_id: Option<String>,
    pub sync_token: Option<String>,
}

impl Default for SyncState {
    fn default() -> Self {
        Self {
            last_sync: Utc::now(),
            last_message_id: None,
            sync_token: None,
        }
    }
}

/// Email account configuration
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EmailAccount {
    pub id: Uuid,
    pub email: String,
    pub provider: EmailProvider,
    pub credentials: CredentialRef,
    pub sync_state: SyncState,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
}

impl EmailAccount {
    pub fn new(email: String, provider: EmailProvider, credentials: CredentialRef) -> Self {
        Self {
            id: Uuid::new_v4(),
            email,
            provider,
            credentials,
            sync_state: SyncState::default(),
            is_active: true,
            created_at: Utc::now(),
        }
    }
}

/// Standardized email address with optional display name
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EmailAddress {
    pub name: Option<String>,
    pub email: String,
}

impl EmailAddress {
    pub fn new(name: Option<String>, email: String) -> Self {
        Self { name, email }
    }

    pub fn parse(raw: &str) -> Self {
        let trimmed = raw.trim();
        if let Some(start) = trimmed.find('<') {
            if let Some(end) = trimmed.find('>') {
                let name = trimmed[..start].trim().trim_matches('"');
                let addr = trimmed[start + 1..end].trim();
                return Self {
                    name: if name.is_empty() { None } else { Some(name.to_string()) },
                    email: addr.to_string(),
                };
            }
        }
        Self {
            name: None,
            email: trimmed.to_string(),
        }
    }
}

/// Category classification according to Section 2.1 & Section 4
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EmailCategory {
    ActionRequired,
    Fyi,
    Newsletter,
    Receipt,
    Spam,
}

impl EmailCategory {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::ActionRequired => "action_required",
            Self::Fyi => "fyi",
            Self::Newsletter => "newsletter",
            Self::Receipt => "receipt",
            Self::Spam => "spam",
        }
    }

    pub fn from_str_loose(s: &str) -> Option<Self> {
        match s.to_lowercase().trim() {
            "action_required" | "action required" | "action" => Some(Self::ActionRequired),
            "fyi" | "informational" => Some(Self::Fyi),
            "newsletter" | "marketing" | "promo" => Some(Self::Newsletter),
            "receipt" | "invoice" | "order" => Some(Self::Receipt),
            "spam" | "junk" => Some(Self::Spam),
            _ => None,
        }
    }
}

/// Canonical metadata model for an email message
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Email {
    pub id: Uuid,
    pub message_id: String,
    pub account_id: Uuid,
    pub from: EmailAddress,
    pub to: Vec<EmailAddress>,
    pub cc: Vec<EmailAddress>,
    pub subject: String,
    pub date: DateTime<Utc>,
    pub body_snippet: String, // First 500 chars (body itself not persisted per Privacy Rule 1)
    pub has_attachments: bool,
    pub thread_id: Option<String>,
    pub in_reply_to: Option<String>,
    pub category: Option<EmailCategory>,
    pub classification_confidence: Option<f32>,
    pub classification_reasoning: Option<String>,
    pub is_read: bool,
    pub is_archived: bool,
}

/// Raw message fetched from IMAP or Gmail API prior to parsing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawMessage {
    pub message_id: String,
    pub thread_id: Option<String>,
    pub date: DateTime<Utc>,
    pub from_raw: String,
    pub to_raw: Vec<String>,
    pub cc_raw: Vec<String>,
    pub subject: String,
    pub body_text: String,
    pub has_attachments: bool,
}

impl RawMessage {
    /// Convert to canonical Email metadata struct (truncating body to snippet)
    pub fn into_email(self, account_id: Uuid) -> Email {
        let snippet = if self.body_text.len() > 500 {
            self.body_text[..500].to_string()
        } else {
            self.body_text
        };

        Email {
            id: Uuid::new_v4(),
            message_id: self.message_id,
            account_id,
            from: EmailAddress::parse(&self.from_raw),
            to: self.to_raw.iter().map(|s| EmailAddress::parse(s)).collect(),
            cc: self.cc_raw.iter().map(|s| EmailAddress::parse(s)).collect(),
            subject: self.subject,
            date: self.date,
            body_snippet: snippet,
            has_attachments: self.has_attachments,
            thread_id: self.thread_id,
            in_reply_to: None,
            category: None,
            classification_confidence: None,
            classification_reasoning: None,
            is_read: false,
            is_archived: false,
        }
    }
}

/// Outgoing email message definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutgoingMessage {
    pub to: Vec<EmailAddress>,
    pub cc: Vec<EmailAddress>,
    pub subject: String,
    pub body: String,
    pub in_reply_to: Option<String>,
}
