from pathlib import Path

from nevis_pipeline.pipeline import run_pipeline


ROOT = Path(__file__).resolve().parents[1]


def test_clarifications_name_every_blocked_household(tmp_path):
    text = run_pipeline(ROOT / "sources", tmp_path, mode="replay")["clarifications"]

    for name in ("Maria Delgado", "George Whitfield", "Louis Petit", "Joris Vandermeer"):
        assert name in text
    assert "Omar Farouk" in text
    assert "Active" in text and "Deceased" in text


def test_clarifications_include_only_real_custodian_holders(tmp_path):
    text = run_pipeline(ROOT / "sources", tmp_path, mode="replay")["clarifications"]

    assert "Carlos Vasquez" in text
    assert "Priyanka Mehta" in text
    assert "**Account_Holder" not in text
