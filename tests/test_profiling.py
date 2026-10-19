from pathlib import Path

from nevis_pipeline.profiling import profile_sources


ROOT = Path(__file__).resolve().parents[1]


def test_profiles_every_csv_and_classifies_client_columns():
    profile = profile_sources(ROOT / "sources")

    csv_profiles = profile["csv_files"]
    assert len(csv_profiles) == 3
    clients = next(item for item in csv_profiles if item["dataset"] == "clients")
    columns = {item["name"]: item for item in clients["columns"]}

    assert columns["Name"]["type"] == "text"
    assert columns["Status"]["type"] == "enum"
    assert columns["Status"]["values"] == [
        "Active", "Churned", "Client", "Former", "Legacy", "Prospect", "active "
    ]
    assert columns["Client Since"]["type"] == "date"
    assert columns["Website"]["type"] == "url"
    assert columns["Tags"]["type"] == "multi_enum"


def test_profiles_currency_code_and_amount_in_workbook():
    profile = profile_sources(ROOT / "sources")
    positions = next(item for item in profile["workbooks"] if item["dataset"] == "custodian_positions")
    columns = {item["name"]: item for item in positions["columns"]}

    assert columns["Currency"]["type"] == "currency_code"
    assert columns["Currency"]["values"] == ["CHF", "EUR", "USD"]
    assert columns["Market_Value"]["type"] == "currency_amount"
    assert columns["Cost_Basis"]["type"] == "currency_amount"
    assert columns["As_Of_Date"]["type"] == "date"
