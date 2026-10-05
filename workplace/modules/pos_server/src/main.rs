use std::path::PathBuf;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use serde_json::{json, Value};
use pos_server::{PersonalOsService, McpServer, bind_listener, start_http_server};

fn get_db_path() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let dir = PathBuf::from(home).join(".pos");
    let _ = std::fs::create_dir_all(&dir);
    dir.join("personal_os.db")
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let db_path = get_db_path();
    let service = Arc::new(PersonalOsService::open(&db_path).unwrap_or_else(|_| {
        eprintln!("⚠️ Notice: Opening in-memory fallback database");
        PersonalOsService::new_in_memory().expect("Failed in-memory fallback")
    }));

    let mcp = Arc::new(McpServer::new(Arc::clone(&service)));

    // Bind and start the background HTTP REST & Web Gateway server
    let (http_listener, http_port) = bind_listener(8080).await;
    let mcp_http = Arc::clone(&mcp);
    let service_http = Arc::clone(&service);
    tokio::spawn(async move {
        start_http_server(http_listener, mcp_http, service_http).await;
    });

    // Display exported ports and interactive service links
    eprintln!("🌐 Personal OS API Daemon & MCP Server v1.2.0");
    eprintln!("   Database: {}", db_path.display());
    eprintln!("   Status: Active & Listening for requests\n");
    eprintln!("   =================================================================");
    eprintln!("   EXPORTED NETWORK SERVICES & INTERACTIVE LINKS:");
    eprintln!("   =================================================================");
    eprintln!("   • Interactive Web Gateway:  http://127.0.0.1:{}", http_port);
    eprintln!("   • System Health & Invariants: http://127.0.0.1:{}/health", http_port);
    eprintln!("   • Tools Manifest (JSON):    http://127.0.0.1:{}/tools", http_port);
    eprintln!("   • Direct Tool Invocations:  POST http://127.0.0.1:{}/tools/:tool_name", http_port);
    eprintln!("   • MCP JSON-RPC over HTTP:   POST http://127.0.0.1:{}/mcp", http_port);
    eprintln!("   • Observability Hub Portal: http://127.0.0.1:8088 (./run_modules.sh portal)");
    eprintln!("   • Stdio MCP Protocol:       Active on stdin/stdout (JSON-RPC 2.0)");
    eprintln!("   =================================================================\n");
    eprintln!("   12 Consolidated Action-Based MCP Tools Registered:");
    for tool in mcp.list_tools() {
        eprintln!("     • {}: {}", tool.name, tool.description);
    }
    eprintln!("\n   Interactive Terminal Commands: type 'status', 'tools', 'ports', 'help', or 'exit'.");
    eprintln!();

    let stdin = tokio::io::stdin();
    let mut reader = BufReader::new(stdin).lines();
    let mut stdout = tokio::io::stdout();

    while let Ok(Some(line)) = reader.next_line().await {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        // Handle interactive terminal commands
        match trimmed {
            "exit" | "quit" | "q" => {
                eprintln!("👋 Shutting down Personal OS Server cleanly... Goodbye!");
                std::process::exit(0);
            }
            "ports" | "links" | "endpoints" => {
                eprintln!("Exported Links:");
                eprintln!("  • Web UI:     http://127.0.0.1:{}", http_port);
                eprintln!("  • Health:     http://127.0.0.1:{}/health", http_port);
                eprintln!("  • Tools:      http://127.0.0.1:{}/tools", http_port);
                eprintln!("  • Tool Call:  POST http://127.0.0.1:{}/tools/:name", http_port);
                eprintln!("  • MCP HTTP:   POST http://127.0.0.1:{}/mcp", http_port);
                eprintln!("  • Portal:     http://127.0.0.1:8088");
                continue;
            }
            "status" => {
                let status = service.get_system_status();
                eprintln!("{}", serde_json::to_string_pretty(&status).unwrap_or_default());
                continue;
            }
            "tools" => {
                for tool in mcp.list_tools() {
                    eprintln!("  • {}: {}", tool.name, tool.description);
                }
                continue;
            }
            "help" => {
                eprintln!("Commands:");
                eprintln!("  ports   - Show all exported service links and HTTP endpoints");
                eprintln!("  status  - Show system health, invariants, and Merkle DAG status");
                eprintln!("  tools   - List the 12 action-based MCP tools");
                eprintln!("  exit    - Cleanly shut down the server daemon");
                eprintln!("  (Or send standard JSON-RPC 2.0 lines on stdin)");
                continue;
            }
            _ => {}
        }

        // Parse JSON-RPC request
        if let Ok(req) = serde_json::from_str::<Value>(trimmed) {
            let id = req.get("id").cloned().unwrap_or(Value::Null);
            let method = req.get("method").and_then(|m| m.as_str()).unwrap_or("");
            let params = req.get("params").cloned().unwrap_or(json!({}));

            let response = match method {
                "initialize" => {
                    json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {
                                    "listChanged": false
                                }
                            },
                            "serverInfo": {
                                "name": "personal_os_server",
                                "version": "1.2.0"
                            }
                        }
                    })
                }
                "tools/list" => {
                    let tools = mcp.list_tools();
                    json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "result": {
                            "tools": tools
                        }
                    })
                }
                "tools/call" => {
                    let name = params.get("name").and_then(|n| n.as_str()).unwrap_or("");
                    let arguments = params.get("arguments").cloned().unwrap_or(json!({}));
                    let tool_result = mcp.call_tool(name, &arguments).await;
                    json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": serde_json::to_string_pretty(&tool_result).unwrap_or_default()
                                }
                            ],
                            "isError": false
                        }
                    })
                }
                "ping" => {
                    json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "result": "pong"
                    })
                }
                _ => {
                    json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "error": {
                            "code": -32601,
                            "message": format!("Method not found: {}", method)
                        }
                    })
                }
            };

            let out_str = serde_json::to_string(&response)? + "\n";
            stdout.write_all(out_str.as_bytes()).await?;
            stdout.flush().await?;
        }
    }

    Ok(())
}
