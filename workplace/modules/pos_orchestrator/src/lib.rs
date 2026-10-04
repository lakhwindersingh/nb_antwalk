//! Meta-Orchestration Layer for Personal OS
//!
//! Provides autonomous request routing and multi-processor coordination.
//! Routes incoming requests to specialized processors based on semantic intent classification.

pub mod classifier;
pub mod registry;
pub mod router;
pub mod types;
pub mod error;

pub use classifier::{IntentClassifier, Classification};
pub use registry::{ProcessorRegistry, ProcessorSpec};
pub use router::{Router, RoutingPlan};
pub use types::*;
pub use error::{OrchestratorError, Result};

/// Re-export commonly used types
pub mod prelude {
    pub use crate::classifier::{IntentClassifier, Classification};
    pub use crate::registry::{ProcessorRegistry, ProcessorSpec};
    pub use crate::router::{Router, RoutingPlan};
    pub use crate::types::*;
    pub use crate::error::{OrchestratorError, Result};
}
