//! Email client trait and provider implementations
//!
//! Defined in Section 2.1 of `.nb/plan/extensions/email_triage/detailed.md`.

use crate::models::{OutgoingMessage, RawMessage};
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use std::sync::Arc;
use tokio::sync::RwLock;

pub type Result<T> = std::result::Result<T, crate::error::EmailError>;

/// Contract for email providers (IMAP, Gmail, Mock)
#[async_trait]
pub trait EmailClient: Send + Sync {
    async fn authenticate(&mut self, secret: &str) -> Result<()>;
    async fn fetch_messages(&self, since: DateTime<Utc>) -> Result<Vec<RawMessage>>;
    async fn mark_read(&self, message_id: &str) -> Result<()>;
    async fn archive(&self, message_id: &str) -> Result<()>;
    async fn send(&self, message: &OutgoingMessage) -> Result<()>;
}

/// In-memory Mock Email Client for testing and local simulation
#[derive(Clone, Default)]
pub struct MockEmailClient {
    authenticated: Arc<RwLock<bool>>,
    messages: Arc<RwLock<Vec<RawMessage>>>,
    sent_messages: Arc<RwLock<Vec<OutgoingMessage>>>,
    read_flags: Arc<RwLock<Vec<String>>>,
    archived_flags: Arc<RwLock<Vec<String>>>,
}

impl MockEmailClient {
    pub fn new() -> Self {
        Self::default()
    }

    pub async fn add_message(&self, msg: RawMessage) {
        let mut msgs = self.messages.write().await;
        msgs.push(msg);
    }

    pub async fn get_sent_messages(&self) -> Vec<OutgoingMessage> {
        self.sent_messages.read().await.clone()
    }

    pub async fn is_marked_read(&self, msg_id: &str) -> bool {
        self.read_flags.read().await.contains(&msg_id.to_string())
    }

    pub async fn is_archived(&self, msg_id: &str) -> bool {
        self.archived_flags.read().await.contains(&msg_id.to_string())
    }
}

#[async_trait]
impl EmailClient for MockEmailClient {
    async fn authenticate(&mut self, secret: &str) -> Result<()> {
        if secret.is_empty() {
            return Err(crate::error::EmailError::Authentication(
                "Secret token cannot be empty".to_string(),
            ));
        }
        let mut auth = self.authenticated.write().await;
        *auth = true;
        Ok(())
    }

    async fn fetch_messages(&self, since: DateTime<Utc>) -> Result<Vec<RawMessage>> {
        let auth = *self.authenticated.read().await;
        if !auth {
            return Err(crate::error::EmailError::Authentication(
                "Client is not authenticated".to_string(),
            ));
        }
        let msgs = self.messages.read().await;
        let filtered: Vec<RawMessage> = msgs
            .iter()
            .filter(|m| m.date >= since)
            .cloned()
            .collect();
        Ok(filtered)
    }

    async fn mark_read(&self, message_id: &str) -> Result<()> {
        let mut flags = self.read_flags.write().await;
        if !flags.contains(&message_id.to_string()) {
            flags.push(message_id.to_string());
        }
        Ok(())
    }

    async fn archive(&self, message_id: &str) -> Result<()> {
        let mut flags = self.archived_flags.write().await;
        if !flags.contains(&message_id.to_string()) {
            flags.push(message_id.to_string());
        }
        Ok(())
    }

    async fn send(&self, message: &OutgoingMessage) -> Result<()> {
        let mut sent = self.sent_messages.write().await;
        sent.push(message.clone());
        Ok(())
    }
}
