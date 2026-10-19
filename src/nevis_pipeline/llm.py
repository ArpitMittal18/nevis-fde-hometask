from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class SemanticAgent:
    """Focused semantic stages with real OpenAI and reproducible replay modes."""

    def __init__(self, mode: str = "replay", model: str | None = None):
        if mode not in {"replay", "real"}:
            raise ValueError("mode must be 'replay' or 'real'")
        self.mode = mode
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        if self.provider == "anthropic":
            default_model = "claude-sonnet-4-5-20250929"
        elif self.provider == "hermes":
            default_model = "gpt-5.6-sol"
        else:
            default_model = "gpt-4.1-mini"
        self.model = model or os.getenv("LLM_MODEL", default_model)
        self.calls: list[dict[str, Any]] = []
        key_name = "ANTHROPIC_API_KEY" if self.provider == "anthropic" else "OPENAI_API_KEY"
        self.api_key = os.getenv(key_name)
        if mode == "real" and self.provider != "hermes" and not self.api_key:
            raise RuntimeError(f"{key_name} is required for --mode real with provider {self.provider}")

    def _real_json(self, stage: str, instructions: str, payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        if self.provider == "anthropic":
            return self._anthropic_json(stage, instructions, payload, schema)
        if self.provider == "hermes":
            return self._hermes_json(stage, instructions, payload, schema)
        started = time.monotonic()
        body = {
            "model": self.model,
            "instructions": instructions,
            "input": json.dumps(payload, ensure_ascii=False),
            "temperature": 0,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": stage,
                    "schema": schema,
                    "strict": True,
                }
            },
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"OpenAI call failed ({exc.code}): {exc.read().decode()}") from exc
        text = raw.get("output_text")
        if not text:
            chunks = []
            for item in raw.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        chunks.append(content.get("text", ""))
            text = "".join(chunks)
        result = json.loads(text)
        self.calls.append({"stage": stage, "provider": "openai", "model": self.model, "response_id": raw.get("id"), "latency_ms": round((time.monotonic()-started)*1000), "real_call": True})
        return result

    def _anthropic_json(self, stage: str, instructions: str, payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        body = {
            "model": self.model,
            "max_tokens": 1200,
            "temperature": 0,
            "system": instructions,
            "messages": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            "tools": [{"name": "emit_json", "description": "Return the structured decision", "input_schema": schema}],
            "tool_choice": {"type": "tool", "name": "emit_json"},
        }
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(body).encode(),
            headers={"x-api-key": self.api_key or "", "anthropic-version": "2023-06-01", "content-type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Anthropic call failed ({exc.code}): {exc.read().decode()}") from exc
        tool_use = next((item for item in raw.get("content", []) if item.get("type") == "tool_use" and item.get("name") == "emit_json"), None)
        if not tool_use:
            raise RuntimeError("Anthropic response did not contain the required emit_json tool call")
        self.calls.append({"stage": stage, "provider": "anthropic", "model": self.model, "response_id": raw.get("id"), "latency_ms": round((time.monotonic()-started)*1000), "real_call": True})
        return tool_use["input"]

    def _hermes_json(self, stage: str, instructions: str, payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        prompt = "\n".join([
            instructions,
            "Return only one JSON object matching this JSON Schema; do not use Markdown fences:",
            json.dumps(schema, ensure_ascii=False),
            "Input:",
            json.dumps(payload, ensure_ascii=False),
        ])
        completed = subprocess.run(
            ["hermes", "chat", "-Q", "--provider", "openai-codex", "-m", self.model, "-q", prompt],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Hermes LLM call failed: {completed.stderr.strip()}")
        session_match = re.search(r"session_id:\s*([^\s]+)", completed.stdout + "\n" + completed.stderr)
        json_start = completed.stdout.find("{")
        if json_start < 0:
            raise RuntimeError(f"Hermes LLM call returned no JSON: {completed.stdout[:500]}")
        result, _ = json.JSONDecoder().raw_decode(completed.stdout[json_start:])
        self.calls.append({
            "stage": stage,
            "provider": "openai-codex-via-hermes",
            "model": self.model,
            "response_id": session_match.group(1) if session_match else None,
            "latency_ms": round((time.monotonic() - started) * 1000),
            "real_call": True,
        })
        return result

    def extract_page_signals(self, title: str, body: str, source: str) -> dict[str, Any]:
        if self.mode == "real":
            return self._real_json(
                "extract_page_signals",
                "Extract only explicit facts from this wealth-management CRM note. Never invent a fact.",
                {"title": title, "body": body},
                {
                    "type": "object",
                    "properties": {
                        "relationships": {"type": "array", "items": {"type": "string"}},
                        "aliases": {"type": "array", "items": {"type": "string"}},
                        "account_ownership": {"type": "array", "items": {"type": "string"}},
                        "contradictions": {"type": "array", "items": {"type": "string"}},
                        "annotations": {"type": "array", "items": {"type": "string"}},
                        "evidence_quotes": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    },
                    "required": ["relationships", "aliases", "account_ownership", "contradictions", "annotations", "evidence_quotes", "confidence"],
                    "additionalProperties": False
                },
            )
        lower = body.lower()
        signals = {
            "relationships": [], "aliases": [], "account_ownership": [],
            "contradictions": [], "annotations": [], "evidence_quotes": [body] if body else [],
            "confidence": 0.98 if body else 1.0,
        }
        if "wife of robert" in lower:
            signals["relationships"].append("Linda Chen is spouse of Robert Chen and belongs to the same household")
        if "duplicate" in lower and "petrov" in lower:
            signals["aliases"].append("Petrov, Dmitri is the same person as Dmitri Petrov")
        if "ira" in lower and "llc" in lower:
            signals["account_ownership"].append("Kenji Nakamura IRA household placement is unresolved")
        if "deceased" in lower:
            signals["contradictions"].append("Active status may conflict with deceased annotation")
        for token in ("harborline", "email only", "do not contact", "held away", "deceased"):
            if token in lower:
                signals["annotations"].append(token.replace(" ", "_"))
        self.calls.append({"stage":"extract_page_signals","provider":"replay","model":"deterministic-replay-v1","source":source,"real_call":False})
        return signals

    def adjudicate(self, subject: str, candidates: list[str], evidence: list[str]) -> dict[str, Any]:
        if self.mode == "real":
            return self._real_json(
                "adjudicate_confidence",
                "Choose only from candidates or choose null. Confidence must reflect ambiguity; do not invent entities.",
                {"subject": subject, "candidates": candidates, "evidence": evidence},
                {
                    "type": "object",
                    "properties": {
                        "choice": {"type": ["string", "null"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "rationale": {"type": "string"},
                        "evidence": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["choice", "confidence", "rationale", "evidence"],
                    "additionalProperties": False
                },
            )
        choice = candidates[0] if len(candidates) == 1 else None
        result = {"choice": choice, "confidence": 0.99 if choice else 0.2, "rationale": "Unique evidence-backed candidate" if choice else "Ambiguous or unmatched", "evidence": evidence}
        self.calls.append({"stage":"adjudicate_confidence","provider":"replay","model":"deterministic-replay-v1","subject":subject,"real_call":False})
        return result

    def manifest(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "provider": self.provider if self.mode == "real" else "replay",
            "model": self.model if self.mode == "real" else "deterministic-replay-v1",
            "real_llm_used": any(call.get("real_call") for call in self.calls),
            "call_count": len(self.calls),
            "calls": self.calls,
            "warning": None if self.mode == "real" else "Replay mode is reproducible but is not evidence of a real LLM run.",
        }
