//! `pos_email` - Core Email Engine & Daemon for Personal OS
//!
//! Provides RFC 5322 parsing, metadata persistence, SQLite local store,
//! and sync loop execution per `.nb/plan/extensions/email_triage/detailed.md`.

pub mod client;
pub mod db;
pub mod error;
pub mod models;
pub mod sync;

pub use client::{EmailClient, MockEmailClient};
pub use db::EmailStore;
pub use error::{EmailError, Result};
pub use models::{
    CredentialRef, Email, EmailAccount, EmailAddress, EmailCategory, EmailProvider, OutgoingMessage,
    RawMessage, SyncState,
};
pub use sync::{EmailSyncEngine, SyncResult};
