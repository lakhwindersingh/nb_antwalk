use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use serde_json::{json, Value};
use crate::mcp::McpServer;
use crate::service::PersonalOsService;

pub async fn bind_listener(preferred_port: u16) -> (TcpListener, u16) {
    let port = std::env::var("POS_PORT")
        .ok()
        .and_then(|p| p.parse::<u16>().ok())
        .unwrap_or(preferred_port);

    for p in port..port + 50 {
        if let Ok(listener) = TcpListener::bind(("127.0.0.1", p)).await {
            return (listener, p);
        }
    }

    let listener = TcpListener::bind(("127.0.0.1", 0))
        .await
        .expect("Failed to bind any TCP listener");
    let bound_port = listener.local_addr().expect("local addr").port();
    (listener, bound_port)
}

pub async fn start_http_server(
    listener: TcpListener,
    mcp: Arc<McpServer>,
    service: Arc<PersonalOsService>,
) {
    while let Ok((stream, _)) = listener.accept().await {
        let mcp = Arc::clone(&mcp);
        let service = Arc::clone(&service);
        tokio::spawn(async move {
            if let Err(e) = handle_connection(stream, mcp, service).await {
                eprintln!("HTTP connection error: {}", e);
            }
        });
    }
}

async fn handle_connection(
    mut stream: TcpStream,
    mcp: Arc<McpServer>,
    service: Arc<PersonalOsService>,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let mut buffer = vec![0u8; 16384];
    let bytes_read = stream.read(&mut buffer).await?;
    if bytes_read == 0 {
        return Ok(());
    }

    let request_str = String::from_utf8_lossy(&buffer[..bytes_read]);
    let mut lines = request_str.lines();
    let request_line = match lines.next() {
        Some(l) => l,
        None => return Ok(()),
    };

    let parts: Vec<&str> = request_line.split_whitespace().collect();
    if parts.len() < 2 {
        return Ok(());
    }

    let method = parts[0];
    let uri = parts[1];

    // CORS preflight
    if method == "OPTIONS" {
        let response = "HTTP/1.1 200 OK\r\n\
Access-Control-Allow-Origin: *\r\n\
Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n\
Access-Control-Allow-Headers: *\r\n\
Content-Length: 0\r\n\
Connection: close\r\n\r\n";
        stream.write_all(response.as_bytes()).await?;
        return Ok(());
    }

    // Extract body if present
    let body_str = if let Some(pos) = request_str.find("\r\n\r\n") {
        &request_str[pos + 4..]
    } else {
        ""
    };

    let (status, content_type, response_body) = match (method, uri) {
        ("GET", "/") | ("GET", "/index.html") => {
            let tools = mcp.list_tools();
            let mut tools_html = String::new();
            for t in &tools {
                tools_html.push_str(&format!(
                    r#"<li class="tool-item">
                        <div class="tool-title"><code>{}</code></div>
                        <div class="tool-desc">{}</div>
                    </li>"#,
                    t.name, t.description
                ));
            }

            let html = format!(
                r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal OS • Service Gateway & MCP API</title>
    <style>
        :root {{
            --bg: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --text-heading: #f0f6fc;
            --accent: #58a6ff;
            --accent-green: #3fb950;
            --accent-purple: #bc8cff;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 30px;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: var(--text-heading);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .badge {{
            background: #238636;
            color: #ffffff;
            font-size: 0.8rem;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
        }}
        .subtitle {{
            color: #8b949e;
            font-size: 1rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        @media (max-width: 768px) {{
            .grid {{ grid-template-columns: 1fr; }}
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }}
        .card h2 {{
            color: var(--text-heading);
            margin-top: 0;
            font-size: 1.2rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }}
        .endpoint-link {{
            display: block;
            background: #21262d;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 10px;
            text-decoration: none;
            color: var(--accent);
            font-family: monospace;
            font-size: 0.95rem;
            transition: all 0.2s ease;
        }}
        .endpoint-link:hover {{
            background: #30363d;
            border-color: var(--accent);
        }}
        .endpoint-link .method {{
            font-weight: bold;
            color: var(--accent-green);
            margin-right: 8px;
        }}
        .tools-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .tool-item {{
            background: #21262d;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 10px;
            border-left: 4px solid var(--accent-purple);
        }}
        .tool-title code {{
            color: var(--accent);
            font-weight: bold;
            font-size: 1rem;
        }}
        .tool-desc {{
            font-size: 0.88rem;
            color: #8b949e;
            margin-top: 4px;
        }}
        .action-button {{
            background: #238636;
            color: white;
            padding: 8px 14px;
            border-radius: 6px;
            text-decoration: none;
            display: inline-block;
            font-weight: 600;
            font-size: 0.9rem;
            margin-top: 10px;
        }}
        .action-button:hover {{
            background: #2ea043;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌐 Personal OS Service Gateway <span class="badge">ONLINE</span></h1>
            <div class="subtitle">Daemon, Model Context Protocol (MCP) Server & Observability Hub</div>
        </header>

        <div class="grid">
            <div class="card">
                <h2>🔗 Exported Interactive Endpoints</h2>
                <a class="endpoint-link" href="/health" target="_blank">
                    <span class="method">GET</span>/health — System Invariants & Health
                </a>
                <a class="endpoint-link" href="/tools" target="_blank">
                    <span class="method">GET</span>/tools — 12 MCP Tools Manifest
                </a>
                <a class="endpoint-link" href="http://127.0.0.1:8088" target="_blank">
                    <span class="method">PORTAL</span>http://127.0.0.1:8088 — Percipience Observability Hub
                </a>
                <div style="margin-top: 15px; font-size: 0.85rem; color: #8b949e;">
                    <strong>Direct Tool Invocations:</strong><br>
                    <code>POST /tools/:tool_name</code> with JSON body<br><br>
                    <strong>MCP Protocol Endpoint:</strong><br>
                    <code>POST /mcp</code> with JSON-RPC 2.0 payload
                </div>
            </div>

            <div class="card">
                <h2>🛡️ Active Security Invariants</h2>
                <ul style="padding-left: 20px; line-height: 1.8; margin-bottom: 0;">
                    <li><strong>Invariant 1:</strong> Zero-Knowledge Ephemeral Leases (Zeroize)</li>
                    <li><strong>Invariant 2:</strong> HITL Financial & Secret Gate Approval</li>
                    <li><strong>Invariant 3:</strong> Offline-First SQLite WAL & FTS5</li>
                    <li><strong>Invariant 4:</strong> Cryptographic Merkle State Continuity</li>
                    <li><strong>Invariant 5:</strong> Memory Safety (100% Safe Rust)</li>
                    <li><strong>Invariant 10:</strong> Dual-Pass Egress Privacy Sentinel</li>
                </ul>
            </div>
        </div>

        <div class="card">
            <h2>🛠️ Registered MCP Tools (12 Action-Based Tools)</h2>
            <ul class="tools-list">
                {}
            </ul>
        </div>
    </div>
</body>
</html>"#,
                tools_html
            );
            (200, "text/html; charset=utf-8", html)
        }
        ("GET", "/health") | ("GET", "/api/status") => {
            let status = service.get_system_status();
            (200, "application/json", serde_json::to_string_pretty(&status).unwrap_or_default())
        }
        ("GET", "/tools") => {
            let tools = mcp.list_tools();
            (200, "application/json", serde_json::to_string_pretty(&tools).unwrap_or_default())
        }
        ("POST", "/mcp") | ("POST", "/api/mcp") => {
            if let Ok(req) = serde_json::from_str::<Value>(body_str) {
                let id = req.get("id").cloned().unwrap_or(Value::Null);
                let method = req.get("method").and_then(|m| m.as_str()).unwrap_or("");
                let params = req.get("params").cloned().unwrap_or(json!({}));

                let response = match method {
                    "initialize" => json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": { "listChanged": false }
                            },
                            "serverInfo": {
                                "name": "personal_os_server",
                                "version": "1.2.0"
                            }
                        }
                    }),
                    "tools/list" => {
                        let tools = mcp.list_tools();
                        json!({
                            "jsonrpc": "2.0",
                            "id": id,
                            "result": { "tools": tools }
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
                    "ping" => json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "result": "pong"
                    }),
                    _ => json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "error": {
                            "code": -32601,
                            "message": format!("Method not found: {}", method)
                        }
                    }),
                };
                (200, "application/json", serde_json::to_string_pretty(&response).unwrap_or_default())
            } else {
                (400, "application/json", json!({"error": "Invalid JSON-RPC payload"}).to_string())
            }
        }
        ("POST", path) if path.starts_with("/tools/") => {
            let tool_name = path.trim_start_matches("/tools/");
            let arguments = if body_str.trim().is_empty() {
                json!({})
            } else {
                serde_json::from_str::<Value>(body_str).unwrap_or(json!({}))
            };

            let tool_result = mcp.call_tool(tool_name, &arguments).await;
            (200, "application/json", serde_json::to_string_pretty(&tool_result).unwrap_or_default())
        }
        _ => (404, "application/json", json!({"error": "Not Found", "uri": uri}).to_string()),
    };

    let response = format!(
        "HTTP/1.1 {}\r\nContent-Type: {}\r\nContent-Length: {}\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n{}",
        match status {
            200 => "200 OK",
            400 => "400 Bad Request",
            404 => "404 Not Found",
            _ => "500 Internal Server Error",
        },
        content_type,
        response_body.len(),
        response_body
    );

    stream.write_all(response.as_bytes()).await?;
    stream.flush().await?;
    Ok(())
}
