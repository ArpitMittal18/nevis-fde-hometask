# Source Data Profile

Generated before canonical mapping. Types describe the source columns, not the final Nevis schema.

## advisor_roster

Source: `sources/advisor_roster.csv` · Rows: **7**

| Column | Type | Nulls | Distinct | Observed values / examples |
|---|---:|---:|---:|---|
| `advisor_id` | `identifier` | 0 | 7 | `ADV-001`, `ADV-002`, `ADV-003`, `ADV-004`, `ADV-005` |
| `full_name` | `text` | 0 | 7 | `David Feldman`, `Elena Sokolova`, `Grace Bennett`, `James Okafor`, `Marcus Webb` |
| `role` | `enum` | 0 | 3 | `Advisor`, `Relationship Manager`, `Senior Advisor` |
| `office` | `enum` | 0 | 4 | `Boston`, `Chicago`, `New York`, `San Francisco` |

## clients

Source: `sources/notion_export/Clients 484b3fe4ea9195d2052e7bc37063ffc7.csv` · Rows: **57**

| Column | Type | Nulls | Distinct | Observed values / examples |
|---|---:|---:|---:|---|
| `Name` | `text` | 0 | 57 | `Ada Okonkwo`, `Adaeze Osei`, `Amara Nwosu`, `Anna Kowalski`, `Astrid Johansson` |
| `Status` | `enum` | 0 | 7 | `Active`, `Churned`, `Client`, `Former`, `Legacy`, `Prospect`, `active ` |
| `Advisor` | `enum` | 4 | 9 | `David Feldman`, `E. Sokolova`, `Elena Sokolova`, `Grace Bennett`, `James Okafor`, `Marcus Webb`, `P. Raman`, `Priya Raman`, `Sofia Marchetti` |
| `Service Rep` | `enum` | 52 | 2 | `A. Novak`, `Marcus Webb` |
| `Household` | `text` | 1 | 53 | `Abramson Household`, `Al-Rashid`, `Ashford`, `Bakker Household`, `Bauer Household` |
| `Segment` | `enum` | 0 | 4 | `Corporate`, `HNW`, `High Net Worth`, `Mass Affluent` |
| `Client Since` | `date` | 0 | 49 | `April 18, 2014`, `April 26, 2016`, `April 27, 2013`, `April 3, 2018`, `August 27, 2019` |
| `Website` | `url` | 55 | 2 | `www.example-chen.com`, `www.nakamura-holdings.example` |
| `Risk Profile` | `enum` | 7 | 5 | `Aggressive`, `Balanced`, `Conservative`, `Growth`, `Moderate` |
| `Fee Schedule` | `enum` | 5 | 7 | `0.85%`, `0.85% – negotiated`, `1.00%`, `1.10%`, `See LOE`, `Tier 1`, `Tier 2` |
| `Referred By` | `text` | 54 | 3 | `Emily Harrington`, `Gregory Palme`, `Seminar 2023` |
| `Tags` | `multi_enum` | 52 | 5 | `Deceased`, `Do Not Contact`, `ESG`, `Held Away`, `VIP` |

## meetings

Source: `sources/notion_export/Meetings 2b26fa77d1142f88db92d6b69dc697fd.csv` · Rows: **18**

| Column | Type | Nulls | Distinct | Observed values / examples |
|---|---:|---:|---:|---|
| `Name` | `text` | 0 | 18 | `Annual Review — Johansson`, `Check-in — Harrington`, `Discovery — Bauer`, `Intro Call — Costa`, `Intro Call — Fairbanks` |
| `Client` | `text` | 0 | 18 | `Ada Okonkwo`, `Astrid Johansson`, `Bill Thompson`, `Bob Chen`, `Emily Harrington` |
| `Type` | `enum` | 0 | 8 | `Annual Review`, `Check-in`, `Discovery`, `Intro Call`, `Onboarding`, `Prospecting`, `QBR`, `Review` |
| `Date` | `date` | 0 | 18 | `April 2, 2025`, `April 20, 2025`, `April 30, 2025`, `February 18, 2025`, `January 15, 2025` |
| `Attendee` | `enum` | 1 | 10 | `A. Novak`, `David Feldman`, `E. Sokolova`, `Elena Sokolova`, `Grace Bennett`, `James Okafor`, `Marcus Webb`, `P. Raman`, `Priya Raman`, `Sofia Marchetti` |

## custodian_positions — sheet `Positions`

Source: `sources/custodian_positions.xlsx` · Rows: **53**

| Column | Type | Nulls | Distinct | Observed values / examples |
|---|---:|---:|---:|---|
| `Account_Number` | `identifier` | 0 | 53 | `CU-5001`, `CU-5002`, `CU-5003`, `CU-5004`, `CU-5005` |
| `Account_Holder` | `text` | 0 | 49 | `Ada Okonkwo Revocable Trust`, `Adaeze Osei`, `Anna Kowalski`, `Astrid Johansson`, `Beatriz Gomes` |
| `Account_Type` | `enum` | 0 | 8 | `Corporate`, `IRA`, `Individual`, `Joint TIC`, `Joint WROS`, `Rollover IRA`, `Roth IRA`, `Trust-Rev` |
| `Market_Value` | `currency_amount` | 0 | 46 | `1220000`, `12400`, `1240000`, `1340000`, `1450000` |
| `Cost_Basis` | `currency_amount` | 49 | 4 | `1100000`, `1750000`, `1980000`, `750000` |
| `Currency` | `currency_code` | 0 | 3 | `CHF`, `EUR`, `USD` |
| `As_Of_Date` | `date` | 0 | 4 | `2023-09-30`, `2024-09-30`, `2024-12-31`, `2025-06-30` |
| `Custodian` | `enum` | 0 | 5 | `Fidelity`, `Lombard Intl`, `Pershing`, `Pictet`, `Schwab` |

## Type legend

- `identifier` — Stable source identifier, not a category
- `enum` — Single categorical value; values lists the observed domain
- `multi_enum` — Comma-separated categorical values
- `date` — Date or date-like source value
- `currency_code` — ISO-like currency category; values lists observed currencies
- `currency_amount` — Monetary amount requiring an associated currency
- `number` — Non-currency numeric value
- `boolean` — True/false value
- `url` — Web address
- `text` — Free text, name, or reference-like value

