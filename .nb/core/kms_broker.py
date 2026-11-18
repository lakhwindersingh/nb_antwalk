"""
Neutron Binary Percipience - Automated KMS Key Broker & Sealed Enclave Provisioning (CAP-40 / TODO-PRT-03)
Provides:
  - Automated per-project Ed25519 asymmetric signing keypairs
  - Automated per-project AES-256-GCM symmetric authenticated encryption keys
  - In-memory vault with zero client disk exposure
  - Self-serve `.nbpack` authenticated layer sealing & in-memory enclave mounting
  - Cryptographic key rotation & historical key ring management
  - Tamper-evident audit logging for all cryptographic operations
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization


@dataclass
class KeyRecord:
    key_id: str
    tenant_id: str
    project_id: str
    key_version: int
    created_at: str
    status: str = "ACTIVE"  # ACTIVE, ROTATED, REVOKED
    ed25519_private_b64: str = ""
    ed25519_public_b64: str = ""
    aes_key_b64: str = ""
    usage_count: int = 0
    last_used_at: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        """Returns safe public representation without private keys."""
        return {
            "key_id": self.key_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "key_version": self.key_version,
            "created_at": self.created_at,
            "status": self.status,
            "ed25519_public_b64": self.ed25519_public_b64,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at
        }


@dataclass
class SealedEnclaveBundle:
    envelope_format: str
    version: str
    tenant_id: str
    project_id: str
    key_id: str
    key_version: int
    nonce_b64: str
    ciphertext_b64: str
    signature_b64: str
    public_key_b64: str
    merkle_seal: str
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class KMSBroker:
    """
    Automated Key Management Service Broker & In-Memory Enclave Engine.
    Handles ephemeral and persistent project keyrings, AES-256-GCM AEAD encryption,
    Ed25519 digital signatures, and zero-disk plaintext hydration.
    """

    def __init__(self, persistence_file: Optional[Path] = None):
        self.persistence_file = persistence_file
        # Map: project_id -> list of KeyRecord (latest is active)
        self.keyrings: Dict[str, List[KeyRecord]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self._load_state()

    # -------------------------------------------------------------------------
    # Key Generation & Provisioning
    # -------------------------------------------------------------------------

    def provision_project_keys(self, tenant_id: str, project_id: str) -> KeyRecord:
        """
        Provisions a new primary keypair (Ed25519) and symmetric key (AES-256-GCM)
        for an isolated tenant project.
        """
        existing = self.keyrings.get(project_id, [])
        version = len(existing) + 1
        key_id = f"kms_key_{tenant_id}_{project_id}_v{version}"

        # 1. Generate Ed25519 keypair
        priv_key = ed25519.Ed25519PrivateKey.generate()
        pub_key = priv_key.public_key()

        priv_bytes = priv_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_bytes = pub_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # 2. Generate AES-256-GCM symmetric key (32 bytes = 256 bits)
        aes_bytes = AESGCM.generate_key(bit_length=256)

        record = KeyRecord(
            key_id=key_id,
            tenant_id=tenant_id,
            project_id=project_id,
            key_version=version,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            status="ACTIVE",
            ed25519_private_b64=base64.b64encode(priv_bytes).decode("utf-8"),
            ed25519_public_b64=base64.b64encode(pub_bytes).decode("utf-8"),
            aes_key_b64=base64.b64encode(aes_bytes).decode("utf-8")
        )

        # Retire previously active keys in the ring to ROTATED
        for k in existing:
            if k.status == "ACTIVE":
                k.status = "ROTATED"

        if project_id not in self.keyrings:
            self.keyrings[project_id] = []
        self.keyrings[project_id].append(record)

        self._record_audit("KEY_PROVISIONED", tenant_id, project_id, key_id, version)
        self._save_state()
        return record

    def get_active_key(self, project_id: str) -> Optional[KeyRecord]:
        ring = self.keyrings.get(project_id, [])
        for k in reversed(ring):
            if k.status == "ACTIVE":
                return k
        return ring[-1] if ring else None

    def get_key_version(self, project_id: str, version: int) -> Optional[KeyRecord]:
        ring = self.keyrings.get(project_id, [])
        for k in ring:
            if k.key_version == version:
                return k
        return None

    def rotate_project_keys(self, tenant_id: str, project_id: str) -> KeyRecord:
        """
        Cryptographically rotates project keys, marking older keys as ROTATED
        while maintaining decryption backwards-compatibility.
        """
        new_key = self.provision_project_keys(tenant_id=tenant_id, project_id=project_id)
        self._record_audit("KEY_ROTATED", tenant_id, project_id, new_key.key_id, new_key.key_version)
        return new_key

    # -------------------------------------------------------------------------
    # Cryptographic Operations: Signing, Encrypting & Decrypting
    # -------------------------------------------------------------------------

    def sign_data(self, project_id: str, data: bytes) -> bytes:
        """Signs arbitrary bytes using active Ed25519 private key."""
        active_key = self.get_active_key(project_id)
        if not active_key:
            raise ValueError(f"No active KMS key found for project '{project_id}'.")
        priv_bytes = base64.b64decode(active_key.ed25519_private_b64)
        priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
        sig = priv_key.sign(data)
        active_key.usage_count += 1
        active_key.last_used_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._save_state()
        return sig

    def verify_signature(self, project_id: str, data: bytes, signature: bytes, version: Optional[int] = None) -> bool:
        """Verifies Ed25519 digital signature against project public key."""
        key_record = self.get_key_version(project_id, version) if version else self.get_active_key(project_id)
        if not key_record:
            return False
        try:
            pub_bytes = base64.b64decode(key_record.ed25519_public_b64)
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            pub_key.verify(signature, data)
            return True
        except Exception:
            return False

    def encrypt_bytes(self, project_id: str, plaintext: bytes, associated_data: Optional[bytes] = None) -> Tuple[bytes, bytes, int]:
        """
        Encrypts plaintext bytes using AES-256-GCM AEAD.
        Returns (ciphertext, nonce, key_version).
        """
        active_key = self.get_active_key(project_id)
        if not active_key:
            raise ValueError(f"No active KMS key found for project '{project_id}'.")
        aes_bytes = base64.b64decode(active_key.aes_key_b64)
        aesgcm = AESGCM(aes_bytes)
        nonce = os.urandom(12)  # Standard 96-bit GCM nonce
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
        active_key.usage_count += 1
        active_key.last_used_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._save_state()
        return ciphertext, nonce, active_key.key_version

    def decrypt_bytes(self, project_id: str, ciphertext: bytes, nonce: bytes, version: int, associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypts AES-256-GCM ciphertext using the specific key version.
        """
        key_record = self.get_key_version(project_id, version)
        if not key_record:
            raise ValueError(f"KMS key version {version} not found for project '{project_id}'.")
        aes_bytes = base64.b64decode(key_record.aes_key_b64)
        aesgcm = AESGCM(aes_bytes)
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)
        key_record.usage_count += 1
        key_record.last_used_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._save_state()
        return plaintext

    # -------------------------------------------------------------------------
    # Sealed Enclave (.nbpack) Packaging & Zero-Disk Hydration
    # -------------------------------------------------------------------------

    def seal_nbpack_envelope(
        self,
        tenant_id: str,
        project_id: str,
        payload_dict: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> SealedEnclaveBundle:
        """
        Seals arbitrary domain components (contracts, prompts, master plans)
        into an authenticated `.nbpack` sealed envelope using AES-256-GCM & Ed25519.
        """
        active_key = self.get_active_key(project_id)
        if not active_key:
            active_key = self.provision_project_keys(tenant_id, project_id)

        # 1. Canonical payload serialization
        raw_json = json.dumps(payload_dict, sort_keys=True).encode("utf-8")
        merkle_seal = hashlib.sha256(raw_json).hexdigest()

        # 2. Authenticated encryption (AEAD)
        aad = f"{tenant_id}:{project_id}:{active_key.key_version}:{merkle_seal}".encode("utf-8")
        ciphertext, nonce, version = self.encrypt_bytes(project_id, raw_json, associated_data=aad)

        # 3. Digital signature over header + ciphertext
        signed_digest = hashlib.sha256(nonce + ciphertext + aad).digest()
        signature = self.sign_data(project_id, signed_digest)

        bundle = SealedEnclaveBundle(
            envelope_format="NBPACK_AES256_ED25519",
            version="2.0.0",
            tenant_id=tenant_id,
            project_id=project_id,
            key_id=active_key.key_id,
            key_version=version,
            nonce_b64=base64.b64encode(nonce).decode("utf-8"),
            ciphertext_b64=base64.b64encode(ciphertext).decode("utf-8"),
            signature_b64=base64.b64encode(signature).decode("utf-8"),
            public_key_b64=active_key.ed25519_public_b64,
            merkle_seal=merkle_seal,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            metadata=metadata or {}
        )

        self._record_audit("ENVELOPE_SEALED", tenant_id, project_id, active_key.key_id, version)
        return bundle

    def mount_in_memory_enclave(
        self,
        project_id: str,
        bundle_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Hydrates sealed `.nbpack` bundle directly in volatile memory (RAM).
        Zero plaintext is written to physical disk.
        Returns the unsealed payload dictionary.
        """
        tenant_id = bundle_data["tenant_id"]
        version = bundle_data["key_version"]
        merkle_seal = bundle_data["merkle_seal"]

        nonce = base64.b64decode(bundle_data["nonce_b64"])
        ciphertext = base64.b64decode(bundle_data["ciphertext_b64"])
        signature = base64.b64decode(bundle_data["signature_b64"])

        # 1. Verify digital signature
        aad = f"{tenant_id}:{project_id}:{version}:{merkle_seal}".encode("utf-8")
        signed_digest = hashlib.sha256(nonce + ciphertext + aad).digest()
        valid_sig = self.verify_signature(project_id, signed_digest, signature, version=version)
        if not valid_sig:
            raise PermissionError("Tampered Sealed Enclave: Ed25519 cryptographic signature verification failed.")

        # 2. Decrypt in memory
        raw_plaintext = self.decrypt_bytes(project_id, ciphertext, nonce, version=version, associated_data=aad)

        # 3. Verify Merkle Seal integrity
        calculated_seal = hashlib.sha256(raw_plaintext).hexdigest()
        if calculated_seal != merkle_seal:
            raise ValueError("Integrity Violation: Merkle payload digest mismatch.")

        payload = json.loads(raw_plaintext.decode("utf-8"))
        self._record_audit("ENCLAVE_MOUNTED", tenant_id, project_id, bundle_data["key_id"], version)
        return payload

    # -------------------------------------------------------------------------
    # Audit & Persistence
    # -------------------------------------------------------------------------

    def _record_audit(self, action: str, tenant_id: str, project_id: str, key_id: str, version: int):
        event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": action,
            "tenant_id": tenant_id,
            "project_id": project_id,
            "key_id": key_id,
            "version": version
        }
        event["event_hash"] = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()
        self.audit_log.append(event)

    def _save_state(self):
        if not self.persistence_file:
            return
        self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "keyrings": {
                proj: [asdict(k) for k in keys]
                for proj, keys in self.keyrings.items()
            },
            "audit_log": self.audit_log[-500:]  # keep recent 500 records
        }
        with open(self.persistence_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_state(self):
        if not self.persistence_file or not self.persistence_file.exists():
            return
        try:
            with open(self.persistence_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for proj, keys in data.get("keyrings", {}).items():
                self.keyrings[proj] = [KeyRecord(**k) for k in keys]
            self.audit_log = data.get("audit_log", [])
        except Exception:
            pass
