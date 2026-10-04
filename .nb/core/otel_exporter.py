"""
Percipience OpenTelemetry (OTel) GenAI Semantic Conventions & Distributed Tracing Engine (CAP-36)
Emits W3C-compliant distributed trace spans with standardized GenAI semantic attributes
(gen_ai.system, gen_ai.request.model, gen_ai.usage.input_tokens, TTFT) to enterprise APMs.
"""

import time
import uuid
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name == "workplace" else Path(__file__).resolve().parents[1]


class OpenTelemetryGenAIExporter:
    """
    OpenTelemetry GenAI Semantic Convention Exporter.
    Generates W3C `traceparent` headers and structured GenAI spans.
    """

    SPANS_LOG_PATH = (REPO_ROOT / ".nb" / "context" / "ledger" / "otel_spans.jsonl" if (REPO_ROOT / ".nb" / "context").exists() else REPO_ROOT / "context" / "ledger" / "otel_spans.jsonl")

    def __init__(self, service_name: str = "percipience-context-os"):
        self.service_name = service_name
        self.active_spans: Dict[str, Dict[str, Any]] = {}
        self.completed_spans: List[Dict[str, Any]] = []

    @staticmethod
    def generate_trace_id() -> str:
        """Generates 32-character hexadecimal W3C trace ID."""
        return uuid.uuid4().hex

    @staticmethod
    def generate_span_id() -> str:
        """Generates 16-character hexadecimal W3C span ID."""
        return uuid.uuid4().hex[:16]

    @classmethod
    def generate_w3c_traceparent(
        cls,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        sampled: bool = True
    ) -> str:
        """Generates W3C traceparent header: 00-{trace_id}-{parent_id}-{flags}"""
        t_id = trace_id or cls.generate_trace_id()
        s_id = parent_span_id or cls.generate_span_id()
        flags = "01" if sampled else "00"
        return f"00-{t_id}-{s_id}-{flags}"

    @classmethod
    def parse_w3c_traceparent(cls, traceparent: str) -> Dict[str, str]:
        """Parses W3C traceparent header string."""
        parts = traceparent.split("-")
        if len(parts) != 4:
            raise ValueError(f"Invalid W3C traceparent header: {traceparent}")
        return {
            "version": parts[0],
            "trace_id": parts[1],
            "parent_span_id": parts[2],
            "trace_flags": parts[3],
            "is_sampled": parts[3] == "01"
        }

    def start_genai_span(
        self,
        name: str,
        model_name: str,
        system_vendor: str = "anthropic",
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        temperature: float = 0.0,
        extra_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Starts an OpenTelemetry GenAI span following standard semantic conventions.
        """
        span_id = self.generate_span_id()
        t_id = trace_id or self.generate_trace_id()
        start_time = time.time()

        span = {
            "name": name,
            "context": {
                "trace_id": t_id,
                "span_id": span_id,
                "parent_span_id": parent_span_id,
                "w3c_traceparent": f"00-{t_id}-{span_id}-01"
            },
            "kind": "SPAN_KIND_CLIENT",
            "start_time_unix_nano": int(start_time * 1e9),
            "attributes": {
                "service.name": self.service_name,
                "gen_ai.system": system_vendor,
                "gen_ai.request.model": model_name,
                "gen_ai.request.temperature": temperature,
                **(extra_attributes or {})
            },
            "events": [],
            "status": {"code": "STATUS_CODE_UNSET"}
        }

        self.active_spans[span_id] = span
        return span

    def record_ttft(self, span_id: str, ttft_seconds: float) -> None:
        """Records Time-To-First-Token (TTFT) event in active span."""
        if span_id in self.active_spans:
            self.active_spans[span_id]["events"].append({
                "name": "gen_ai.time_to_first_token",
                "time_unix_nano": int(time.time() * 1e9),
                "attributes": {"gen_ai.ttft_seconds": round(ttft_seconds, 4)}
            })

    def end_genai_span(
        self,
        span_id: str,
        input_tokens: int,
        output_tokens: int,
        finish_reason: str = "stop",
        status_code: str = "STATUS_CODE_OK",
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Completes the GenAI span, calculates latency, records token metrics, and persists to ledger.
        """
        if span_id not in self.active_spans:
            raise KeyError(f"No active span found with ID: {span_id}")

        span = self.active_spans.pop(span_id)
        end_time = time.time()
        start_time_sec = span["start_time_unix_nano"] / 1e9
        duration_ms = round((end_time - start_time_sec) * 1000, 2)

        span["end_time_unix_nano"] = int(end_time * 1e9)
        span["duration_ms"] = duration_ms
        span["attributes"]["gen_ai.usage.input_tokens"] = input_tokens
        span["attributes"]["gen_ai.usage.output_tokens"] = output_tokens
        span["attributes"]["gen_ai.usage.total_tokens"] = input_tokens + output_tokens
        span["attributes"]["gen_ai.response.finish_reasons"] = [finish_reason]

        span["status"]["code"] = status_code
        if error_message:
            span["status"]["description"] = error_message

        self.completed_spans.append(span)
        self._append_to_file(span)
        return span

    def _append_to_file(self, span: Dict[str, Any]) -> None:
        """Appends span to jsonl file for observability pipelines."""
        try:
            self.SPANS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(self.SPANS_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(span) + "\n")
        except Exception:
            pass
