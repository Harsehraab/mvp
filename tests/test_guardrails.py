import json

from crew_ai.guardrails import guardrail_check


class FakeResponse:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    def __init__(self, content: str):
        self._content = content

    def invoke(self, messages):
        return FakeResponse(self._content)


def test_guardrail_parses_valid_json():
    llm = FakeLLM('{"Toxicity":"no","Prompt Injection":"no","PII (except name)":"no","Violence":"no","verdict":"allow","rationale":"safe"}')
    res = guardrail_check("Hello world", llm=llm)
    assert "parsed" in res
    parsed = res["parsed"]
    # Assert normalized keys and values
    assert parsed["verdict"] == "allow"
    assert parsed["toxicity"] == "no"
    assert parsed["prompt_injection"] == "no"
    assert parsed["pii_except_name"] == "no"
    assert parsed["violence"] == "no"
    assert parsed["rationale"] == "safe"


def test_guardrail_handles_non_json_response():
    llm = FakeLLM("I refuse to answer")
    res = guardrail_check("some prompt", llm=llm, max_attempts=1)
    assert res.get("error") in ("no_valid_json", "no_llm") or "warning" in res
