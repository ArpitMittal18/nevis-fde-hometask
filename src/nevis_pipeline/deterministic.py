from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable


def load_json_yaml(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def clean(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def stable_id(prefix: str, *parts: object) -> str:
    identity = "|".join(key(part) for part in parts)
    digest = hashlib.sha256(identity.encode()).hexdigest()[:12]
    return f"{prefix}-{digest}"


def parse_date(value: object) -> str:
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    text = clean(value)
    for fmt in ("%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Unsupported date: {value!r}")


def normalize_status(value: object, household_name: str = "") -> tuple[str, list[str], str]:
    normalized = key(value)
    mapping = {"active": "ACTIVE", "client": "ACTIVE", "legacy": "ACTIVE", "former": "INACTIVE", "churned": "INACTIVE", "prospect": "PROSPECT"}
    if "thompson" in key(household_name):
        return "INACTIVE", [], "thompson_inactive_v1"
    if normalized not in mapping:
        raise ValueError(f"Unknown status: {value!r}")
    tags = ["acquired_from:harborline"] if normalized == "legacy" else []
    rule = "legacy_active_v1" if normalized == "legacy" else "status_normalization_v1"
    return mapping[normalized], tags, rule


def normalize_account_type(value: object) -> str:
    normalized = key(value)
    mapping = {"individual": "INDIVIDUAL", "joint wros": "JOINT", "joint tic": "JOINT", "trust rev": "TRUST", "rollover ira": "IRA", "ira": "IRA", "roth ira": "ROTH_IRA", "corporate": "CORPORATE"}
    return mapping.get(normalized, "OTHER")


def normalize_interaction_type(value: object) -> str:
    normalized = key(value)
    if normalized in {"annual review", "check in", "qbr", "review"}:
        return "REVIEW"
    if normalized in {"prospecting", "intro call", "discovery"}:
        return "PROSPECTING"
    if normalized == "onboarding":
        return "ONBOARDING"
    return "OTHER"


def advisor_alias(value: object, advisors: Iterable[dict]) -> dict | None:
    requested = key(value)
    if not requested:
        return None
    roster = list(advisors)
    exact = [item for item in roster if key(item["full_name"]) == requested]
    if len(exact) == 1:
        return exact[0]
    tokens = requested.split()
    candidates = []
    for item in roster:
        names = key(item["full_name"]).split()
        if len(tokens) == 2 and len(names) >= 2 and tokens[-1] == names[-1] and tokens[0][0] == names[0][0]:
            candidates.append(item)
    return candidates[0] if len(candidates) == 1 else None


def parse_person_name(value: object) -> tuple[str, str]:
    text = clean(value)
    if "," in text:
        last, first = [part.strip() for part in text.split(",", 1)]
    else:
        parts = text.split()
        first, last = " ".join(parts[:-1]), parts[-1]
    return first, last


def convert_to_usd(amount: object, currency: str, rates: dict[str, str]) -> float:
    if amount is None:
        raise ValueError("market value cannot be null")
    rate = Decimal(rates[currency])
    result = Decimal(str(amount)) * rate
    return float(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def household_label(value: object, fallback_name: str) -> str:
    text = clean(value) or clean(fallback_name)
    text = re.sub(r"\s+Household$", "", text, flags=re.I)
    if key(text) in {"petrov dmitri", "dmitri petrov"}:
        return "Petrov"
    return text
