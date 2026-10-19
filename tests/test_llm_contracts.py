import io
import json

from nevis_pipeline.llm import SemanticAgent


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_real_agent_requests_strict_structured_output(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured.update(json.loads(request.data))
        return FakeResponse({"id": "resp_test", "output_text": json.dumps({
            "choice": "Chen", "confidence": 0.99, "rationale": "unique", "evidence": ["Bob Chen"]
        })})

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    agent = SemanticAgent(mode="real", model="test-model")
    result = agent.adjudicate("Bob Chen", ["Chen"], ["Bob is Robert"])

    assert result["choice"] == "Chen"
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["text"]["format"]["strict"] is True
    assert agent.manifest()["calls"][0]["response_id"] == "resp_test"


def test_anthropic_agent_uses_schema_bound_tool(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        return FakeResponse({
            "id": "msg_test",
            "content": [{"type": "tool_use", "name": "emit_json", "input": {
                "choice": "Chen", "confidence": 0.99, "rationale": "unique", "evidence": ["Bob Chen"]
            }}],
        })

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    agent = SemanticAgent(mode="real", model="claude-test")
    result = agent.adjudicate("Bob Chen", ["Chen"], ["Bob is Robert"])

    assert result["choice"] == "Chen"
    assert captured["url"].endswith("/v1/messages")
    assert captured["body"]["tool_choice"] == {"type": "tool", "name": "emit_json"}
    assert captured["body"]["tools"][0]["input_schema"]["type"] == "object"
    assert agent.manifest()["calls"][0]["response_id"] == "msg_test"


def test_hermes_agent_records_real_session_id(monkeypatch):
    class Completed:
        returncode = 0
        stdout = '{"choice":"Chen","confidence":0.98,"rationale":"unique","evidence":["Bob"]}\n'
        stderr = "session_id: 20261018_test\n"

    monkeypatch.setenv("LLM_PROVIDER", "hermes")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Completed())
    agent = SemanticAgent(mode="real", model="gpt-test")
    result = agent.adjudicate("Bob Chen", ["Chen"], ["Bob"])

    assert result["choice"] == "Chen"
    assert agent.manifest()["provider"] == "hermes"
    assert agent.manifest()["calls"][0]["response_id"] == "20261018_test"
    assert agent.manifest()["real_llm_used"] is True
