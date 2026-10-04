use chrono::{Duration, Utc};
use pos_email::{
    CredentialRef, EmailAccount, EmailCategory, EmailProvider, EmailStore,
    EmailSyncEngine, MockEmailClient, RawMessage,
};

#[tokio::test]
async fn test_account_creation_and_sync() {
    let store = EmailStore::open_in_memory().expect("in-memory db open failed");

    let account = EmailAccount::new(
        "testuser@antwalk.local".to_string(),
        EmailProvider::Imap {
            host: "imap.antwalk.local".to_string(),
            port: 993,
            tls: true,
        },
        CredentialRef {
            vault_item_id: "vault_cred_001".to_string(),
            secret_key_alias: "default".to_string(),
        },
    );

    store.insert_account(&account).expect("insert account failed");
    let loaded = store.get_account(account.id).expect("get account failed").expect("account missing");
    assert_eq!(loaded.email, "testuser@antwalk.local");

    // Setup mock client with 2 messages
    let mock_client = MockEmailClient::new();
    let now = Utc::now();

    mock_client
        .add_message(RawMessage {
            message_id: "<msg-1@antwalk.local>".to_string(),
            thread_id: Some("thread-1".to_string()),
            date: now - Duration::minutes(10),
            from_raw: "Sarah Chen <sarah@company.com>".to_string(),
            to_raw: vec!["testuser@antwalk.local".to_string()],
            cc_raw: vec![],
            subject: "Q4 Planning sync?".to_string(),
            body_text: "Can we sync tomorrow at 2pm regarding Q4 roadmaps?".to_string(),
            has_attachments: false,
        })
        .await;

    mock_client
        .add_message(RawMessage {
            message_id: "<msg-2@antwalk.local>".to_string(),
            thread_id: Some("thread-2".to_string()),
            date: now - Duration::minutes(5),
            from_raw: "Stripe Billing <invoices@stripe.com>".to_string(),
            to_raw: vec!["testuser@antwalk.local".to_string()],
            cc_raw: vec![],
            subject: "Invoice #10294 Paid".to_string(),
            body_text: "Your receipt for $49.00 USD is ready. Thank you for your payment.".to_string(),
            has_attachments: true,
        })
        .await;

    let mut engine = EmailSyncEngine::new(mock_client, store.clone());
    let mut sync_acc = loaded;
    sync_acc.sync_state.last_sync = now - Duration::hours(1);

    let res = engine
        .sync_account(&sync_acc, "mock_secret")
        .await
        .expect("sync failed");

    assert_eq!(res.fetched_count, 2);
    assert_eq!(res.stored_count, 2);

    // Verify emails in store
    let email1 = store
        .get_email_by_message_id("<msg-1@antwalk.local>")
        .expect("query failed")
        .expect("email1 not found");
    assert_eq!(email1.subject, "Q4 Planning sync?");
    assert_eq!(email1.from.name.as_deref(), Some("Sarah Chen"));
    assert_eq!(email1.from.email, "sarah@company.com");

    let email2 = store
        .get_email_by_message_id("<msg-2@antwalk.local>")
        .expect("query failed")
        .expect("email2 not found");
    assert!(email2.has_attachments);

    // Update classification
    store
        .update_classification(
            email1.id,
            EmailCategory::ActionRequired,
            0.95,
            "Direct meeting inquiry with question mark",
        )
        .expect("update classification failed");

    let action_emails = store
        .get_emails_by_category(EmailCategory::ActionRequired, 10)
        .expect("query by category failed");
    assert_eq!(action_emails.len(), 1);
    assert_eq!(action_emails[0].message_id, "<msg-1@antwalk.local>");
}
