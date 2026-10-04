//! Error types for the orchestrator system

use thiserror::Error;

pub type Result<T> = std::result::Result<T, OrchestratorError>;

#[derive(Debug, Error)]
pub enum OrchestratorError {
    // Classification errors
    #[error("Classification failed: {0}")]
    ClassificationFailed(String),

    #[error("Low confidence classification: {confidence}")]
    LowConfidence { confidence: f64 },

    #[error("Invalid intent: {0}")]
    InvalidIntent(String),

    // Registry errors
    #[error("Processor not found: {0}")]
    ProcessorNotFound(String),

    #[error("No matching processor for intent: {0}")]
    NoMatchingProcessor(String),

    #[error("Processor validation failed: {processor_id} - missing {missing:?}")]
    ProcessorValidationFailed {
        processor_id: String,
        missing: Vec<String>,
    },

    #[error("Processor registry load failed: {0}")]
    RegistryLoadFailed(String),

    // Routing errors
    #[error("Routing plan generation failed: {0}")]
    RoutingPlanFailed(String),

    #[error("Circular dependency detected in routing plan")]
    CircularDependency,

    #[error("Resource allocation failed: {0}")]
    ResourceAllocationFailed(String),

    // Execution errors
    #[error("Processor execution failed: {processor_id} - {reason}")]
    ProcessorExecutionFailed {
        processor_id: String,
        reason: String,
    },

    #[error("Processor timeout: {processor_id}")]
    ProcessorTimeout { processor_id: String },

    #[error("Output schema validation failed: {0}")]
    OutputValidationFailed(String),

    // IO errors
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("YAML parsing error: {0}")]
    YamlParse(#[from] serde_yaml::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    // Schema validation errors
    #[error("Schema validation error: {0}")]
    SchemaValidation(String),

    // LLM errors
    #[error("LLM call failed: {0}")]
    LlmCallFailed(String),

    // Generic errors
    #[error("Internal error: {0}")]
    Internal(String),

    #[error(transparent)]
    Other(#[from] anyhow::Error),
}

/// Error codes matching WIRE_CONTRACTS.yaml
#[derive(Debug, Clone, Copy)]
pub enum ErrorCode {
    /// ORH-001: Invalid request format or missing required fields
    InvalidRequest,

    /// ORH-002: Classification confidence below threshold
    LowConfidence,

    /// ORH-003: No processor matches classified intent
    NoProcessorMatch,

    /// ORH-004: Processor output does not match schema
    OutputSchemaViolation,

    /// ORH-005: Processor execution timeout
    ProcessorTimeout,

    /// ORH-006: Circular dependency in routing plan
    CircularDependency,
}

impl ErrorCode {
    pub fn as_str(&self) -> &'static str {
        match self {
            ErrorCode::InvalidRequest => "ORH-001",
            ErrorCode::LowConfidence => "ORH-002",
            ErrorCode::NoProcessorMatch => "ORH-003",
            ErrorCode::OutputSchemaViolation => "ORH-004",
            ErrorCode::ProcessorTimeout => "ORH-005",
            ErrorCode::CircularDependency => "ORH-006",
        }
    }
}
