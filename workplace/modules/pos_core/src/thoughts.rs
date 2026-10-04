use serde::{Deserialize, Serialize};
use regex::Regex;
use std::sync::OnceLock;

static WIKILINK_RE: OnceLock<Regex> = OnceLock::new();

fn get_wikilink_re() -> &'static Regex {
    WIKILINK_RE.get_or_init(|| Regex::new(r"\[\[([^\]]+)\]\]").unwrap())
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ThoughtType {
    Fleeting,
    Journal,
    Atomic,
    Concept,
}

impl Default for ThoughtType {
    fn default() -> Self {
        Self::Fleeting
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Thought {
    pub id: String,
    pub title: String,
    pub content_raw: String,
    pub thought_type: ThoughtType,
    pub tags: Vec<String>,
    pub actionability_score: f64,
    pub ambiguity_score: f64,
}

impl Thought {
    /// Extracts all bidirectional wikilinks ([[Target]]) from content
    pub fn extract_wikilinks(&self) -> Vec<String> {
        let re = get_wikilink_re();
        re.captures_iter(&self.content_raw)
            .filter_map(|cap| cap.get(1).map(|m| m.as_str().trim().to_string()))
            .collect()
    }
}
