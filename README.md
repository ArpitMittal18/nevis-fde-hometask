# Nevis FDE Mapping Pipeline

A runnable pipeline that maps Beaconcrest Advisors' Notion CRM, custodian workbook, advisor roster, and stakeholder Slack decisions into the five-entity Nevis canonical model. It combines deterministic data engineering with focused LLM stages, confidence routing, provenance, and post-mapping validation.

## Process — quick read

1. **Profile sources** — inventory every column, infer types, and enumerate enum/currency domains.
2. **Ingest** — load CSV, Excel, Markdown, and Slack inputs while retaining source rows and checksums.
3. **Apply stakeholder rules** — use Dana's documented answers for Legacy, advisor ownership, AUM, FX, duplicates, and inactive households.
4. **Normalize deterministically** — clean strings, parse dates, standardize enums, resolve known advisor aliases, and generate stable IDs.
5. **Extract semantic evidence with an LLM** — identify explicit relationships, aliases, annotations, and contradictions in Notion notes.
6. **Build canonical entities** — create advisors, households, clients, accounts, and interactions.
7. **Resolve bounded ambiguity** — ask the LLM to choose only from supplied candidates or return `null`.
8. **Route by confidence** — auto-apply defensible mappings and quarantine unresolved records.
9. **Add provenance and validate** — record field-level lineage and enforce IDs, relationships, currency, value, and AUM rules in Python.
10. **Publish atomically** — write canonical data, decisions, clarifications, source profiles, and the LLM manifest only after hard validation passes.

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

### Hermes Agent and OpenAI

This project was built and validated with **Hermes Agent**. Hermes was already connected to **OpenAI/OpenAI Codex**, and the committed real-run artifacts were generated through that authenticated Hermes provider using `gpt-5.6-sol`. The pipeline also supports direct OpenAI Responses API calls through `OPENAI_API_KEY`; reviewers do not need Hermes because replay mode runs locally without credentials.

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

## Where AI is—and is not—used

| Uses an LLM | Does not use an LLM |
|---|---|
| Interpret unstructured Notion page notes | Read CSV, Excel, and Markdown files |
| Extract explicit relationships, aliases, annotations, and contradictions | Profile columns and observed value domains |
| Adjudicate ambiguous matches against a supplied candidate list | Parse dates, clean strings, or generate stable IDs |
| Return structured evidence and confidence | Normalize known statuses, account types, and interaction types |
| | Calculate FX conversions or AUM |
| | Apply stakeholder rules or validate canonical relationships |

The model cannot invent an entity: it must choose a supplied candidate or return `null`. Auto-applied mappings must remain evidence-backed and pass deterministic validation. Advisor gaps, orphans, contradictions, stale active positions, and ambiguous ownership are quarantined as clarification questions.

## Knowledge layer

`config/client_rules.yml` stores versioned stakeholder answers with Slack citations. Rules encode that Legacy means active Harborline lineage, Advisor—not Service Rep—owns the relationship, AUM uses market value, reporting currency is USD, Petrov is a duplicate, and Thompson is inactive. A future answer should be added as a higher-priority versioned rule instead of changing historical evidence.

`config/fx_rates.yml` caches the 2025-06-30 ECB reference rates used by the run. Numeric FX rates never come from the LLM.

## Current data-quality flags

The sample run asks Dana about missing advisor ownership, Omar Farouk's Active/Deceased contradiction, Nakamura IRA ownership, custodian-only holders, stale positions, and the Redwood Capital orphan interaction. It does not re-ask questions already resolved in Slack.

## Production hardening

For production, store LLM cache entries and stakeholder rules in a versioned database, add provider retries/rate limiting, use a formal FX service with holiday fallback policy, add PII controls, and publish validation/lineage metrics to monitoring.
