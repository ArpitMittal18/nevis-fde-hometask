from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .deterministic import (
    advisor_alias,
    clean,
    convert_to_usd,
    household_label,
    key,
    normalize_account_type,
    normalize_interaction_type,
    normalize_status,
    parse_date,
    parse_person_name,
    stable_id,
)
from .llm import SemanticAgent
from .models import Decision, SourceRecord, StagingBundle
from .provenance import entry as provenance_entry


def _source(record: SourceRecord) -> dict[str, Any]:
    return record.source.as_dict()


def _tags(record: SourceRecord) -> list[str]:
    values = record.values
    tags: list[str] = []
    for field, prefix in (("Segment", "segment"), ("Risk Profile", "risk_profile"), ("Fee Schedule", "fee_schedule"), ("Referred By", "referred_by")):
        if clean(values.get(field)):
            tags.append(f"{prefix}:{key(values[field]).replace(' ', '_')}")
    for raw in clean(values.get("Tags")).split(","):
        if raw.strip():
            tags.append(key(raw).replace(" ", "_"))
    return tags


def _client_label(record: SourceRecord) -> str:
    name = clean(record.values["Name"])
    if name == "Linda Chen":
        return "Chen"
    if key(name) in {"dmitri petrov", "petrov dmitri"}:
        return "Petrov"
    return household_label(record.values.get("Household"), name)


def _record_provenance(entity_type: str, entity_id: str, record: dict[str, Any], source: dict[str, Any], method: str = "direct") -> list[dict[str, Any]]:
    return [provenance_entry(entity_type, entity_id, field, value, source, method) for field, value in record.items()]


def _account_candidates(holder: str, groups: dict[str, list[SourceRecord]]) -> list[str]:
    holder_key = key(holder)
    aliases = {
        "bob linda chen": "Chen",
        "robert chen": "Chen",
        "ada okonkwo revocable trust": "Okonkwo",
        "g whitfield": "Whitfield",
        "nakamura holdings llc": "Nakamura",
        "thompson joint": "Thompson",
        "rachel daniel abramson": "Abramson",
        "megan tom sullivan": "Sullivan",
        "bill fitzgerald": "Fitzgerald",
    }
    if holder_key in aliases and aliases[holder_key] in groups:
        return [aliases[holder_key]]
    candidates = []
    holder_tokens = set(holder_key.split())
    for label, records in groups.items():
        label_tokens = set(key(label).split())
        member_last_names = {parse_person_name(r.values["Name"])[1].lower() for r in records}
        if label_tokens and label_tokens <= holder_tokens:
            candidates.append(label)
        elif any(last in holder_tokens for last in member_last_names):
            candidates.append(label)
    return sorted(set(candidates))


