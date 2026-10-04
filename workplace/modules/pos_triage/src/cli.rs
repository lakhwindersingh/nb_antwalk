//! Smart inbox query and CLI rendering helpers
//!
//! Defined in Section 6 of `.nb/plan/extensions/email_triage/concise.md`.

use pos_email::{Email, EmailCategory, EmailStore};

pub struct SmartInboxFormatter;

impl SmartInboxFormatter {
    /// Formats a list of categorized emails into a rich CLI dashboard view
    pub fn render_inbox(category: EmailCategory, emails: &[Email]) -> String {
        let title = match category {
            EmailCategory::ActionRequired => "Action Required",
            EmailCategory::Fyi => "FYI / Notifications",
            EmailCategory::Newsletter => "Newsletters & Subscriptions",
            EmailCategory::Receipt => "Receipts & Orders",
            EmailCategory::Spam => "Spam / Quarantine",
        };

        let mut out = String::new();
        out.push_str("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        out.push_str(&format!("{} ({} emails)\n", title, emails.len()));
        out.push_str("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

        if emails.is_empty() {
            out.push_str("  (No emails in this category)\n");
            return out;
        }

        for (i, email) in emails.iter().enumerate() {
            let sender = email
                .from
                .name
                .as_deref()
                .unwrap_or(email.from.email.as_str());

            out.push_str(&format!(
                "[{}] {} - \"{}\" ({})\n",
                i + 1,
                sender,
                email.subject,
                email.date.format("%Y-%m-%d %H:%M")
            ));

            if let Some(conf) = email.classification_confidence {
                out.push_str(&format!(
                    "    → Confidence: {:.0}% | Reason: {}\n",
                    conf * 100.0,
                    email.classification_reasoning.as_deref().unwrap_or("auto-classified")
                ));
            }

            if email.has_attachments {
                out.push_str("    → 📎 [Attachments present]\n");
            }
        }

        out
    }

    /// Query and format smart inbox from store
    pub fn display_inbox(store: &EmailStore, category: EmailCategory, limit: usize) -> String {
        let emails = store
            .get_emails_by_category(category, limit)
            .unwrap_or_default();
        Self::render_inbox(category, &emails)
    }
}
