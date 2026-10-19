import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_client_rules_capture_question_answer_conditions_and_effect():
    rules = json.loads((ROOT / "config" / "client_rules.yml").read_text())["rules"]

    assert rules
    for rule in rules:
        assert rule["asked_question"].strip()
        assert rule["answer"].strip()
        assert rule["conditions"]
        assert isinstance(rule["effect"], dict)
        assert rule["effect"]
