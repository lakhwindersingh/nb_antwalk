use std::process::Command;

#[test]
fn test_cli_help() {
    let output = Command::new("cargo")
        .args(&["run", "--bin", "pos", "--", "--help"])
        .current_dir(env!("CARGO_MANIFEST_DIR"))
        .output()
        .expect("Failed to execute CLI");

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("Personal OS: Offline-First Agentic Life Operating System"));
    assert!(stdout.contains("status"));
    assert!(stdout.contains("route"));
    assert!(stdout.contains("thought"));
    assert!(stdout.contains("project"));
    assert!(stdout.contains("vault"));
    assert!(stdout.contains("finance"));
    assert!(stdout.contains("email"));
    assert!(stdout.contains("doctor"));
}

#[test]
fn test_cli_doctor() {
    let output = Command::new("cargo")
        .args(&["run", "--bin", "pos", "--", "doctor"])
        .current_dir(env!("CARGO_MANIFEST_DIR"))
        .output()
        .expect("Failed to execute CLI doctor");

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("Running Personal OS System Health & Invariant Doctor"));
    assert!(stdout.contains("Invariant 1: Zero-Knowledge Memory"));
    assert!(stdout.contains("All 6 Platform Security Invariants are HEALTHY"));
}
