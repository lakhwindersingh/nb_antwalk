#!/usr/bin/env python3
"""
Percipience Offline Plugin Auto-Upgrade Resolver
=================================================

Canonical Python engine (mirrored by the Kotlin ``PluginUpdateChecker``) that
discovers locally-available Percipience plugin / runtime updates from the file
system only — no network access is ever performed.

The IDE plugin embeds a version manifest (``percipience/version.json``). On
startup (and on demand) the plugin scans a set of local directories for newer
manifests / prebuilt plugin archives, compares semantic versions, and — when a
strictly newer, schema-compatible candidate is found — upgrades the workspace
runtime (``.nb/`` scaffolding: core engines, workflows, hooks, scripts, CLI,
config, plans) and records the applied version in
``.nb/config/runtime_version.json``.

Scanned locations (in priority order):
  1. ``PERCIPIENCE_UPDATE_DIR`` (os.pathsep-separated directories)
  2. ``<workspace>/.nb/bundles`` (prebuilt ``percipience-intellij-plugin-*``)
  3. ``<workspace>/.nb/updates``
  4. ``~/.percipience/updates``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

MANIFEST_SCHEMA = 1
MANIFEST_FILENAME = "version.json"
# Path of the manifest *inside* a packaged plugin archive (.jar/.zip).
ARCHIVE_MANIFEST_PATHS = ("percipience/version.json", "version.json")
# Installed-plugin embedded resource (classpath: /percipience/version.json).
EMBEDDED_MANIFEST_RESOURCE = "percipience/version.json"
# Workspace marker recording the last applied runtime version.
RUNTIME_VERSION_RELPATH = ".nb/config/runtime_version.json"

CURRENT_PLUGIN_VERSION = "1.3.0"
CURRENT_PLATFORM_VERSION = "7.5.0"
DEFAULT_CHANNEL = "stable"

# Payload directory (inside a candidate archive / staged dir) -> workspace dest
PAYLOAD_MAP: Dict[str, str] = {
    "core": ".nb/core",
    "bin": ".nb/bin",
    "config": ".nb/config",
    "workflows": ".nb/agentic/custom/workflows",
    "hooks": ".nb/git_hooks",
    "scripts": ".nb/scripts",
    "plan": ".nb/plan",
}


# --------------------------------------------------------------------------- #
# Semver
# --------------------------------------------------------------------------- #

def parse_semver(version: Any) -> tuple:
    """Parses a (loose) semantic version into a comparable int tuple."""
    if version is None:
        return (0, 0, 0)
    text = str(version).strip().lstrip("vV")
    core = text.split("-", 1)[0].split("+", 1)[0]
    parts: List[int] = []
    for chunk in core.split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(candidate_version: Any, current_version: Any) -> bool:
    """True iff ``candidate_version`` is strictly greater than ``current_version``."""
    return parse_semver(candidate_version) > parse_semver(current_version)


# --------------------------------------------------------------------------- #
# Manifest IO
# --------------------------------------------------------------------------- #

def build_manifest(
    plugin_version: str = CURRENT_PLUGIN_VERSION,
    platform_version: str = CURRENT_PLATFORM_VERSION,
    tier: str = "plan_free",
    channel: str = DEFAULT_CHANNEL,
    released_at: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Builds the canonical version-manifest dictionary."""
    manifest: Dict[str, Any] = {
        "manifest_schema": MANIFEST_SCHEMA,
        "plugin_version": plugin_version,
        "platform_version": platform_version,
        "tier": tier,
        "channel": channel,
        "released_at": released_at or datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        manifest.update(extra)
    return manifest


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def read_manifest_from_dir(directory: Path) -> Optional[Dict[str, Any]]:
    """Reads a manifest from a staged update directory."""
    for rel in ("percipience/version.json", "version.json"):
        cand = directory / rel
        if cand.is_file():
            data = _read_json(cand)
            if data:
                return data
    return None


def _open_archive(archive: Path) -> zipfile.ZipFile:
    """
    Opens a plugin archive, transparently unwrapping the JetBrains
    distribution layout (``<plugin>/lib/<plugin>.jar``) to reach the inner JAR
    that carries the ``percipience/`` payload and manifest.
    """
    outer = zipfile.ZipFile(archive, "r")
    names = outer.namelist()
    has_payload = any("percipience/" in n for n in names)
    inner_jars = [n for n in names if n.lower().endswith(".jar")]
    if not has_payload and inner_jars:
        import io
        inner = io.BytesIO(outer.read(inner_jars[0]))
        outer.close()
        return zipfile.ZipFile(inner, "r")
    return outer


def read_manifest_from_archive(archive: Path) -> Optional[Dict[str, Any]]:
    """Reads the embedded manifest from a .jar / .zip plugin archive."""
    if not archive.is_file():
        return None
    try:
        with _open_archive(archive) as zf:
            names = set(zf.namelist())
            for rel in ARCHIVE_MANIFEST_PATHS:
                if rel in names:
                    try:
                        data = json.loads(zf.read(rel).decode("utf-8"))
                        if data:
                            return data
                    except Exception:
                        continue
    except Exception:
        return None
    return None


def read_manifest(path: Path) -> Optional[Dict[str, Any]]:
    """Reads a manifest from either a staged directory or a plugin archive."""
    if path.is_dir():
        return read_manifest_from_dir(path)
    if path.is_file() and path.suffix.lower() in (".jar", ".zip"):
        return read_manifest_from_archive(path)
    return None


def emit_version_manifest(
    dest_dir: Path,
    plugin_version: str = CURRENT_PLUGIN_VERSION,
    platform_version: str = CURRENT_PLATFORM_VERSION,
    tier: str = "plan_free",
    channel: str = DEFAULT_CHANNEL,
    released_at: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Path:
    """Writes the version manifest into ``dest_dir`` as ``version.json``."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(
        plugin_version=plugin_version,
        platform_version=platform_version,
        tier=tier,
        channel=channel,
        released_at=released_at,
        extra=extra,
    )
    out = dest_dir / MANIFEST_FILENAME
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# Local filesystem discovery
# --------------------------------------------------------------------------- #

def default_update_dirs(workspace_root: Path, env: Optional[Dict[str, str]] = None) -> List[Path]:
    """Returns the ordered list of local directories scanned for updates."""
    env = env if env is not None else os.environ
    workspace_root = Path(workspace_root)

    dirs: List[Path] = []
    env_dir = env.get("PERCIPIENCE_UPDATE_DIR")
    if env_dir:
        for part in env_dir.split(os.pathsep):
            if part.strip():
                dirs.append(Path(part.strip()))

    dirs.append(workspace_root / ".nb" / "bundles")
    dirs.append(workspace_root / ".nb" / "updates")
    dirs.append(Path(env.get("HOME", str(Path.home()))) / ".percipience" / "updates")
    return dirs


def _candidate_from(path: Path, source: str) -> Optional[Dict[str, Any]]:
    manifest = read_manifest(path)
    if not manifest or "plugin_version" not in manifest:
        return None
    return {
        "plugin_version": str(manifest.get("plugin_version")),
        "platform_version": str(manifest.get("platform_version", CURRENT_PLATFORM_VERSION)),
        "tier": str(manifest.get("tier", "plan_free")),
        "channel": str(manifest.get("channel", DEFAULT_CHANNEL)),
        "manifest_schema": int(manifest.get("manifest_schema", MANIFEST_SCHEMA)),
        "released_at": manifest.get("released_at"),
        "path": str(path),
        "kind": "dir" if path.is_dir() else "archive",
        "source": source,
    }


def discover_local_candidates(
    workspace_root: Path,
    env: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Scans the local file system and returns all discovered update candidates."""
    workspace_root = Path(workspace_root)
    candidates: List[Dict[str, Any]] = []
    seen: set = set()

    def add(path: Path, source: str) -> None:
        cand = _candidate_from(path, source)
        if cand is None:
            return
        key = (cand["plugin_version"], cand["path"])
        if key in seen:
            return
        seen.add(key)
        candidates.append(cand)

    for directory in default_update_dirs(workspace_root, env):
        if not directory.exists():
            continue
        # The directory itself may be a staged update root (contains version.json)
        if (directory / MANIFEST_FILENAME).is_file() or (directory / EMBEDDED_MANIFEST_RESOURCE).is_file():
            add(directory, str(directory))
            continue
        for entry in sorted(directory.iterdir()):
            if entry.is_dir():
                add(entry, str(directory))
            elif entry.is_file() and entry.suffix.lower() in (".jar", ".zip"):
                add(entry, str(directory))

    candidates.sort(key=lambda c: parse_semver(c["plugin_version"]), reverse=True)
    return candidates


def select_upgrade(
    current_version: str,
    candidates: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Returns the highest upgrade candidate newer than the current version."""
    eligible = [
        c for c in candidates
        if c.get("manifest_schema", MANIFEST_SCHEMA) == MANIFEST_SCHEMA
        and is_newer(c.get("plugin_version"), current_version)
    ]
    if not eligible:
        return None
    eligible.sort(key=lambda c: parse_semver(c["plugin_version"]), reverse=True)
    return eligible[0]


# --------------------------------------------------------------------------- #
# Runtime upgrade application
# --------------------------------------------------------------------------- #

def applied_runtime_version(workspace_root: Path) -> Optional[str]:
    """Returns the last applied runtime version recorded in the workspace."""
    marker = Path(workspace_root) / RUNTIME_VERSION_RELPATH
    data = _read_json(marker) if marker.is_file() else None
    if data:
        return str(data.get("plugin_version")) if data.get("plugin_version") else None
    return None


def _iter_payload_files(src: Path):
    """Yields (relative_payload_path, absolute_path) for a staged dir / archive member."""
    if src.is_dir():
        for root_rel in PAYLOAD_MAP:
            base = src / root_rel
            if not base.exists():
                continue
            for f in sorted(base.rglob("*")):
                if f.is_file() and not f.name.startswith("."):
                    yield f"{root_rel}/{f.relative_to(base).as_posix()}", f
        return

    with _open_archive(src) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            # Locate the "percipience/" payload root inside the (possibly nested) archive.
            idx = name.find("percipience/")
            if idx == -1:
                continue
            rel = name[idx + len("percipience/"):]
            root_rel = rel.split("/", 1)[0]
            if root_rel not in PAYLOAD_MAP:
                continue
            member = name
            yield f"{root_rel}/{rel.split('/', 1)[1]}" if "/" in rel else rel, _ZipMember(zf, member)


class _ZipMember:
    """Lazy file-like wrapper for an archive member so the loop can treat both sources alike."""

    def __init__(self, zf: zipfile.ZipFile, name: str):
        self._zf = zf
        self._name = name

    def read_bytes(self) -> bytes:
        return self._zf.read(self._name)


def apply_runtime_upgrade(
    workspace_root: Path,
    candidate: Dict[str, Any],
) -> Dict[str, Any]:
    """Materializes a candidate's payload into the workspace ``.nb/`` tree."""
    workspace_root = Path(workspace_root)
    src = Path(candidate["path"])
    previous = applied_runtime_version(workspace_root)

    upgraded_files: List[str] = []
    for rel_payload, src_file in _iter_payload_files(src):
        root_rel, _, sub_rel = rel_payload.partition("/")
        if root_rel not in PAYLOAD_MAP:
            continue
        dest = workspace_root / PAYLOAD_MAP[root_rel] / sub_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(src_file, _ZipMember):
            dest.write_bytes(src_file.read_bytes())
        else:
            shutil.copy2(src_file, dest)
        if root_rel in ("bin", "hooks", "scripts"):
            try:
                dest.chmod(0o755)
            except Exception:
                pass
        upgraded_files.append(str(dest.relative_to(workspace_root)))

    marker = workspace_root / RUNTIME_VERSION_RELPATH
    marker.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "plugin_version": candidate["plugin_version"],
        "platform_version": candidate.get("platform_version"),
        "tier": candidate.get("tier"),
        "channel": candidate.get("channel"),
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "source": candidate.get("path"),
        "source_kind": candidate.get("kind"),
        "previous_version": previous,
        "files_upgraded": len(upgraded_files),
        "files": sorted(upgraded_files),
    }
    marker.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "UPGRADED",
        "plugin_version": candidate["plugin_version"],
        "previous_version": previous,
        "tier": candidate.get("tier"),
        "source": candidate.get("path"),
        "files_upgraded": len(upgraded_files),
        "marker": str(marker.relative_to(workspace_root)),
    }


# --------------------------------------------------------------------------- #
# High level: check for upgrade
# --------------------------------------------------------------------------- #

def check_for_upgrade(
    workspace_root: Path,
    current_version: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Scans the local file system and reports whether an upgrade is available."""
    workspace_root = Path(workspace_root)
    current = current_version or CURRENT_PLUGIN_VERSION
    candidates = discover_local_candidates(workspace_root, env)
    best = select_upgrade(current, candidates)
    return {
        "current_version": current,
        "applied_runtime_version": applied_runtime_version(workspace_root),
        "candidates_found": len(candidates),
        "candidates": candidates,
        "upgrade_available": best is not None,
        "selected": best,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Percipience offline plugin auto-upgrade resolver")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Scan the local file system for plugin updates")
    check.add_argument("--workspace", default=os.getcwd())
    check.add_argument("--current-version", default=CURRENT_PLUGIN_VERSION)

    apply_p = sub.add_parser("apply", help="Apply the best available local update")
    apply_p.add_argument("--workspace", default=os.getcwd())
    apply_p.add_argument("--current-version", default=CURRENT_PLUGIN_VERSION)

    emit = sub.add_parser("emit-manifest", help="Emit a version.json manifest")
    emit.add_argument("--dir", required=True)
    emit.add_argument("--plugin-version", default=CURRENT_PLUGIN_VERSION)
    emit.add_argument("--platform-version", default=CURRENT_PLATFORM_VERSION)
    emit.add_argument("--tier", default="plan_free")
    emit.add_argument("--channel", default=DEFAULT_CHANNEL)

    args = parser.parse_args()

    if args.command == "check":
        print(json.dumps(check_for_upgrade(Path(args.workspace), args.current_version), indent=2))
        return 0

    if args.command == "apply":
        report = check_for_upgrade(Path(args.workspace), args.current_version)
        if not report["upgrade_available"]:
            print("No upgrade available.")
            return 0
        result = apply_runtime_upgrade(Path(args.workspace), report["selected"])
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "emit-manifest":
        out = emit_version_manifest(
            Path(args.dir),
            plugin_version=args.plugin_version,
            platform_version=args.platform_version,
            tier=args.tier,
            channel=args.channel,
        )
        print(str(out))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(_cli())
