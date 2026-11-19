"""
Percipience Post-Generation Output Guardrails & Safety Rails (CAP-39 / TODO-COMP-07)
Enterprise Competitor Parity: NeMo Guardrails / Guardrails AI.
Executes post-generation AST structural verification, dangerous system call detection,
forbidden shell command interception, and path traversal auditing before code is written to disk.
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class OutputGuardrailVisitor(ast.NodeVisitor):
    """
    AST Visitor analyzing Python syntax trees for unsafe operations,
    eval execution, arbitrary shell commands, and dangerous modules.
    """

    BANNED_CALLS = {
        "eval": "Dynamic code evaluation via eval()",
        "exec": "Dynamic code execution via exec()",
        "system": "Direct OS shell execution via os.system()",
        "popen": "Arbitrary process execution via os.popen()",
    }

    BANNED_MODULES = {
        "pty": "Pseudo-terminal manipulation",
        "telnetlib": "Unencrypted Telnet connection",
    }

    def __init__(self):
        self.violations: List[Dict[str, Any]] = []

    def visit_Call(self, node: ast.Call):
        # 1. Direct function call: eval(...), exec(...)
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.BANNED_CALLS:
                self.violations.append({
                    "type": "DANGEROUS_CALL",
                    "severity": "CRITICAL",
                    "line": node.lineno,
                    "description": self.BANNED_CALLS[func_name],
                    "target": func_name
                })

        # 2. Attribute call: os.system(...), subprocess.Popen(..., shell=True)
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in self.BANNED_CALLS:
                self.violations.append({
                    "type": "DANGEROUS_OS_EXECUTION",
                    "severity": "CRITICAL",
                    "line": node.lineno,
                    "description": self.BANNED_CALLS[attr_name],
                    "target": attr_name
                })

            # Check subprocess calls for shell=True
            if attr_name in ("Popen", "call", "check_call", "check_output", "run"):
                for kw in node.keywords:
                    if kw.arg == "shell":
                        # Check if shell is assigned True constant
                        if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            self.violations.append({
                                "type": "SHELL_INJECTION_RISK",
                                "severity": "CRITICAL",
                                "line": node.lineno,
                                "description": f"subprocess.{attr_name}(shell=True) enables arbitrary command injection",
                                "target": f"subprocess.{attr_name}"
                            })

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name in self.BANNED_MODULES:
                self.violations.append({
                    "type": "BANNED_IMPORT",
                    "severity": "HIGH",
                    "line": node.lineno,
                    "description": f"Banned security-sensitive module import: {alias.name} ({self.BANNED_MODULES[alias.name]})",
                    "target": alias.name
                })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module in self.BANNED_MODULES:
            self.violations.append({
                "type": "BANNED_IMPORT",
                "severity": "HIGH",
                "line": node.lineno,
                "description": f"Banned security-sensitive module import: {node.module}",
                "target": node.module
            })
        self.generic_visit(node)


class OutputGuardrailValidator:
    """
    Enforces post-generation execution policies, AST structural validity,
    and hallucination safety rails before code patches or files are committed.
    """

    # Banned supply-chain packages across ecosystems
    BANNED_SUPPLY_CHAIN_PKGS = {
        "event-stream", "flatmap-stream", "crypto-miner", "telemetry-hack", "malicious-pkg"
    }

    # Sensitive host filesystem paths prohibited from disk writes
    FORBIDDEN_FILESYSTEM_PATHS = [
        re.compile(r'(?i)(?:/etc/(?:passwd|shadow|sudoers)|/root/|/proc/|/sys/|~?/\.ssh/)'),
        re.compile(r'\.\./\.\./')  # Multilevel directory traversal
    ]

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or REPO_ROOT

    def validate_code_output(
        self,
        code_content: str,
        language: str = "python",
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates generated code against AST structural safety, dangerous system calls,
        rogue packages, and path traversal policies.
        """
        violations: List[Dict[str, Any]] = []
        is_syntax_valid = True

        # 1. Structural AST Parsing & Syntax Verification
        if language.lower() in ("python", "py"):
            try:
                tree = ast.parse(code_content, filename=file_path or "<agent_generated_code>")
                # Run AST Security Visitor
                visitor = OutputGuardrailVisitor()
                visitor.visit(tree)
                violations.extend(visitor.violations)
            except SyntaxError as e:
                is_syntax_valid = False
                violations.append({
                    "type": "SYNTAX_ERROR",
                    "severity": "CRITICAL",
                    "line": e.lineno,
                    "column": e.offset,
                    "description": f"Invalid Python syntax: {e.msg}",
                    "target": e.text.strip() if e.text else ""
                })
        elif language.lower() in ("json",):
            try:
                json.loads(code_content)
            except Exception as e:
                is_syntax_valid = False
                violations.append({
                    "type": "MALFORMED_JSON",
                    "severity": "CRITICAL",
                    "description": f"Malformed JSON: {str(e)}"
                })

        # 2. General regex checks for JavaScript/TypeScript shell execution
        if language.lower() in ("typescript", "javascript", "ts", "js"):
            js_shell_pattern = re.compile(r'\b(?:child_process\s*\.\s*(?:exec|spawn)\s*\(|eval\s*\(|new\s+Function\s*\()')
            for idx, line in enumerate(code_content.splitlines(), start=1):
                if js_shell_pattern.search(line):
                    violations.append({
                        "type": "UNVERIFIED_SHELL_EXECUTION",
                        "severity": "CRITICAL",
                        "line": idx,
                        "description": "Dangerous JavaScript/Node shell execution or dynamic eval",
                        "target": line.strip()
                    })

        # 3. Supply-chain package blacklist verification
        for pkg in self.BANNED_SUPPLY_CHAIN_PKGS:
            pattern = re.compile(rf'(?:import\s+.*from\s+[\"\']{re.escape(pkg)}[\"\']|require\([\"\']{re.escape(pkg)}[\"\']\)|import\s+{re.escape(pkg)})')
            if pattern.search(code_content):
                violations.append({
                    "type": "COMPROMISED_DEPENDENCY",
                    "severity": "CRITICAL",
                    "description": f"Compromised supply-chain dependency detected: '{pkg}'",
                    "target": pkg
                })

        # 4. Filesystem path traversal and host escape boundaries
        for f_pattern in self.FORBIDDEN_FILESYSTEM_PATHS:
            match = f_pattern.search(code_content)
            if match:
                violations.append({
                    "type": "PATH_TRAVERSAL_BREACH",
                    "severity": "CRITICAL",
                    "description": "Unauthorized filesystem traversal or access to root OS path",
                    "target": match.group(0)
                })

        # 5. Hallucinated internal imports verification (if file_path in workspace)
        phantom_violations = self._detect_phantom_internal_imports(code_content, language)
        violations.extend(phantom_violations)

        # 6. Scoring & Action Recommendation
        critical_count = sum(1 for v in violations if v.get("severity") == "CRITICAL")
        high_count = sum(1 for v in violations if v.get("severity") == "HIGH")

        safety_score = 1.0 - (critical_count * 0.40 + high_count * 0.20)
        safety_score = max(0.0, min(1.0, round(safety_score, 2)))

        if critical_count > 0 or not is_syntax_valid:
            action = "REJECT_AND_REPROMPT"
            is_valid = False
        elif high_count > 0:
            action = "QUARANTINE_CODE"
            is_valid = False
        else:
            action = "ALLOW_WRITE"
            is_valid = True

        # Synthesize remediation instructions for DiagnosticRePromptEngine
        remediation_prompt = self._synthesize_remediation_prompt(violations, file_path)

        return {
            "is_valid": is_valid,
            "is_syntax_valid": is_syntax_valid,
            "action": action,
            "safety_score": safety_score,
            "violations_count": len(violations),
            "violations": violations,
            "file_path": file_path,
            "remediation_prompt": remediation_prompt
        }

    def _detect_phantom_internal_imports(self, code_content: str, language: str) -> List[Dict[str, Any]]:
        """Checks if code imports nonexistent modules from internal core namespace."""
        violations = []
        if language.lower() not in ("python", "py"):
            return violations

        import_pattern = re.compile(r'from\s+core\.([a-zA-Z0-9_]+)\s+import')
        matches = import_pattern.findall(code_content)

        known_core_files: Set[str] = set()
        for base in [self.workspace_root / ".nb" / "core", self.workspace_root / "workplace" / "core"]:
            if base.exists():
                for f in base.glob("*.py"):
                    known_core_files.add(f.stem)

        for mod_name in matches:
            if known_core_files and mod_name not in known_core_files:
                violations.append({
                    "type": "HALLUCINATED_INTERNAL_IMPORT",
                    "severity": "HIGH",
                    "description": f"Hallucinated internal engine: 'from core.{mod_name}' does not exist in workspace",
                    "target": mod_name
                })
        return violations

    def _synthesize_remediation_prompt(self, violations: List[Dict[str, Any]], file_path: Optional[str]) -> str:
        """Constructs an isolated, zero-noise remediation prompt for self-healing."""
        if not violations:
            return ""
        lines = [
            f"### Output Guardrail Safety Violation in `{file_path or 'generated_module'}`",
            "The generated code violated runtime policy invariants. Correct the implementation:",
        ]
        for v in violations:
            lines.append(f"- [{v.get('type')}] ({v.get('severity')}): {v.get('description')} (target: `{v.get('target', 'N/A')}`)")
        lines.append("Enforce safe APIs only: do not use eval, shell=True, forbidden paths, or hallucinated imports.")
        return "\n".join(lines)
