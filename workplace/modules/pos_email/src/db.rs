//! SQLite metadata store for `pos_email`
//!
//! Implements Section 3 SQLite schema of `.nb/plan/extensions/email_triage/detailed.md`.

use crate::error::{EmailError, Result};
use crate::models::{
    CredentialRef, Email, EmailAccount, EmailAddress, EmailCategory, EmailProvider, SyncState,
};
use chrono::{DateTime, Utc};
use parking_lot::Mutex;
use rusqlite::{params, Connection};
use std::path::Path;
use std::sync::Arc;
use uuid::Uuid;

/// Thread-safe SQLite store for email accounts and metadata
#[derive(Clone)]
pub struct EmailStore {
    conn: Arc<Mutex<Connection>>,
}

impl EmailStore {
    /// Open SQLite database at given path (or in-memory if :memory:)
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        let store = Self {
            conn: Arc::new(Mutex::new(conn)),
        };
        store.run_migrations()?;
        Ok(store)
    }

    /// Open an ephemeral in-memory database (useful for testing)
    pub fn open_in_memory() -> Result<Self> {
        let conn = Connection::open_in_memory()?;
        let store = Self {
            conn: Arc::new(Mutex::new(conn)),
        };
        store.run_migrations()?;
        Ok(store)
    }

    /// Run SQLite DDL migrations matching Section 3 schema
    pub fn run_migrations(&self) -> Result<()> {
        let conn = self.conn.lock();
        conn.execute_batch(
            r#"
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS email_accounts (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                provider TEXT NOT NULL CHECK (provider IN ('gmail', 'imap', 'exchange')),
                provider_config TEXT NOT NULL,
                vault_credential_id TEXT NOT NULL,
                last_sync TEXT,
                last_message_id TEXT,
                sync_token TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                message_id TEXT UNIQUE NOT NULL,
                account_id TEXT NOT NULL REFERENCES email_accounts(id) ON DELETE CASCADE,
                thread_id TEXT,
                in_reply_to TEXT,
                from_name TEXT,
                from_email TEXT NOT NULL,
                to_emails TEXT NOT NULL,
                cc_emails TEXT,
                subject TEXT NOT NULL,
                date TEXT NOT NULL,
                body_snippet TEXT NOT NULL,
                has_attachments INTEGER NOT NULL DEFAULT 0,
                category TEXT CHECK (category IN ('action_required', 'fyi', 'newsletter', 'receipt', 'spam')),
                classification_confidence REAL,
                classification_reasoning TEXT,
                is_read INTEGER NOT NULL DEFAULT 0,
                is_archived INTEGER NOT NULL DEFAULT 0,
                fetched_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_emails_account_date ON emails (account_id, date DESC);
            CREATE INDEX IF NOT EXISTS idx_emails_category ON emails (category, date DESC);
            CREATE INDEX IF NOT EXISTS idx_emails_thread ON emails (thread_id);

            CREATE TABLE IF NOT EXISTS email_summaries (
                id TEXT PRIMARY KEY,
                email_id TEXT UNIQUE NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
                summary TEXT NOT NULL,
                key_points TEXT NOT NULL,
                generated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS email_extracted_entities (
                id TEXT PRIMARY KEY,
                email_id TEXT NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
                entity_type TEXT NOT NULL CHECK (entity_type IN ('task', 'event', 'contact', 'receipt')),
                entity_id TEXT NOT NULL,
                pillar TEXT NOT NULL CHECK (pillar IN ('projects', 'activities', 'interactions', 'purchases')),
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_entities_email ON email_extracted_entities (email_id);
            CREATE INDEX IF NOT EXISTS idx_entities_target ON email_extracted_entities (pillar, entity_id);

            CREATE TABLE IF NOT EXISTS email_reply_drafts (
                id TEXT PRIMARY KEY,
                email_id TEXT NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
                draft_body TEXT NOT NULL,
                tone TEXT NOT NULL,
                confidence REAL NOT NULL,
                generated_at TEXT NOT NULL,
                sent INTEGER NOT NULL DEFAULT 0,
                sent_at TEXT
            );
            "#,
        )?;
        Ok(())
    }

    // --- Account Operations ---

    pub fn insert_account(&self, account: &EmailAccount) -> Result<()> {
        let conn = self.conn.lock();
        let provider_str = match &account.provider {
            EmailProvider::Gmail { .. } => "gmail",
            EmailProvider::Imap { .. } => "imap",
            EmailProvider::Exchange { .. } => "exchange",
        };
        let config_json = serde_json::to_string(&account.provider)?;

        conn.execute(
            r#"
            INSERT INTO email_accounts (
                id, email, provider, provider_config, vault_credential_id,
                last_sync, last_message_id, sync_token, is_active, created_at
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)
            "#,
            params![
                account.id.to_string(),
                account.email,
                provider_str,
                config_json,
                account.credentials.vault_item_id,
                account.sync_state.last_sync.to_rfc3339(),
                account.sync_state.last_message_id,
                account.sync_state.sync_token,
                if account.is_active { 1 } else { 0 },
                account.created_at.to_rfc3339(),
            ],
        )?;
        Ok(())
    }

    pub fn get_account(&self, account_id: Uuid) -> Result<Option<EmailAccount>> {
        let conn = self.conn.lock();
        let mut stmt = conn.prepare(
            r#"
            SELECT id, email, provider_config, vault_credential_id,
                   last_sync, last_message_id, sync_token, is_active, created_at
            FROM email_accounts WHERE id = ?1
            "#,
        )?;

        let mut rows = stmt.query(params![account_id.to_string()])?;
        if let Some(row) = rows.next()? {
            let id_str: String = row.get(0)?;
            let email: String = row.get(1)?;
            let config_json: String = row.get(2)?;
            let vault_id: String = row.get(3)?;
            let last_sync_str: Option<String> = row.get(4)?;
            let last_msg: Option<String> = row.get(5)?;
            let token: Option<String> = row.get(6)?;
            let is_active_int: i32 = row.get(7)?;
            let created_at_str: String = row.get(8)?;

            let provider: EmailProvider = serde_json::from_str(&config_json)?;
            let last_sync = last_sync_str
                .and_then(|s| DateTime::parse_from_rfc3339(&s).ok())
                .map(|dt| dt.with_timezone(&Utc))
                .unwrap_or_else(Utc::now);

            let created_at = DateTime::parse_from_rfc3339(&created_at_str)
                .map(|dt| dt.with_timezone(&Utc))
                .unwrap_or_else(|_| Utc::now());

            Ok(Some(EmailAccount {
                id: Uuid::parse_str(&id_str).map_err(|e| EmailError::Database(e.to_string()))?,
                email,
                provider,
                credentials: CredentialRef {
                    vault_item_id: vault_id,
                    secret_key_alias: "default".to_string(),
                },
                sync_state: SyncState {
                    last_sync,
                    last_message_id: last_msg,
                    sync_token: token,
                },
                is_active: is_active_int == 1,
                created_at,
            }))
        } else {
            Ok(None)
        }
    }

    pub fn get_account_by_email(&self, email_addr: &str) -> Result<Option<EmailAccount>> {
        let maybe_id = {
            let conn = self.conn.lock();
            let mut stmt = conn.prepare("SELECT id FROM email_accounts WHERE email = ?1")?;
            let mut rows = stmt.query(params![email_addr])?;
            if let Some(row) = rows.next()? {
                let id_str: String = row.get(0)?;
                Some(Uuid::parse_str(&id_str).map_err(|e| EmailError::Database(e.to_string()))?)
            } else {
                None
            }
        };

        if let Some(id) = maybe_id {
            self.get_account(id)
        } else {
            Ok(None)
        }
    }

    pub fn update_sync_state(&self, account_id: Uuid, sync_state: &SyncState) -> Result<()> {
        let conn = self.conn.lock();
        conn.execute(
            r#"
            UPDATE email_accounts
            SET last_sync = ?1, last_message_id = ?2, sync_token = ?3
            WHERE id = ?4
            "#,
            params![
                sync_state.last_sync.to_rfc3339(),
                sync_state.last_message_id,
                sync_state.sync_token,
                account_id.to_string(),
            ],
        )?;
        Ok(())
    }

    // --- Email Metadata Operations ---

    pub fn insert_email(&self, email: &Email) -> Result<()> {
        let conn = self.conn.lock();
        let to_json = serde_json::to_string(&email.to)?;
        let cc_json = serde_json::to_string(&email.cc)?;
        let category_str = email.category.map(|c| c.as_str());

        conn.execute(
            r#"
            INSERT INTO emails (
                id, message_id, account_id, thread_id, in_reply_to,
                from_name, from_email, to_emails, cc_emails, subject,
                date, body_snippet, has_attachments, category,
                classification_confidence, classification_reasoning,
                is_read, is_archived, fetched_at
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?18, ?19)
            ON CONFLICT(message_id) DO UPDATE SET
                subject = excluded.subject,
                category = excluded.category,
                classification_confidence = excluded.classification_confidence,
                classification_reasoning = excluded.classification_reasoning,
                is_read = excluded.is_read,
                is_archived = excluded.is_archived
            "#,
            params![
                email.id.to_string(),
                email.message_id,
                email.account_id.to_string(),
                email.thread_id,
                email.in_reply_to,
                email.from.name,
                email.from.email,
                to_json,
                cc_json,
                email.subject,
                email.date.to_rfc3339(),
                email.body_snippet,
                if email.has_attachments { 1 } else { 0 },
                category_str,
                email.classification_confidence,
                email.classification_reasoning,
                if email.is_read { 1 } else { 0 },
                if email.is_archived { 1 } else { 0 },
                Utc::now().to_rfc3339(),
            ],
        )?;
        Ok(())
    }

    pub fn update_classification(
        &self,
        email_id: Uuid,
        category: EmailCategory,
        confidence: f32,
        reasoning: &str,
    ) -> Result<()> {
        let conn = self.conn.lock();
        conn.execute(
            r#"
            UPDATE emails
            SET category = ?1, classification_confidence = ?2, classification_reasoning = ?3
            WHERE id = ?4
            "#,
            params![category.as_str(), confidence, reasoning, email_id.to_string()],
        )?;
        Ok(())
    }

    pub fn get_email_by_message_id(&self, message_id: &str) -> Result<Option<Email>> {
        let conn = self.conn.lock();
        let mut stmt = conn.prepare(
            r#"
            SELECT id, message_id, account_id, thread_id, in_reply_to,
                   from_name, from_email, to_emails, cc_emails, subject,
                   date, body_snippet, has_attachments, category,
                   classification_confidence, classification_reasoning,
                   is_read, is_archived
            FROM emails WHERE message_id = ?1
            "#,
        )?;

        let mut rows = stmt.query(params![message_id])?;
        if let Some(row) = rows.next()? {
            self.map_email_row(row)
        } else {
            Ok(None)
        }
    }

    pub fn get_emails_by_category(
        &self,
        category: EmailCategory,
        limit: usize,
    ) -> Result<Vec<Email>> {
        let conn = self.conn.lock();
        let mut stmt = conn.prepare(
            r#"
            SELECT id, message_id, account_id, thread_id, in_reply_to,
                   from_name, from_email, to_emails, cc_emails, subject,
                   date, body_snippet, has_attachments, category,
                   classification_confidence, classification_reasoning,
                   is_read, is_archived
            FROM emails
            WHERE category = ?1 AND is_archived = 0
            ORDER BY date DESC
            LIMIT ?2
            "#,
        )?;

        let rows = stmt.query_map(params![category.as_str(), limit as i64], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, Option<String>>(3)?,
                row.get::<_, Option<String>>(4)?,
                row.get::<_, Option<String>>(5)?,
                row.get::<_, String>(6)?,
                row.get::<_, String>(7)?,
                row.get::<_, Option<String>>(8)?,
                row.get::<_, String>(9)?,
                row.get::<_, String>(10)?,
                row.get::<_, String>(11)?,
                row.get::<_, i32>(12)?,
                row.get::<_, Option<String>>(13)?,
                row.get::<_, Option<f32>>(14)?,
                row.get::<_, Option<String>>(15)?,
                row.get::<_, i32>(16)?,
                row.get::<_, i32>(17)?,
            ))
        })?;

        let mut emails = Vec::new();
        for item in rows {
            let (
                id_s,
                msg_id,
                acc_s,
                thread_id,
                reply_to,
                from_name,
                from_email,
                to_json,
                cc_json,
                subject,
                date_s,
                snippet,
                has_att,
                cat_s,
                conf,
                reasoning,
                is_read,
                is_arch,
            ) = item?;

            let id = Uuid::parse_str(&id_s).unwrap_or_else(|_| Uuid::new_v4());
            let account_id = Uuid::parse_str(&acc_s).unwrap_or_else(|_| Uuid::new_v4());
            let to: Vec<EmailAddress> = serde_json::from_str(&to_json).unwrap_or_default();
            let cc: Vec<EmailAddress> = cc_json
                .and_then(|s| serde_json::from_str(&s).ok())
                .unwrap_or_default();
            let date = DateTime::parse_from_rfc3339(&date_s)
                .map(|dt| dt.with_timezone(&Utc))
                .unwrap_or_else(|_| Utc::now());
            let cat = cat_s.as_deref().and_then(EmailCategory::from_str_loose);

            emails.push(Email {
                id,
                message_id: msg_id,
                account_id,
                from: EmailAddress::new(from_name, from_email),
                to,
                cc,
                subject,
                date,
                body_snippet: snippet,
                has_attachments: has_att == 1,
                thread_id,
                in_reply_to: reply_to,
                category: cat,
                classification_confidence: conf,
                classification_reasoning: reasoning,
                is_read: is_read == 1,
                is_archived: is_arch == 1,
            });
        }

        Ok(emails)
    }

    pub fn list_unclassified_emails(&self, limit: usize) -> Result<Vec<Email>> {
        let conn = self.conn.lock();
        let mut stmt = conn.prepare(
            r#"
            SELECT id, message_id, account_id, thread_id, in_reply_to,
                   from_name, from_email, to_emails, cc_emails, subject,
                   date, body_snippet, has_attachments, category,
                   classification_confidence, classification_reasoning,
                   is_read, is_archived
            FROM emails
            WHERE category IS NULL
            ORDER BY date DESC
            LIMIT ?1
            "#,
        )?;

        let rows = stmt.query_map(params![limit as i64], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, Option<String>>(3)?,
                row.get::<_, Option<String>>(4)?,
                row.get::<_, Option<String>>(5)?,
                row.get::<_, String>(6)?,
                row.get::<_, String>(7)?,
                row.get::<_, Option<String>>(8)?,
                row.get::<_, String>(9)?,
                row.get::<_, String>(10)?,
                row.get::<_, String>(11)?,
                row.get::<_, i32>(12)?,
                row.get::<_, Option<String>>(13)?,
                row.get::<_, Option<f32>>(14)?,
                row.get::<_, Option<String>>(15)?,
                row.get::<_, i32>(16)?,
                row.get::<_, i32>(17)?,
            ))
        })?;

        let mut emails = Vec::new();
        for item in rows {
            let (
                id_s,
                msg_id,
                acc_s,
                thread_id,
                reply_to,
                from_name,
                from_email,
                to_json,
                cc_json,
                subject,
                date_s,
                snippet,
                has_att,
                cat_s,
                conf,
                reasoning,
                is_read,
                is_arch,
            ) = item?;

            let id = Uuid::parse_str(&id_s).unwrap_or_else(|_| Uuid::new_v4());
            let account_id = Uuid::parse_str(&acc_s).unwrap_or_else(|_| Uuid::new_v4());
            let to: Vec<EmailAddress> = serde_json::from_str(&to_json).unwrap_or_default();
            let cc: Vec<EmailAddress> = cc_json
                .and_then(|s| serde_json::from_str(&s).ok())
                .unwrap_or_default();
            let date = DateTime::parse_from_rfc3339(&date_s)
                .map(|dt| dt.with_timezone(&Utc))
                .unwrap_or_else(|_| Utc::now());
            let cat = cat_s.as_deref().and_then(EmailCategory::from_str_loose);

            emails.push(Email {
                id,
                message_id: msg_id,
                account_id,
                from: EmailAddress::new(from_name, from_email),
                to,
                cc,
                subject,
                date,
                body_snippet: snippet,
                has_attachments: has_att == 1,
                thread_id,
                in_reply_to: reply_to,
                category: cat,
                classification_confidence: conf,
                classification_reasoning: reasoning,
                is_read: is_read == 1,
                is_archived: is_arch == 1,
            });
        }

        Ok(emails)
    }

    // --- Entity Linkage Operations ---

    pub fn link_extracted_entity(
        &self,
        email_id: Uuid,
        entity_type: &str,
        entity_id: &str,
        pillar: &str,
    ) -> Result<()> {
        let conn = self.conn.lock();
        conn.execute(
            r#"
            INSERT INTO email_extracted_entities (id, email_id, entity_type, entity_id, pillar, created_at)
            VALUES (?1, ?2, ?3, ?4, ?5, ?6)
            "#,
            params![
                Uuid::new_v4().to_string(),
                email_id.to_string(),
                entity_type,
                entity_id,
                pillar,
                Utc::now().to_rfc3339(),
            ],
        )?;
        Ok(())
    }

    fn map_email_row(&self, row: &rusqlite::Row) -> Result<Option<Email>> {
        let id_str: String = row.get(0)?;
        let msg_id: String = row.get(1)?;
        let acc_str: String = row.get(2)?;
        let thread_id: Option<String> = row.get(3)?;
        let in_reply_to: Option<String> = row.get(4)?;
        let from_name: Option<String> = row.get(5)?;
        let from_email: String = row.get(6)?;
        let to_json: String = row.get(7)?;
        let cc_json: Option<String> = row.get(8)?;
        let subject: String = row.get(9)?;
        let date_str: String = row.get(10)?;
        let snippet: String = row.get(11)?;
        let has_attachments: i32 = row.get(12)?;
        let category_str: Option<String> = row.get(13)?;
        let conf: Option<f32> = row.get(14)?;
        let reasoning: Option<String> = row.get(15)?;
        let is_read: i32 = row.get(16)?;
        let is_archived: i32 = row.get(17)?;

        let id = Uuid::parse_str(&id_str).map_err(|e| EmailError::Database(e.to_string()))?;
        let account_id =
            Uuid::parse_str(&acc_str).map_err(|e| EmailError::Database(e.to_string()))?;
        let to: Vec<EmailAddress> = serde_json::from_str(&to_json)?;
        let cc: Vec<EmailAddress> = cc_json
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default();
        let date = DateTime::parse_from_rfc3339(&date_str)
            .map(|dt| dt.with_timezone(&Utc))
            .unwrap_or_else(|_| Utc::now());
        let category = category_str.as_deref().and_then(EmailCategory::from_str_loose);

        Ok(Some(Email {
            id,
            message_id: msg_id,
            account_id,
            from: EmailAddress::new(from_name, from_email),
            to,
            cc,
            subject,
            date,
            body_snippet: snippet,
            has_attachments: has_attachments == 1,
            thread_id,
            in_reply_to,
            category,
            classification_confidence: conf,
            classification_reasoning: reasoning,
            is_read: is_read == 1,
            is_archived: is_archived == 1,
        }))
    }
}
