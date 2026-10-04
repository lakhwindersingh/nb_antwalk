# Personal OS: Non-Negotiable System Invariants

**Document Version**: 1.0.0  
**Last Updated**: 2024-10-04  
**Enforcement Level**: CRITICAL - System MUST NOT violate these invariants under any circumstances

---

## 1. Zero-Knowledge Memory Invariant

### Rule
Plaintext credentials, API keys, passwords, private keys, and personally identifiable authentication secrets MUST NEVER be written to:
- Persistent log files (stdout, stderr, file logs)
- SQLite database columns (except encrypted `vault_items.encrypted_payload`)
- LLM context windows or prompts
- Network transmission payloads (except over authenticated TLS to trusted endpoints)
- Core dumps, crash reports, or debug output
- Git repositories or version control

### Enforcement Mechanisms
1. **Zeroize on Drop**: All types holding plaintext secrets MUST implement `zeroize::ZeroizeOnDrop`
2. **Redaction Sentinel**: All egress text streams pass through `RedactionSentinel` before output
3. **Compile-Time Type Safety**: Secret types wrapped in `SecretBuffer<T>` with no `Debug` or `Display` traits
4. **Audit Trail**: Every vault access logged to immutable Merkle ledger in `.nb/context/ledger/context_ledger.yaml`

### Examples
```rust
// ✅ CORRECT - Memory scrubbed on drop
use zeroize::{Zeroize, ZeroizeOnDrop};

#[derive(Zeroize, ZeroizeOnDrop)]
struct SecretBuffer {
    inner: Vec<u8>,
}

// ❌ INCORRECT - Secret exposed in logs
println!("API Key: {}", api_key); // FORBIDDEN
```

---

## 2. Human-in-the-Loop (HITL) Financial & Secret Gate

### Rule
Autonomous agents and background workflows are STRICTLY FORBIDDEN from executing the following actions without explicit interactive user approval:

#### Financial Operations Requiring HITL
- Finalizing any payment, purchase, or monetary transaction (amount > $0.00)
- Authorizing recurring subscription charges
- Modifying bank account or payment method configurations
- Exporting financial reports containing account numbers or routing information

#### Credential Operations Requiring HITL
- Exporting permanent credentials: SSH private keys, X.509 certificates, PGP keys, encryption master keys
- First-time vault access by a newly registered agent
- Credential leases during non-business hours (22:00-06:00 local time) based on policy
- Generating or rotating root master keys

#### Repository Operations Requiring HITL
- Executing `git reset --hard` on non-ephemeral branches (main, master, production)
- Force-pushing to protected branches
- Deleting project root workspaces or repositories
- Permanently purging git history or objects

### Enforcement Mechanism
Actions requiring HITL are queued in `user/hitl/financial_authorization_queue.md` and `user/hitl/vault_approval_queue.md`. The system daemon polls for user approval via CLI or web dashboard. Timeout: 5 minutes for routine operations, indefinite for financial/security operations.

---

## 3. Local-First Offline Resilience

### Rule
ALL core subsystem operations MUST function completely disconnected from external internet services. Cloud connectivity is OPTIONAL for sync and backup only.

#### Operations That MUST Work Offline
- File ingestion, BLAKE3 hashing, and local CAS storage
- Hybrid search (Tantivy BM25 + local vector embeddings)
- Project task tracking and git repository management
- Thought capture, knowledge graph traversal, daily journal
- Calendar event storage and habit tracking (sync deferred)
- Workflow DAG execution (excluding workflows explicitly requiring external APIs)
- Vault encryption/decryption and lease issuance

#### Graceful Degradation When Offline
- **Embedding Generation**: Fall back to local sentence-transformers model (e.g., all-MiniLM-L6-v2) instead of OpenAI API
- **External Task Sync**: Queue sync operations for retry when connectivity restored
- **Calendar Sync**: Use last-cached iCal/CalDAV state; flag stale data
- **LLM-Powered Features**: Use rule-based deterministic fallbacks or defer to user

