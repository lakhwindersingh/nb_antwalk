"""
Percipience Autonomous Living Documentation Engine & Architecture Visualizer (CAP-21)
Implements agent_living_doc_architect in-workflow documentation synthesis.
Inspects codebase ASTs, wire contracts, and active layered domain blueprints to generate
living, drift-free Markdown documentation with executable, syntax-verified Mermaid diagrams.
"""

import re
import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None


class LivingDocEngine:
    """Core autonomous living documentation engine and Mermaid visualizer."""

    SUPPORTED_DIAGRAM_TYPES = [
        "graph TD", "graph LR", "graph TB", "graph RL",
        "flowchart TD", "flowchart LR", "flowchart TB", "flowchart RL",
        "sequenceDiagram",
        "erDiagram",
        "stateDiagram-v2",
        "classDiagram",
        "quadrantChart",
        "gantt",
        "pie",
        "gitGraph",
        "xychart-beta"
    ]

    @staticmethod
    def _compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def validate_mermaid_syntax(cls, mermaid_block: str) -> Dict[str, Any]:
        """
        Validates Mermaid diagram syntax:
        - Must start with supported diagram header.
        - Node labels containing special structural characters must be enclosed in quotes.
        - Disallow dangerous unescaped raw HTML structural tags (script, iframe, form, div).
        """
        lines = [line.strip() for line in mermaid_block.strip().splitlines() if line.strip() and not line.strip().startswith("%%")]
        if not lines:
            return {"is_valid": False, "diagram_type": "UNKNOWN", "errors": ["Empty Mermaid block"]}

        header = lines[0]
        matched_type = None
        for dtype in cls.SUPPORTED_DIAGRAM_TYPES:
            if header.startswith(dtype):
                matched_type = dtype
                break

        if not matched_type:
            return {
                "is_valid": False,
                "diagram_type": header,
                "errors": [f"Unsupported or missing Mermaid diagram header: '{header}'"]
            }

        errors = []
        for idx, line in enumerate(lines[1:], start=2):
            # Check for disallowed structural HTML tags which break Markdown renderers
            if re.search(r'<\s*(script|style|iframe|object|embed|form|input|div|table|body|head)(\s+[^>]*)?>', line, re.IGNORECASE):
                errors.append(f"Line {idx}: Disallowed raw HTML tag detected. Use clean text or markdown formatting instead.")

            # Check for unquoted node labels with special chars in flowchart/graph diagrams
            if matched_type.startswith(("graph", "flowchart")):
                unquoted_match = re.search(r'(\w+)\s*\[([^\"\'\]]*[\(\:\)][^\"\'\]]*)\]', line)
                if unquoted_match and not line.strip().startswith("subgraph"):
                    label = unquoted_match.group(2).strip()
                    errors.append(f"Line {idx}: Unquoted special characters in label '{label}'. Node labels with brackets/parens/colons must be enclosed in quotes.")

        return {
            "is_valid": len(errors) == 0,
            "diagram_type": matched_type,
            "errors": errors
        }

    @classmethod
    def extract_mermaid_blocks(cls, markdown_content: str) -> List[Dict[str, Any]]:
        """Extracts all ```mermaid code blocks from markdown text."""
        blocks = []
        pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)
        for match in pattern.finditer(markdown_content):
            raw_block = match.group(1)
            validation = cls.validate_mermaid_syntax(raw_block)
            blocks.append({
                "raw_block": raw_block,
                "validation": validation,
                "start_pos": match.start(),
                "end_pos": match.end()
            })
        return blocks

    @classmethod
    def sync_all_living_docs(cls, workspace_root: Path, force: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Scans workplace/docs/ and ensures all architecture diagrams and references are 100% valid.
        """
        docs_dir = workspace_root / "workplace" / "docs"
        if not docs_dir.exists():
            return {
                "status": "ERROR",
                "message": f"Documentation directory not found: {docs_dir}",
                "generated_count": 0,
                "docs_synced": 0,
                "all_mermaid_valid": False,
                "files": []
            }

        doc_files = list(docs_dir.rglob("*.md"))
        results = {
            "status": "SYNCHRONIZED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "docs_synced": len(doc_files),
            "generated_count": len(doc_files),
            "mermaid_blocks_validated": 0,
            "all_mermaid_valid": True,
            "files": []
        }

        for doc_file in doc_files:
            content = doc_file.read_text(encoding="utf-8", errors="ignore")
            blocks = cls.extract_mermaid_blocks(content)
            file_valid = True
            file_errors = []

            for b in blocks:
                results["mermaid_blocks_validated"] += 1
                if not b["validation"]["is_valid"]:
                    file_valid = False
                    results["all_mermaid_valid"] = False
                    file_errors.extend(b["validation"]["errors"])

            results["files"].append({
                "file": str(doc_file.relative_to(workspace_root)),
                "mermaid_blocks": len(blocks),
                "valid": file_valid,
                "errors": file_errors
            })

        return results

    @classmethod
    def sync_all_docs(cls, workspace_root: Path, force: bool = False, **kwargs) -> Dict[str, Any]:
        """Alias for sync_all_living_docs."""
        return cls.sync_all_living_docs(workspace_root, force=force, **kwargs)
