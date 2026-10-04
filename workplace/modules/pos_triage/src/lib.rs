//! `pos_triage` - Email Classification, Entity Extraction, and Pillar Integration
//!
//! Defined in Section 2.2 of `.nb/plan/extensions/email_triage/detailed.md`.

pub mod classifier;
pub mod cli;
pub mod error;
pub mod features;
pub mod extractor;
pub mod integration;

pub use classifier::{Classification, EmailClassifier, LlmClient, MockLlmClient};
pub use cli::SmartInboxFormatter;
pub use error::{Result, TriageError};
pub use extractor::{
    EntityExtractor, ExtractedContact, ExtractedEvent, ExtractedReceipt, ExtractedTask,
};
pub use features::{EmailFeatures, FeatureExtractor};
pub use integration::{DispatchedEntity, PillarDispatcher};
