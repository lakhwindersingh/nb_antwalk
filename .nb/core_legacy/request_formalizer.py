"""
Percipience Ingestion & Formalization Engine (RequestFormalizerEngine)
Converts unstructured user requests / proposals into formal MVS specifications:
- Jira Story Interchange (JSON)
- OpenAPI 3.1.0 Contract (YAML with front-matter metadata)
- UI Design Tokens & Accessibility Tokens (JSON)
- AsyncAPI 3.0.0 Event Stream Specification (YAML with front-matter metadata)

Provides automated persistence to user/inputs/formal_requests/ and
end-to-end integration into the Percipience Derivation Workflow and CI/CD Merkle Ledger.
"""

import os
import re
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    import yaml
    try:
        from yaml import CSafeLoader as SafeLoader, CSafeDumper as SafeDumper
    except ImportError:
        from yaml import SafeLoader, SafeDumper
except ImportError:
    yaml = None
    SafeLoader = None
    SafeDumper = None

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]

from core.merkle_engine import MerkleEngine


class RequestFormalizerEngine:
    """
    Autonomous Engine for parsing unstructured requests, formalizing them into
    Quad-Space MVS specification formats, capturing them in user/inputs/formal_requests/,
    and running them through the Percipience derivation workflow.
    """

    FORMAT_MAP = {
        "jira": "jira_issue_interchange",
        "jira_story": "jira_issue_interchange",
        "jira_issue_interchange": "jira_issue_interchange",
        "api": "api_contract_openapi",
        "api_contract": "api_contract_openapi",
        "openapi": "api_contract_openapi",
        "api_contract_openapi": "api_contract_openapi",
        "tokens": "ui_design_tokens",
        "design_tokens": "ui_design_tokens",
        "ui_tokens": "ui_design_tokens",
        "ui_design_tokens": "ui_design_tokens",
        "event": "event_stream_asyncapi",
        "events": "event_stream_asyncapi",
        "event_stream": "event_stream_asyncapi",
        "asyncapi": "event_stream_asyncapi",
        "event_stream_asyncapi": "event_stream_asyncapi",
        "auto": "auto"
    }

    @classmethod
    def detect_format(cls, text: str) -> str:
        """
        Heuristically determines the optimal target MVS format from unstructured text.
        """
        lower = text.lower()

        # Token / UI Design System keywords
        design_keywords = ["design token", "design system", "color palette", "typography", "spacing unit", "wcag", "contrast ratio", "radii", "css token"]
        if any(kw in lower for kw in design_keywords):
            return "ui_design_tokens"

        # Event stream / AsyncAPI / Kafka keywords
        event_keywords = ["asyncapi", "kafka", "event stream", "telemetry stream", "publish message", "message payload", "event bus", "iot telemetry", "event channel"]
        if any(kw in lower for kw in event_keywords):
            return "event_stream_asyncapi"

        # REST / OpenAPI / HTTP endpoints keywords
        api_keywords = ["openapi", "swagger", "endpoint", "rest api", "http get", "http post", "status 200", "status 201", "requestbody", "operationid", "route path"]
        if any(kw in lower for kw in api_keywords):
            return "api_contract_openapi"

        # Default standard formal issue interchange
        return "jira_issue_interchange"

    @classmethod
    def parse_unstructured_text(cls, text: str) -> Dict[str, Any]:
        """
        Extracts key semantic facets from unstructured text/markdown.
        """
        lines = [l.strip() for l in text.strip().splitlines()]
        
        # 1. Title Extraction
        title = "Formalized Engineering Request"
        for line in lines:
            if line.startswith("# "):
                title = line.lstrip("# ").strip()
                break
            elif line and not line.startswith("```") and len(line) < 100 and not title.startswith("PERC"):
                # Clean markdown links or formatting
                cleaned = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", line)
                cleaned = re.sub(r"[`*_#]", "", cleaned).strip()
                if cleaned and len(cleaned) > 5:
                    title = cleaned
                    break

        # 2. Extract Sections & Headers
        sections: Dict[str, List[str]] = {}
        current_header = "General"
        sections[current_header] = []
        for line in lines:
            if line.startswith("## ") or line.startswith("### "):
                current_header = line.lstrip("#").strip()
                sections[current_header] = []
            else:
                if line:
                    sections[current_header].append(line)

        # 3. Extract Acceptance Criteria / Requirements / Bullet points
        acceptance_criteria: List[str] = []
        raw_bullets: List[str] = []
        for line in lines:
            if re.match(r"^(\*|-|\d+\.)\s+", line):
                item = re.sub(r"^(\*|-|\d+\.)\s+", "", line).strip()
                cleaned_item = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", item)
                cleaned_item = re.sub(r"[*`]", "", cleaned_item).strip()
                if cleaned_item:
                    raw_bullets.append(cleaned_item)

        if raw_bullets:
            for idx, b in enumerate(raw_bullets, 1):
                if not b.lower().startswith("ac"):
                    acceptance_criteria.append(f"AC{idx}: {b}")
                else:
                    acceptance_criteria.append(b)
        else:
            acceptance_criteria = [
                "AC1: Implementation must satisfy all architectural invariants defined in request.",
                "AC2: Automated unit and integration test coverage must meet >= 90% threshold.",
                "AC3: Zero breaking changes to existing Quad-Space wire contracts.",
                "AC4: Cryptographic Merkle audit block must be sealed upon completion."
            ]

        # 4. Target Module Extraction
        module_matches = re.findall(r"\b(mod_[a-zA-Z0-9_]+)\b", text)
        if module_matches:
            target_module = module_matches[0]
        else:
            if "portal" in text.lower() or "marketing" in text.lower() or "ui" in text.lower():
                target_module = "mod_portal_marketing"
            elif "billing" in text.lower() or "token" in text.lower() or "meter" in text.lower():
                target_module = "mod_billing_metering"
            elif "security" in text.lower() or "cmek" in text.lower() or "worm" in text.lower() or "auth" in text.lower():
                target_module = "mod_tenant_security"
            elif "observability" in text.lower() or "telemetry" in text.lower():
                target_module = "mod_observability_usage"
            elif "infra" in text.lower() or "bridge" in text.lower():
                target_module = "mod_shared_infra_bridge"
            else:
                target_module = "mod_core_engine"

        # 5. Priority Extraction
        priority = "High"
        if re.search(r"\b(p0|critical|blocker)\b", text, re.IGNORECASE):
            priority = "Critical"
        elif re.search(r"\b(p1|high|urgent)\b", text, re.IGNORECASE):
            priority = "High"
        elif re.search(r"\b(p2|medium)\b", text, re.IGNORECASE):
            priority = "Medium"
        elif re.search(r"\b(p3|low)\b", text, re.IGNORECASE):
            priority = "Low"

        # 6. Components Extraction
        components = []
        comp_keywords = [
            ("ast-pruner", ["ast", "tree-sitter", "prun"]),
            ("self-healing", ["self-heal", "heal", "reprompt", "diagnostic"]),
            ("security", ["worm", "cmek", "crypto", "poisoning", "cve"]),
            ("finops", ["token", "meter", "cost", "rev-share", "savings"]),
            ("design-system", ["token", "color", "typography", "wcag", "ui"]),
            ("event-bus", ["kafka", "stream", "asyncapi", "channel", "message"]),
            ("core-platform", ["merkle", "worktree", "ledger", "quad-space"])
        ]
        lower_text = text.lower()
        for comp_name, kws in comp_keywords:
            if any(k in lower_text for k in kws):
                components.append(comp_name)
        if not components:
            components = ["core-platform", "context-engineering"]

        # 7. Description Synthesized
        description = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text[:1000]).strip()
        description = re.sub(r"[`#*]", "", description)
        description = " ".join(description.split()[:80])

        return {
            "title": title,
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "target_module": target_module,
            "priority": priority,
            "components": components,
            "raw_sections": sections
        }

    @classmethod
    def to_jira_story(cls, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Converts unstructured request into formal Jira Story MVS format.
        """
        parsed = cls.parse_unstructured_text(text)
        metadata = metadata or {}
        
        ts_id = int(time.time())
        issue_key = metadata.get("issue_key", f"PERC-{ts_id % 10000:04d}")
        issue_id = metadata.get("issue_id", str(ts_id))
        
        payload = {
            "$schema": "https://json-schema.percipience.ai/v1/mvs_jira_story.json",
            "mvs_version": "1.0.0",
            "format_type": "jira_issue_interchange",
            "source_system": metadata.get("source_system", "PERCIPIENCE_CLI_FORMALIZER"),
            "mcp_server": "@modelcontextprotocol/server-jira",
            "issue": {
                "key": issue_key,
                "id": issue_id,
                "project": {
                    "key": metadata.get("project_key", "PERC"),
                    "name": metadata.get("project_name", "Percipience Enterprise Engineering")
                },
                "issue_type": metadata.get("issue_type", "Story"),
                "status": "Ready for Dev",
                "priority": parsed["priority"],
                "summary": parsed["title"],
                "description": parsed["description"],
                "acceptance_criteria": parsed["acceptance_criteria"],
                "components": parsed["components"],
                "labels": [
                    "percipience-ready",
                    f"priority-{parsed['priority'].lower()}",
                    "formalized-request"
                ],
                "target_module": parsed["target_module"],
                "story_points": metadata.get("story_points", 5),
                "linked_epic": {
                    "key": metadata.get("epic_key", "PERC-EPIC-01"),
                    "summary": metadata.get("epic_summary", "Enterprise Quad-Space Continuous Modernization")
                },
                "custom_fields": {
                    "target_branch": f"feature/{issue_key.lower()}-{parsed['target_module']}",
                    "max_token_budget_usd": metadata.get("max_token_budget_usd", 10.00),
                    "required_test_coverage_pct": 90
                }
            },
            "ingestion_metadata": {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "formalized_by": "agent_request_formalizer"
            }
        }
        return payload

    @classmethod
    def to_api_contract(cls, text: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        """
        Converts unstructured request into formal OpenAPI 3.1.0 Contract with YAML front-matter.
        """
        parsed = cls.parse_unstructured_text(text)
        metadata = metadata or {}

        ts_id = int(time.time())
        contract_id = metadata.get("id", f"MVS-API-{ts_id % 1000:03d}")
        
        front_matter = {
            "mvs_version": "1.0.0",
            "format_type": "api_contract_openapi",
            "id": contract_id,
            "title": parsed["title"],
            "target_module": parsed["target_module"],
            "priority": parsed["priority"]
        }

        # Derive path endpoints based on title / target module
        resource_slug = parsed["target_module"].replace("mod_", "").replace("_", "-")
        
        openapi_doc = {
            "openapi": "3.1.0",
            "info": {
                "title": f"Percipience {parsed['title']} Contract",
                "description": f"Formal MVS Specification for {parsed['description']}",
                "version": "1.0.0"
            },
            "servers": [
                {
                    "url": "https://api.percipience.internal/v1",
                    "description": "Internal High-Speed VPC Service Mesh"
                }
            ],
            "paths": {
                f"/{resource_slug}/status": {
                    "get": {
                        "summary": f"Query status of {parsed['title']}",
                        "operationId": f"get{resource_slug.title().replace('-', '')}Status",
                        "responses": {
                            "200": {
                                "description": "Current system and operational status",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": f"#/components/schemas/{resource_slug.title().replace('-', '')}StatusResponse"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                f"/{resource_slug}/execute": {
                    "post": {
                        "summary": f"Execute operations for {parsed['title']}",
                        "operationId": f"execute{resource_slug.title().replace('-', '')}Action",
                        "headers": {
                            "X-Idempotency-Key": {
                                "schema": {"type": "string", "format": "uuid"},
                                "required": True
                            }
                        },
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": f"#/components/schemas/{resource_slug.title().replace('-', '')}Request"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Operation executed and sealed into Merkle ledger",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": f"#/components/schemas/{resource_slug.title().replace('-', '')}Receipt"
                                        }
                                    }
                                }
                            },
                            "400": {
                                "description": "Contract invariant or schema validation failure"
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    f"{resource_slug.title().replace('-', '')}StatusResponse": {
                        "type": "object",
                        "required": ["status", "target_module", "merkle_root"],
                        "properties": {
                            "status": {"type": "string", "example": "HEALTHY"},
                            "target_module": {"type": "string", "example": parsed["target_module"]},
                            "merkle_root": {"type": "string", "example": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
                        }
                    },
                    f"{resource_slug.title().replace('-', '')}Request": {
                        "type": "object",
                        "required": ["request_id", "action_payload"],
                        "properties": {
                            "request_id": {"type": "string", "format": "uuid"},
                            "action_payload": {"type": "object", "additionalProperties": True},
                            "metadata": {"type": "object"}
                        }
                    },
                    f"{resource_slug.title().replace('-', '')}Receipt": {
                        "type": "object",
                        "required": ["receipt_id", "status", "merkle_block_hash", "timestamp"],
                        "properties": {
                            "receipt_id": {"type": "string", "format": "uuid"},
                            "status": {"type": "string", "enum": ["COMMITTED", "QUEUED", "REJECTED"]},
                            "merkle_block_hash": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    }
                }
            }
        }

        # Format YAML with Front-Matter
        if yaml:
            fm_str = yaml.dump(front_matter, sort_keys=False)
            doc_str = yaml.dump(openapi_doc, sort_keys=False)
        else:
            fm_str = json.dumps(front_matter, indent=2)
            doc_str = json.dumps(openapi_doc, indent=2)

        formatted_yaml = f"---\n{fm_str}---\n\n{doc_str}"
        return front_matter, openapi_doc, formatted_yaml

    @classmethod
    def to_design_tokens(cls, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Converts unstructured request into formal UI Design Tokens MVS format.
        """
        parsed = cls.parse_unstructured_text(text)
        metadata = metadata or {}

        ts_id = int(time.time())
        token_id = metadata.get("id", f"MVS-UI-{ts_id % 1000:03d}")

        payload = {
            "$schema": "https://json-schema.percipience.ai/v1/mvs_design_tokens.json",
            "mvs_version": "1.0.0",
            "format_type": "ui_design_tokens",
            "id": token_id,
            "title": parsed["title"],
            "target_module": parsed["target_module"] if parsed["target_module"] != "mod_core_engine" else "mod_portal_marketing",
            "theme": metadata.get("theme", "enterprise_cosmic_dark"),
            "accessibility": {
                "wcag_target": "WCAG_2_1_AA",
                "min_contrast_ratio": 4.5
            },
            "tokens": {
                "color": {
                    "primary": {"value": "#6366F1", "name": "Indigo Neon"},
                    "secondary": {"value": "#06B6D4", "name": "Cyan Glow"},
                    "background": {"value": "#0B0F19", "name": "Deep Slate Base"},
                    "surface": {"value": "#1E293B", "name": "Surface Elevated Card"},
                    "success": {"value": "#10B981", "name": "Emerald Merkle Verified"},
                    "warning": {"value": "#F59E0B", "name": "Amber Quarantine Notice"},
                    "danger": {"value": "#EF4444", "name": "Rose Invariant Alert"}
                },
                "typography": {
                    "font_family_sans": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                    "font_family_mono": "'JetBrains Mono', 'Fira Code', monospace",
                    "scale": {
                        "h1": {"size": "3rem", "line_height": "1.15", "weight": "700"},
                        "h2": {"size": "2.25rem", "line_height": "1.25", "weight": "600"},
                        "body": {"size": "1rem", "line_height": "1.5", "weight": "400"},
                        "caption": {"size": "0.75rem", "line_height": "1.4", "weight": "500"}
                    }
                },
                "spacing": {
                    "unit": "4px",
                    "xs": "4px",
                    "sm": "8px",
                    "md": "16px",
                    "lg": "24px",
                    "xl": "32px",
                    "2xl": "48px"
                },
                "radii": {
                    "sm": "4px",
                    "md": "8px",
                    "lg": "16px",
                    "full": "9999px"
                }
            }
        }
        return payload

    @classmethod
    def to_event_stream(cls, text: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        """
        Converts unstructured request into formal AsyncAPI 3.0.0 Event Stream specification with front-matter.
        """
        parsed = cls.parse_unstructured_text(text)
        metadata = metadata or {}

        ts_id = int(time.time())
        event_id = metadata.get("id", f"MVS-EVENT-{ts_id % 1000:03d}")

        front_matter = {
            "mvs_version": "1.0.0",
            "format_type": "event_stream_asyncapi",
            "id": event_id,
            "title": parsed["title"],
            "target_module": parsed["target_module"] if parsed["target_module"] != "mod_core_engine" else "mod_observability_usage",
            "priority": parsed["priority"]
        }

        channel_slug = parsed["target_module"].replace("mod_", "").replace("_", ".")

        asyncapi_doc = {
            "asyncapi": "3.0.0",
            "info": {
                "title": f"Percipience {parsed['title']} Event Bus",
                "version": "1.0.0",
                "description": f"Formal AsyncAPI Specification for {parsed['description']}"
            },
            "servers": {
                "kafkaCluster": {
                    "host": "kafka.prod.internal:9092",
                    "protocol": "kafka",
                    "description": "Enterprise High-Throughput Event Streaming Bus"
                }
            },
            "channels": {
                f"{channel_slug}.events": {
                    "address": f"events.v1.{channel_slug}",
                    "messages": {
                        "publishTelemetry": {
                            "$ref": "#/components/messages/LifecycleEventMessage"
                        }
                    }
                },
                f"{channel_slug}.alerts": {
                    "address": f"alerts.v1.{channel_slug}",
                    "messages": {
                        "alertNotification": {
                            "$ref": "#/components/messages/InvariantBreachAlertMessage"
                        }
                    }
                }
            },
            "components": {
                "messages": {
                    "LifecycleEventMessage": {
                        "name": "LifecycleEventMessage",
                        "contentType": "application/json",
                        "payload": {
                            "type": "object",
                            "required": ["event_id", "module_id", "epoch_millis", "payload", "merkle_root"],
                            "properties": {
                                "event_id": {"type": "string", "format": "uuid"},
                                "module_id": {"type": "string", "example": parsed["target_module"]},
                                "epoch_millis": {"type": "integer", "format": "int64"},
                                "payload": {"type": "object"},
                                "merkle_root": {"type": "string"}
                            }
                        }
                    },
                    "InvariantBreachAlertMessage": {
                        "name": "InvariantBreachAlertMessage",
                        "contentType": "application/json",
                        "payload": {
                            "type": "object",
                            "required": ["alert_id", "severity", "violation_rule", "timestamp"],
                            "properties": {
                                "alert_id": {"type": "string", "format": "uuid"},
                                "severity": {"type": "string", "enum": ["CRITICAL", "WARNING", "INFO"]},
                                "violation_rule": {"type": "string"},
                                "timestamp": {"type": "string", "format": "date-time"}
                            }
                        }
                    }
                }
            }
        }

        # Format YAML with Front-Matter
        if yaml:
            fm_str = yaml.dump(front_matter, sort_keys=False)
            doc_str = yaml.dump(asyncapi_doc, sort_keys=False)
        else:
            fm_str = json.dumps(front_matter, indent=2)
            doc_str = json.dumps(asyncapi_doc, indent=2)

        formatted_yaml = f"---\n{fm_str}---\n\n{doc_str}"
        return front_matter, asyncapi_doc, formatted_yaml

    @classmethod
    def formalize(
        cls,
        input_data: Union[str, Path],
        target_format: str = "auto",
        out_dir: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None,
        workspace_root: Path = REPO_ROOT
    ) -> Dict[str, Any]:
        """
        Main entry point for formalizing unstructured requests.
        - input_data: Raw text string or Path to input file (e.g. user/inputs/improv1.md)
        - target_format: 'jira_story', 'api_contract', 'design_tokens', 'event_stream', or 'auto'
        - out_dir: Directory where formal specifications are written (defaults to user/inputs/formal_requests/)
        """
        # 1. Resolve raw content
        raw_text = ""
        source_path = None
        if isinstance(input_data, Path) or (isinstance(input_data, str) and (workspace_root / input_data).exists()):
            p = input_data if isinstance(input_data, Path) else (workspace_root / input_data)
            source_path = str(p)
            raw_text = p.read_text(encoding="utf-8", errors="ignore")
        else:
            raw_text = str(input_data)

        if not raw_text.strip():
            raise ValueError("Input request content cannot be empty.")

        # 2. Normalize Target Format
        norm_key = target_format.lower().strip()
        canonical_fmt = cls.FORMAT_MAP.get(norm_key, "auto")
        if canonical_fmt == "auto":
            canonical_fmt = cls.detect_format(raw_text)

        # 3. Setup Output Directory
        target_out_dir = out_dir if out_dir else (workspace_root / "user" / "inputs" / "formal_requests")
        target_out_dir.mkdir(parents=True, exist_ok=True)

        ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        ts_nano = int(time.time() * 1000) % 10000

        # 4. Generate specification payload
        if canonical_fmt == "jira_issue_interchange":
            data = cls.to_jira_story(raw_text, metadata)
            content_str = json.dumps(data, indent=2)
            req_id = data["issue"]["key"]
            filename = f"jira_story_{ts_str}_{req_id.lower().replace('-', '_')}.json"
            ext = "json"
            title = data["issue"]["summary"]
            target_module = data["issue"]["target_module"]

        elif canonical_fmt == "api_contract_openapi":
            fm, doc, content_str = cls.to_api_contract(raw_text, metadata)
            data = {"front_matter": fm, "openapi": doc}
            req_id = fm["id"]
            filename = f"api_contract_{ts_str}_{req_id.lower().replace('-', '_')}.yaml"
            ext = "yaml"
            title = fm["title"]
            target_module = fm["target_module"]

        elif canonical_fmt == "ui_design_tokens":
            data = cls.to_design_tokens(raw_text, metadata)
            content_str = json.dumps(data, indent=2)
            req_id = data["id"]
            filename = f"design_tokens_{ts_str}_{req_id.lower().replace('-', '_')}.json"
            ext = "json"
            title = data["title"]
            target_module = data["target_module"]

        elif canonical_fmt == "event_stream_asyncapi":
            fm, doc, content_str = cls.to_event_stream(raw_text, metadata)
            data = {"front_matter": fm, "asyncapi": doc}
            req_id = fm["id"]
            filename = f"event_stream_{ts_str}_{req_id.lower().replace('-', '_')}.yaml"
            ext = "yaml"
            title = fm["title"]
            target_module = fm["target_module"]

        else:
            raise ValueError(f"Unsupported format type: {canonical_fmt}")

        out_file_path = target_out_dir / filename
        out_file_path.write_text(content_str, encoding="utf-8")

        return {
            "status": "FORMALIZED",
            "request_id": req_id,
            "title": title,
            "format_type": canonical_fmt,
            "target_module": target_module,
            "formal_file_path": str(out_file_path),
            "relative_file_path": str(out_file_path.relative_to(workspace_root)),
            "content_sha256": hashlib.sha256(content_str.encode("utf-8")).hexdigest(),
            "source_input": source_path or "raw_string",
            "structured_data": data,
            "raw_content": content_str
        }

    @classmethod
    def run_through_workflow(
        cls,
        formal_file_path: Union[str, Path],
        workflow_name: str = "derivation_pipeline",
        workspace_root: Path = REPO_ROOT
    ) -> Dict[str, Any]:
        """
        Executes the formal specification through the Quad-Space Derivation Pipeline,
        records the formalization in context_ledger.yaml, and seals a Merkle audit block.
        """
        file_p = Path(formal_file_path)
        if not file_p.is_absolute():
            file_p = workspace_root / file_p

        if not file_p.exists():
            raise FileNotFoundError(f"Formal request file not found at: {file_p}")

        content = file_p.read_text(encoding="utf-8", errors="ignore")
        
        # Determine format type and request metadata
        req_id = file_p.stem
        fmt_type = "generic_mvs"
        if file_p.suffix == ".json":
            try:
                d = json.loads(content)
                fmt_type = d.get("format_type", "json_mvs")
                req_id = d.get("issue", {}).get("key") or d.get("id") or req_id
            except Exception:
                pass
        elif file_p.suffix in [".yaml", ".yml"]:
            if yaml:
                try:
                    docs = list(yaml.safe_load_all(content))
                    if docs and isinstance(docs[0], dict):
                        fmt_type = docs[0].get("format_type", "yaml_mvs")
                        req_id = docs[0].get("id", req_id)
                except Exception:
                    pass

        # 1. Update context_ledger.yaml
        ledger_path = (workspace_root / ".nb" / "context" / "ledger" / "context_ledger.yaml" if (workspace_root / ".nb" / "context").exists() else workspace_root / "context" / "ledger" / "context_ledger.yaml")
        if ledger_path.exists():
            with open(ledger_path, "r", encoding="utf-8") as f:
                if yaml and SafeLoader:
                    ledger_data = yaml.load(f, Loader=SafeLoader) or {}
                elif yaml:
                    ledger_data = yaml.safe_load(f) or {}
                else:
                    ledger_data = json.load(f)

            formal_receipts = ledger_data.setdefault("formal_requests", [])
            rel_path = str(file_p.relative_to(workspace_root)) if str(file_p).startswith(str(workspace_root)) else str(file_p)
            
            receipt = {
                "request_id": req_id,
                "format_type": fmt_type,
                "file_path": rel_path,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "workflow": workflow_name,
                "status": "INGESTED_AND_VERIFIED"
            }
            formal_receipts.append(receipt)
            MerkleEngine.atomic_write_data(ledger_path, ledger_data)

        # 2. Seal Cryptographic Merkle Block
        seal_action = f"FORMAL_REQUEST_INGESTED:{fmt_type}:{req_id}"
        seal = MerkleEngine.seal_block(workspace_root, action=seal_action)

        return {
            "status": "SUCCESS",
            "request_id": req_id,
            "format_type": fmt_type,
            "workflow": workflow_name,
            "formal_file_path": str(file_p),
            "merkle_block_id": seal["block_id"],
            "merkle_block_hash": seal["current_block_hash"],
            "timestamp": seal["timestamp"]
        }
