"""Regression test for the `/decide replay` render path.

Root cause of the reported bug: mcp_server/server.py's `deliberate` tool built
its response from RoundResult but omitted the `candidates` field, even though
RoundResult.candidates exists. slack_app/app.py::_post_beats accessed
delib["rounds"][0]["candidates"] and raised KeyError. No test exercised
_post_beats end-to-end, so the gap shipped silently.

NOTE: this was NOT a fixture schema issue — the committed fixture already
nests candidates correctly under rounds[i]["candidates"]; regenerating it would
not have fixed anything. The fix is in the MCP wrapper's response shape.
"""

import asyncio
import json

from slack_app.agent import run_session_over_mcp
from slack_app.app import _post_beats, _run_replay_or_report
from slack_app.run_scripted import load_fixture


class FakeClient:
    def __init__(self):
        self.messages: list[dict] = []
        self.ephemerals: list[dict] = []

    async def chat_postMessage(self, channel, blocks, text):
        self.messages.append({"channel": channel, "blocks": blocks, "text": text})

    async def chat_postEphemeral(self, channel, user, text):
        self.ephemerals.append({"channel": channel, "user": user, "text": text})


def _blob(client: FakeClient) -> str:
    return json.dumps(client.messages)


def test_post_beats_renders_the_full_replay_without_keyerror():
    fx = load_fixture()
    result = asyncio.run(run_session_over_mcp(fx, session_id="test-replay-render"))
    client = FakeClient()

    asyncio.run(_post_beats(client, "#training", result, fx["steelman_text"]))

    assert len(client.messages) >= 6
    blob = _blob(client)
    # candidates reveal (the bug: this key was missing from the MCP response)
    assert fx["rounds"][1]["candidates"][0] in blob or fx["rounds"][1]["candidates"][1] in blob
    # steelman
    assert "steelman" in blob.lower() or "accuracy and audit-trail" in blob.lower()
    # postmortem citation (the evidence beat)
    assert "incidents-postmortem" in blob or "postmortem" in blob
    # quorum + the bridged winner
    assert "QUORUM MET" in blob
    assert result["debrief"]["winner"] in blob


def test_replay_success_posts_no_ephemeral():
    fx = load_fixture()
    client = FakeClient()
    asyncio.run(_run_replay_or_report(client, "#training", "U123", fx))
    assert client.ephemerals == []
    assert len(client.messages) >= 6


def test_replay_failure_reports_ephemeral_not_silent(monkeypatch):
    import slack_app.app as app_mod

    async def _boom(fx, session_id):
        raise RuntimeError("engine unreachable")

    monkeypatch.setattr(app_mod, "run_session_over_mcp", _boom)
    client = FakeClient()
    asyncio.run(_run_replay_or_report(client, "#training", "U123", load_fixture()))

    assert len(client.ephemerals) == 1
    assert client.ephemerals[0]["user"] == "U123"
    assert "Replay failed" in client.ephemerals[0]["text"]
    assert "engine unreachable" in client.ephemerals[0]["text"]
