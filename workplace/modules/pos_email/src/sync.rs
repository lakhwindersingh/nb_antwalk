//! Sync engine for polling mailboxes and persisting metadata
//!
//! Defined in Section 1 & Section 4 Sequence Diagram of `.nb/plan/extensions/email_triage/concise.md`.

use crate::client::EmailClient;
use crate::db::EmailStore;
use crate::error::Result;
use crate::models::{Email, EmailAccount, SyncState};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::time::Instant;
use uuid::Uuid;

/// Summary metrics returned upon sync completion
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncResult {
    pub account_id: Uuid,
    pub fetched_count: usize,
    pub stored_count: usize,
    pub duration_ms: u64,
}

pub struct EmailSyncEngine<C: EmailClient> {
    client: C,
    store: EmailStore,
}

impl<C: EmailClient> EmailSyncEngine<C> {
    pub fn new(client: C, store: EmailStore) -> Self {
        Self { client, store }
    }

    /// Perform a synchronization pass for the given account
    pub async fn sync_account(&mut self, account: &EmailAccount, secret: &str) -> Result<SyncResult> {
        let start_time = Instant::now();

        // 1. Authenticate with provider
        self.client.authenticate(secret).await?;

        // 2. Fetch raw messages since last_sync
        let since = account.sync_state.last_sync;
        let raw_messages = self.client.fetch_messages(since).await?;
        let fetched_count = raw_messages.len();

        // 3. Transform and persist metadata into SQLite
        let mut stored_count = 0;
        let mut latest_message_id = account.sync_state.last_message_id.clone();
        let mut latest_date = since;

        for raw in raw_messages {
            if raw.date > latest_date {
                latest_date = raw.date;
                latest_message_id = Some(raw.message_id.clone());
            }

            let email: Email = raw.into_email(account.id);
            self.store.insert_email(&email)?;
            stored_count += 1;
        }

        // 4. Advance and commit account sync state cursor
        let new_state = SyncState {
            last_sync: if fetched_count > 0 { latest_date } else { Utc::now() },
            last_message_id: latest_message_id,
            sync_token: account.sync_state.sync_token.clone(),
        };
        self.store.update_sync_state(account.id, &new_state)?;

        let duration_ms = start_time.elapsed().as_millis() as u64;

        Ok(SyncResult {
            account_id: account.id,
            fetched_count,
            stored_count,
            duration_ms,
        })
    }
}
