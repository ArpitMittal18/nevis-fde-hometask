from pathlib import Path

from nevis_pipeline.ingest import ingest_sources


ROOT = Path(__file__).resolve().parents[1]


def test_ingest_skips_xlsx_header_row():
    bundle = ingest_sources(ROOT / "sources")

    assert len(bundle.accounts) == 53
    assert bundle.accounts[0].values["Account_Number"] == "CU-5001"
    assert all(record.values["Account_Holder"] != "Account_Holder" for record in bundle.accounts)


def test_ingest_preserves_notion_page_body():
    bundle = ingest_sources(ROOT / "sources")
    linda = next(record for record in bundle.clients if record.values["Name"] == "Linda Chen")

    assert "Wife of Robert Chen" in linda.page_body
    assert linda.page_path and linda.page_path.endswith(".md")
