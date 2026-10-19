from __future__ import annotations

from typing import Any


def entry(
    entity_type: str,
    entity_id: str,
    field: str,
    value: Any,
    source: dict[str, Any],
    method: str,
    confidence: float = 1.0,
    rule_id: str | None = None,
    evidence: str | None = None,
) -> dict[str, Any]:
    item = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "field": field,
        "value": value,
        "source": source,
        "method": method,
        "confidence": confidence,
    }
    if rule_id:
        item["rule_id"] = rule_id
    if evidence:
        item["evidence"] = evidence
    return item
