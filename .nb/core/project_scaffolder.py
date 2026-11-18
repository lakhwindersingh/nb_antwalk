"""
Neutron Binary Percipience - One-Click Project Scaffolding Wizard (CAP-40 / TODO-PRT-02)
Automates the instant provisioning of new enterprise customer projects:
  - Generates standard Quad-Space layouts (.nb/context, .nb/agentic, workplace, user)
  - Initializes isolated context_ledger.yaml & context_ledger.public.yaml
  - Mints genesis cryptographic recovery block: RP_GENESIS_000
  - Provisions automated KMS keypairs (Ed25519) and symmetric ciphers (AES-256-GCM) via KMSBroker
  - Enforces tenant isolation and registers the project in TenantManager
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
import datetime
import hashlib
import json
import os
from pathlib import Path
import yaml

from .tenant_manager import TenantManager, Project, TenantRole
from .kms_broker import KMSBroker


@dataclass
class ScaffoldResult:
    status: str
    tenant_id: str
    project_id: str
    project_name: str
    mode: str
    billing_tier: str
    target_dir: str
    genesis_recovery_point: str
    genesis_merkle_hash: str
    kms_key_id: str
    created_directories: List[str] = field(default_factory=list)
    created_files: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProjectScaffolder:
    """
    Automated Wizard for Scaffolding Quad-Space Project Topologies with
    Merkle Chain Genesis Block and KMS Key Initialization.
    """

    def __init__(
        self,
        tenant_manager: Optional[TenantManager] = None,
        kms_broker: Optional[KMSBroker] = None
    ):
        self.tenant_manager = tenant_manager or TenantManager()
        self.kms_broker = kms_broker or KMSBroker()

    def scaffold_project(
        self,
        tenant_id: str,
        project_id: str,
        project_name: str,
        target_dir: Path,
        mode: str = "multi_module",  # single_module, multi_module
        billing_tier: str = "plan_enterprise",
        admin_user_id: Optional[str] = None,
        template_type: str = "enterprise_saas",
        initial_module_name: str = "mod_core_service"
    ) -> ScaffoldResult:
        """
        Executes one-click Quad-Space scaffolding into target_dir.
        """
        target_dir = Path(target_dir).resolve()

        # 1. Verify Authorization if admin_user_id provided
        if admin_user_id:
            authorized, reason = self.tenant_manager.authorize(
                user_id=admin_user_id,
                action="project:scaffold",
                tenant_id=tenant_id
            )
            if not authorized:
                raise PermissionError(f"Scaffolding Denied: {reason}")

        # 2. Register or verify tenant & project in TenantManager
        if not self.tenant_manager.get_tenant(tenant_id):
            self.tenant_manager.create_tenant(
                tenant_id=tenant_id,
                name=f"Tenant {tenant_id}",
                tier=billing_tier
            )

        project = self.tenant_manager.get_project(project_id)
        if not project:
            project = self.tenant_manager.create_project(
                tenant_id=tenant_id,
                project_id=project_id,
                name=project_name,
                mode=mode,
                billing_tier=billing_tier
            )

        created_dirs: List[str] = []
        created_files: List[str] = []

        def _mkdir(p: Path):
            p.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(p.relative_to(target_dir)))

        def _write(p: Path, content: str):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            created_files.append(str(p.relative_to(target_dir)))

        # 3. Create Quad-Space Directory Hierarchy
        # 3a. .nb / Context Space (contracts, ledgers, rules)
        _mkdir(target_dir / ".nb" / "context" / "contracts")
        _mkdir(target_dir / ".nb" / "context" / "ledger")
        _mkdir(target_dir / ".nb" / "context" / "rules")
        _mkdir(target_dir / ".nb" / "config")
        _mkdir(target_dir / ".nb" / "bin")

        # 3b. .nb / Agentic Space (prompts, workflows)
        _mkdir(target_dir / ".nb" / "agentic" / "prompts")
        _mkdir(target_dir / ".nb" / "agentic" / "workflows")

        # 3c. Workplace Space (customer code, configs, tests, docs)
        if mode == "multi_module":
            _mkdir(target_dir / "workplace" / "modules" / initial_module_name / "src")
            _mkdir(target_dir / "workplace" / "modules" / initial_module_name / "tests")
            _mkdir(target_dir / "workplace" / "shared")
        else:
            _mkdir(target_dir / "workplace" / "src")
            _mkdir(target_dir / "workplace" / "tests")

        _mkdir(target_dir / "workplace" / "config")
        _mkdir(target_dir / "workplace" / "docs")

        # 3d. User Space (inputs, hitl quarantine, outputs/dashboards)
        _mkdir(target_dir / "user" / "inputs" / "specs")
        _mkdir(target_dir / "user" / "inputs" / "templates")
        _mkdir(target_dir / "user" / "hitl")
        _mkdir(target_dir / "user" / "outputs" / "dashboard")

        # 4. Mint Cryptographic Genesis Recovery Block: RP_GENESIS_000
        genesis_rp_id = "RP_GENESIS_000"
        genesis_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        prev_root = "0" * 64

        genesis_block_meta = {
            "block_height": 0,
            "recovery_point_id": genesis_rp_id,
            "action": "PROJECT_GENESIS_SCAFFOLDED",
            "tenant_id": tenant_id,
            "project_id": project_id,
            "project_name": project_name,
            "mode": mode,
            "billing_tier": billing_tier,
            "timestamp": genesis_timestamp,
            "previous_merkle_root": prev_root
        }
        genesis_merkle_hash = hashlib.sha256(
            json.dumps(genesis_block_meta, sort_keys=True).encode("utf-8")
        ).hexdigest()

        # 5. Populate context_ledger.yaml
        ledger_content = {
            "ledger_version": "8.0.0",
            "tenant_id": tenant_id,
            "project_id": project_id,
            "project_name": project_name,
            "mode": mode,
            "billing_tier": billing_tier,
            "genesis_sealed_at": genesis_timestamp,
            "merkle_chain": [
                {
                    "block_height": 0,
                    "recovery_point_id": genesis_rp_id,
                    "action": "PROJECT_GENESIS_SCAFFOLDED",
                    "timestamp": genesis_timestamp,
                    "merkle_block_hash": genesis_merkle_hash,
                    "previous_merkle_root": prev_root,
                    "details": {
                        "initial_topology": f"Quad-Space ({mode})",
                        "scaffold_template": template_type
                    }
                }
            ],
            "recovery_points": [
                {
                    "id": genesis_rp_id,
                    "block_height": 0,
                    "merkle_block_hash": genesis_merkle_hash,
                    "commit_sha": "0000000000000000000000000000000000000000",
                    "module_scope": "global_system",
                    "created_at": genesis_timestamp,
                    "description": "Genesis project state scaffolded via One-Click Wizard."
                }
            ],
            "quarantines": []
        }
        _write(
            target_dir / ".nb" / "context" / "ledger" / "context_ledger.yaml",
            yaml.dump(ledger_content, sort_keys=False)
        )

        # Public sanitized ledger
        public_ledger = {
            "ledger_version": "8.0.0",
            "tenant_id": tenant_id,
            "project_id": project_id,
            "merkle_height": 0,
            "latest_merkle_root": genesis_merkle_hash,
            "active_recovery_point": genesis_rp_id,
            "quarantined_issues_count": 0,
            "last_verified_at": genesis_timestamp
        }
        _write(
            target_dir / ".nb" / "context" / "ledger" / "context_ledger.public.yaml",
            yaml.dump(public_ledger, sort_keys=False)
        )

        # 6. Scaffold Wire Contract Skeletons
        service_contract = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "contract_id": f"contract_{project_id}_service_v1",
            "schema_version": "1.0.0",
            "tenant_id": tenant_id,
            "project_id": project_id,
            "title": f"{project_name} Service Interface Contract",
            "type": "object",
            "required": ["request_id", "timestamp", "payload"],
            "properties": {
                "request_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "payload": {"type": "object"}
            }
        }
        _write(
            target_dir / ".nb" / "context" / "contracts" / "service_contract.json",
            json.dumps(service_contract, indent=2)
        )

        # 7. Scaffold Invariant Rules
        rules_markdown = f"""# Project Security & Architecture Invariants
