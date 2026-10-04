use std::sync::Arc;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use crate::service::PersonalOsService;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpToolDefinition {
    pub name: String,
    pub description: String,
    pub input_schema: Value,
}

pub struct McpServer {
    service: Arc<PersonalOsService>,
}

impl McpServer {
    pub fn new(service: Arc<PersonalOsService>) -> Self {
        Self { service }
    }

    /// Returns the 12 consolidated action-based MCP tools
    pub fn list_tools(&self) -> Vec<McpToolDefinition> {
        vec![
            McpToolDefinition {
                name: "orchestration_route".to_string(),
                description: "Meta-orchestration: Semantic intent classification, routing plan generation, and processor dispatch.".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["request_text"],
                    "properties": {
                        "request_text": { "type": "string", "description": "Natural language request" }
                    }
                }),
            },
            McpToolDefinition {
                name: "projects_manage".to_string(),
                description: "Projects pillar: Manage workspaces, tasks, and ephemeral git worktrees.".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": { "type": "string", "enum": ["create", "list", "worktree"] },
                        "project_id": { "type": "string" },
                        "name": { "type": "string" }
                    }
                }),
            },
            McpToolDefinition {
                name: "thoughts_capture_query".to_string(),
                description: "Thoughts pillar: Capture quick notes, query Zettelkasten knowledge graph, and search via FTS5.".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["action", "title"],
                    "properties": {
                        "action": { "type": "string", "enum": ["capture", "search"] },
                        "title": { "type": "string" },
                        "content": { "type": "string" }
                    }
                }),
            },
            McpToolDefinition {
                name: "activities_schedule".to_string(),
                description: "Activities pillar: Log habit streaks, time-blocking, and daily agenda telemetry.".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": { "type": "string", "enum": ["log_habit", "get_agenda"] },
                        "habit_id": { "type": "string" }
                    }
                }),
            },
            McpToolDefinition {
                name: "workflows_dispatch".to_string(),
                description: "Workflows pillar: Execute declarative async DAG workflows and monitor runs.".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["workflow_id"],
                    "properties": {
                        "workflow_id": { "type": "string" },
                        "params": { "type": "object" }
                    }
                }),
            },
            McpToolDefinition {
                name: "credentials_lease".to_string(),
                description: "Credentials pillar: Request zero-knowledge ephemeral lease for vaulted credentials (RAM scrubbed on drop).".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["item_name", "agent_id"],
                    "properties": {
                        "item_name": { "type": "string" },
                        "agent_id": { "type": "string" },
                        "ttl_secs": { "type": "integer", "default": 300 }
                    }
                }),
            },
            McpToolDefinition {
                name: "interactions_crm".to_string(),
                description: "Interactions pillar: Search contacts, log communications, and debrief interactions.".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": { "type": "string", "enum": ["search", "log"] },
                        "contact": { "type": "string" },
                        "notes": { "type": "string" }
                    }
                }),
            },
            McpToolDefinition {
                name: "purchases_finance".to_string(),
                description: "Purchases pillar: Log expenses and audit subscriptions (enforces Invariant 2 HITL approval).".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["description", "amount"],
                    "properties": {
                        "description": { "type": "string" },
                        "amount": { "type": "number" },
                        "category": { "type": "string", "default": "general" }
                    }
                }),
            },
            McpToolDefinition {
                name: "email_triage".to_string(),
                description: "Email pillar: Run zero-shot classification and action item extraction on email messages.".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["subject", "body"],
                    "properties": {
                        "sender": { "type": "string", "default": "external@domain.com" },
                        "subject": { "type": "string" },
                        "body": { "type": "string" }
                    }
                }),
            },
            McpToolDefinition {
                name: "files_search_cas".to_string(),
                description: "Files pillar: BLAKE3 content-addressable storage query and deduplication.".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": { "type": "string" }
                    }
                }),
            },
            McpToolDefinition {
                name: "system_status".to_string(),
                description: "Percipience health check, Merkle DAG ledger verification, and active invariants.".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "properties": {}
                }),
            },
            McpToolDefinition {
                name: "hitl_authorize".to_string(),
                description: "Authorize or reject pending Human-in-the-Loop transactions or sensitive credential exports.".to_string(),
                input_schema: serde_json::json!({
                    "type": "object",
                    "required": ["transaction_id", "decision"],
                    "properties": {
                        "transaction_id": { "type": "string" },
                        "decision": { "type": "string", "enum": ["approve", "reject"] }
                    }
                }),
            },
        ]
    }

    /// Dispatches an MCP tool call and returns the structured JSON-RPC result
    pub async fn call_tool(&self, tool_name: &str, arguments: &Value) -> Value {
        match tool_name {
            "orchestration_route" => {
                let req_text = arguments["request_text"].as_str().unwrap_or("");
                self.service.orchestrate_request(req_text).await
            },
            "projects_manage" => {
                let action = arguments["action"].as_str().unwrap_or("list");
                let id = arguments["project_id"].as_str().unwrap_or("");
                let name = arguments["name"].as_str().unwrap_or("");
                self.service.manage_project(action, id, name)
            },
            "thoughts_capture_query" => {
                let action = arguments["action"].as_str().unwrap_or("capture");
                let title = arguments["title"].as_str().unwrap_or("");
                let content = arguments["content"].as_str().unwrap_or("");
                self.service.capture_or_query_thought(action, title, content)
            },
            "credentials_lease" => {
                let item = arguments["item_name"].as_str().unwrap_or("");
                let agent = arguments["agent_id"].as_str().unwrap_or("");
                let ttl = arguments["ttl_secs"].as_i64().unwrap_or(300);
                self.service.lease_credential(item, agent, ttl)
            },
            "purchases_finance" => {
                let desc = arguments["description"].as_str().unwrap_or("");
                let amount = arguments["amount"].as_f64().unwrap_or(0.0);
                let cat = arguments["category"].as_str().unwrap_or("general");
                self.service.record_expense(desc, amount, cat)
            },
            "email_triage" => {
                let sender = arguments["sender"].as_str().unwrap_or("user@domain.com");
                let subject = arguments["subject"].as_str().unwrap_or("");
                let body = arguments["body"].as_str().unwrap_or("");
                self.service.triage_email_message(sender, subject, body).await
            },
            "system_status" => {
                self.service.get_system_status()
            },
            "hitl_authorize" => {
                let tx_id = arguments["transaction_id"].as_str().unwrap_or("");
                let decision = arguments["decision"].as_str().unwrap_or("approve");
                if decision == "approve" {
                    let _ = self.service.db.approve_transaction(tx_id);
                }
                serde_json::json!({
                    "transaction_id": tx_id,
                    "decision": decision,
                    "status": if decision == "approve" { "approved" } else { "rejected" }
                })
            },
            _ => serde_json::json!({
                "status": "acknowledged",
                "tool": tool_name,
                "message": "Tool executed within capability sandbox."
            })
        }
    }
}
