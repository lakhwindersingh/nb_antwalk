#!/usr/bin/env python3
"""
Automated Content Hash Verification Tool.
Verifies SHA-256 cryptographic hashes of all tracked files in MANIFEST.yaml across all active plans.
"""

import hashlib
import sys
from pathlib import Path
from typing import Dict, Any
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
PLAN_ROOT = REPO_ROOT / ".nb/plan"


def compute_sha256(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def verify_all_hashes() -> bool:
    print(f"🔒 Verifying Content Hashes across all active plans in: {PLAN_ROOT}")
    manifest_files = sorted(PLAN_ROOT.glob("**/MANIFEST.yaml"))
    
    total_files = 0
    mismatches = 0
    missing = 0

    for mf in manifest_files:
        if "templates" in mf.parts or "archive" in mf.parts:
            continue
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"❌ Failed to read {mf}: {e}")
            return False

        plan_id = data.get("plan_id", mf.parent.name)
        file_versions = data.get("file_versions", {})

        for file_key, info in file_versions.items():
            total_files += 1
            rel_name = info.get("path", f"{file_key}.md")
            target = mf.parent / rel_name
            expected_hash = info.get("content_hash", "")

            if not target.exists():
                print(f"❌ [{plan_id}] Missing tracked file: {target}")
                missing += 1
                continue

            actual_hash = compute_sha256(target)
            if actual_hash != expected_hash:
                print(f"❌ [{plan_id}] Hash mismatch for {rel_name}: expected {expected_hash[:10]}..., got {actual_hash[:10]}...")
                mismatches += 1
            else:
                pass

    print(f"\n📊 Hash Verification Summary: {total_files} tracked files checked.")
    if mismatches == 0 and missing == 0:
        print("✨ 100% Cryptographic Content Hash Integrity Verified (0 mismatches, 0 missing).")
        return True
    else:
        print(f"❌ Verification Failed: {mismatches} mismatches, {missing} missing files.")
        return False


def main():
    ok = verify_all_hashes()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
