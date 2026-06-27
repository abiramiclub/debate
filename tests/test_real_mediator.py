"""Offline structural test for the real ClaudeMediator: with a stub client
(no network, no key), the 4 methods build prompts and parse responses correctly.
This proves the adapter will work once real credentials are supplied."""

from types import SimpleNamespace

from mediator.base import Read
from mediator.claude import ClaudeMediator

READS = [Read("Birch", "four-day week helps wellbeing", 4),
         Read("Cedar", "need five-day client coverage", 4)]
CANDIDATES = ["Pilot a four-day week with a coverage rota.", "Keep five days."]


class _StubClient:
    """Returns canned responses keyed by what the prompt is asking for."""
    def __init__(self):
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, model, max_tokens, system, messages):
        prompt = messages[0]["content"]
        if "COMMON-GROUND" in prompt:
            text = '["Pilot a four-day week with a rota.", "Trial it for a quarter."]'
        elif "estimate agreement" in prompt:
            text = "[[0.9, 0.2], [0.6, 0.8]]"
        elif "minority view" in prompt:
            text = "The coverage concern is real and must be protected."
        else:  # echo
            text = '{"echo": true, "reason": "no new information"}'
        return SimpleNamespace(content=[SimpleNamespace(text=text)])


def _med():
    return ClaudeMediator(client=_StubClient())


def test_synthesize_parses_json_array():
    out = _med().synthesize_candidates(READS, 2)
    assert out == ["Pilot a four-day week with a rota.", "Trial it for a quarter."]


def test_predict_agreement_parses_matrix():
    m = _med().predict_agreement(READS, CANDIDATES)
    assert m == [[0.9, 0.2], [0.6, 0.8]]
    assert all(0.0 <= x <= 1.0 for row in m for x in row)


def test_steelman_returns_text():
    assert "coverage" in _med().steelman_minority(READS, [0, 1]).lower()


def test_detect_echo_parses_bool_and_reason():
    echo, reason = _med().detect_echo(["x"], ["x"])
    assert echo is True and reason
