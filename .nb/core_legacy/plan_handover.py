"""Versioned, content-addressed plan handovers and artifact verification."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Tuple


class PlanHandoverVerifier:
    """Build and validate evidence binding plan inputs, dependencies and outputs."""

    SCHEMA_VERSION = 1
    HANDOVER_FIELDS = {
        "schema_version", "plan_id", "status", "manifest_sha256", "specification_sha256",
        "prerequisite_handover_hashes", "artifacts", "recovery_point_id", "handover_hash",
    }

    @staticmethod
    def _sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _is_sha256(value: Any) -> bool:
        return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)

    @staticmethod
    def _canonical_hash(value: Dict[str, Any]) -> str:
        serialized = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    @staticmethod
    def _workspace_file(workspace_root: Path, relative_path: str) -> Path:
        root = Path(workspace_root).resolve()
        path = Path(relative_path)
        if path.is_absolute():
            raise ValueError(f"Artifact path must be workspace-relative: {relative_path}")
        resolved = (root / path).resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(f"Artifact path escapes workspace: {relative_path}")
        return resolved

    @classmethod
    def _input_hashes(cls, plan: Dict[str, Any], workspace_root: Path) -> Tuple[str, str]:
        manifest_path = Path(plan["manifest_path"]).resolve()
        root = Path(workspace_root).resolve()
        if not manifest_path.is_relative_to(root):
            raise ValueError(f"Plan manifest is outside the workspace: {manifest_path}")
        if not manifest_path.is_file():
            raise ValueError(f"Plan manifest is missing: {manifest_path}")
        manifest_hash = cls._sha256(manifest_path.read_bytes())
        specifications = []
        for spec_path in sorted(Path(path).resolve() for path in plan.get("spec_files", [])):
            if not spec_path.is_file():
                raise ValueError(f"Plan specification is missing: {spec_path}")
            if not spec_path.is_relative_to(root):
                raise ValueError(f"Plan specification is outside the workspace: {spec_path}")
            specifications.append(
                {
                    "path": spec_path.relative_to(root).as_posix(),
                    "sha256": cls._sha256(spec_path.read_bytes()),
                }
            )
        return manifest_hash, cls._canonical_hash({"specifications": specifications})

    @classmethod
    def build_handover(
        cls,
        plan: Dict[str, Any],
        workspace_root: Path,
        artifact_paths: Iterable[str],
        prerequisite_handovers: Mapping[str, Dict[str, Any]],
        recovery_point_id: str,
    ) -> Dict[str, Any]:
        """Create a handover from actual files and already verified prerequisites."""
        required_dependency_ids = set(plan.get("dependency_ids", []))
        if set(prerequisite_handovers) != required_dependency_ids:
            raise ValueError("Prerequisite handovers must match the plan's direct dependencies exactly")
        manifest_hash, specification_hash = cls._input_hashes(plan, workspace_root)
        artifacts = {}
        for relative_path in artifact_paths:
            normalized = Path(relative_path).as_posix()
            artifact_path = cls._workspace_file(workspace_root, normalized)
            if not artifact_path.is_file():
                raise ValueError(f"Handover artifact is missing: {normalized}")
            artifacts[normalized] = cls._sha256(artifact_path.read_bytes())
        if not artifacts:
            raise ValueError("A successful handover must include at least one output artifact")
        if any(not isinstance(record, dict) for record in prerequisite_handovers.values()):
            raise ValueError("Prerequisite handover is malformed")
        prerequisite_hashes = {
            plan_id: record.get("handover_hash")
            for plan_id, record in sorted(prerequisite_handovers.items())
        }
        if any(not cls._is_sha256(value) for value in prerequisite_hashes.values()):
            raise ValueError("Prerequisite handover is missing its content hash")
        if not isinstance(recovery_point_id, str) or not recovery_point_id.strip():
            raise ValueError("A successful handover must reference a recovery point")

        handover = {
            "schema_version": cls.SCHEMA_VERSION,
            "plan_id": plan["plan_id"],
            "status": "SUCCESS",
            "manifest_sha256": manifest_hash,
            "specification_sha256": specification_hash,
            "prerequisite_handover_hashes": prerequisite_hashes,
            "artifacts": dict(sorted(artifacts.items())),
            "recovery_point_id": recovery_point_id.strip(),
        }
        handover["handover_hash"] = cls._canonical_hash(handover)
        return handover

    @classmethod
    def validate_handover(
        cls,
        handover: Dict[str, Any],
        plan: Dict[str, Any],
        workspace_root: Path,
        prerequisite_handovers: Mapping[str, Dict[str, Any]],
        recovery_point_verifier,
    ) -> Tuple[bool, str]:
        """Verify hashes and chain inputs; missing evidence is never accepted."""
        if not isinstance(handover, dict):
            return False, "Handover evidence is missing or malformed"
        if set(handover) != cls.HANDOVER_FIELDS:
            return False, "Handover fields do not match the contract"
        if type(handover.get("schema_version")) is not int or handover.get("schema_version") != cls.SCHEMA_VERSION:
            return False, "Unsupported handover schema version"
        if handover.get("status") != "SUCCESS" or handover.get("plan_id") != plan.get("plan_id"):
            return False, "Handover status or plan identity does not match"

        handover_payload = {key: value for key, value in handover.items() if key != "handover_hash"}
        try:
            expected_handover_hash = cls._canonical_hash(handover_payload)
        except (TypeError, ValueError):
            return False, "Handover contents are not valid JSON"
        if handover.get("handover_hash") != expected_handover_hash:
            return False, "Handover content hash mismatch"

        try:
            manifest_hash, specification_hash = cls._input_hashes(plan, workspace_root)
        except (KeyError, OSError, ValueError) as exc:
            return False, str(exc)
        if handover.get("manifest_sha256") != manifest_hash:
            return False, "Plan manifest hash mismatch"
        if handover.get("specification_sha256") != specification_hash:
            return False, "Plan specification hash mismatch"

        required_dependency_ids = set(plan.get("dependency_ids", []))
        if set(prerequisite_handovers) != required_dependency_ids:
            return False, "Supplied prerequisite handovers do not match direct dependencies"
        if any(not isinstance(record, dict) for record in prerequisite_handovers.values()):
            return False, "Prerequisite handover is malformed"
        expected_prerequisite_hashes = {
            plan_id: record.get("handover_hash")
            for plan_id, record in sorted(prerequisite_handovers.items())
        }
        if any(not cls._is_sha256(value) for value in expected_prerequisite_hashes.values()):
            return False, "Prerequisite handover hash is malformed"
        if handover.get("prerequisite_handover_hashes") != expected_prerequisite_hashes:
            return False, "Prerequisite handover chain does not match"

        artifacts = handover.get("artifacts")
        if not isinstance(artifacts, dict) or not artifacts:
            return False, "No output artifact hashes were supplied"
        try:
            for relative_path, expected_hash in artifacts.items():
                artifact_path = cls._workspace_file(workspace_root, relative_path)
                if not artifact_path.is_file() or cls._sha256(artifact_path.read_bytes()) != expected_hash:
                    return False, f"Artifact hash mismatch: {relative_path}"
        except (OSError, TypeError, ValueError) as exc:
            return False, str(exc)

        recovery_point_id = handover.get("recovery_point_id")
        if not isinstance(recovery_point_id, str) or not recovery_point_id:
            return False, "Recovery point is missing"
        if not callable(recovery_point_verifier):
            return False, "Recovery point could not be verified"
        try:
            if not recovery_point_verifier(recovery_point_id):
                return False, "Recovery point could not be verified"
        except Exception:
            return False, "Recovery point could not be verified"
        return True, "Verified"

    @classmethod
    def verify_handover(cls, *args, **kwargs) -> bool:
        return cls.validate_handover(*args, **kwargs)[0]