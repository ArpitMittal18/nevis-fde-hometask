from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceRef:
    path: str
    row: int | None = None
    lines: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in vars(self).items() if v is not None}


@dataclass
class SourceRecord:
    values: dict[str, Any]
    source: SourceRef
    page_path: str | None = None
    page_body: str = ""


@dataclass
class StagingBundle:
    clients: list[SourceRecord]
    meetings: list[SourceRecord]
    accounts: list[SourceRecord]
    advisors: list[SourceRecord]
    slack_text: str
    input_checksums: dict[str, str] = field(default_factory=dict)


@dataclass
class Decision:
    entity_type: str
    source_ref: dict[str, Any]
    outcome: str
    reason: str
    confidence: float
    candidates: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return vars(self)
