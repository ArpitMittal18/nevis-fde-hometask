# Design

## Shape

The pipeline is a small stage orchestrator: **source profiling → ingest → stakeholder knowledge → deterministic normalization → focused LLM analysis → confidence routing → canonical validation → atomic artifacts**. Source profiling inventories every CSV/workbook column before mapping, classifies it as an identifier, enum, multi-enum, date, currency code, currency amount, number, boolean, URL, or text, and records null/distinct counts plus observed categorical domains. I chose a custom orchestrator over a heavy agent framework because this task benefits from visible control flow: it is easy to see which values came from source data, a stakeholder rule, an LLM decision, or a derivation. The OpenAI Responses API supplies strict JSON-schema outputs while Python owns record state and side effects.

The canonical artifact contains schema-clean `advisor`, `household`, `client`, `account`, and `interaction` arrays. Provenance is a separate field-level ledger keyed by entity, ID, and field. It captures source path/row, method, rule/model evidence, and confidence without polluting the target schema. A decision log accounts for auto-applied, merged, and quarantined source records.

## Deterministic vs. LLM work

Deterministic code handles CSV/XLSX/Markdown parsing, dates, stable IDs, known enums, exact/unique advisor aliases, market-value selection, Decimal FX conversion, and referential validation. These operations have crisp expected answers and should not depend on model behavior.

The LLM earns its place in two bounded stages: extracting explicit relationships/aliases/contradictions from page bodies, and adjudicating an ambiguous source entity against a supplied candidate list. It cannot invent an advisor or household. A model decision is auto-applied only when evidence supports a unique candidate, confidence clears policy, and all hard canonical constraints pass; otherwise it becomes a clarification. Replay mode is deterministic and clearly labeled as non-LLM, while real runs retain response IDs in the manifest.

## Stakeholder knowledge

Round-1 Slack answers are versioned in `config/client_rules.yml` and reapplied on every sync:

1. `Legacy` is operationally active; preserve `acquired_from:harborline` lineage.
2. CRM `Advisor` owns the household; never substitute `Service Rep`.
3. Blank Advisor values must be flagged, especially records referencing former contractor A. Novak.
4. AUM uses market value, never cost basis.
5. Reporting currency is USD; convert foreign balances at a documented quarter-end rate.
6. The two Petrov records are one person and must be collapsed with both sources retained.
7. Thompson is inactive and excluded from active-AUM reporting.

Each rule carries a stable ID, scope, priority, status, and source citation. A correction should add a higher-priority rule that supersedes the old one, preserving history instead of silently rewriting it. The same mechanism can host reusable generic rules below client-specific human answers.

## Validation and trade-offs

Validation rejects duplicate IDs, invalid foreign keys, missing primary advisors, orphan accounts/interactions, unconverted foreign values, and negative balances. It derives household AUM from accounts and uses null—not zero—when no account is known. Source and decision counts make silent drops visible. Active AUM excludes inactive households while preserving valid account records.

The design intentionally prefers a short clarification list over aggressive fuzzy matching. This leaves several records quarantined—missing advisor assignments, custodian-only holders, the Nakamura IRA, stale positions, Redwood Capital, and the Active/Deceased contradiction—but each question includes evidence, options, and a proposed default. The principal trade-off is lower automatic coverage in exchange for trustworthy AUM and ownership. In production I would add persistent LLM caching, a rule approval UI, richer identity features, PII controls, and monitored FX/validation services.
