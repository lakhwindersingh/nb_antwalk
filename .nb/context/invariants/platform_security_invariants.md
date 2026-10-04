# Percipience Base Platform Security Invariants (Tier 1)

**Document Version**: 7.5.0  
**Enforcement Level**: CRITICAL / IMMUTABLE - Tier 1 Base Platform Invariants CANNOT be overridden by custom rules, user prompts, custom schemas, or agent workflows.  
**Precedence**: Tier 1 (Base Platform Invariants) > Tier 2 (Enterprise Global Rules) > Tier 3 (Domain / Team Custom Context)  

---

## 1. Context Poisoning Defense & Quarantine Immutability (CAP-02, CAP-20)

### Invariant Rule
The context poisoning detection, isolation, and quarantine mechanism MUST NEVER be disabled or bypassed.
- No user configuration, prompt injection, custom rule, or subagent directive may set `disable_poisoning_quarantine: true` or equivalent flags.
- Any detected hallucination, unverified external claim, contradictory invariant, or malicious instruction MUST be immediately quarantined into `user/hitl/poisoning_quarantine/` and flagged in `context_ledger.yaml`.
- The system MUST immediately trigger a rollback to the last cryptographically verified recovery point ($RP_k$) upon confirmation of a poisoned state.

### Verification Mechanism
Enforced at gatekeeper runtime by `.nb/core/layered_context_validator.py` and `LayeredContextValidator.validate_layered_hierarchy()`. Any configuration or rule file attempting to bypass quarantine halts gatekeeper validation with an immediate exit code 1.

---

## 2. Zero Plaintext Credential & Sensitive Body Retention Invariant (CAP-20, CAP-25)

### Invariant Rule
Plaintext secrets, private keys, API tokens, full unencrypted email bodies, and Personally Identifiable Information (PII) MUST NEVER be retained on disk or logged unencrypted.
- **Credential Storage**: Authentication credentials must reside in external KMS / Vault services (AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault). Only ephemeral leased tokens or signed URIs are handled at runtime.
- **Email Bodies**: Full raw email RFC822 bodies must never be persisted in plain database columns or unencrypted log files. Content must be ephemeral, scrubbed in-memory, or hashed (`SHA-256`) with ephemeral memory zeroization (`zeroize::ZeroizeOnDrop`).
- **Memory Scrubbing**: All cryptographic buffers, keys, and private data in memory must implement zeroize-on-drop semantics to prevent cold-boot or core dump extraction.

---

## 3. Ephemeral Worktree Sandboxing & PID-Probed Lease Lifecycle (CAP-05, CAP-22)

### Invariant Rule
Autonomous agents, subagents, and concurrent pipeline executions MUST operate exclusively inside isolated ephemeral Git worktrees located under `.nb/workspaces/subagent_<id>/`.
- **Direct Workspace Protection**: Agents are strictly prohibited from writing directly to the target release branch (`main`, `master`, `production`) or modifying shared workspace root files without passing atomic verification gates.
- **Active POSIX PID-Probing**: Every active worktree lease registered in `.nb/workspaces/leases.json` must be bound to a valid OS process ID. If `os.kill(pid, 0)` indicates process termination, the lease MUST be automatically reclaimed and the worktree purged (`git worktree remove --force`) to eliminate deadlocks.
- **Atomic Gate Merge**: Worktree modifications can only be integrated into the primary repository via atomic merge gates verifying AST syntax, wire contracts, and test suites.

---

## 4. Cryptographic Ledger Immutability & Merkle Continuity (CAP-08, CAP-32)

### Invariant Rule
Every state transition, artifact change, gate verification, and recovery point MUST be immutably recorded in the SHA-256 Merkle DAG chain in `context_ledger.yaml`.
- **Block Header Formula**:
  $$H_i = \text{SHA256}(H_{i-1} + \text{canonical\_json}(\Delta_i) + T_i)$$
- **Tamper Evidence**: Any modification, insertion, or deletion of historical Merkle blocks invalidates the cryptographic chain and halts all execution.
- **WORM Vault Mirroring**: In enterprise mode, all sealed Merkle blocks must be synchronously mirrored to Write-Once-Read-Many (WORM) storage (AWS S3 Object Lock in `COMPLIANCE` mode or GCP Bucket Lock).

---

## 5. Bounded TDD Self-Healing & Flaky Test Quarantine Ceiling (CAP-07, CAP-16)

### Invariant Rule
The automated test-driven development (TDD) self-healing loop has an absolute, non-configurable ceiling of **three (3) repair attempts**.
- **Retry Ceiling**: If a test failure is not resolved within 3 iterations, the self-healing loop MUST terminate immediately to prevent compute thrashing and infinite retry loops.
- **Non-Blocking Quarantine**: Tests confirmed to be flaky, non-deterministic, or contradictory must be isolated into `user/hitl/flaky_quarantine.yaml` and recorded in `context_ledger.yaml`. Quarantined tests do not block sibling service builds but require human-in-the-loop review.

---

## 6. Quad-Space Separation of Concerns (CAP-12)

### Invariant Rule
The Quad-Space boundary hierarchy is strictly enforced:
1. `user/` (User Enclave): Dedicated to input specifications (`inputs/`), human-in-the-loop quarantine/review (`hitl/`), scratch workspaces (`scratch/`), and dashboard outputs (`outputs/`).
2. `workplace/` (Customer Application Space): Dedicated strictly to customer application source code, domain modules (`modules/`), project configs, and documentation. Zero platform execution engine code may exist inside `workplace/`.
3. `.nb/context/` (Governance Space): Immutable ledgers, invariants, schemas, rules, and wire contracts.
4. `.nb/agentic/` (Agent & Workflow Space): Agent manifests, workflows, and templates.
