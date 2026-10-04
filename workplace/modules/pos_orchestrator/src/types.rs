//! Core types for the orchestrator system

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Intent categories for request classification
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Intent {
    ProjectGeneration,
    DataAnalysis,
    Reconciliation,
    Computation,
    InformationExtraction,
    Synthesis,
    Monitoring,
    Optimization,
}

impl Intent {
    pub fn as_str(&self) -> &'static str {
        match self {
            Intent::ProjectGeneration => "project_generation",
            Intent::DataAnalysis => "data_analysis",
            Intent::Reconciliation => "reconciliation",
            Intent::Computation => "computation",
            Intent::InformationExtraction => "information_extraction",
            Intent::Synthesis => "synthesis",
            Intent::Monitoring => "monitoring",
            Intent::Optimization => "optimization",
        }
    }
}

/// Complexity level of a request
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ComplexityLevel {
    Simple,
    Moderate,
    Complex,
    Exploratory,
}

/// Compute tier for resource allocation
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ComputeTier {
    TierA,
    TierB,
    TierC,
}

/// LLM call frequency estimate
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LlmCallFrequency {
    None,
    LowFrequency,
    HighFrequency,
}

/// Extracted entity from request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entity {
    pub entity_type: String,
    pub value: String,
    pub relevance: f64,
}

/// Resource requirements estimation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceEstimates {
    pub ephemeral_worktrees: bool,
    pub git_operations: bool,
    pub llm_calls: LlmCallFrequency,
    pub compute_tier: ComputeTier,
    pub estimated_duration_seconds: u64,
}

/// Warning about classification or execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Warning {
    pub warning_type: String,
    pub message: String,
    pub severity: WarningSeverity,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum WarningSeverity {
    Low,
    Medium,
    High,
}

/// Resource allocation for execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceAllocation {
    pub ephemeral_worktrees: Vec<String>,
    pub compute_allocations: Vec<ComputeAllocation>,
    pub estimated_total_duration_seconds: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComputeAllocation {
    pub allocation_id: String,
    pub compute_tier: ComputeTier,
    pub max_memory_mb: u64,
    pub max_disk_mb: u64,
}

/// Processor execution step
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessorStep {
    pub processor_id: String,
    pub execution_order: u32,
    pub dependencies: Vec<String>,
    pub input_mapping: serde_json::Value,
    pub resource_allocation: ResourceAllocation,
    pub fallback_processor_id: Option<String>,
}

/// Execution status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionStatus {
    Pending,
    Running,
    Completed,
    Failed,
    TimedOut,
    Cancelled,
}

/// Result from a processor execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessorResult {
    pub processor_id: String,
    pub status: ExecutionStatus,
    pub output: serde_json::Value,
    pub artifacts: Vec<Artifact>,
    pub duration_seconds: f64,
    pub error: Option<String>,
    pub telemetry: HashMap<String, serde_json::Value>,
}

/// Output artifact
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Artifact {
    pub artifact_type: String,
    pub path: String,
    pub description: String,
}

/// Aggregated output from multiple processors
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregatedOutput {
    pub summary: String,
    pub artifacts: Vec<Artifact>,
    pub actionable_items: Vec<ActionItem>,
    pub cross_processor_insights: Vec<Insight>,
}

/// Actionable item for user follow-up
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionItem {
    pub item_type: String,
    pub description: String,
    pub priority: ActionPriority,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ActionPriority {
    Low,
    Medium,
    High,
}

/// Cross-processor insight
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Insight {
    pub insight_type: String,
    pub content: String,
    pub confidence: f64,
    pub supporting_processors: Vec<String>,
}

/// Request context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RequestContext {
    pub user_id: Option<String>,
    pub session_id: Option<String>,
    pub urgency: Option<String>,
    pub available_context: Vec<String>,
    pub data_sensitivity: Option<String>,
}

/// Execution summary
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionSummary {
    pub execution_id: Uuid,
    pub total_duration_seconds: f64,
    pub processors_executed: usize,
    pub success_rate: f64,
    pub cost_estimate: Option<CostEstimate>,
    pub resource_usage: ResourceUsage,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostEstimate {
    pub total_usd: f64,
    pub llm_calls_cost: f64,
    pub compute_cost: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceUsage {
    pub peak_memory_mb: u64,
    pub total_disk_mb: u64,
    pub llm_calls: u32,
}
