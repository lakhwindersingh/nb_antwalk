//! Error types for `pos_email`

use thiserror::Error;

pub type Result<T> = std::result::Result<T, EmailError>;

#[derive(Error, Debug)]
pub enum EmailError {
    #[error("Authentication failed: {0}")]
    Authentication(String),

    #[error("Database error: {0}")]
    Database(String),

    #[error("Network/IO error: {0}")]
    Network(String),

    #[error("Parse error: {0}")]
    Parse(String),

    #[error("Entity not found: {0}")]
    NotFound(String),

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

impl From<rusqlite::Error> for EmailError {
    fn from(err: rusqlite::Error) -> Self {
        EmailError::Database(err.to_string())
    }
}
