Hi Dana — thanks again for the first round. We applied those answers and reran the mapping. These are the remaining items that block a confident canonical record:

## 1. Primary advisor assignments

Who is the advisor for each household below? We did not fall back to Service Rep, per your guidance.

- **Household: Delgado; Clients: Maria Delgado** — A required primary advisor cannot be determined without guessing
- **Household: Petit; Clients: Louis Petit** — A required primary advisor cannot be determined without guessing
- **Household: Vandermeer; Clients: Joris Vandermeer** — A required primary advisor cannot be determined without guessing
- **Household: Whitfield; Clients: George Whitfield** — A required primary advisor cannot be determined without guessing

Candidates from the current roster: Priya Raman, Marcus Webb, Elena Sokolova, James Okafor, Sofia Marchetti, David Feldman, Grace Bennett.
**Proposed default:** leave these households out of the clean canonical output until you assign an advisor.

## 2. Omar Farouk status

Should Omar Farouk's household remain **Active**, move to **Inactive**, or be represented under an estate/contact record?

Evidence: Household: Farouk; Clients: Omar Farouk; the CRM is Active but tagged Deceased.
**Proposed default:** quarantine the household and account until status is confirmed.

## 3. Kenji Nakamura IRA

Should Kenji's personal IRA roll up to the **Nakamura Holdings household** or a **separate Kenji Nakamura household**?

Evidence: the client and meeting notes explicitly say the family has not decided.
**Proposed default:** keep the IRA quarantined; continue mapping the corporate account to Nakamura Holdings.

## 4. Custodian-only account holders

Which existing household, if any, should own these custodian records: **Carlos Vasquez, Priyanka Mehta**?

**Proposed default:** keep them quarantined rather than create households that do not exist in the CRM.

## 5. Stale quarter-end positions

Should we use the last known balances or wait for corrected 2025-06-30 positions? Evidence: Active-household position is stale (2024-09-30 vs 2025-06-30).

**Proposed default:** exclude stale positions from current AUM until refreshed, while retaining the household.

## 6. Redwood Capital meeting

Is Redwood Capital an existing prospect household under another CRM name, or should it be added to the CRM first?

Evidence: the meeting export has a Redwood Capital relation, but no client/household record exists. Canonical rules prevent creating a household from a meeting.
**Proposed default:** quarantine the interaction until a CRM household exists.

## Quick reply format

`Advisor assignments: [household → advisor]; Nakamura IRA: [corporate/separate]; custodian-only holders: [mapping/new]; stale balances: [last known/wait]; Redwood: [alias/add first]`

