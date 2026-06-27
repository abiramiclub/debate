"""Structurally validate the committed Block Kit debrief against the schema
checker, and confirm a freshly built one still validates."""

import json
import os
import tempfile

from demo.build_debrief import build_blocks, validate_blockkit
from demo.run_ab import load_fixture, run_constitution

DEBRIEF = os.path.join(os.path.dirname(__file__), "..", "demo", "debrief_blockkit.json")


def test_committed_debrief_validates():
    with open(DEBRIEF) as f:
        payload = json.load(f)
    assert validate_blockkit(payload)
    assert payload["blocks"][0]["type"] == "header"


def test_freshly_built_debrief_validates():
    fx = load_fixture()
    path = os.path.join(tempfile.mkdtemp(), "audit.jsonl")
    session, _, debrief = run_constitution(fx, path)
    payload = build_blocks(fx, session, debrief)
    assert validate_blockkit(payload)
