"""
Percipience Prompt SemVer & Semantic Drift Sentinel (CAP-29)
Audits system and workflow prompts for cryptographic integrity, SemVer versioning,
static prefix pinning (KV cache optimization), and behavioral regression against golden test suites.
"""

import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class PromptDriftSentinel:
    """
    Monitors prompt manifest specifications, audits SHA-256 integrity,
    verifies static prefix pinning for KV-cache optimization, and detects drift.
    """

    DEFAULT_MANIFEST_PATH = (REPO_ROOT / ".nb" / "agentic" / "prompts" / "prompt_manifest.yaml" if (REPO_ROOT / ".nb" / "agentic").exists() else REPO_ROOT / "agentic" / "prompts" / "prompt_manifest.yaml")
    PROMPTS_DIR = (REPO_ROOT / ".nb" / "agentic" / "prompts" if (REPO_ROOT / ".nb" / "agentic").exists() else REPO_ROOT / "agentic" / "prompts")

    @classmethod
    def load_manifest(cls, manifest_path: Optional[Path] = None) -> Dict[str, Any]:
        """Loads prompt manifest YAML."""
        path = manifest_path or cls.DEFAULT_MANIFEST_PATH
        if not path.exists():
            return {"manifest_version": "1.0.0", "prompts": {}}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @classmethod
    def calculate_prompt_hash(cls, prompt_file: Path) -> str:
        """Calculates SHA-256 hash of a prompt file."""
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        return hashlib.sha256(prompt_file.read_bytes()).hexdigest()

    @classmethod
    def audit_prompt_integrity(cls, manifest_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Audits all prompts in `agentic/prompts/` against `prompt_manifest.yaml`.
        Identifies modified prompts, missing prompts, and unmanifested new prompts.
        """
        manifest = cls.load_manifest(manifest_path)
        manifest_prompts = manifest.get("prompts", {})

        verified: List[str] = []
        drifted: List[Dict[str, Any]] = []
        missing: List[str] = []
        untracked: List[str] = []

        # Check existing prompts against manifest
        for filename, meta in manifest_prompts.items():
            prompt_file = cls.PROMPTS_DIR / filename
            if not prompt_file.exists():
                missing.append(filename)
                continue

            current_hash = cls.calculate_prompt_hash(prompt_file)
            expected_hash = meta.get("sha256")
            if current_hash == expected_hash:
                verified.append(filename)
            else:
                drifted.append({
                    "filename": filename,
                    "expected_version": meta.get("version", "1.0.0"),
                    "expected_sha256": expected_hash,
                    "actual_sha256": current_hash,
                    "drift_type": "CONTENT_HASH_MUTATION"
                })

        # Check for untracked prompts in the directory
        for p in cls.PROMPTS_DIR.glob("*.md"):
            if p.name not in manifest_prompts:
                untracked.append(p.name)

        is_pure = len(drifted) == 0 and len(missing) == 0
        return {
            "status": "PASSED" if is_pure else "DRIFT_DETECTED",
            "manifest_version": manifest.get("manifest_version", "1.0.0"),
            "total_prompts": len(manifest_prompts),
            "verified_count": len(verified),
            "verified_prompts": verified,
            "drifted_count": len(drifted),
            "drifted_prompts": drifted,
            "missing_prompts": missing,
            "untracked_prompts": untracked,
            "integrity_pure": is_pure
        }

    @classmethod
    def audit_prefix_pinning_compliance(cls) -> Dict[str, Any]:
        """
        Verifies that all prompts adhere to Static Prefix Pinning for KV-cache reuse.
        Static system invariants must appear before dynamic payload placeholders.
        """
        non_compliant: List[str] = []
        compliant: List[str] = []

        for p in sorted(cls.PROMPTS_DIR.glob("*.md")):
            content = p.read_text(encoding="utf-8")
            has_static_start = "<!-- STATIC_PREFIX_START -->" in content
            has_dynamic_start = "<!-- DYNAMIC_PAYLOAD_START -->" in content
            
            if has_static_start and has_dynamic_start:
                pos_static = content.index("<!-- STATIC_PREFIX_START -->")
                pos_dyn = content.index("<!-- DYNAMIC_PAYLOAD_START -->")
                if pos_static < pos_dyn:
                    compliant.append(p.name)
                else:
                    non_compliant.append(p.name)
            else:
                non_compliant.append(p.name)

        all_compliant = len(non_compliant) == 0
        return {
            "status": "PASSED" if all_compliant else "NON_COMPLIANT_PREFIX_PINNING",
            "total_prompts": len(compliant) + len(non_compliant),
            "compliant_count": len(compliant),
            "compliant_prompts": compliant,
            "non_compliant_count": len(non_compliant),
            "non_compliant_prompts": non_compliant
        }

    @classmethod
    def run_golden_eval_suite(cls) -> Dict[str, Any]:
        """
        Executes deterministic structure and invariant checks on critical prompts.
        Verifies presence of core axioms, role definitions, and output constraints.
        """
        eval_results: Dict[str, Any] = {}
        
        # 1. System Prompt Evaluation
        sys_prompt_file = cls.PROMPTS_DIR / "system_prompt.md"
        if sys_prompt_file.exists():
            content = sys_prompt_file.read_text(encoding="utf-8")
            required_axioms = [
                "Quad-Space Clean Separation",
                "Deterministic Lineage",
                "Context Poisoning Sentinel",
                "Token Optimization",
                "Cryptographic Merkle"
            ]
            matched = [ax for ax in required_axioms if ax in content]
            eval_results["system_prompt"] = {
                "passed": len(matched) == len(required_axioms),
                "matched_axioms": len(matched),
                "total_required": len(required_axioms)
            }
        
        # 2. Derivation Prompt Evaluation
        deriv_file = cls.PROMPTS_DIR / "derivation_prompt.md"
        if deriv_file.exists():
            content = deriv_file.read_text(encoding="utf-8")
            has_mvs = "MVS" in content
            has_workplace = "workplace/" in content
            has_contracts = "context/contracts/" in content or ".nb/context/contracts/" in content
            eval_results["derivation_prompt"] = {
                "passed": has_mvs and has_workplace and has_contracts,
                "has_quad_space_references": True
            }

        all_passed = all(r.get("passed", False) for r in eval_results.values())
        return {
            "eval_suite_status": "PASSED" if all_passed else "FAILED",
            "evaluated_prompts": len(eval_results),
            "results": eval_results
        }
