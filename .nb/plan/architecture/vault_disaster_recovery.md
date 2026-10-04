---
gap_id: "GAP-006"
name: "Vault Disaster Recovery via BIP-39 & Shamir Secret Sharing"
priority: "P0"
status: "specification"
created: "2026-10-04"
---

# Vault Disaster Recovery: BIP-39 Mnemonic Seed & Shamir Secret Sharing

## Problem Statement

Current vault implementation (`pos_vault`) stores the master encryption key exclusively in the **OS keychain** (`keyring-rs`):

```rust
// Current approach (single point of failure)
let keyring = Entry::new("personal_os", "master_key")?;
keyring.set_password(&master_key_base64)?;
```

**Catastrophic Failure Scenarios**:
1. **Hardware Loss**: Laptop stolen, phone lost → all encrypted data unrecoverable
2. **OS Reinstall**: macOS clean install wipes Keychain → master key lost
3. **Keychain Corruption**: Rare but documented macOS Keychain database corruption
4. **Account Lockout**: Apple ID disabled → iCloud Keychain sync broken
5. **Secure Enclave Failure**: T2/M1 chip hardware fault → key inaccessible

**Impact**:
- **Permanent data loss**: All encrypted thoughts, credentials, sync blocks irrecoverable
- **No key escrow**: Unlike BitWarden/1Password, no recovery mechanism
- **Trust barrier**: Users reluctant to store sensitive data without backup guarantee

**Current State**:
- Zero redundancy in key storage
- No key derivation from memorable seed
- No threshold-based recovery (multi-device)
- No paper backup option

---

## Solution Architecture: BIP-39 + Shamir Secret Sharing

Implement **dual-layer key recovery**:
1. **BIP-39 mnemonic seed** (12/24-word phrase) as primary recovery mechanism
2. **Shamir's Secret Sharing (SSS)** for threshold-based multi-device recovery
3. **OS Keychain** remains the hot storage for convenience

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                  Initial Vault Setup (pos vault init)         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 1: Generate BIP-39 Mnemonic (12 or 24 words)           │
│  - Use cryptographic RNG (getrandom)                          │
│  - Standard BIP-39 wordlist (2048 words)                      │
│  - Example: "abandon ability able about above absent absorb   │
│    abstract absurd abuse access accident"                     │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 2: Derive Master Key via PBKDF2 (BIP-39 Standard)      │
│  - Input: mnemonic + optional passphrase                      │
│  - PBKDF2-HMAC-SHA512 with 2048 iterations                   │
│  - Output: 512-bit seed → first 256 bits = master key        │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 3: Split Master Key via Shamir Secret Sharing          │
│  - Scheme: (2, 3) threshold                                   │
│  - Share 1: Store in macOS Keychain                          │
│  - Share 2: Store in iOS Secure Enclave (via iCloud Keychain)│
│  - Share 3: Display as QR code for paper backup              │
│  - Any 2 shares can reconstruct master key                   │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 4: Store in OS Keychain (Hot Storage for Convenience)  │
│  - macOS Keychain: keyring-rs API                            │
│  - iOS Keychain: kSecAttrAccessible when unlocked            │
│  - Linux: freedesktop.org Secret Service                     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  Recovery Scenarios                           │
└──────────────────────────────────────────────────────────────┘

┌────────────────────┐  ┌────────────────────┐  ┌──────────────┐
│  Scenario A:       │  │  Scenario B:       │  │  Scenario C: │
│  Enter 12-word     │  │  Scan 2 of 3       │  │  iCloud      │
│  mnemonic phrase   │  │  Shamir QR codes   │  │  Keychain    │
│  → Derive master   │  │  → Reconstruct     │  │  sync to new │
│  key via PBKDF2    │  │  master key        │  │  device      │
└────────────────────┘  └────────────────────┘  └──────────────┘
```

---

## Implementation Specification

### 1. BIP-39 Mnemonic Generation

```rust
// workplace/modules/pos_vault/src/bip39.rs

use bip39::{Language, Mnemonic, Seed};
use rand::Rng;
use sha2::{Sha512, Digest};
use pbkdf2::pbkdf2_hmac;

pub struct MnemonicGenerator;

