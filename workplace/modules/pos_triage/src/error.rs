//! Error definitions for `pos_triage`

use thiserror::Error;

pub type Result<T> = std::result::Result<T, TriageError>;

#[derive(Error, Debug)]
pub enum TriageError {
    #[error("Classification error: {0}")]
    Classification(String),

    #[error("Extraction error: {0}")]
    Extraction(String),

    #[error("LLM provider error: {0}")]
    Llm(String),

    #[error("Pillar dispatch error: {0}")]
    PillarDispatch(String),

    #[error("Email engine error: {0}")]
    Email(#[from] pos_email::EmailError),

    #[error("JSON Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}