### Verification
```bash
# Test offline mode
sudo pfctl -e && sudo pfctl -f /dev/stdin <<EOF
block drop all
EOF

pos daemon start --offline-mode
pos search "rust async patterns"  # Must succeed
pos thought "New idea about zero-copy"  # Must succeed
pos vault lease github_token agent_test  # Must succeed
```

---

## 4. Cryptographic State Tamper Evidence

### Rule
All state-modifying operations that affect security posture, financial records, or vault access MUST append an immutable, cryptographically chained entry to the Percipience Merkle ledger (`.nb/context/ledger/context_ledger.yaml`).

#### Operations Requiring Ledger Entry
- Vault secret storage, lease issuance, lease revocation
- Financial transaction logs (purchases, expenses, subscriptions)
- Project workspace creation or deletion
- Credential access attempts (success or failure)
- Workflow execution that modifies external state
- Configuration changes to security policies

#### Ledger Entry Structure
```yaml
- entry_id: "ledger_a3f9c8d2e1b4"
  timestamp: "2024-10-04T14:32:18Z"
  operation: "vault_lease_granted"
  agent_id: "agent_file_indexer"
  resource: "vault_item:github_token"
  previous_hash: "sha256:7a8b9c0d..."
  current_hash: "sha256:1f2e3d4c..."
  signature: "ed25519:9a8b7c6d..."
```

#### Tamper Detection
The ledger forms a Merkle chain where each entry includes `previous_hash`. Any modification to a historical entry invalidates the chain. Daily integrity verification runs via:
```bash
./.nb/bin/percipience audit --verify-chain
```

---

## 5. Memory Safety & Rust Soundness

### Rule
The Personal OS codebase MUST maintain 100% safe Rust with ZERO `unsafe` blocks, except in the following whitelisted scenarios:

#### Permitted `unsafe` Usage (Requires Review)
1. **FFI Bindings**: Interfacing with OS keychain APIs (Security.framework, libsecret, Windows Credential Manager)
2. **SIMD Optimizations**: Explicit SIMD intrinsics for BLAKE3 hashing or vector dot products (if performance-critical)
3. **Zeroize Internal Implementation**: Memory scrubbing via `core::ptr::write_volatile` (already encapsulated in `zeroize` crate)

#### Forbidden Patterns
- Raw pointer dereferencing without proven invariants
- Transmuting types without size/alignment guarantees
- Manually implementing `Send`/`Sync` without soundness proof
- Bypassing borrow checker via `Rc::get_mut_unchecked` or similar

### Enforcement
```bash
# Audit unsafe usage
cargo geiger --all-targets

# Expect: All crates show 0% unsafe in application code
```

---

## 6. Least-Privilege Agent Execution

### Rule
Every subagent, workflow, or background routine operates with a **capability token** that explicitly enumerates permitted operations. Agents CANNOT escalate privileges or access resources outside their granted capabilities.

#### Capability Token Structure
```json
{
  "agent_id": "agent_file_indexer",
  "issued_at": "2024-10-04T12:00:00Z",
  "expires_at": "2024-10-04T13:00:00Z",
  "capabilities": [
    "files:read",
    "files:index",
    "search:query",
    "vault:lease:read_only_api_keys"
  ],
  "restrictions": {
    "max_file_size_bytes": 104857600,
    "allowed_directories": ["/Users/lakhwinder/Documents", "/Users/lakhwinder/Downloads"]
  }
}
```

#### Enforcement
The `pos_agents` module validates every operation against the agent's capability token. Unauthorized actions return `POS_ERR_002: Unauthorized`.

---

## 7. Data Retention & Privacy Boundaries

### Rule
Personal OS respects user privacy and data minimization principles:

#### Data That MUST NOT Be Stored
- Plaintext passwords (store hashed credentials only, or encrypt in vault)
- Full credit card numbers (store last 4 digits and encrypted full number in vault)
- Social Security Numbers or national IDs (encrypt if absolutely necessary)
- Raw biometric data (fingerprints, facial recognition vectors)