impl MnemonicGenerator {
    /// Generate 12-word mnemonic (128-bit entropy)
    pub fn generate_12_word() -> Result<Mnemonic, VaultError> {
        let mut rng = rand::thread_rng();
        let entropy: [u8; 16] = rng.gen();
        Mnemonic::from_entropy(&entropy, Language::English)
            .map_err(|e| VaultError::MnemonicGeneration(e.to_string()))
    }
    
    /// Generate 24-word mnemonic (256-bit entropy) - recommended
    pub fn generate_24_word() -> Result<Mnemonic, VaultError> {
        let mut rng = rand::thread_rng();
        let entropy: [u8; 32] = rng.gen();
        Mnemonic::from_entropy(&entropy, Language::English)
            .map_err(|e| VaultError::MnemonicGeneration(e.to_string()))
    }
    
    /// Validate user-provided mnemonic
    pub fn validate(phrase: &str) -> Result<Mnemonic, VaultError> {
        Mnemonic::from_phrase(phrase, Language::English)
            .map_err(|e| VaultError::InvalidMnemonic(e.to_string()))
    }
}

pub struct KeyDerivation;

impl KeyDerivation {
    /// Derive 256-bit master key from mnemonic (BIP-39 standard)
    pub fn derive_master_key(
        mnemonic: &Mnemonic,
        passphrase: Option<&str>,
    ) -> Result<[u8; 32], VaultError> {
        // BIP-39: seed = PBKDF2-HMAC-SHA512(mnemonic, "mnemonic" + passphrase, 2048)
        let seed = Seed::new(mnemonic, passphrase.unwrap_or(""));
        let seed_bytes = seed.as_bytes();  // 512 bits
        
        // Take first 256 bits as master encryption key
        let mut master_key = [0u8; 32];
        master_key.copy_from_slice(&seed_bytes[0..32]);
        
        Ok(master_key)
    }
    
    /// Derive child keys for specific purposes (BIP-32-like hierarchy)
    pub fn derive_child_key(
        master_key: &[u8; 32],
        purpose: KeyPurpose,
    ) -> Result<[u8; 32], VaultError> {
        let context = match purpose {
            KeyPurpose::Encryption => b"pos-encryption-v1",
            KeyPurpose::Signing => b"pos-signing-v1",
            KeyPurpose::SyncAuth => b"pos-sync-auth-v1",
        };
        
        let mut child_key = [0u8; 32];
        pbkdf2_hmac::<Sha512>(master_key, context, 1, &mut child_key);
        
        Ok(child_key)
    }
}

#[derive(Debug, Clone, Copy)]
pub enum KeyPurpose {
    Encryption,  // For encrypting vault entries
    Signing,     // For signing sync updates
    SyncAuth,    // For authenticating peer devices
}
```

### 2. Shamir Secret Sharing Implementation

```rust
// workplace/modules/pos_vault/src/shamir.rs

use sharks::{Share, Sharks};  // Shamir Secret Sharing library

pub struct ShamirSplitter;

impl ShamirSplitter {
    /// Split master key into N shares requiring K to reconstruct
    pub fn split_key(
        master_key: &[u8; 32],
        threshold: u8,
        total_shares: u8,
    ) -> Result<Vec<Share>, VaultError> {
        if threshold > total_shares {
            return Err(VaultError::InvalidShamirThreshold);
        }
        
        let sharks = Sharks(threshold);
        let dealer = sharks.dealer(master_key);
        
        let shares: Vec<Share> = dealer.take(total_shares as usize).collect();
        
        Ok(shares)
    }
    
    /// Reconstruct master key from K shares
    pub fn reconstruct_key(
        shares: &[Share],
    ) -> Result<[u8; 32], VaultError> {
        let sharks = Sharks(shares.len() as u8);
        let reconstructed = sharks.recover(shares.iter())
            .map_err(|e| VaultError::ShamirReconstruction(e.to_string()))?;
        
        let mut master_key = [0u8; 32];
        master_key.copy_from_slice(&reconstructed);
        
        Ok(master_key)
    }
    
    /// Encode share as QR code for paper backup
    pub fn share_to_qr_code(share: &Share) -> Result<String, VaultError> {
        // Encode share as base32 for readability
        let share_bytes = share.as_bytes();
        let base32 = base32::encode(base32::Alphabet::RFC4648 { padding: false }, share_bytes);
        
        // Add version prefix and checksum
        let versioned = format!("POS-SHARE-V1:{}", base32);
        
        Ok(versioned)
    }
    
