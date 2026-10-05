pub mod service;
pub mod mcp;
pub mod http;

pub use service::PersonalOsService;
pub use mcp::{McpServer, McpToolDefinition};
pub use http::{bind_listener, start_http_server};

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error + Send + Sync>>;
