"""Live path plumbing: real reads -> live-generated candidates + agreement (via a
STUB ClaudeMediator client, no network) -> the engine's deterministic selection,
gates, and audit over MCP -> bridged quorum. Proves the wiring the live /decide
uses; the actual LLM call is validated in the sandbox."""

import asyncio
import json
import re
from types import SimpleNamespace

from slack_app.agent import run_live_session_over_mcp

POLARIZED = ["Ship the chatbot; people want a chat UI.",
             "Build the wiki; accuracy and auditability matter."]
COMPROMISE = ["Build the sourced wiki first; add a thin conversational layer on top.",
              "Just build the chatbot.", "Just build the wiki."]
EVIDENCE_MARK = "postmortem"

PARTICIPANTS = [
    {"user_id": "alex", "handle": "Birch", "actor_type": "human"},
    {"user_id": "bturing", "handle": "Willow", "actor_type": "agent"},
    {"user_id": "chen", "handle": "Rowan", "actor_type": "human"},
    {"user_id": "dimitri", "handle": "Maple", "actor_type": "human"},
    {"user_id": "esme", "handle": "Cedar", "actor_type": "human"},
]
READS = [
    {"handle": "Birch", "text": "a chat UI is what people want", "confidence": 4},
    {"handle": "Willow", "text": "chat just feels nicer", "confidence": 4},
    {"handle": "Rowan", "text": "guardrails can come later", "confidence": 4},
    {"handle": "Maple", "text": "accuracy and an audit trail matter", "confidence": 5},
    {"handle": "Cedar", "text": "we got paged at 3am; accuracy isn't optional", "confidence": 5},
]
EVIDENCE = {"text": "From the #incidents postmortem: the bot hallucinated a refund step.",
            "source": "https://acme.slack.com/archives/C0/p1", "handle": "Linden", "label": "fixture"}


class _StubClient:
    """Deterministic stand-in for the Anthropic client. Evidence-aware synthesis
    (compromise once the postmortem is in view) and candidate-count-aware
    agreement (polarized for 2 candidates, broadly-endorsed for 3)."""

    def __init__(self):
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, model, max_tokens, system, messages):
        p = messages[0]["content"]
        if "COMMON-GROUND" in p:
            text = json.dumps(COMPROMISE if EVIDENCE_MARK in p else POLARIZED)
        elif "estimate agreement" in p:
            n_cand = len(re.findall(r"C\d+:", p))
            rows = ([[0.85, 0.90, 0.15]] * 3 + [[0.82, 0.15, 0.88]] * 2) if n_cand >= 3 \
                else ([[0.90, 0.15]] * 3 + [[0.15, 0.90]] * 2)
            text = json.dumps(rows)
        elif "minority view" in p:
            text = "The accuracy and audit-trail concern deserves fair weight."
        else:
            text = '{"echo": false, "reason": "n/a"}'
        return SimpleNamespace(content=[SimpleNamespace(text=text)])


def test_live_path_reaches_bridged_quorum_over_mcp():
    out = asyncio.run(run_live_session_over_mcp(
        question="chatbot or wiki?", reads=READS, participants=PARTICIPANTS,
        client=_StubClient(), evidence=EVIDENCE, session_id="test-live"))

    assert out["delib"]["reached_quorum"] is True
    assert out["debrief"]["winner"] == COMPROMISE[0]
    actions = [e["action"] for e in out["debrief"]["audit"]]
    for beat in ("store_read", "inject_evidence", "check_quorum",
                 "steelman_minority", "debrief"):
        assert beat in actions, beat
    ai = [p["handle"] for p in out["debrief"]["participants"] if p["actor_type"] == "agent"]
    assert ai == ["Willow"]