**Tenant**: `{tenant_id}` | **Project**: `{project_id}`

## 1. Non-Negotiable Boundaries
- **Tenant Isolation**: All operations must execute strictly within tenant context `{tenant_id}`.
- **Merkle Ledger Immutability**: All state transitions must seal a SHA-256 block into `.nb/context/ledger/context_ledger.yaml`.
- **Contract Adherence**: Module changes must pass validation against `.nb/context/contracts/service_contract.json`.
- **Zero Raw Plaintext Leaks**: Enclave assets (.nbpack) must hydrate into volatile memory with zero disk leakage.
"""
        _write(target_dir / ".nb" / "context" / "rules" / "security_invariants.md", rules_markdown)

        # 8. Scaffold Project Configuration
        project_config = {
            "project": {
                "tenant_id": tenant_id,
                "project_id": project_id,
                "name": project_name,
                "mode": mode,
                "billing_tier": billing_tier,
                "created_at": genesis_timestamp
            },
            "context_engineering": {
                "attention_budget": {
                    "invariants_pct": 15,
                    "contracts_pct": 25,
                    "ast_symbols_pct": 35,
                    "agent_memory_pct": 10,
                    "output_buffer_pct": 15
                },
                "cognitive_routing": {
                    "tier_a_threshold": 0.75,
                    "fallback_model": "claude-3-5-sonnet-20241022"
                }
            }
        }
        _write(
            target_dir / ".nb" / "config" / "project_config.yaml",
            yaml.dump(project_config, sort_keys=False)
        )

        # 9. Scaffold Autonomous CI/CD Workflow
        cicd_workflow = {
            "workflow_id": "basic_autonomous_cicd",
            "version": "1.0.0",
            "tenant_id": tenant_id,
            "project_id": project_id,
            "steps": [
                {"step_id": "sustain_maintenance", "action": "audit_and_reconcile"},
                {"step_id": "ast_token_reduction", "action": "prune_source_ast"},
                {"step_id": "contract_and_test_gate", "action": "verify_contracts_and_tests"},
                {"step_id": "bounded_auto_heal", "action": "self_heal", "max_retries": 1},
                {"step_id": "merkle_state_seal", "action": "commit_and_seal_merkle"}
            ]
        }
        _write(
            target_dir / ".nb" / "agentic" / "workflows" / "basic_autonomous_cicd.yaml",
            yaml.dump(cicd_workflow, sort_keys=False)
        )

        # 10. Provision Automated KMS Keys
        kms_key = self.kms_broker.provision_project_keys(tenant_id=tenant_id, project_id=project_id)

        # 11. Register local workstation node in TenantManager
        local_node_id = f"node_{project_id}_local"
        self.tenant_manager.register_workspace_node(
            tenant_id=tenant_id,
            project_id=project_id,
            node_id=local_node_id,
            hostname=os.uname().nodename if hasattr(os, "uname") else "local-host",
            worktree_path=str(target_dir),
            metadata={"scaffolded_by": admin_user_id or "system"}
        )

        return ScaffoldResult(
            status="SUCCESS",
            tenant_id=tenant_id,
            project_id=project_id,
            project_name=project_name,
            mode=mode,
            billing_tier=billing_tier,
            target_dir=str(target_dir),
            genesis_recovery_point=genesis_rp_id,
            genesis_merkle_hash=genesis_merkle_hash,
            kms_key_id=kms_key.key_id,
            created_directories=created_dirs,
            created_files=created_files
        )
