from __future__ import annotations

from collections import Counter
from typing import Any


def validate(canonical: dict[str, Any]) -> dict[str, Any]:
    hard_errors: list[str] = []
    warnings: list[str] = []

    entity_specs = {
        "advisors": ("advisor_id",),
        "households": ("household_id",),
        "clients": ("client_id",),
        "accounts": ("account_id",),
        "interactions": ("interaction_id",),
    }
    for collection, (pk,) in entity_specs.items():
        ids = [record[pk] for record in canonical[collection]]
        duplicates = [value for value, count in Counter(ids).items() if count > 1]
        if duplicates:
            hard_errors.append(f"Duplicate {pk}: {duplicates}")

    advisor_ids = {item["advisor_id"] for item in canonical["advisors"]}
    household_ids = {item["household_id"] for item in canonical["households"]}
    for household in canonical["households"]:
        if not household.get("primary_advisor_id") or household["primary_advisor_id"] not in advisor_ids:
            hard_errors.append(f"Household {household['household_id']} lacks a valid primary advisor")
    for client in canonical["clients"]:
        if client["household_id"] not in household_ids:
            hard_errors.append(f"Orphan client {client['client_id']}")
    for account in canonical["accounts"]:
        if account["household_id"] not in household_ids:
            hard_errors.append(f"Orphan account {account['account_id']}")
        if account["currency_original"] != "USD" and account["market_value_usd"] is None:
            hard_errors.append(f"Unconverted foreign account {account['account_id']}")
        if account["market_value_usd"] < 0:
            hard_errors.append(f"Negative market value {account['account_id']}")
    for interaction in canonical["interactions"]:
        if interaction["household_id"] not in household_ids:
            hard_errors.append(f"Orphan interaction {interaction['interaction_id']}")
        if interaction["advisor_id"] is not None and interaction["advisor_id"] not in advisor_ids:
            hard_errors.append(f"Unknown interaction advisor {interaction['interaction_id']}")

    active_ids = {h["household_id"] for h in canonical["households"] if h["status"] == "ACTIVE"}
    active_aum = round(sum(a["market_value_usd"] for a in canonical["accounts"] if a["household_id"] in active_ids), 2)
    household_aum = {}
    for household in canonical["households"]:
        amounts = [a["market_value_usd"] for a in canonical["accounts"] if a["household_id"] == household["household_id"]]
        household_aum[household["household_id"]] = round(sum(amounts), 2) if amounts else None

    return {
        "hard_errors": hard_errors,
        "warnings": warnings,
        "entity_counts": {name: len(canonical[name]) for name in entity_specs},
        "active_aum_usd": active_aum,
        "household_aum_usd": household_aum,
    }
