use pos_core::*;

#[test]
fn test_storage_and_fts5_lexical_search() {
    let db = Database::open_in_memory().expect("Failed to open DB");

    // Test Project Insertion
    db.insert_project("proj_1", "Personal OS", Some("/workspaces/pos"), Some("git@github.com:personal-os"))
        .expect("Failed to insert project");
    let projects = db.list_projects().expect("Failed to list projects");
    assert_eq!(projects.len(), 1);
    assert_eq!(projects[0].1, "Personal OS");

    // Test Thought & FTS5 search
    db.insert_thought(
        "th_1",
        "Agentic Architecture",
        "We are designing an offline-first agentic operating system in Rust.",
        "concept",
        &["rust".to_string(), "ai".to_string()],
    ).expect("Failed to insert thought");

    let fts_results = db.search_thoughts_fts("offline-first").expect("FTS search failed");
    assert_eq!(fts_results.len(), 1);
    assert_eq!(fts_results[0].1, "Agentic Architecture");
}

#[test]
fn test_zero_knowledge_vault_hygiene() {
    let vault = VaultManager::new();
    let secret = SecretBuffer::from_str("sk-proj-super-secret-key-12345");
    assert_eq!(secret.len(), 30);

    // Verify Debug representation is redacted
    let debug_str = format!("{:?}", secret);
    assert!(debug_str.contains("[REDACTED_MEMORY"));
    assert!(!debug_str.contains("super-secret-key"));

    // Store in vault
    vault.store_secret("openai_api_key", secret);

    // Issue ephemeral lease
    let lease = vault.issue_lease("openai_api_key", "subagent_triage", 60)
        .expect("Failed to issue lease");
    assert!(lease.is_valid());

    // Access secret via lease
    let retrieved = vault.access_secret(&lease.lease_id)
        .expect("Failed to access secret");
    assert_eq!(retrieved.expose_secret(), b"sk-proj-super-secret-key-12345");

    // Revoke lease
    assert!(vault.revoke_lease(&lease.lease_id));
    assert!(vault.access_secret(&lease.lease_id).is_none());
}

#[test]
fn test_privacy_redaction_sentinel() {
    let raw_text = "Here is my secret sk-1234567890123456789012 and email test@example.com for card 4111-2222-3333-4444.";
    let redacted = RedactionSentinel::redact(raw_text);

    assert!(!redacted.contains("sk-1234567890123456789012"));
    assert!(!redacted.contains("test@example.com"));
    assert!(!redacted.contains("4111-2222-3333-4444"));
    assert!(redacted.contains("[REDACTED_SECRET]"));
}

#[test]
fn test_hitl_financial_gate() {
    assert!(HitlFinancialGate::requires_human_authorization(49.99));
    assert!(!HitlFinancialGate::requires_human_authorization(0.00));

    assert_eq!(
        HitlFinancialGate::evaluate_transaction_state(100.0),
        TransactionStatus::PendingHitl
    );
    assert_eq!(
        HitlFinancialGate::evaluate_transaction_state(0.0),
        TransactionStatus::Approved
    );
}

#[test]
fn test_wikilinks_extraction() {
    let thought = Thought {
        id: "th_2".to_string(),
        title: "Daily Note".to_string(),
        content_raw: "Today I reviewed [[Personal OS]] and coordinated with [[Email Triage]].".to_string(),
        thought_type: ThoughtType::Journal,
        tags: vec!["log".to_string()],
        actionability_score: 0.8,
        ambiguity_score: 0.1,
    };

    let links = thought.extract_wikilinks();
    assert_eq!(links.len(), 2);
    assert!(links.contains(&"Personal OS".to_string()));
    assert!(links.contains(&"Email Triage".to_string()));
}

#[test]
fn test_habit_streak_calculation() {
    assert_eq!(StreakCalculator::calculate_next_streak(5, true), 6);
    assert_eq!(StreakCalculator::calculate_next_streak(5, false), 1);
}

#[test]
fn test_merkle_block_chaining() {
    let block0 = MerkleBlockHeader::new(0, "00000000000000000000000000000000", "GENESIS");
    let block1 = MerkleBlockHeader::new(1, &block0.block_hash, "RECORD_THOUGHT");

    assert_eq!(block1.prev_block_hash, block0.block_hash);
    assert_ne!(block0.block_hash, block1.block_hash);
}
