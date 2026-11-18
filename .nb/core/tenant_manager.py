"""
Neutron Binary Percipience - Multi-Tenant Organization & Project Hierarchy Manager (CAP-40 / TODO-PRT-01)
Enforces hierarchical tenant isolation:
  Organization (Tenant) -> Projects -> Repositories -> Workspaces / Nodes
Provides:
  - Tenant-scoped PostgreSQL RLS (Row-Level Security) schemas & policy generator
  - RBAC Authorization Engine (Enterprise Super Admin, Project Lead, Security Auditor, Agent Worker)
  - In-memory and file-backed tenant hierarchy governance
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
import datetime
import hashlib
import json
import os
from pathlib import Path


class TenantRole(str, Enum):
    ENTERPRISE_SUPER_ADMIN = "ENTERPRISE_SUPER_ADMIN"
    PROJECT_LEAD = "PROJECT_LEAD"
    SECURITY_AUDITOR = "SECURITY_AUDITOR"
    AGENT_WORKER = "AGENT_WORKER"


# Permission catalog definition
ROLE_PERMISSIONS: Dict[TenantRole, Set[str]] = {
    TenantRole.ENTERPRISE_SUPER_ADMIN: {
        "tenant:create", "tenant:read", "tenant:update", "tenant:delete", "tenant:manage",
        "project:create", "project:read", "project:update", "project:delete", "project:scaffold",
        "repo:create", "repo:read", "repo:update", "repo:delete",
        "node:register", "node:read", "node:manage", "node:evict", "node:heartbeat", "node:telemetry",
        "user:assign", "user:revoke", "user:read",
        "kms:manage", "kms:rotate", "kms:seal", "kms:mount",
        "audit:read", "merkle:verify", "worm:read", "quarantine:read", "quarantine:resolve",
        "policy:read", "policy:write", "cicd:run", "rollback:execute"
    },
    TenantRole.PROJECT_LEAD: {
        "tenant:read",
        "project:create", "project:read", "project:update", "project:scaffold",
        "repo:create", "repo:read", "repo:update",
        "node:register", "node:read", "node:manage", "node:heartbeat", "node:telemetry",
        "user:read",
        "kms:seal", "kms:mount",
        "audit:read", "merkle:verify", "worm:read", "quarantine:read",
        "policy:read", "policy:write", "cicd:run", "rollback:execute"
    },
    TenantRole.SECURITY_AUDITOR: {
        "tenant:read",
        "project:read",
        "repo:read",
        "node:read",
        "user:read",
        "audit:read", "merkle:verify", "worm:read", "quarantine:read",
        "policy:read"
    },
    TenantRole.AGENT_WORKER: {
        "tenant:read",
        "project:read",
        "repo:read",
        "node:register", "node:read", "node:heartbeat", "node:telemetry",
        "worktree:lease", "worktree:execute",
        "ast:prune", "tokens:track", "cicd:run", "kms:seal"
    }
}


@dataclass
class WorkspaceNode:
    node_id: str
    project_id: str
    tenant_id: str
    hostname: str
    ip_address: str = "127.0.0.1"
    os_info: str = "macOS/Linux"
    worktree_path: str = ""
    status: str = "HEALTHY"  # HEALTHY, HEALING, OFFLINE, QUARANTINED
    last_heartbeat: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Repository:
    repo_id: str
    project_id: str
    tenant_id: str
    name: str
    url: str
    auth_type: str = "ssh_key"  # ssh_key, bearer_token, github_app
    default_branch: str = "main"
    status: str = "CONNECTED"
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Project:
    project_id: str
    tenant_id: str
    name: str
    slug: str
    mode: str = "multi_module"  # single_module, multi_module
    billing_tier: str = "plan_enterprise"  # plan_free, plan_team, plan_business, plan_enterprise
    status: str = "ACTIVE"
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    repositories: List[str] = field(default_factory=list)  # list of repo_ids
    workspace_nodes: List[str] = field(default_factory=list)  # list of node_ids
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TenantUser:
    user_id: str
    tenant_id: str
    email: str
    display_name: str
    role: TenantRole
    project_assignments: List[str] = field(default_factory=lambda: ["*"])  # ["*"] or list of project_ids
    api_key_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["role"] = self.role.value
        return d


@dataclass
class Tenant:
    tenant_id: str
    name: str
    slug: str
    tier: str = "plan_enterprise"
    status: str = "ACTIVE"  # ACTIVE, SUSPENDED, PROVISIONING
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TenantManager:
    """
    Hierarchical Tenant Isolation and RBAC Engine.
    Manages Organization (Tenant) -> Projects -> Repositories -> Workspaces/Nodes hierarchy,
    evaluates RBAC authorization matrix, and generates PostgreSQL RLS DDL schemas.
    """

    def __init__(self, persistence_file: Optional[Path] = None):
        self.persistence_file = persistence_file
        self.tenants: Dict[str, Tenant] = {}
        self.projects: Dict[str, Project] = {}
        self.repositories: Dict[str, Repository] = {}
        self.workspace_nodes: Dict[str, WorkspaceNode] = {}
        self.users: Dict[str, TenantUser] = {}
        self._load_state()

    # -------------------------------------------------------------------------
    # Tenant Lifecycle
    # -------------------------------------------------------------------------

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        tier: str = "plan_enterprise",
        settings: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        if tenant_id in self.tenants:
            raise ValueError(f"Tenant '{tenant_id}' already exists.")
        slug = name.lower().replace(" ", "-").replace("_", "-")
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            tier=tier,
            settings=settings or {},
            metadata=metadata or {}
        )
        self.tenants[tenant_id] = tenant
        self._save_state()
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.tenants.get(tenant_id)

    def list_tenants(self) -> List[Tenant]:
        return list(self.tenants.values())

    # -------------------------------------------------------------------------
    # Project Lifecycle
    # -------------------------------------------------------------------------

    def create_project(
        self,
        tenant_id: str,
        project_id: str,
        name: str,
        mode: str = "multi_module",
        billing_tier: str = "plan_enterprise",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Project:
        if tenant_id not in self.tenants:
            raise ValueError(f"Parent tenant '{tenant_id}' does not exist.")
        if project_id in self.projects:
            raise ValueError(f"Project '{project_id}' already exists.")
        slug = name.lower().replace(" ", "-").replace("_", "-")
        project = Project(
            project_id=project_id,
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            mode=mode,
            billing_tier=billing_tier,
            metadata=metadata or {}
        )
        self.projects[project_id] = project
        self._save_state()
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        return self.projects.get(project_id)

    def list_projects(self, tenant_id: Optional[str] = None) -> List[Project]:
        if tenant_id:
            return [p for p in self.projects.values() if p.tenant_id == tenant_id]
        return list(self.projects.values())

    # -------------------------------------------------------------------------
    # Repository Lifecycle
    # -------------------------------------------------------------------------

    def register_repository(
        self,
        tenant_id: str,
        project_id: str,
        repo_id: str,
        name: str,
        url: str,
        auth_type: str = "ssh_key",
        default_branch: str = "main"
    ) -> Repository:
        project = self.projects.get(project_id)
        if not project or project.tenant_id != tenant_id:
            raise ValueError(f"Project '{project_id}' not found under tenant '{tenant_id}'.")
        if repo_id in self.repositories:
            raise ValueError(f"Repository '{repo_id}' already exists.")
        repo = Repository(
            repo_id=repo_id,
            project_id=project_id,
            tenant_id=tenant_id,
            name=name,
            url=url,
            auth_type=auth_type,
            default_branch=default_branch
        )
        self.repositories[repo_id] = repo
        if repo_id not in project.repositories:
            project.repositories.append(repo_id)
        self._save_state()
        return repo

    def list_repositories(self, project_id: Optional[str] = None) -> List[Repository]:
        if project_id:
            return [r for r in self.repositories.values() if r.project_id == project_id]
        return list(self.repositories.values())

    # -------------------------------------------------------------------------
    # Workspace / Fleet Node Lifecycle
    # -------------------------------------------------------------------------

    def register_workspace_node(
        self,
        tenant_id: str,
        project_id: str,
        node_id: str,
        hostname: str,
        ip_address: str = "127.0.0.1",
        worktree_path: str = "",
        os_info: str = "macOS/Linux",
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkspaceNode:
        project = self.projects.get(project_id)
        if not project or project.tenant_id != tenant_id:
            raise ValueError(f"Project '{project_id}' not found under tenant '{tenant_id}'.")
        node = WorkspaceNode(
            node_id=node_id,
            project_id=project_id,
            tenant_id=tenant_id,
            hostname=hostname,
            ip_address=ip_address,
            os_info=os_info,
            worktree_path=worktree_path,
            metadata=metadata or {}
        )
        self.workspace_nodes[node_id] = node
        if node_id not in project.workspace_nodes:
            project.workspace_nodes.append(node_id)
        self._save_state()
        return node

    def update_node_heartbeat(self, node_id: str, status: str = "HEALTHY", metadata_patch: Optional[Dict[str, Any]] = None) -> Optional[WorkspaceNode]:
        node = self.workspace_nodes.get(node_id)
        if not node:
            return None
        node.status = status
        node.last_heartbeat = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if metadata_patch:
            node.metadata.update(metadata_patch)
        self._save_state()
        return node

    def list_nodes(self, project_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[WorkspaceNode]:
        res = list(self.workspace_nodes.values())
        if tenant_id:
            res = [n for n in res if n.tenant_id == tenant_id]
        if project_id:
            res = [n for n in res if n.project_id == project_id]
        return res

    # -------------------------------------------------------------------------
    # User & IAM Lifecycle
    # -------------------------------------------------------------------------

    def register_user(
        self,
        tenant_id: str,
        user_id: str,
        email: str,
        display_name: str,
        role: TenantRole,
        project_assignments: Optional[List[str]] = None,
        api_key: Optional[str] = None
    ) -> TenantUser:
        if tenant_id not in self.tenants:
            raise ValueError(f"Tenant '{tenant_id}' does not exist.")
        key_hash = hashlib.sha256(api_key.encode()).hexdigest() if api_key else ""
        user = TenantUser(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            display_name=display_name,
            role=role,
            project_assignments=project_assignments or ["*"],
            api_key_hash=key_hash
        )
        self.users[user_id] = user
        self._save_state()
        return user

    def get_user(self, user_id: str) -> Optional[TenantUser]:
        return self.users.get(user_id)

    # -------------------------------------------------------------------------
    # RBAC Authorization Engine
    # -------------------------------------------------------------------------

    def authorize(
        self,
        user_id: str,
        action: str,
        tenant_id: str,
        project_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Evaluates RBAC authorization for a given action on a tenant and optional project.
        Returns (is_authorized, reason).
        """
        user = self.users.get(user_id)
        if not user:
            return False, f"User '{user_id}' is not registered."

        # Super admin can operate across enterprise or assigned tenant
        if user.role == TenantRole.ENTERPRISE_SUPER_ADMIN:
            allowed = action in ROLE_PERMISSIONS[user.role]
            if not allowed:
                return False, f"Action '{action}' is not permitted even for Super Admin."
            return True, "Authorized via Enterprise Super Admin role."

        # Tenant isolation check
        if user.tenant_id != tenant_id:
            return False, f"User tenant '{user.tenant_id}' does not match target tenant '{tenant_id}'."

        # Permission matrix check
        role_actions = ROLE_PERMISSIONS.get(user.role, set())
        if action not in role_actions:
            return False, f"Role '{user.role.value}' does not have permission '{action}'."

        # Project boundary check
        if project_id and "*" not in user.project_assignments:
            if project_id not in user.project_assignments:
                return False, f"User is not assigned to project '{project_id}'."

        return True, f"Authorized via role '{user.role.value}'."

    # -------------------------------------------------------------------------
    # Hierarchical Tree Explorer
    # -------------------------------------------------------------------------

    def get_tenant_hierarchy(self, tenant_id: str) -> Dict[str, Any]:
        """
        Constructs the full hierarchical tree:
        Tenant -> Projects -> Repositories & Workspaces / Nodes
        """
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant '{tenant_id}' does not exist.")

        proj_list = []
        for p in self.list_projects(tenant_id=tenant_id):
            repos = [r.to_dict() for r in self.list_repositories(project_id=p.project_id)]
            nodes = [n.to_dict() for n in self.list_nodes(project_id=p.project_id)]
            proj_list.append({
                "project": p.to_dict(),
                "repositories": repos,
                "workspace_nodes": nodes,
                "counts": {
                    "repositories": len(repos),
                    "active_nodes": len([n for n in nodes if n["status"] == "HEALTHY"]),
                    "total_nodes": len(nodes)
                }
            })

        tenant_users = [u.to_dict() for u in self.users.values() if u.tenant_id == tenant_id]

        return {
            "tenant": tenant.to_dict(),
            "projects": proj_list,
            "users": tenant_users,
            "summary": {
                "total_projects": len(proj_list),
                "total_users": len(tenant_users),
                "total_nodes": sum(len(p["workspace_nodes"]) for p in proj_list)
            }
        }

    # -------------------------------------------------------------------------
    # PostgreSQL Row-Level Security (RLS) Generator & Simulator
    # -------------------------------------------------------------------------

    @staticmethod
    def generate_rls_sql_schema() -> str:
        """
        Generates production PostgreSQL DDL and Row-Level Security (RLS) policies
        enforcing strict tenant isolation across all enterprise persistence tables.
        """
        return """-- ============================================================================
-- Neutron Binary Percipience - Multi-Tenant PostgreSQL RLS Schema
-- Enforces absolute cryptographic and relational tenant isolation.
-- ============================================================================

-- 1. Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(64) NOT NULL DEFAULT 'plan_enterprise',
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- 2. Projects Table
CREATE TABLE IF NOT EXISTS projects (
    project_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    mode VARCHAR(32) NOT NULL DEFAULT 'multi_module',
    billing_tier VARCHAR(64) NOT NULL DEFAULT 'plan_enterprise',
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_tenant_project_slug UNIQUE (tenant_id, slug)
);

-- 3. Repositories Table
CREATE TABLE IF NOT EXISTS repositories (
    repo_id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    auth_type VARCHAR(32) NOT NULL DEFAULT 'ssh_key',
    default_branch VARCHAR(64) NOT NULL DEFAULT 'main',
    status VARCHAR(32) NOT NULL DEFAULT 'CONNECTED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Workspace Fleet Nodes Table
CREATE TABLE IF NOT EXISTS workspace_nodes (
    node_id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    hostname VARCHAR(255) NOT NULL,
    ip_address INET NOT NULL DEFAULT '127.0.0.1',
    os_info VARCHAR(128) NOT NULL DEFAULT 'macOS/Linux',
    worktree_path TEXT NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'HEALTHY',
    last_heartbeat TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- 5. Tenant Merkle State Ledgers Table
CREATE TABLE IF NOT EXISTS context_ledgers (
    ledger_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    project_id VARCHAR(64) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    block_height BIGINT NOT NULL,
    recovery_point_id VARCHAR(64) NOT NULL,
    merkle_block_hash CHAR(64) NOT NULL,
    previous_merkle_root CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- ============================================================================
-- ENABLE ROW LEVEL SECURITY (RLS) ON ALL TENANT-SCOPED TABLES
-- ============================================================================

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_ledgers ENABLE ROW LEVEL SECURITY;

-- Force RLS even for table owners (prevents accidental superuser bypass)
ALTER TABLE tenants FORCE ROW LEVEL SECURITY;
ALTER TABLE projects FORCE ROW LEVEL SECURITY;
ALTER TABLE repositories FORCE ROW LEVEL SECURITY;
ALTER TABLE workspace_nodes FORCE ROW LEVEL SECURITY;
ALTER TABLE context_ledgers FORCE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES USING SESSION TENANT CONTEXT: current_setting('app.current_tenant_id')
-- ============================================================================

-- Tenants Isolation Policy
DROP POLICY IF EXISTS tenant_isolation_policy ON tenants;
CREATE POLICY tenant_isolation_policy ON tenants
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''));

-- Projects Isolation Policy
DROP POLICY IF EXISTS project_isolation_policy ON projects;
CREATE POLICY project_isolation_policy ON projects
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''));

-- Repositories Isolation Policy
DROP POLICY IF EXISTS repository_isolation_policy ON repositories;
CREATE POLICY repository_isolation_policy ON repositories
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''));

-- Workspace Nodes Isolation Policy
DROP POLICY IF EXISTS workspace_node_isolation_policy ON workspace_nodes;
CREATE POLICY workspace_node_isolation_policy ON workspace_nodes
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''));

-- Context Ledgers Isolation Policy
DROP POLICY IF EXISTS context_ledger_isolation_policy ON context_ledgers;
CREATE POLICY context_ledger_isolation_policy ON context_ledgers
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''));

-- ============================================================================
-- SESSION HELPER FUNCTION: set_tenant_context(tenant_id, user_role)
-- ============================================================================

CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id TEXT, p_role TEXT DEFAULT 'AGENT_WORKER')
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', p_tenant_id, true);
    PERFORM set_config('app.user_role', p_role, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""

    @staticmethod
    def simulate_rls_filter(
        table_rows: List[Dict[str, Any]],
        session_tenant_id: str,
        session_role: TenantRole = TenantRole.AGENT_WORKER
    ) -> List[Dict[str, Any]]:
        """
        Simulates PostgreSQL RLS execution in memory to verify cross-tenant
        data isolation and zero-leakage constraints.
        """
        if session_role == TenantRole.ENTERPRISE_SUPER_ADMIN and session_tenant_id == "*":
            return list(table_rows)

        filtered = []
        for row in table_rows:
            row_tenant = row.get("tenant_id")
            if row_tenant and row_tenant == session_tenant_id:
                filtered.append(dict(row))
        return filtered

    # -------------------------------------------------------------------------
    # Internal Persistence
    # -------------------------------------------------------------------------

    def _save_state(self):
        if not self.persistence_file:
            return
        self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tenants": {k: v.to_dict() for k, v in self.tenants.items()},
            "projects": {k: v.to_dict() for k, v in self.projects.items()},
            "repositories": {k: v.to_dict() for k, v in self.repositories.items()},
            "workspace_nodes": {k: v.to_dict() for k, v in self.workspace_nodes.items()},
            "users": {k: v.to_dict() for k, v in self.users.items()}
        }
        with open(self.persistence_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_state(self):
        if not self.persistence_file or not self.persistence_file.exists():
            return
        try:
            with open(self.persistence_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            import dataclasses
            def _filter_dc(cls_type, d):
                valid = {f.name for f in dataclasses.fields(cls_type)}
                return {k: v for k, v in d.items() if k in valid}

            for k, v in data.get("tenants", {}).items():
                self.tenants[k] = Tenant(**_filter_dc(Tenant, v))
            for k, v in data.get("projects", {}).items():
                self.projects[k] = Project(**_filter_dc(Project, v))
            for k, v in data.get("repositories", {}).items():
                self.repositories[k] = Repository(**_filter_dc(Repository, v))
            for k, v in data.get("workspace_nodes", {}).items():
                self.workspace_nodes[k] = WorkspaceNode(**_filter_dc(WorkspaceNode, v))
            for k, v in data.get("users", {}).items():
                v_copy = dict(v)
                v_copy["role"] = TenantRole(v_copy["role"])
                self.users[k] = TenantUser(**_filter_dc(TenantUser, v_copy))
        except Exception:
            pass
