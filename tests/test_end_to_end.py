from pathlib import Path

from nevis_pipeline.pipeline import run_pipeline


ROOT = Path(__file__).resolve().parents[1]


def test_sample_pipeline_produces_schema_clean_outputs(tmp_path):
    result = run_pipeline(
        sources_dir=ROOT / "sources",
        output_dir=tmp_path,
        mode="replay",
    )

    assert result["source_counts"] == {
        "clients": 57,
        "meetings": 18,
        "accounts": 53,
        "advisors": 7,
    }
    canonical = result["canonical"]
    assert set(canonical) >= {
        "run_metadata",
        "advisors",
        "households",
        "clients",
        "accounts",
        "interactions",
        "provenance",
        "validation_summary",
    }
    assert len(canonical["advisors"]) == 7
    assert not canonical["validation_summary"]["hard_errors"]
    assert all(h["primary_advisor_id"] for h in canonical["households"])
    assert all(a["household_id"] for a in canonical["accounts"])
    assert all(i["household_id"] for i in canonical["interactions"])
    assert (tmp_path / "canonical_output.json").exists()
    assert (tmp_path / "clarifications_round_2.md").exists()
    assert (tmp_path / "decision_log.json").exists()
    assert (tmp_path / "llm_run_manifest.json").exists()
    assert (tmp_path / "source_profile.json").exists()
    assert (tmp_path / "source_profile.md").exists()
    assert result["source_profile"]["csv_files"]


def test_round_two_does_not_reask_resolved_round_one_questions(tmp_path):
    result = run_pipeline(ROOT / "sources", tmp_path, mode="replay")
    text = result["clarifications"].lower()

    assert "who is the advisor for" in text
    assert "nakamura" in text
    assert "redwood capital" in text
    assert "what does legacy mean" not in text
    assert "market value or cost basis" not in text
    assert "is petrov a duplicate" not in text
    assert "should thompson be inactive" not in text
