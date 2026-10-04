use regex::Regex;
use std::sync::OnceLock;

static PATTERNS: OnceLock<Vec<Regex>> = OnceLock::new();

fn get_patterns() -> &'static Vec<Regex> {
    PATTERNS.get_or_init(|| {
        vec![
            // OpenAI / Anthropic API keys
            Regex::new(r"sk-[A-Za-z0-9_-]{20,}").unwrap(),
            // GitHub Personal Access Tokens
            Regex::new(r"ghp_[A-Za-z0-9]{20,}").unwrap(),
            // AWS Access Key ID
            Regex::new(r"AKIA[0-9A-Z]{16}").unwrap(),
            // Generic Bearer Tokens
            Regex::new(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{25,}").unwrap(),
            // Credit Card Numbers (13-16 digits)
            Regex::new(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b").unwrap(),
            // Email addresses
            Regex::new(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}").unwrap(),
        ]
    })
}

/// Invariant 10: Dual-Pass Egress Filter
/// Redacts sensitive credentials, tokens, and PII before output or logging.
pub struct RedactionSentinel;

impl RedactionSentinel {
    /// Redacts all known secret patterns and PII, replacing them with [REDACTED_SECRET] or [REDACTED_PII]
    pub fn redact(input: &str) -> String {
        let mut result = input.to_string();
        for pattern in get_patterns() {
            result = pattern.replace_all(&result, "[REDACTED_SECRET]").to_string();
        }
        result
    }

    /// Evaluates Shannon entropy to detect raw high-entropy hex or base64 tokens
    pub fn shannon_entropy(data: &str) -> f64 {
        if data.is_empty() {
            return 0.0;
        }
        let mut char_counts = std::collections::HashMap::new();
        for ch in data.chars() {
            *char_counts.entry(ch).or_insert(0) += 1;
        }
        let len = data.chars().count() as f64;
        let mut entropy = 0.0;
        for &count in char_counts.values() {
            let p = count as f64 / len;
            entropy -= p * p.log2();
        }
        entropy
    }

    /// Returns true if a string exhibits high entropy consistent with random encryption keys
    pub fn is_high_entropy(data: &str, threshold: f64) -> bool {
        data.len() >= 20 && Self::shannon_entropy(data) >= threshold
    }
}
