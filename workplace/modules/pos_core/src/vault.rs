use std::fmt;
use zeroize::{Zeroize, ZeroizeOnDrop};
use chrono::{DateTime, Duration, Utc};
use uuid::Uuid;
use std::collections::HashMap;
use parking_lot::RwLock;

/// Invariant 1: Zero-Knowledge Memory Invariant
/// SecretBuffer scrubs its memory upon being dropped.
/// Explicitly forbids automatic Debug or Display string dumps of secrets.
#[derive(Zeroize, ZeroizeOnDrop)]
pub struct SecretBuffer {
    inner: Vec<u8>,
}

impl SecretBuffer {
    pub fn new(secret: Vec<u8>) -> Self {
        Self { inner: secret }
    }

    pub fn from_str(secret: &str) -> Self {
        Self { inner: secret.as_bytes().to_vec() }
    }

    pub fn expose_secret(&self) -> &[u8] {
        &self.inner
    }

    pub fn len(&self) -> usize {
        self.inner.len()
    }

    pub fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }
}

// Ensure secrets are never leaked in debug format
impl fmt::Debug for SecretBuffer {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "SecretBuffer([REDACTED_MEMORY; {} bytes])", self.inner.len())
    }
}

impl fmt::Display for SecretBuffer {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[REDACTED_SECRET]")
    }
}

/// Capability-based ephemeral lease token for subagents
#[derive(Debug, Clone)]
pub struct LeaseToken {
    pub lease_id: String,
    pub item_name: String,
    pub agent_id: String,
    pub issued_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub revoked: bool,
}

impl LeaseToken {
    pub fn is_valid(&self) -> bool {
        !self.revoked && Utc::now() < self.expires_at
    }
}

pub struct VaultManager {
    secrets: RwLock<HashMap<String, Vec<u8>>>,
    leases: RwLock<HashMap<String, LeaseToken>>,
}

impl VaultManager {
    pub fn new() -> Self {
        Self {
            secrets: RwLock::new(HashMap::new()),
            leases: RwLock::new(HashMap::new()),
        }
    }

    pub fn store_secret(&self, name: &str, secret: SecretBuffer) {
        let mut store = self.secrets.write();
        store.insert(name.to_string(), secret.expose_secret().to_vec());
    }

    /// Issues an ephemeral lease token for a subagent (default TTL: 300 seconds)
    pub fn issue_lease(&self, name: &str, agent_id: &str, ttl_secs: i64) -> Option<LeaseToken> {
        let store = self.secrets.read();
        if !store.contains_key(name) {
            return None;
        }

        let lease = LeaseToken {
            lease_id: format!("lease_{}", Uuid::new_v4()),
            item_name: name.to_string(),
            agent_id: agent_id.to_string(),
            issued_at: Utc::now(),
            expires_at: Utc::now() + Duration::seconds(ttl_secs),
            revoked: false,
        };

        let mut leases = self.leases.write();
        leases.insert(lease.lease_id.clone(), lease.clone());
        Some(lease)
    }

    /// Accesses a secret via a valid lease token. Returns a scrubbed SecretBuffer.
    pub fn access_secret(&self, lease_id: &str) -> Option<SecretBuffer> {
        let leases = self.leases.read();
        let lease = leases.get(lease_id)?;

        if !lease.is_valid() {
            return None;
        }

        let store = self.secrets.read();
        let raw = store.get(&lease.item_name)?;
        Some(SecretBuffer::new(raw.clone()))
    }

    pub fn revoke_lease(&self, lease_id: &str) -> bool {
        let mut leases = self.leases.write();
        if let Some(lease) = leases.get_mut(lease_id) {
            lease.revoked = true;
            true
        } else {
            false
        }
    }
}
