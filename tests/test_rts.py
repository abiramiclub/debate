"""RTS adapter: offline proof of parsing + the position-neutrality gate, plus a
token-gated live check that runs only when SLACK_RTS_TOKEN is set."""

import os

import pytest

from constitution.evidence import RTSAdapter, RTSAdapterStub, _advocates_position


def test_neutrality_gate():
    assert _advocates_position("You should adopt the four-day week.")
    assert not _advocates_position(
        "A 2022 pilot reported output was maintained with a coverage rota.")


def test_requires_token():
    with pytest.raises(ValueError):
        RTSAdapter(token="")


def test_fetch_parses_and_skips_advocacy(monkeypatch):
    ad = RTSAdapter(token="xoxb-test")
    # First result advocates (must be skipped); second is a neutral, sourced fact.
    monkeypatch.setattr(ad, "_call", lambda q: [
        {"text": "We should obviously adopt this.", "permalink": "https://x/1"},
        {"text": "A 2022 trial maintained output with a rota.", "permalink": "https://x/2"},
    ])
    ev = ad.fetch({"query": "four day week"})
    assert ev is not None
    assert ev.source == "https://x/2"
    assert ev.label == "rts"


def test_fetch_returns_none_when_all_advocacy(monkeypatch):
    ad = RTSAdapter(token="xoxb-test")
    monkeypatch.setattr(ad, "_call", lambda q: [
        {"text": "You should vote for this.", "permalink": "https://x/1"}])
    assert ad.fetch({"query": "x"}) is None


def test_stub_still_fails_loudly():
    with pytest.raises(NotImplementedError):
        RTSAdapterStub().fetch({})


@pytest.mark.skipif(not os.environ.get("SLACK_RTS_TOKEN"),
                    reason="no SLACK_RTS_TOKEN — live RTS seam needs the sandbox token")
def test_live_rts_roundtrip():
    ad = RTSAdapter(os.environ["SLACK_RTS_TOKEN"])
    ev = ad.fetch({"query": "four-day week pilot results"})
    assert ev is None or (ev.source and ev.text)
