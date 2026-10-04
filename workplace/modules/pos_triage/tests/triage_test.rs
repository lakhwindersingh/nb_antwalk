use chrono::Utc;
use pos_email::{CredentialRef, Email, EmailAccount, EmailAddress, EmailCategory, EmailProvider, EmailStore};
use pos_triage::{
    EmailClassifier, EntityExtractor, FeatureExtractor, MockLlmClient, PillarDispatcher,
    SmartInboxFormatter,
};
use std::sync::Arc;
use uuid::Uuid;

fn make_test_email(account_id: Uuid, from_name: &str, from_email: &str, subject: &str, body: &str) -> Email {
    Email {
        id: Uuid::new_v4(),
        message_id: format!("<{}@test.antwalk>", Uuid::new_v4()),
        account_id,
        from: EmailAddress::new(Some(from_name.to_string()), from_email.to_string()),
        to: vec![EmailAddress::new(Some("User".to_string()), "user@example.com".to_string())],
        cc: vec![],
        subject: subject.to_string(),
        date: Utc::now(),
        body_snippet: body.to_string(),
        has_attachments: false,
        thread_id: None,
        in_reply_to: None,
        category: None,
        classification_confidence: None,
        classification_reasoning: None,
        is_read: false,
        is_archived: false,
    }
}

fn create_test_account(store: &EmailStore) -> EmailAccount {
    let account = EmailAccount::new(
        "user@example.com".to_string(),
        EmailProvider::Imap {
            host: "imap.example.com".to_string(),
            port: 993,
            tls: true,
        },
        CredentialRef {
            vault_item_id: "test_vault_item".to_string(),
            secret_key_alias: "default".to_string(),
        },
    );
    store.insert_account(&account).expect("insert test account failed");
    account
}

#[tokio::test]
async fn test_feature_extraction() {
    let extractor = FeatureExtractor::new();
    let account_id = Uuid::new_v4();

    let email = make_test_email(
        account_id,
        "John Doe",
        "john@doe.com",
        "URGENT: Project deadline review?",
        "Please review the attached contract. Total amount due is $1250.00. Unsubscribe here.",
    );

    let features = extractor.extract(&email, Some("user@example.com"));
    assert!(features.has_question_mark);
    assert!(features.has_deadline_words);
    assert!(features.has_unsubscribe_link);
    assert!(features.has_price_pattern);
    assert_eq!(features.extracted_price, Some(1250.00));
}

#[tokio::test]
async fn test_rule_based_classification() {
    let classifier = EmailClassifier::new(None);
    let account_id = Uuid::new_v4();

    // 1. Receipt
    let receipt_email = make_test_email(
        account_id,
        "Stripe",
        "receipts@stripe.com",
        "Your payment receipt #8812",
        "You paid $49.00 USD for Pro plan subscription.",
    );
    let c1 = classifier.classify(&receipt_email, None).await.unwrap();
    assert_eq!(c1.category, EmailCategory::Receipt);
    assert!(c1.confidence >= 0.90);

    // 2. Newsletter
    let newsletter_email = make_test_email(
        account_id,
        "Tech Digest",
        "newsletter@techdigest.io",
        "Weekly AI News #42",
        "Top stories this week... To opt out, click unsubscribe.",
    );
    let c2 = classifier.classify(&newsletter_email, None).await.unwrap();
    assert_eq!(c2.category, EmailCategory::Newsletter);

    // 3. Action Required
    let action_email = make_test_email(
        account_id,
        "Alice Boss",
        "alice@company.com",
        "Urgent: Need your signoff by tomorrow",
        "Could you check the pull request before our deployment?",
    );
    let c3 = classifier.classify(&action_email, None).await.unwrap();
    assert_eq!(c3.category, EmailCategory::ActionRequired);
}

#[tokio::test]
async fn test_llm_classification() {
    let mock_json = r#"{"category": "action_required", "confidence": 0.94, "reasoning": "Direct PR review request with tomorrow deadline"}"#;
    let mock_llm = Arc::new(MockLlmClient::new(mock_json));
    let classifier = EmailClassifier::new(Some(mock_llm));
    let account_id = Uuid::new_v4();

    let email = make_test_email(
        account_id,
        "Engineer Bob",
        "bob@github.com",
        "PR #402 ready for review",
        "Hey, can you review this PR when you get a chance?",
    );

    let res = classifier.classify(&email, None).await.unwrap();
    assert_eq!(res.category, EmailCategory::ActionRequired);
    assert_eq!(res.confidence, 0.94);
    assert_eq!(res.reasoning, "Direct PR review request with tomorrow deadline");
}

#[tokio::test]
async fn test_entity_extraction_and_pillar_dispatch() {
    let store = EmailStore::open_in_memory().unwrap();
    let account = create_test_account(&store);

    let email = make_test_email(
        account.id,
        "Billing Dept",
        "billing@aws.amazon.com",
        "AWS Monthly Invoice #991",
        "Your invoice is ready. Total charged: $240.50.",
    );
    store.insert_email(&email).unwrap();

    let extractor = EntityExtractor::new(None);
    let dispatcher = PillarDispatcher::new(store.clone());

    // Extract receipt
    let receipt = extractor.extract_receipt(&email).await.unwrap();
    assert_eq!(receipt.amount_cents, 24050);

    // Dispatch to Purchases pillar
    let dispatched = dispatcher.dispatch_receipt(email.id, &receipt).unwrap();
    assert_eq!(dispatched.pillar, "purchases");
    assert_eq!(dispatcher.total_dispatched(), 1);

    // Extract contact
    let contacts = extractor.extract_contacts(&email).await.unwrap();
    assert_eq!(contacts.len(), 1);
    assert_eq!(contacts[0].email, "billing@aws.amazon.com");

    let disp_contact = dispatcher.dispatch_contact(email.id, &contacts[0]).unwrap();
    assert_eq!(disp_contact.pillar, "interactions");
    assert_eq!(dispatcher.total_dispatched(), 2);
}

#[tokio::test]
async fn test_smart_inbox_formatter() {
    let mut email = make_test_email(
        Uuid::new_v4(),
        "Sarah Chen",
        "sarah@company.com",
        "Design review sync?",
        "Are you free tomorrow afternoon?",
    );
    email.category = Some(EmailCategory::ActionRequired);
    email.classification_confidence = Some(0.92);
    email.classification_reasoning = Some("Meeting request".to_string());

    let rendered = SmartInboxFormatter::render_inbox(EmailCategory::ActionRequired, &[email]);
    assert!(rendered.contains("Action Required (1 emails)"));
    assert!(rendered.contains("Sarah Chen"));
    assert!(rendered.contains("Confidence: 92%"));
}
