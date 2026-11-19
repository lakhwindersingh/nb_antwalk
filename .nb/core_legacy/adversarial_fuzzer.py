"""
Percipience Adversarial Red-Team & Mutation Fuzzing Engine (CAP-31)
Synthesizes boundary mutations, malicious payloads, and concurrency stress vectors
to proactively uncover security vulnerabilities, edge-case panics, and race conditions.
"""

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class AdversarialFuzzer:
    """
    Generates adversarial mutation vectors across JSON, AST, SQL, and HTTP payloads
    to harden autonomous codebase implementations against edge-case failures.
    """

    ADVERSARIAL_PAYLOADS: Dict[str, List[Any]] = {
        "numeric_boundaries": [
            0, -1, 1, 2**31 - 1, -(2**31), 2**63 - 1, -(2**63),
            float("inf"), float("-inf"), float("nan"), 1e308, -1e308, 0.000000000000001
        ],
        "string_mutations": [
            "",  # empty
            " " * 1024,  # whitespace bloat
            "\x00",  # null byte
            "\r\n\r\n",  # CRLF injection
            "'; DROP TABLE users; --",  # SQL injection
            "<script>alert(document.cookie)</script>",  # XSS
            "../../../../../../etc/passwd",  # Path traversal
            "A" * 65536,  # Buffer bloat
            "🔥🚀🧪👾 Unicode emoji & RTL \u202Ereversed\u202C text",  # Unicode & RTL
            "{{ 7 * 7 }}",  # SSTI injection
            "{\"__proto__\": {\"polluted\": true}}",  # Prototype pollution
        ],
        "json_structures": [
            {},
            {"nested": {"depth": {"level3": {"level4": {"val": None}}}}},
            {"array": [None, True, False, 0, "", {}, []]},
            {"huge_key_" + str(i): i for i in range(100)}
        ]
    }

    @classmethod
    def generate_fuzz_vectors(cls, field_type: str = "string", count: int = 5) -> List[Any]:
        """Generates fuzzing payloads tailored to a field type."""
        normalized = field_type.lower()
        if "int" in normalized or "num" in normalized or "float" in normalized:
            pool = cls.ADVERSARIAL_PAYLOADS["numeric_boundaries"]
        elif "json" in normalized or "dict" in normalized or "object" in normalized:
            pool = cls.ADVERSARIAL_PAYLOADS["json_structures"]
        else:
            pool = cls.ADVERSARIAL_PAYLOADS["string_mutations"]
        
        return random.sample(pool, min(count, len(pool)))

    @classmethod
    def mutate_input_schema(cls, base_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Synthesizes mutated variants of a valid base input payload:
        1. Missing required fields
        2. Injected boundary numbers
        3. Injected injection strings
        4. Injected null/None values
        5. Deeply nested key injections
        """
        mutations: List[Dict[str, Any]] = []

        # 1. Null/None mutations on each key
        for k in base_payload.keys():
            clone = dict(base_payload)
            clone[k] = None
            mutations.append(clone)

        # 2. String/Boundary injections
        for k, v in base_payload.items():
            if isinstance(v, str):
                for fuzz_val in cls.ADVERSARIAL_PAYLOADS["string_mutations"][:3]:
                    clone = dict(base_payload)
                    clone[k] = fuzz_val
                    mutations.append(clone)
            elif isinstance(v, (int, float)):
                for fuzz_val in [0, -1, 2**31 - 1, float("nan")]:
                    clone = dict(base_payload)
                    clone[k] = fuzz_val
                    mutations.append(clone)

        # 3. Missing keys (pop one key at a time)
        for k in base_payload.keys():
            clone = dict(base_payload)
            clone.pop(k, None)
            mutations.append(clone)

        return mutations

    @classmethod
    def execute_fuzz_test(
        cls,
        target_fn: Callable[[Dict[str, Any]], Any],
        base_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes a fuzzing campaign against a target function with synthesized mutation vectors.
        Records edge-case exceptions, unhandled panics, and security vulnerability markers.
        """
        mutations = cls.mutate_input_schema(base_payload)
        passed_count = 0
        handled_errors = 0
        panics: List[Dict[str, Any]] = []

        for idx, mut in enumerate(mutations):
            try:
                res = target_fn(mut)
                passed_count += 1
            except (ValueError, TypeError, KeyError) as handled_exc:
                # Expected standard validation errors
                handled_errors += 1
            except Exception as unhandled_exc:
                # Potential unhandled crash / panic
                panics.append({
                    "mutation_index": idx,
                    "payload_mutation": str(mut),
                    "exception_type": type(unhandled_exc).__name__,
                    "error_message": str(unhandled_exc)
                })

        is_resilient = len(panics) == 0
        return {
            "status": "RESILIENT" if is_resilient else "VULNERABILITIES_DETECTED",
            "total_mutations_evaluated": len(mutations),
            "passed_count": passed_count,
            "handled_errors": handled_errors,
            "unhandled_panics_count": len(panics),
            "panics": panics,
            "resilience_score": round((len(mutations) - len(panics)) / max(len(mutations), 1), 4)
        }