    /// Decode share from QR code
    pub fn qr_code_to_share(qr_data: &str) -> Result<Share, VaultError> {
        let stripped = qr_data.strip_prefix("POS-SHARE-V1:")
            .ok_or(VaultError::InvalidShareFormat)?;
        
        let share_bytes = base32::decode(base32::Alphabet::RFC4648 { padding: false }, stripped)
            .ok_or(VaultError::InvalidShareEncoding)?;
        
        Share::try_from(share_bytes.as_slice())
            .map_err(|e| VaultError::InvalidShare(e.to_string()))
    }
}
```

### 3. Vault Initialization Flow

```rust
// workplace/modules/pos_vault/src/init.rs

pub struct VaultInitializer {
    keyring: KeyringManager,
}

impl VaultInitializer {
    /// Initialize vault with BIP-39 + Shamir recovery
    pub async fn init_with_recovery(
        &self,
        word_count: WordCount,
        passphrase: Option<String>,
        shamir_config: ShamirConfig,
    ) -> Result<VaultInitResult, VaultError> {
        // Step 1: Generate BIP-39 mnemonic
        let mnemonic = match word_count {
            WordCount::Words12 => MnemonicGenerator::generate_12_word()?,
            WordCount::Words24 => MnemonicGenerator::generate_24_word()?,
        };
        
        info!("Generated {}-word BIP-39 mnemonic", word_count as u8);
        
        // Step 2: Derive master key
        let master_key = KeyDerivation::derive_master_key(
            &mnemonic,
            passphrase.as_deref(),
        )?;
        
        // Step 3: Split key via Shamir Secret Sharing
        let shares = ShamirSplitter::split_key(
            &master_key,
            shamir_config.threshold,
            shamir_config.total_shares,
        )?;
        
        info!("Split master key into {} shares (threshold: {})",
            shares.len(), shamir_config.threshold);
        
        // Step 4: Store shares
        let mut share_locations = Vec::new();
        
        // Share 1: macOS Keychain
        self.keyring.store_share(ShareLocation::MacOSKeychain, &shares[0]).await?;
        share_locations.push(ShareLocation::MacOSKeychain);
        
        // Share 2: iOS Keychain (via iCloud Keychain sync)
        if shamir_config.use_icloud_keychain {
            self.keyring.store_share(ShareLocation::ICloudKeychain, &shares[1]).await?;
            share_locations.push(ShareLocation::ICloudKeychain);
        }
        
        // Share 3: Generate QR codes for paper backup
        let qr_codes: Vec<String> = shares[2..]
            .iter()
            .map(|s| ShamirSplitter::share_to_qr_code(s))
            .collect::<Result<Vec<_>, _>>()?;
        
        // Step 5: Store master key in OS keychain for convenience
        self.keyring.store_master_key(&master_key).await?;
        
        Ok(VaultInitResult {
            mnemonic: mnemonic.phrase().to_string(),
            qr_code_shares: qr_codes,
            share_locations,
            master_key_fingerprint: Self::fingerprint(&master_key),
        })
    }
    
    /// Recover vault from BIP-39 mnemonic
    pub async fn recover_from_mnemonic(
        &self,
        mnemonic_phrase: &str,
        passphrase: Option<&str>,
    ) -> Result<[u8; 32], VaultError> {
        // Validate mnemonic
        let mnemonic = MnemonicGenerator::validate(mnemonic_phrase)?;
        
        // Derive master key
        let master_key = KeyDerivation::derive_master_key(&mnemonic, passphrase)?;
        
        // Store in OS keychain
        self.keyring.store_master_key(&master_key).await?;
        
        info!("Vault recovered from BIP-39 mnemonic");
        
        Ok(master_key)
    }
    
    /// Recover vault from Shamir shares
    pub async fn recover_from_shares(
        &self,
        share_qr_codes: Vec<String>,
    ) -> Result<[u8; 32], VaultError> {
        if share_qr_codes.len() < 2 {
            return Err(VaultError::InsufficientShares);
        }
        
        // Decode QR codes to shares
        let shares: Vec<Share> = share_qr_codes
            .iter()
            .map(|qr| ShamirSplitter::qr_code_to_share(qr))
            .collect::<Result<Vec<_>, _>>()?;
        
        // Reconstruct master key
        let master_key = ShamirSplitter::reconstruct_key(&shares)?;
        
        // Store in OS keychain
        self.keyring.store_master_key(&master_key).await?;
        
        info!("Vault recovered from {} Shamir shares", shares.len());
        
        Ok(master_key)
    }
    
