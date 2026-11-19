"""
Percipience Inbound Indirect Prompt Injection Firewall (CAP-38 / TODO-COMP-06)
Enterprise Competitor Parity: Prompt Armor / Lakera Guard.
Scans untrusted inbound payloads (Jira tickets, PR comments, issue descriptions, external web texts)
for adversarial delimiters, jailbreaks, prompt hijacking overrides, obfuscated base64 attacks,
and role usurpation prior to context assembly.
"""

import re
import json
import base64
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class PromptInjectionGuard:
    """
    Inbound Indirect Prompt Injection Firewall & Jailbreak Sentinel.
    Analyzes payloads for adversarial prompts, instruction escape sequences, and evasion vectors.
    """

    # Structured detection rules with category, pattern, severity, and weight
    INJECTION_RULES: List[Dict[str, Any]] = [
        # 1. Direct instruction overrides & jailbreak markers
        {
            "category": "DIRECT_JAILBREAK",
            "severity": "CRITICAL",
            "weight": 0.50,
            "pattern": re.compile(
                r'(?i)\b(?:ignore|disregard|forget|bypass|override)\b.*?\b(?:instructions|system prompt|prior guidelines|guardrails|safety rules)\b'
            ),
            "description": "Direct instruction override or safety filter bypass command"
        },
        {
            "category": "JAILBREAK_PERSONA",
            "severity": "CRITICAL",
            "weight": 0.45,
            "pattern": re.compile(
                r'(?i)\b(?:DAN mode|jailbreak|developer mode enabled|unrestricted mode|evil mode|do anything now)\b'
            ),
            "description": "Adversarial jailbreak persona activation (e.g. DAN, developer mode)"
        },
        {
            "category": "ROLE_SWITCH",
            "severity": "HIGH",
            "weight": 0.40,
            "pattern": re.compile(
                r'(?i)\b(?:you are now in|switch to|act as an?)\s+(?:unrestricted|developer|raw|jailbroken|unfiltered)\s+(?:mode|ai|assistant)\b'
            ),
            "description": "Forced persona switch to unrestricted or unfiltered assistant"
        },

        # 2. Boundary hijacking & instruction delimiters
        {
            "category": "DELIMITER_HIJACK",
            "severity": "CRITICAL",
            "weight": 0.50,
            "pattern": re.compile(
                r'(?i)(?:"""\s*SYSTEM:|\[INST\]|<<SYS>>|<\|im_start\|>|<\|system\|>|<system>|=== SYSTEM OVERRIDE ===)'
            ),
            "description": "Synthetic prompt system delimiter or chat template boundary injection"
        },
        {
            "category": "CHAT_ROLE_INJECTION",
            "severity": "HIGH",
            "weight": 0.40,
            "pattern": re.compile(
                r'(?i)(?:\{\s*"role"\s*:\s*"system"\s*\}|^(?:Human|Assistant|System):\s+)',
                re.MULTILINE
            ),
            "description": "Structured role-switching injection payload in external text"
        },

        # 3. Role usurpation & administrative spoofing
        {
            "category": "ROLE_USURPATION",
            "severity": "HIGH",
            "weight": 0.35,
            "pattern": re.compile(
                r'(?i)\b(?:I am the|speaking as the)\s+(?:system administrator|root user|security auditor|lead architect|Anthropic engineer)\b'
            ),
            "description": "Spoofed administrative authority claiming bypass authorization"
        },
        {
            "category": "EMERGENCY_OVERRIDE_SPOOF",
            "severity": "HIGH",
            "weight": 0.35,
            "pattern": re.compile(
                r'(?i)\b(?:emergency bypass authorized|override protocol\s+0x[0-9a-f]+|disable all security gates)\b'
            ),
            "description": "Fabricated security override protocol command"
        },

        # 4. Data exfiltration & prompt leakage probes
        {
            "category": "PROMPT_EXFILTRATION",
            "severity": "HIGH",
            "weight": 0.40,
            "pattern": re.compile(
                r'(?i)\b(?:repeat all instructions verbatim|output your initial prompt|print your system instructions|disclose your rules)\b'
            ),
            "description": "System prompt exfiltration probe"
        },
        {
            "category": "EGRESS_EXFILTRATION",
            "severity": "CRITICAL",
            "weight": 0.45,
            "pattern": re.compile(
                r'(?i)\b(?:curl|wget|fetch|send|post)\b.*?\b(?:webhook\.site|requestbin|ngrok\.io|https?://[a-zA-Z0-9_\-\.]+/exfil)\b'
            ),
            "description": "Automated data exfiltration URL or webhook payload"
        },

        # 5. Obfuscation & invisible evasion
        {
            "category": "ZERO_WIDTH_EVASION",
            "severity": "MEDIUM",
            "weight": 0.25,
            "pattern": re.compile(r'[\u200B-\u200D\uFEFF]'),
            "description": "Invisible zero-width Unicode characters used for steganographic filter evasion"
        }
    ]

    QUARANTINE_LOG = REPO_ROOT / "user" / "hitl" / "injection_quarantine.jsonl"

    def __init__(self):
        self._telemetry = {
            "total_payloads_scanned": 0,
            "allowed_count": 0,
            "quarantined_count": 0,
            "blocked_count": 0,
            "injections_by_category": {}
        }

    def scan_payload(
        self,
        payload: str,
        source: str = "external_untrusted",
        strict: bool = False
    ) -> Dict[str, Any]:
        """
        Scans inbound payload for prompt injection, jailbreaks, and adversarial markers.
        Returns risk score, verdict, violation list, and optional sanitized output.
        """
        t0 = time.perf_counter()
        violations: List[Dict[str, Any]] = []
        raw_score = 0.0

        # 1. Regex pattern matching across known adversarial vectors
        for rule in self.INJECTION_RULES:
            match = rule["pattern"].search(payload)
            if match:
                snippet = match.group(0)[:80]
                violations.append({
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "weight": rule["weight"],
                    "description": rule["description"],
                    "snippet": snippet
                })
                raw_score += rule["weight"]
                cat = rule["category"]
                self._telemetry["injections_by_category"][cat] = self._telemetry["injections_by_category"].get(cat, 0) + 1

        # 2. Check for base64 obfuscated attack strings
        b64_violations = self._scan_base64_obfuscation(payload)
        for v in b64_violations:
            violations.append(v)
            raw_score += v["weight"]
            cat = v["category"]
            self._telemetry["injections_by_category"][cat] = self._telemetry["injections_by_category"].get(cat, 0) + 1

        # Compute clamped risk score (0.00 to 1.00)
        risk_score = min(1.0, round(raw_score, 3))

        # Determine verdict
        threshold_block = 0.60 if strict else 0.70
        threshold_quarantine = 0.25 if strict else 0.30

        if risk_score >= threshold_block:
            verdict = "BLOCKED"
            is_safe = False
            self._telemetry["blocked_count"] += 1
        elif risk_score >= threshold_quarantine:
            verdict = "QUARANTINED"
            is_safe = False
            self._telemetry["quarantined_count"] += 1
        else:
            verdict = "ALLOWED"
            is_safe = True
            self._telemetry["allowed_count"] += 1

        self._telemetry["total_payloads_scanned"] += 1
        scan_duration_ms = round((time.perf_counter() - t0) * 1000, 3)

        result = {
            "is_safe": is_safe,
            "verdict": verdict,
            "risk_score": risk_score,
            "source": source,
            "violations_count": len(violations),
            "violations": violations,
            "scan_duration_ms": scan_duration_ms,
            "neutralized_payload": self.neutralize_payload(payload) if not is_safe else payload
        }

        # Log incident if quarantined or blocked
        if not is_safe:
            self._log_quarantine(result, payload)

        return result

    def _scan_base64_obfuscation(self, payload: str) -> List[Dict[str, Any]]:
        """Detects base64 encoded strings hiding prompt injections."""
        violations = []
        b64_pattern = re.compile(r'[A-Za-z0-9+/]{16,}={0,2}')
        candidates = b64_pattern.findall(payload)

        suspicious_keywords = [
            "ignore previous", "ignore all", "disregard all", "system prompt", "jailbreak",
            "dan mode", "developer mode", "system override", "bypass safety", "act as",
            "forget previous", "unrestricted", "new instructions", "now you are"
        ]

        for cand in candidates:
            try:
                pad = (4 - len(cand) % 4) % 4
                padded = cand + ("=" * pad)
                decoded_bytes = base64.b64decode(padded)
                decoded_str = decoded_bytes.decode('utf-8', errors='ignore').lower()
                for kw in suspicious_keywords:
                    if kw in decoded_str:
                        violations.append({
                            "category": "OBFUSCATED_BASE64_INJECTION",
                            "severity": "CRITICAL",
                            "weight": 0.50,
                            "description": f"Base64-encoded jailbreak string detected ({kw})",
                            "snippet": cand[:30] + f" -> '{decoded_str[:40]}...'"
                        })
                        break
            except Exception:
                pass
        return violations

    def neutralize_payload(self, payload: str) -> str:
        """
        Disarms adversarial delimiters and wraps untrusted input into safe data envelope.
        """
        neutralized = payload
        # Strip invisible zero-width characters
        neutralized = re.sub(r'[\u200B-\u200D\uFEFF]', '', neutralized)

        # Defang system and template delimiters
        substitutions = [
            (r'"""\s*SYSTEM:', '""" (neutralized) SYSTEM:'),
            (r'\[INST\]', '[UNTRUSTED_INST]'),
            (r'<<SYS>>', '[[UNTRUSTED_SYS]]'),
            (r'<\|im_start\|>', '&lt;|im_start|&gt;'),
            (r'<\|system\|>', '&lt;|system|&gt;'),
            (r'<system>', '&lt;system&gt;'),
            (r'=== SYSTEM OVERRIDE ===', '=== (neutralized override) ===')
        ]
        for pattern, repl in substitutions:
            neutralized = re.sub(pattern, repl, neutralized, flags=re.IGNORECASE)

        # Wrap in quarantined external data container
        safe_envelope = (
            "<untrusted_external_payload sanitized=\"true\" guardrail=\"PromptInjectionGuard\">\n"
            f"{neutralized.strip()}\n"
            "</untrusted_external_payload>"
        )
        return safe_envelope

    def _log_quarantine(self, result: Dict[str, Any], raw_payload: str) -> None:
        """Records suspicious payloads to user/hitl/injection_quarantine.jsonl."""
        try:
            self.QUARANTINE_LOG.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "timestamp": time.time(),
                "verdict": result["verdict"],
                "risk_score": result["risk_score"],
                "source": result["source"],
                "violations": result["violations"],
                "raw_payload_preview": raw_payload[:200]
            }
            with open(self.QUARANTINE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns firewall inspection statistics."""
        return {
            "status": "OPERATIONAL",
            "framework_parity": "Prompt Armor / Lakera Guard",
            "telemetry": dict(self._telemetry)
        }
