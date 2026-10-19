from __future__ import annotations

from collections import defaultdict
from typing import Any


def generate_clarifications(decisions: list[dict[str, Any]], advisors: list[dict[str, Any]]) -> str:
    flagged = [item for item in decisions if item["outcome"] == "flag"]
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in flagged:
        by_type[item["entity_type"]].append(item)

    advisor_names = ", ".join(item["full_name"] for item in advisors)
    lines = [
        "Hi Dana — thanks again for the first round. We applied those answers and reran the mapping. These are the remaining items that block a confident canonical record:",
        "",
    ]
    household_flags = by_type.get("household", [])
    advisor_flags = [item for item in household_flags if "primary advisor" in item["reason"]]
    status_flags = [item for item in household_flags if "Deceased" in item["reason"]]
    if advisor_flags:
        lines.extend(["## 1. Primary advisor assignments", "", "Who is the advisor for each household below? We did not fall back to Service Rep, per your guidance.", ""])
        for item in advisor_flags:
            evidence = "; ".join(item.get("evidence") or [])
            lines.append(f"- **{evidence}** — {item['reason']}")
        lines.extend(["", f"Candidates from the current roster: {advisor_names}.", "**Proposed default:** leave these households out of the clean canonical output until you assign an advisor.", ""])
    if status_flags:
        for item in status_flags:
            evidence = "; ".join(item.get("evidence") or [])
            lines.extend(["## 2. Omar Farouk status", "", "Should Omar Farouk's household remain **Active**, move to **Inactive**, or be represented under an estate/contact record?", "", f"Evidence: {evidence}; the CRM is Active but tagged Deceased.", "**Proposed default:** quarantine the household and account until status is confirmed.", ""])

    account_flags = by_type.get("account", [])
    nakamura = [item for item in account_flags if "Nakamura" in item["reason"]]
    orphans = [item for item in account_flags if "No unique" in item["reason"]]
    stale = [item for item in account_flags if "stale" in item["reason"]]
    blocked = [item for item in account_flags if "Matched household is blocked" in item["reason"]]
    number = 3 if status_flags else 2
    if nakamura:
        lines.extend([f"## {number}. Kenji Nakamura IRA", "", "Should Kenji's personal IRA roll up to the **Nakamura Holdings household** or a **separate Kenji Nakamura household**?", "", "Evidence: the client and meeting notes explicitly say the family has not decided.", "**Proposed default:** keep the IRA quarantined; continue mapping the corporate account to Nakamura Holdings.", ""]); number += 1
    if orphans:
        evidence = ", ".join((item.get("evidence") or ["unknown holder"])[0] for item in orphans)
        lines.extend([f"## {number}. Custodian-only account holders", "", f"Which existing household, if any, should own these custodian records: **{evidence}**?", "", "**Proposed default:** keep them quarantined rather than create households that do not exist in the CRM.", ""]); number += 1
    if stale:
        evidence = "; ".join(item["reason"] for item in stale)
        lines.extend([f"## {number}. Stale quarter-end positions", "", f"Should we use the last known balances or wait for corrected 2025-06-30 positions? Evidence: {evidence}.", "", "**Proposed default:** exclude stale positions from current AUM until refreshed, while retaining the household.", ""]); number += 1

    interaction_flags = by_type.get("interaction", [])
    redwood = [item for item in interaction_flags if "existing CRM household" in item["reason"]]
    if redwood:
        lines.extend([f"## {number}. Redwood Capital meeting", "", "Is Redwood Capital an existing prospect household under another CRM name, or should it be added to the CRM first?", "", "Evidence: the meeting export has a Redwood Capital relation, but no client/household record exists. Canonical rules prevent creating a household from a meeting.", "**Proposed default:** quarantine the interaction until a CRM household exists.", ""]); number += 1

    lines.extend(["## Quick reply format", "", "`Advisor assignments: [household → advisor]; Nakamura IRA: [corporate/separate]; custodian-only holders: [mapping/new]; stale balances: [last known/wait]; Redwood: [alias/add first]`", ""])
    return "\n".join(lines)