    fn fingerprint(key: &[u8; 32]) -> String {
        use sha2::{Sha256, Digest};
        let hash = Sha256::digest(key);
        hex::encode(&hash[0..4])  // First 4 bytes as hex
    }
}

#[derive(Debug)]
pub struct VaultInitResult {
    pub mnemonic: String,
    pub qr_code_shares: Vec<String>,
    pub share_locations: Vec<ShareLocation>,
    pub master_key_fingerprint: String,
}

#[derive(Debug, Clone, Copy)]
pub enum WordCount {
    Words12 = 12,
    Words24 = 24,
}

#[derive(Debug, Clone)]
pub struct ShamirConfig {
    pub threshold: u8,        // K in (K, N) scheme
    pub total_shares: u8,     // N in (K, N) scheme
    pub use_icloud_keychain: bool,
}

impl Default for ShamirConfig {
    fn default() -> Self {
        Self {
            threshold: 2,           // Any 2 of 3 shares
            total_shares: 3,
            use_icloud_keychain: true,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub enum ShareLocation {
    MacOSKeychain,
    ICloudKeychain,
    PaperBackup,
}
```

### 4. CLI Commands

```bash
# Initialize vault with 24-word recovery phrase
pos vault init --recovery-words 24 --shamir 2-of-3

# Output:
# ✅ Vault initialized successfully!
# 
# 🔐 Recovery Phrase (WRITE THIS DOWN):
# abandon ability able about above absent absorb abstract
# absurd abuse access accident account accuse achieve acid
# acoustic acquire across act action actor actress actual
# 
# 📱 Shamir Shares (2 of 3 required for recovery):
# - Share 1: Stored in macOS Keychain
# - Share 2: Stored in iCloud Keychain (synced to iPhone)
# - Share 3: Print QR code below for paper backup
# 
# [QR Code displayed]
# 
# ⚠️  Store recovery phrase in a safe place (fireproof safe, safety deposit box)
# ⚠️  Never share your recovery phrase with anyone

# Recover vault from mnemonic
pos vault recover --mnemonic

# Recover vault from Shamir shares
pos vault recover --shares

# Verify vault integrity
pos vault verify --fingerprint a3f2b9c1

# Export vault backup (encrypted with master key)
pos vault export ~/Desktop/vault_backup_2026-10-04.pos

# Rotate master key (requires current mnemonic)
pos vault rotate-key
```

---

## Security Considerations

### BIP-39 Mnemonic Protection
1. **Never transmit electronically**: No email, cloud storage, messaging apps
2. **Physical security**: Fireproof safe, bank safety deposit box, Shamir split geographically
3. **Memorization**: Users can memorize 12 words with spaced repetition
4. **Passphrase option**: Add 25th word passphrase (not stored anywhere) for plausible deniability

### Shamir Threshold Selection
- **(2, 3)**: Recommended default - lose 1 share, still recoverable
- **(3, 5)**: High-security - geographically distributed shares
- **(1, 1)**: Insecure - no redundancy, equivalent to single key

### Attack Resistance
- **Brute force**: 12 words = 128-bit entropy (2^128 combinations, infeasible)
- **Dictionary attack**: BIP-39 wordlist is standardized, but entropy is sufficient
- **Phishing**: Users must verify `pos` CLI legitimacy before entering mnemonic
- **Keylogger**: Mnemonic entry should use secure input (no echo)

---

## Storage Schema

```sql
-- Vault metadata (non-sensitive)
CREATE TABLE IF NOT EXISTS vault_metadata (
    vault_id TEXT PRIMARY KEY,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    recovery_mechanism TEXT NOT NULL CHECK (recovery_mechanism IN ('bip39', 'bip39+shamir')),
    shamir_threshold INTEGER,
    shamir_total_shares INTEGER,
    master_key_fingerprint TEXT NOT NULL,  -- SHA256(master_key)[0:4]
    last_accessed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Share locations (which devices hold which shares)
CREATE TABLE IF NOT EXISTS shamir_share_registry (
    share_id TEXT PRIMARY KEY,
    vault_id TEXT NOT NULL REFERENCES vault_metadata(vault_id),
    share_index INTEGER NOT NULL,
    location TEXT NOT NULL CHECK (location IN ('macos_keychain', 'icloud_keychain', 'paper_backup', 'custom')),
    stored_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_verified_at DATETIME
);
```

---

## Recovery Testing Strategy

### Automated Tests
```rust
#[cfg(test)]
mod tests {
    #[test]
    fn test_bip39_deterministic() {
        // Same mnemonic always produces same key
        let mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
        let key1 = KeyDerivation::derive_master_key(&Mnemonic::from_phrase(mnemonic, Language::English).unwrap(), None).unwrap();
        let key2 = KeyDerivation::derive_master_key(&Mnemonic::from_phrase(mnemonic, Language::English).unwrap(), None).unwrap();
        assert_eq!(key1, key2);
    }
    
    #[test]
    fn test_shamir_2_of_3() {
        let key = [42u8; 32];
        let shares = ShamirSplitter::split_key(&key, 2, 3).unwrap();
        
        // Any 2 shares reconstruct original key
        let recovered1 = ShamirSplitter::reconstruct_key(&shares[0..2]).unwrap();
        let recovered2 = ShamirSplitter::reconstruct_key(&shares[1..3]).unwrap();
        
        assert_eq!(key, recovered1);
        assert_eq!(key, recovered2);
    }
    
    #[test]
    fn test_insufficient_shares_fails() {
        let key = [42u8; 32];
        let shares = ShamirSplitter::split_key(&key, 2, 3).unwrap();
        
        // 1 share cannot reconstruct
        let result = ShamirSplitter::reconstruct_key(&shares[0..1]);
        assert!(result.is_err());
    }
}
```

### Manual Recovery Drill
1. Initialize new vault on Device A
2. Write down 24-word mnemonic
3. Wipe Device A (simulate loss)
4. Setup new macOS on Device B
5. Recover vault using mnemonic
6. Verify all encrypted data accessible

---

## Migration from Existing Vaults

```rust
impl VaultInitializer {
    /// Migrate existing keychain-only vault to BIP-39 backup
    pub async fn migrate_to_bip39(
        &self,
        existing_master_key: &[u8; 32],
    ) -> Result<VaultInitResult, VaultError> {
        // Generate new BIP-39 mnemonic
        let mnemonic = MnemonicGenerator::generate_24_word()?;
        let new_master_key = KeyDerivation::derive_master_key(&mnemonic, None)?;
        
        // Re-encrypt all vault entries with new key
        self.re_encrypt_vault_entries(existing_master_key, &new_master_key).await?;
        
        // Generate Shamir shares
        let shares = ShamirSplitter::split_key(&new_master_key, 2, 3)?;
        
        // ... (rest of init flow)
        
        info!("Vault migrated to BIP-39 recovery");
        
        Ok(VaultInitResult { /* ... */ })
    }
}
```

---

## Crate Dependencies

```toml
[dependencies]
bip39 = "2.0"              # BIP-39 mnemonic generation
sharks = "0.5"             # Shamir Secret Sharing
pbkdf2 = "0.12"
sha2 = "0.10"
base32 = "0.4"
qrcode = "0.13"            # QR code generation for shares
keyring = "2.3"            # OS keychain integration
```

---

## Benefits

1. **Zero Trust Recovery**: No reliance on single hardware device or cloud service
2. **User Sovereignty**: 12/24-word phrase is human-memorable and universally recoverable
3. **Threshold Security**: Lose 1 share, still recoverable; attacker needs K shares
4. **Standard Compliance**: BIP-39 compatible with hardware wallets (Ledger, Trezor)
5. **Paper Backup**: QR code shares printable for offline storage

---

## Related Gaps

- **GAP-001** (CRDT Sync): Device authentication uses derived signing keys
- **GAP-004** (Privacy): Mnemonic never sent to LLM for any reason
- **GAP-008** (Sandboxing): Recovery flow requires elevated permissions

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Implement `BIP39Generator` and `ShamirSplitter` in `pos_vault/src/recovery.rs`
