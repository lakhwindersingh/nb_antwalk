pub mod service;
pub mod mcp;

pub use service::PersonalOsService;
pub use mcp::{McpServer, McpToolDefinition};

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error + Send + Sync>>;
