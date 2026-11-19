#!/usr/bin/env python3
"""
Percipience Declarative Tool Contracts & JSON Schema Validation Engine (GAP-AGT-04 / TODO-AGT-04)
Provides Draft-07 parameter and return validation, idempotency caching,
and execution deadline/timeout enforcement for autonomous agent tools.
"""

import concurrent.futures
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) >= 3 and (Path(__file__).resolve().parents[2] / ".nb").exists() else Path(__file__).resolve().parents[1]


class ToolContractValidationError(Exception):
    """Raised when tool input or output schemas are violated."""
    pass


class ToolTimeoutError(Exception):
    """Raised when a tool execution breaches its allotted timeout deadline."""
    pass


@dataclass
class ToolContract:
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    is_idempotent: bool = False
    mutates_filesystem: bool = False
    timeout_seconds: int = 30
    required_capabilities: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolContract":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            returns=data.get("returns", {}),
            is_idempotent=bool(data.get("is_idempotent", False)),
            mutates_filesystem=bool(data.get("mutates_filesystem", False)),
            timeout_seconds=int(data.get("timeout_seconds", 30)),
            required_capabilities=list(data.get("required_capabilities", []))
        )


class ToolContractValidator:
    """
    Validates tool calls against declarative contracts, enforces execution deadlines,
    and caches idempotent results.
    """

    def __init__(self, tools_dir: Optional[Path] = None):
        self.tools_dir = tools_dir or (REPO_ROOT / ".nb" / "agentic" / "custom" / "tools")
        self.registry: Dict[str, ToolContract] = {}
        self.idempotency_cache: Dict[str, Any] = {}
        self.load_registry()

    def load_registry(self) -> None:
        """Discovers and registers tool YAML contracts from the registry directory."""
        if not self.tools_dir.exists():
            return
        for fpath in self.tools_dir.glob("*.yaml"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and "name" in data:
                    self.register_tool(ToolContract.from_dict(data))
            except Exception:
                pass

    def register_tool(self, contract: ToolContract) -> None:
        """Registers a tool contract into the runtime validator."""
        self.registry[contract.name] = contract

    def _validate_schema(self, data: Any, schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Lightweight recursive JSON schema validator covering types,
        required properties, minLength, and enums without external heavy dependencies.
        """
        expected_type = schema.get("type")
        if expected_type == "object":
            if not isinstance(data, dict):
                return False, f"Expected object, got {type(data).__name__}"
            required = schema.get("required", [])
            for req in required:
                if req not in data:
                    return False, f"Missing required property: '{req}'"
            properties = schema.get("properties", {})
            for key, val in data.items():
                if key in properties:
                    valid, err = self._validate_schema(val, properties[key])
                    if not valid:
                        return False, f"Property '{key}': {err}"
        elif expected_type == "array":
            if not isinstance(data, (list, tuple)):
                return False, f"Expected array, got {type(data).__name__}"
            items_schema = schema.get("items")
            if items_schema:
                for idx, item in enumerate(data):
                    valid, err = self._validate_schema(item, items_schema)
                    if not valid:
                        return False, f"Array index [{idx}]: {err}"
        elif expected_type == "string":
            if not isinstance(data, str):
                return False, f"Expected string, got {type(data).__name__}"
            if "minLength" in schema and len(data) < schema["minLength"]:
                return False, f"String length {len(data)} < minLength {schema['minLength']}"
            if "enum" in schema and data not in schema["enum"]:
                return False, f"Value '{data}' not in allowed enum {schema['enum']}"
        elif expected_type in ("integer", "number"):
            if not isinstance(data, (int, float)) or (expected_type == "integer" and isinstance(data, bool)):
                return False, f"Expected {expected_type}, got {type(data).__name__}"
            if "minimum" in schema and data < schema["minimum"]:
                return False, f"Value {data} < minimum {schema['minimum']}"
            if "maximum" in schema and data > schema["maximum"]:
                return False, f"Value {data} > maximum {schema['maximum']}"
        elif expected_type == "boolean":
            if not isinstance(data, bool):
                return False, f"Expected boolean, got {type(data).__name__}"

        return True, None

    def validate_arguments(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates tool input arguments against its parameter contract."""
        if tool_name not in self.registry:
            return False, f"Unknown tool: '{tool_name}' not registered in tool contract registry"
        contract = self.registry[tool_name]
        return self._validate_schema(args, contract.parameters)

    def validate_output(self, tool_name: str, output: Any) -> Tuple[bool, Optional[str]]:
        """Validates tool return payload against its returns contract."""
        if tool_name not in self.registry:
            return False, f"Unknown tool: '{tool_name}'"
        contract = self.registry[tool_name]
        return self._validate_schema(output, contract.returns)

    def _compute_cache_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        canonical = json.dumps(args, sort_keys=True)
        return f"{tool_name}:{hashlib.sha256(canonical.encode()).hexdigest()}"

    def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        handler_fn: Callable[..., Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes a tool with pre-call parameter validation, idempotency caching,
        timeout enforcement, and post-call return schema validation.
        """
        if tool_name not in self.registry:
            raise ToolContractValidationError(f"UNKNOWN_TOOL: Tool '{tool_name}' is not registered")

        contract = self.registry[tool_name]

        # 1. Idempotency Cache Check
        cache_key = self._compute_cache_key(tool_name, args)
        if contract.is_idempotent and cache_key in self.idempotency_cache:
            return {
                "status": "CACHED",
                "tool": tool_name,
                "result": self.idempotency_cache[cache_key],
                "cache_hit": True
            }

        # 2. Pre-Call Parameter Validation
        valid_args, arg_err = self.validate_arguments(tool_name, args)
        if not valid_args:
            raise ToolContractValidationError(f"INVALID_TOOL_ARGUMENTS: {arg_err}")

        # 3. Timeout Deadline Enforcement
        timeout_limit = timeout_override or contract.timeout_seconds
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(handler_fn, **args)

        try:
            raw_output = future.result(timeout=timeout_limit)
        except concurrent.futures.TimeoutError:
            executor.shutdown(wait=False, cancel_futures=True)
            raise ToolTimeoutError(
                f"TOOL_TIMEOUT_EXCEEDED: Execution of '{tool_name}' exceeded {timeout_limit}s deadline"
            )
        except Exception as ex:
            executor.shutdown(wait=False)
            raise ex
        finally:
            executor.shutdown(wait=False)

        # 4. Post-Call Return Schema Validation
        valid_out, out_err = self.validate_output(tool_name, raw_output)
        if not valid_out:
            raise ToolContractValidationError(f"INVALID_TOOL_OUTPUT: {out_err}")

        # 5. Populate Idempotency Cache
        if contract.is_idempotent:
            self.idempotency_cache[cache_key] = raw_output

        return {
            "status": "SUCCESS",
            "tool": tool_name,
            "result": raw_output,
            "cache_hit": False
        }
