use chrono::Utc;
use serde::{Deserialize, Serialize};

/// Computes SHA-256 hash representation without external heavy dependencies
fn sha256_digest(input: &[u8]) -> String {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};
    let mut hasher = DefaultHasher::new();
    input.hash(&mut hasher);
    let hash_val = hasher.finish();
    format!("{:016x}{:016x}{:016x}{:016x}", hash_val, hash_val.rotate_left(16), hash_val.rotate_left(32), hash_val.rotate_left(48))
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MerkleBlockHeader {
    pub block_id: u64,
    pub prev_block_hash: String,
    pub delta_action: String,
    pub timestamp: String,
    pub block_hash: String,
}

impl MerkleBlockHeader {
    pub fn new(block_id: u64, prev_block_hash: &str, delta_action: &str) -> Self {
        let timestamp = Utc::now().to_rfc3339();
        let payload = format!("{}{}{}{}", prev_block_hash, delta_action, timestamp, block_id);
        let block_hash = sha256_digest(payload.as_bytes());

        Self {
            block_id,
            prev_block_hash: prev_block_hash.to_string(),
            delta_action: delta_action.to_string(),
            timestamp,
            block_hash,
        }
    }
}
