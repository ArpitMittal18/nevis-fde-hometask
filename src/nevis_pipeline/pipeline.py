from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .clarifications import generate_clarifications
from .deterministic import load_json_yaml
from .ingest import ingest_sources
from .llm import SemanticAgent
from .profiling import profile_sources, render_profile_markdown
from .resolution import resolve
from .validation import validate


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def run_pipeline(
    sources_dir: Path,
    output_dir: Path,
    mode: str = "replay",
    model: str | None = None,
    confidence_threshold: float = 0.90,
) -> dict[str, Any]:
    sources_dir, output_dir = Path(sources_dir).resolve(), Path(output_dir).resolve()
    project_root = sources_dir.parent
    rates = load_json_yaml(project_root / "config" / "fx_rates.yml")
    rules = load_json_yaml(project_root / "config" / "client_rules.yml")
    source_profile = profile_sources(sources_dir)
    bundle = ingest_sources(sources_dir)
    agent = SemanticAgent(mode=mode, model=model)
    resolved = resolve(bundle, agent, rates)

    canonical = {
        "run_metadata": {
            "pipeline_version": "0.1.0",
            "mode": mode,
            "reporting_date": rates["as_of_date"],
            "confidence_threshold": confidence_threshold,
            "input_checksums": bundle.input_checksums,
            "knowledge_rule_ids": [rule["rule_id"] for rule in rules["rules"] if rule["status"] == "active"],
        },
        "advisors": resolved["advisors"],
        "households": resolved["households"],
        "clients": resolved["clients"],
        "accounts": resolved["accounts"],
        "interactions": resolved["interactions"],
        "provenance": resolved["provenance"],
    }
    canonical["validation_summary"] = validate(canonical)
    if canonical["validation_summary"]["hard_errors"]:
        raise ValueError("Hard validation errors: " + "; ".join(canonical["validation_summary"]["hard_errors"]))

    clarifications = generate_clarifications(resolved["decisions"], resolved["advisors"])
    decision_log = {
        "decisions": resolved["decisions"],
        "page_signals": resolved["page_signals"],
        "blocked_households": resolved["blocked_households"],
        "outcome_counts": {
            outcome: sum(1 for item in resolved["decisions"] if item["outcome"] == outcome)
            for outcome in sorted({item["outcome"] for item in resolved["decisions"]})
        },
    }
    manifest = agent.manifest()
    manifest["input_checksums"] = bundle.input_checksums
    manifest["prompt_stages"] = ["extract_page_signals", "adjudicate_confidence"]

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_dir.parent) as temporary:
        temp = Path(temporary)
        _write_json(temp / "canonical_output.json", canonical)
        (temp / "clarifications_round_2.md").write_text(clarifications + "\n", encoding="utf-8")
        _write_json(temp / "decision_log.json", decision_log)
        _write_json(temp / "llm_run_manifest.json", manifest)
        _write_json(temp / "source_profile.json", source_profile)
        (temp / "source_profile.md").write_text(render_profile_markdown(source_profile) + "\n", encoding="utf-8")
        output_dir.mkdir(parents=True, exist_ok=True)
        for name in (
            "canonical_output.json",
            "clarifications_round_2.md",
            "decision_log.json",
            "llm_run_manifest.json",
            "source_profile.json",
            "source_profile.md",
        ):
            os.replace(temp / name, output_dir / name)

    source_counts = {"clients": len(bundle.clients), "meetings": len(bundle.meetings), "accounts": len(bundle.accounts), "advisors": len(bundle.advisors)}
    return {"canonical": canonical, "clarifications": clarifications, "decisions": decision_log, "manifest": manifest, "source_profile": source_profile, "source_counts": source_counts}