#### Data Retention Limits
- **Vault Audit Logs**: Retained indefinitely (tamper-evident)
- **File Watcher Logs**: 90 days (then rotated)
- **LLM API Request Logs**: 30 days (for debugging)
- **Workflow Execution Traces**: 60 days
- **Deleted Items**: Soft-deleted with 30-day recovery window, then hard-deleted

#### Right to Erasure
Users can invoke complete data erasure:
```bash
pos vault destroy --confirm
pos purge --all-data --irreversible
```

---

## 8. Idempotency & Crash Recovery

### Rule
All state-modifying operations MUST be idempotent or transactional to guarantee consistency across crashes, power failures, or process kills.

#### Guarantees
1. **SQLite WAL Mode**: Atomic commits with automatic rollback on crash
2. **Two-Phase Commit for Vault Operations**: 
   - Phase 1: Encrypt secret, write to temp file
   - Phase 2: Move to final location, append ledger entry
3. **Workflow Checkpointing**: Long-running workflows periodically checkpoint progress; resume from last checkpoint on restart
4. **File Ingestion Deduplication**: Re-ingesting the same file (by BLAKE3 hash) is a no-op

#### Recovery Commands
```bash
pos recover --check-integrity
pos recover --repair-indexes
pos recover --rebuild-ledger-chain
```

---

## 9. Rate Limiting & Resource Quotas

### Rule
To prevent resource exhaustion and abuse, the following quotas apply:

#### Per-Agent Limits
- **Vault Lease Requests**: 10 per minute per agent
- **File Ingestion**: 100 MB/s total throughput
- **Search Queries**: 100 per minute per agent
- **Workflow Dispatch**: 50 concurrent workflows

#### Global System Limits
- **Max SQLite Database Size**: 100 GB (warning at 80 GB)
- **Max Blob Store Size**: 500 GB
- **Max Vector Index Size**: 10 million embeddings
- **Max Concurrent Agent Threads**: 32

### Enforcement
Rate limiting tracked in-memory with token bucket algorithm. Quota exceeded returns `POS_ERR_429: Rate Limit Exceeded`.

---

## 10. Redaction & Egress Filtering

### Rule
Before ANY text content leaves the system boundary (CLI output, log files, LLM API calls, webhooks), it MUST pass through the `RedactionSentinel` filter.

#### Redaction Patterns
1. **Known Vault Secrets**: Hash-based detection of stored credentials
2. **API Key Patterns**: Regex detection of common formats:
   - OpenAI: `sk-proj-[A-Za-z0-9]{48}`
   - GitHub: `ghp_[A-Za-z0-9]{36}`
   - AWS: `AKIA[A-Z0-9]{16}`
3. **Entropy Analysis**: High-entropy strings (>4.5 bits/char) flagged for review
4. **PII Patterns**: Email addresses, phone numbers, SSNs

#### Redacted Output Format
```
Original: "My API key is sk-proj-abc123xyz789..."
Redacted: "My API key is [REDACTED_SECRET:sha256:7a8b9c]"
```

---

## Violation Response Protocol

If any invariant is violated:

1. **Immediate Halt**: The offending operation is terminated
2. **Audit Log Entry**: Violation logged with full stack trace
3. **User Notification**: Alert displayed in CLI and web dashboard
4. **Quarantine**: Affected data moved to `user/hitl/poisoning_quarantine.md` for review
5. **Rollback**: State reverted to last known-good Merkle checkpoint if possible

---

## Compliance & Verification

### Daily Automated Checks
```bash
./.nb/bin/percipience audit --full
```

### Manual Security Review Checklist
- [ ] No plaintext secrets in git history (`git log -S "sk-" --all`)
- [ ] All vault operations have corresponding ledger entries
- [ ] Redaction sentinel logs show 0 leaks in past 30 days
- [ ] `cargo geiger` reports 0% unsafe in application code
- [ ] HITL queue is empty (no pending unauthorized operations)

---

**End of Document**
