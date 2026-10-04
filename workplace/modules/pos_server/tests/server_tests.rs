use std::sync::Arc;
use pos_server::{PersonalOsService, McpServer};
use serde_json::json;

#[tokio::test]
async fn test_mcp_tools_list_12_tools() {
    let service = Arc::new(PersonalOsService::new_in_memory().expect("Failed to initialize service"));
    let server = McpServer::new(service);

    let tools = server.list_tools();
    assert_eq!(tools.len(), 12, "Should provide exactly 12 consolidated action-based MCP tools");

    let tool_names: Vec<String> = tools.into_iter().map(|t| t.name).collect();
    assert!(tool_names.contains(&"orchestration_route".to_string()));
    assert!(tool_names.contains(&"projects_manage".to_string()));
    assert!(tool_names.contains(&"thoughts_capture_query".to_string()));
    assert!(tool_names.contains(&"activities_schedule".to_string()));
    assert!(tool_names.contains(&"workflows_dispatch".to_string()));
    assert!(tool_names.contains(&"credentials_lease".to_string()));
    assert!(tool_names.contains(&"interactions_crm".to_string()));
    assert!(tool_names.contains(&"purchases_finance".to_string()));
    assert!(tool_names.contains(&"email_triage".to_string()));
    assert!(tool_names.contains(&"files_search_cas".to_string()));
    assert!(tool_names.contains(&"system_status".to_string()));
    assert!(tool_names.contains(&"hitl_authorize".to_string()));
}

#[tokio::test]
async fn test_mcp_orchestration_route_execution() {
    let service = Arc::new(PersonalOsService::new_in_memory().expect("Failed to initialize service"));
    let server = McpServer::new(service);

    let call_res = server.call_tool(
        "orchestration_route",
        &json!({ "request_text": "I had a thought about building an offline AI engine" }),
    ).await;

    assert!(call_res["status"] == "success" || call_res["status"] == "fallback");
    assert!(call_res["confidence"].as_f64().unwrap() > 0.0);
}

#[tokio::test]
async fn test_mcp_thoughts_capture_and_query() {
    let service = Arc::new(PersonalOsService::new_in_memory().expect("Failed to initialize service"));
    let server = McpServer::new(service);

    let capture_res = server.call_tool(
        "thoughts_capture_query",
        &json!({
            "action": "capture",
            "title": "Rust Architecture",
            "content": "Exploring [[Personal OS]] with [[Rust]]."
        }),
    ).await;
    assert_eq!(capture_res["action"], "capture");
    assert_eq!(capture_res["success"], true);

    let search_res = server.call_tool(
        "thoughts_capture_query",
        &json!({
            "action": "search",
            "title": "Architecture"
        }),
    ).await;
    assert_eq!(search_res["action"], "search");
    assert_eq!(search_res["count"], 1);
}

#[tokio::test]
async fn test_mcp_purchases_finance_hitl_enforcement() {
    let service = Arc::new(PersonalOsService::new_in_memory().expect("Failed to initialize service"));
    let server = McpServer::new(service);

    // Call expense with $89.00 -> Must require HITL
    let res = server.call_tool(
        "purchases_finance",
        &json!({
            "description": "AWS Cloud Services",
            "amount": 89.00,
            "category": "infrastructure"
        }),
    ).await;

    assert_eq!(res["status"], "pending_hitl");
    assert_eq!(res["requires_hitl_authorization"], true);

    // Authorize via HITL
    let tx_id = res["transaction_id"].as_str().unwrap();
    let auth_res = server.call_tool(
        "hitl_authorize",
        &json!({
            "transaction_id": tx_id,
            "decision": "approve"
        }),
    ).await;
    assert_eq!(auth_res["status"], "approved");
}

#[tokio::test]
async fn test_mcp_email_triage_tool() {
    let service = Arc::new(PersonalOsService::new_in_memory().expect("Failed to initialize service"));
    let server = McpServer::new(service);

    let res = server.call_tool(
        "email_triage",
        &json!({
            "sender": "boss@company.com",
            "subject": "Urgent: Project Security Review",
            "body": "Please review the security invariants by tomorrow 5pm."
        }),
    ).await;

    assert!(res["primary_category"].is_string());
    assert!(res["confidence"].as_f64().is_some());
}
