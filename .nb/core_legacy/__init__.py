"""
Percipience Core Workplace Modules:
Multi-Tenant Project Provisioning, Fleet Workspaces, IAM & KMS Enclaves,
Runtime Guardrails, PII Anonymization & Prompt Injection Firewall.
Extends the core namespace to seamlessly merge workplace/core and .nb/core.
"""

import pkgutil
__path__ = pkgutil.extend_path(__path__, __name__)

__all__ = []

try:
    from .tenant_manager import (
        TenantManager,
        TenantRole,
        Tenant,
        Project,
        Repository,
        WorkspaceNode,
        TenantUser,
    )
    __all__.extend([
        "TenantManager",
        "TenantRole",
        "Tenant",
        "Project",
        "Repository",
        "WorkspaceNode",
        "TenantUser",
    ])
except (ImportError, ModuleNotFoundError):
    TenantManager = None
    TenantRole = None
    Tenant = None
    Project = None
    Repository = None
    WorkspaceNode = None
    TenantUser = None

try:
    from .project_scaffolder import ProjectScaffolder, ScaffoldResult
    __all__.extend(["ProjectScaffolder", "ScaffoldResult"])
except (ImportError, ModuleNotFoundError):
    ProjectScaffolder = None
    ScaffoldResult = None

try:
    from .kms_broker import KMSBroker, KeyRecord, SealedEnclaveBundle
    __all__.extend(["KMSBroker", "KeyRecord", "SealedEnclaveBundle"])
except (ImportError, ModuleNotFoundError):
    KMSBroker = None
    KeyRecord = None
    SealedEnclaveBundle = None

try:
    from .project_policy_engine import (
        ProjectPolicyManager,
        ProjectPolicy,
        AttentionSlicingPolicy,
        CognitiveRoutingPolicy,
        ASTPruningPolicy,
        SelfHealingSLAPolicy,
        WireContractRule,
    )
    __all__.extend([
        "ProjectPolicyManager",
        "ProjectPolicy",
        "AttentionSlicingPolicy",
        "CognitiveRoutingPolicy",
        "ASTPruningPolicy",
        "SelfHealingSLAPolicy",
        "WireContractRule",
    ])
except (ImportError, ModuleNotFoundError):
    ProjectPolicyManager = None
    ProjectPolicy = None
    AttentionSlicingPolicy = None
    CognitiveRoutingPolicy = None
    ASTPruningPolicy = None
    SelfHealingSLAPolicy = None
    WireContractRule = None

try:
    from .pii_sanitizer import PIISanitizer
    __all__.append("PIISanitizer")
except (ImportError, ModuleNotFoundError):
    PIISanitizer = None

try:
    from .prompt_injection_guard import PromptInjectionGuard
    __all__.append("PromptInjectionGuard")
except (ImportError, ModuleNotFoundError):
    PromptInjectionGuard = None

try:
    from .output_guardrail_validator import OutputGuardrailValidator
    __all__.append("OutputGuardrailValidator")
except (ImportError, ModuleNotFoundError):
    OutputGuardrailValidator = None
