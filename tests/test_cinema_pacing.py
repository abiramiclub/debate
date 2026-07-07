"""Cinema-pacing regression test for `/decide replay`.

Asserts the pacing map (CINEMA_PACING) is applied ONLY when cinema mode is on:
default (fast) mode makes zero sleep calls and is unchanged; cinema mode sleeps
once per pacing-map entry, in order, with the expected (de-jittered) durations.
"""

import asyncio

import pytest

import slack_app.app as app_mod
from slack_app.run_scripted import load_fixture


class FakeClient:
    def __init__(self):
        self.messages: list[str] = []
        self.ephemerals: list[str] = []

    async def chat_postMessage(self, channel, blocks, text):
        self.messages.append(text)

    async def chat_postEphemeral(self, channel, user, text):
        self.ephemerals.append(text)


@pytest.fixture
def sleep_spy(monkeypatch):
    calls: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    monkeypatch.setattr(app_mod, "_sleep", fake_sleep)
    monkeypatch.setattr(app_mod, "_jitter", lambda seconds: seconds)  # deterministic
    return calls


def test_fast_mode_makes_no_sleep_calls(sleep_spy):
    fx = load_fixture()
    client = FakeClient()
    asyncio.run(app_mod._run_replay_or_report(client, "#training", "U1", fx, cinema=False))

    assert sleep_spy == []
    assert client.ephemerals == []
    # fast mode: banner is the first (and only pre-beat) message — no consent/handles theater
    assert client.messages[0] == "replay"


def test_cinema_mode_sleeps_once_per_pacing_entry_in_order(sleep_spy):
    fx = load_fixture()
    client = FakeClient()
    asyncio.run(app_mod._run_replay_or_report(client, "#training", "U1", fx, cinema=True))

    expected = [seconds for _, seconds in app_mod.CINEMA_PACING]
    assert sleep_spy == expected, "one sleep call per CINEMA_PACING entry, in order, undelayed"


def test_cinema_mode_shows_opener_and_handles_fast_mode_does_not(sleep_spy):
    fx = load_fixture()

    fast = FakeClient()
    asyncio.run(app_mod._run_replay_or_report(fast, "#training", "U1", fx, cinema=False))
    assert "A decision to make" not in fast.messages
    assert "Handles assigned" not in fast.messages

    cinema = FakeClient()
    asyncio.run(app_mod._run_replay_or_report(cinema, "#training", "U1", fx, cinema=True))
    assert "A decision to make" in cinema.messages
    assert "Handles assigned" in cinema.messages
    assert cinema.messages.index("A decision to make") < cinema.messages.index("Handles assigned")
    assert cinema.messages.index("Handles assigned") < cinema.messages.index("replay")


def test_cinema_mode_skips_the_live_button_prompt(sleep_spy):
    fx = load_fixture()
    client = FakeClient()
    asyncio.run(app_mod._run_replay_or_report(client, "#training", "U1", fx, cinema=True))
    assert not any("run the deliberation with the button" in m for m in client.messages)


def test_steelman_rule_label_precedes_the_steelman_quote_both_modes(sleep_spy):
    fx = load_fixture()
    for cinema in (False, True):
        client = FakeClient()
        asyncio.run(app_mod._run_replay_or_report(client, "#training", "U1", fx, cinema=cinema))
        assert "steelman rule" in client.messages
        assert "minority steelman" in client.messages
        assert client.messages.index("steelman rule") < client.messages.index("minority steelman")