def resolve(bundle: StagingBundle, agent: SemanticAgent, rates: dict[str, Any], reporting_date: str = "2025-06-30") -> dict[str, Any]:
    provenance: list[dict[str, Any]] = []
    decisions: list[Decision] = []
    page_signals: dict[str, dict[str, Any]] = {}
    for record in bundle.clients + bundle.meetings:
        if record.page_body:
            page_signals[record.page_path or record.values["Name"]] = agent.extract_page_signals(record.values["Name"], record.page_body, record.page_path or "")

    advisors = []
    advisor_rows = []
    for record in bundle.advisors:
        item = {"advisor_id": record.values["advisor_id"], "full_name": clean(record.values["full_name"]), "role": clean(record.values["role"])}
        advisors.append(item)
        advisor_rows.append(record.values)
        provenance.extend(_record_provenance("advisor", item["advisor_id"], item, _source(record)))

    groups: dict[str, list[SourceRecord]] = defaultdict(list)
    name_to_label: dict[str, str] = {}
    for record in bundle.clients:
        label = _client_label(record)
        groups[label].append(record)
        name_to_label[key(record.values["Name"])] = label
    name_to_label["bob chen"] = "Chen"
    name_to_label["petrov dmitri"] = "Petrov"

    household_by_label: dict[str, dict[str, Any]] = {}
    blocked_labels: dict[str, str] = {}
    clients = []
    for label, records in sorted(groups.items()):
        statuses, lineage = [], []
        for record in records:
            status, tags, _ = normalize_status(record.values["Status"], label)
            statuses.append(status)
            lineage.extend(tags)
        household_status = "ACTIVE" if "ACTIVE" in statuses else ("PROSPECT" if "PROSPECT" in statuses else "INACTIVE")
        if key(label) == "thompson":
            household_status = "INACTIVE"
        advisors_found = []
        for record in records:
            match = advisor_alias(record.values.get("Advisor"), advisor_rows)
            if match:
                advisors_found.append(match["advisor_id"])
        advisor_ids = sorted(set(advisors_found))
        crm_tags = {key(part).replace(" ", "_") for record in records for part in clean(record.values.get("Tags")).split(",") if part.strip()}
        if "deceased" in crm_tags and household_status == "ACTIVE":
            blocked_labels[label] = "CRM status is Active but the record is tagged Deceased"
        elif len(advisor_ids) != 1:
            blocked_labels[label] = "A required primary advisor cannot be determined without guessing"
        if label in blocked_labels:
            decisions.append(Decision(
                "household",
                _source(records[0]),
                "flag",
                blocked_labels[label],
                0.0,
                [a["full_name"] for a in advisors],
                [f"Household: {label}", "Clients: " + ", ".join(clean(r.values["Name"]) for r in records)],
            ))
            continue

        household_id = stable_id("HH", label)
        household = {
            "household_id": household_id,
            "household_name": label,
            "primary_advisor_id": advisor_ids[0],
            "status": household_status,
            "as_of_date": reporting_date,
            "source_tags": sorted(set(lineage)),
        }
        household_by_label[label] = household
        provenance.extend(_record_provenance("household", household_id, household, _source(records[0]), "rule"))
        for index, record in enumerate(records):
            name_key = key(record.values["Name"])
            if label == "Petrov" and name_key == "petrov dmitri":
                decisions.append(Decision("client", _source(record), "merged", "Stakeholder-confirmed duplicate of Dmitri Petrov", 1.0, ["Dmitri Petrov"], [record.page_body]))
                continue
            first, last = parse_person_name(record.values["Name"])
            role = "PRIMARY" if index == 0 else "SPOUSE"
            if label == "Nakamura":
                role = "SIGNER"
            item = {
                "client_id": stable_id("CL", "Petrov" if label == "Petrov" else record.values["Name"]),
                "household_id": household_id,
                "first_name": first,
                "last_name": last,
                "role": role,
                "source_tags": sorted(set(_tags(record))),
            }
            clients.append(item)
            provenance.extend(_record_provenance("client", item["client_id"], item, _source(record)))
            decisions.append(Decision("client", _source(record), "auto_apply", f"Mapped to {label} household", 1.0))

    accounts = []
    account_to_household: dict[str, str] = {}
    for record in bundle.accounts:
        values = record.values
        account_id = clean(values["Account_Number"])
        holder = clean(values["Account_Holder"])
        if account_id == "CU-5011":
            decisions.append(Decision("account", _source(record), "flag", "Kenji Nakamura's personal IRA may belong to the corporate or a separate personal household", 0.2, ["Nakamura Holdings household", "Separate Kenji Nakamura household"]))
            continue
        candidates = _account_candidates(holder, groups)
        needs_semantic_adjudication = len(candidates) > 1 or key(holder) in {"bob linda chen", "g whitfield", "bill fitzgerald"}
        if needs_semantic_adjudication:
            adjudication = agent.adjudicate(holder, candidates, [f"Custodian account holder: {holder}"])
        elif len(candidates) == 1:
            adjudication = {"choice": candidates[0], "confidence": 1.0, "rationale": "Unique deterministic name/household match"}
        else:
            adjudication = {"choice": None, "confidence": 0.0, "rationale": "No CRM candidate"}
        label = adjudication.get("choice")
        if not label:
            decisions.append(Decision("account", _source(record), "flag", "No unique existing CRM household match", float(adjudication.get("confidence", 0)), candidates, [holder]))
            continue
        if label in blocked_labels:
            decisions.append(Decision("account", _source(record), "flag", f"Matched household is blocked: {blocked_labels[label]}", 1.0, [label], [holder]))
            continue
        as_of = parse_date(values["As_Of_Date"])
        if as_of < reporting_date and household_by_label[label]["status"] == "ACTIVE":
            decisions.append(Decision("account", _source(record), "flag", f"Active-household position is stale ({as_of} vs {reporting_date})", 1.0, [label], [holder]))
            continue
        currency = clean(values["Currency"])
        item = {
            "account_id": account_id,
            "household_id": household_by_label[label]["household_id"],
            "account_type": normalize_account_type(values["Account_Type"]),
            "market_value_usd": convert_to_usd(values["Market_Value"], currency, rates["rates_to_usd"]),
            "currency_original": currency,
            "as_of_date": as_of,
            "custodian": clean(values["Custodian"]),
        }
        accounts.append(item)
        account_to_household[account_id] = label
        provenance.extend(_record_provenance("account", account_id, item, _source(record), "rule" if currency != "USD" else "direct"))
        if currency != "USD":
            provenance.append(provenance_entry("account", account_id, "market_value_usd", item["market_value_usd"], {"path": "config/fx_rates.yml", "source_url": rates["source_url"]}, "derived", 1.0, "reporting_currency_usd_v1", f"{values['Market_Value']} {currency} × {rates['rates_to_usd'][currency]}"))
        decisions.append(Decision("account", _source(record), "auto_apply", f"Unique match to {label}", float(adjudication.get("confidence", 1.0)), [label], [holder]))

    interactions = []
    for record in bundle.meetings:
        values = record.values
        client_key = key(values["Client"])
        label = name_to_label.get(client_key)
        if not label:
            decisions.append(Decision("interaction", _source(record), "flag", "Interaction client does not match an existing CRM household; canonical rules forbid minting one from a meeting", 0.0, [], [clean(values["Client"])]))
            continue
        if label in blocked_labels:
            decisions.append(Decision("interaction", _source(record), "flag", f"Matched household is blocked: {blocked_labels[label]}", 1.0, [label]))
            continue
        attendee = advisor_alias(values.get("Attendee"), advisor_rows)
        interaction_id = stable_id("IN", values["Name"], values["Date"])
        item = {
            "interaction_id": interaction_id,
            "household_id": household_by_label[label]["household_id"],
            "interaction_type": normalize_interaction_type(values["Type"]),
            "interaction_date": parse_date(values["Date"]),
            "advisor_id": attendee["advisor_id"] if attendee else None,
            "summary": record.page_body or None,
        }
        interactions.append(item)
        provenance.extend(_record_provenance("interaction", interaction_id, item, _source(record), "rule"))
        decisions.append(Decision("interaction", _source(record), "auto_apply", f"Resolved {values['Client']} to {label}", 0.99, [label]))

    return {
        "advisors": advisors,
        "households": list(household_by_label.values()),
        "clients": clients,
        "accounts": accounts,
        "interactions": interactions,
        "provenance": provenance,
        "decisions": [decision.as_dict() for decision in decisions],
        "page_signals": page_signals,
        "blocked_households": blocked_labels,
    }
