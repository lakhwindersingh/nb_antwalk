#!/usr/bin/env python3
"""
Automated Plan Version Synchronization Tool.
Computes SHA-256 hashes and line counts to update and verify MANIFEST.yaml files across all plan directories.
"""

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class PlanVersionSync:
    def __init__(self, plan_root: Path):
        self.plan_root = Path(plan_root).resolve()

    def compute_hash(self, file_path: Path) -> Optional[str]:
        """Compute SHA-256 hash of file content."""
        if not file_path.exists() or not file_path.is_file():
            return None
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def get_line_count(self, file_path: Path) -> int:
        """Count lines in file."""
        if not file_path.exists() or not file_path.is_file():
            return 0
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return len(f.readlines())

    def get_plan_dirs(self) -> List[Path]:
        """Find all plan directories containing a MANIFEST.yaml file."""
        plan_dirs = []
        for manifest_path in sorted(self.plan_root.glob("**/MANIFEST.yaml")):
            if "templates" in manifest_path.parts or "archive" in manifest_path.parts:
                continue
            plan_dirs.append(manifest_path.parent)
        return plan_dirs

    def update_manifest(self, plan_dir: Path) -> bool:
        """Update MANIFEST.yaml with current file hashes and line counts."""
        manifest_path = plan_dir / "MANIFEST.yaml"
        if not manifest_path.exists():
            print(f"⚠️  No MANIFEST.yaml in {plan_dir.name}")
            return False

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest: Dict[str, Any] = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"❌ Error reading {manifest_path}: {e}")
            return False

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        file_versions = manifest.setdefault("file_versions", {})
        file_types = list(dict.fromkeys(["concise", "detailed", "readme"] + list(file_versions.keys())))
        for file_type in file_types:
            default_path = f"{file_type}.md" if file_type != "readme" else "README.md"
            if file_type not in file_versions:
                file_versions[file_type] = {
                    "path": default_path,
                    "version": manifest.get("version", "1.0.0"),
                    "last_modified": today_str,
                    "content_hash": "",
                    "line_count": 0,
                    "primary_purpose": f"{file_type.capitalize()} documentation",
                }

            file_info = file_versions[file_type]
            file_name = file_info.get("path", default_path)
            target_file = plan_dir / file_name

            if target_file.exists():
                h = self.compute_hash(target_file)
                if h:
                    file_info["content_hash"] = h
                file_info["line_count"] = self.get_line_count(target_file)
                file_info["last_modified"] = today_str

        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        plan_name = manifest.get("plan_name", plan_dir.name)
        print(f"✅ {plan_name} ({plan_dir.relative_to(self.plan_root)}): Updated")
        return True

    def check_sync_status(self, plan_dir: Path) -> Dict[str, Any]:
        """Check if files match their recorded hashes in MANIFEST.yaml."""
        manifest_path = plan_dir / "MANIFEST.yaml"
        if not manifest_path.exists():
            return {"status": "no_manifest", "issues": ["Missing MANIFEST.yaml"]}

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f) or {}
        except Exception as e:
            return {"status": "error", "issues": [f"Invalid YAML: {e}"]}

        issues = []
        file_versions = manifest.get("file_versions", {})

        check_types = list(dict.fromkeys(["concise", "detailed", "readme"] + list(file_versions.keys())))
        for file_type in check_types:
            if file_type not in file_versions:
                issues.append(f"Missing '{file_type}' entry in file_versions")
                continue

            file_info = file_versions[file_type]
            file_path = plan_dir / file_info.get("path", f"{file_type}.md")

            if not file_path.exists():
                issues.append(f"File missing: {file_info.get('path')}")
                continue

            current_hash = self.compute_hash(file_path)
            stored_hash = file_info.get("content_hash")

            if not stored_hash:
                issues.append(f"{file_path.name}: No stored content_hash")
            elif current_hash != stored_hash:
                issues.append(f"{file_path.name}: Hash mismatch (stored={stored_hash[:8]}..., current={current_hash[:8]}...)")

        return {
            "status": "in_sync" if not issues else "out_of_sync",
            "issues": issues,
            "plan_name": manifest.get("plan_name", plan_dir.name),
        }

    def sync_all_plans(self):
        """Sync all plan directories."""
        plan_dirs = self.get_plan_dirs()
        print(f"🔄 Synchronizing {len(plan_dirs)} plan directories...")
        for plan_dir in plan_dirs:
            self.update_manifest(plan_dir)

    def report_sync_status(self) -> bool:
        """Report sync status for all plans. Returns True if all in sync."""
        plan_dirs = self.get_plan_dirs()
        print(f"\n📊 Plan Sync Status Report ({len(plan_dirs)} plans found)\n" + "=" * 50)

        all_ok = True
        for plan_dir in plan_dirs:
            res = self.check_sync_status(plan_dir)
            status = res["status"]
            rel_path = plan_dir.relative_to(self.plan_root)
            name = res.get("plan_name", plan_dir.name)

            if status == "in_sync":
                print(f"✅ [{rel_path}] {name}: In sync")
            elif status == "out_of_sync":
                all_ok = False
                print(f"❌ [{rel_path}] {name}: Out of sync")
                for issue in res["issues"]:
                    print(f"   - {issue}")
            else:
                all_ok = False
                print(f"⚠️  [{rel_path}] {name}: {status}")
                for issue in res.get("issues", []):
                    print(f"   - {issue}")

        print("=" * 50)
        if all_ok and plan_dirs:
            print("✨ All plans verified in sync!\n")
        elif not plan_dirs:
            print("⚠️  No plans found matching MANIFEST pattern.\n")
        else:
            print("❌ Some plans require synchronization.\n")
        return all_ok


def main():
    parser = argparse.ArgumentParser(description="Synchronize and verify plan version manifests.")
    # Auto-resolve plan root based on script location or current working dir
    script_dir = Path(__file__).resolve().parent
    if (script_dir / "master").exists():
        calc_default = script_dir
    elif (script_dir.parent / "master").exists():
        calc_default = script_dir.parent
    elif (script_dir.parent / "plan" / "master").exists():
        calc_default = script_dir.parent / "plan"
    elif Path(".nb/plan/master").exists():
        calc_default = Path(".nb/plan")
    else:
        calc_default = Path(".nb/plan")

    parser.add_argument("plan_root", nargs="?", default=str(calc_default), help="Path to plan directory (default: auto-detected)")
    parser.add_argument("--check-only", "--report", dest="check_only", action="store_true", help="Report sync status without modifying files")
    args = parser.parse_args()

    syncer = PlanVersionSync(Path(args.plan_root))

    if args.check_only:
        ok = syncer.report_sync_status()
        sys.exit(0 if ok else 1)
    else:
        syncer.sync_all_plans()
        ok = syncer.report_sync_status()
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
