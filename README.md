# Nevis FDE Mapping Pipeline

A runnable pipeline that maps Beaconcrest Advisors' Notion CRM, custodian workbook, advisor roster, and stakeholder Slack decisions into the five-entity Nevis canonical model. It combines deterministic data engineering with focused LLM stages, confidence routing, provenance, and post-mapping validation.

## Setup

Python 3.10+ is required (3.11 recommended).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

For a real LLM run:

```bash
export OPENAI_API_KEY='...'
export LLM_MODEL='gpt-4.1-mini'  # optional override
```

Never commit `.env` or an API key.

## One-command run

### Real LLM path

```bash
python -m nevis_pipeline.cli run --sources sources --output outputs --mode real
```

This uses OpenAI Responses API strict JSON-schema outputs for two focused stages:

1. extracting explicit semantic signals from Notion page bodies;
2. adjudicating candidate entity matches and confidence.

The produced `outputs/llm_run_manifest.json` records the provider, model, stage, latency, and real response ID for every call.

### Reproducible offline replay

```bash
python -m nevis_pipeline.cli run --sources sources --output outputs --mode replay
```

Replay mode makes no network calls and is deterministic. It exists so reviewers can run the complete pipeline without an API key. Its manifest explicitly reports `real_llm_used: false`; it is not represented as evidence of a real LLM run.

## Tests

```bash
python -m pytest -q
```

## Generated artifacts

- `outputs/source_profile.md` — human-readable inventory of every CSV/workbook column, inferred type, null count, distinct count, and observed enum/currency values.
- `outputs/source_profile.json` — machine-readable version of the same pre-mapping schema profile.
- `outputs/canonical_output.json` — five canonical entity arrays, field-level provenance, run metadata, and validation summary.
- `outputs/clarifications_round_2.md` — the next concise, evidence-backed message to Dana.
- `outputs/decision_log.json` — auto-applied, merged, and quarantined decisions plus extracted page signals.
- `outputs/llm_run_manifest.json` — model/replay call audit trail and input checksums.

Artifacts are written atomically only after hard validation passes.

## Mapping behavior

- **Deterministic:** parsing, stable IDs, status/account/interaction enums, advisor roster aliases, market-value AUM, FX arithmetic, and hard validation.
- **LLM:** unstructured-note interpretation and confidence adjudication over bounded candidate sets.
- **Auto-apply policy:** a mapping must have a unique evidence-backed candidate, sufficient confidence, and pass every canonical constraint.
- **Flag policy:** required advisor gaps, orphans, contradictions, stale active positions, and ambiguous household ownership are quarantined and turned into answerable questions.

## Knowledge layer

`config/client_rules.yml` stores versioned stakeholder answers with Slack citations. Rules encode that Legacy means active Harborline lineage, Advisor—not Service Rep—owns the relationship, AUM uses market value, reporting currency is USD, Petrov is a duplicate, and Thompson is inactive. A future answer should be added as a higher-priority versioned rule instead of changing historical evidence.

`config/fx_rates.yml` caches the 2025-06-30 ECB reference rates used by the run. Numeric FX rates never come from the LLM.

## Current data-quality flags

The sample run asks Dana about missing advisor ownership, Omar Farouk's Active/Deceased contradiction, Nakamura IRA ownership, custodian-only holders, stale positions, and the Redwood Capital orphan interaction. It does not re-ask questions already resolved in Slack.

## Production hardening

For production, store LLM cache entries and stakeholder rules in a versioned database, add provider retries/rate limiting, use a formal FX service with holiday fallback policy, add PII controls, and publish validation/lineage metrics to monitoring.
