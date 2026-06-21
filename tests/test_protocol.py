"""Tests for the state machine: it runs end-to-end, enforces ordering, keeps the
mediator out of decisions, and writes an audit."""

import os
import tempfile

import pytest

from constitution.protocol import Session, State
from mediator.fake import FakeMediator


def _new_session():
    path = os.path.join(tempfile.mkdtemp(), "audit.jsonl")
    return Session("test", FakeMediator(), audit_path=path)


def _seed(session):
    session.start([("u1", "human"), ("u2", "human"), ("u3", "human")])
    session.submit_read("Birch", "Flexibility and remote work help the team.", 4)
    session.submit_read("Maple", "Office collaboration helps mentorship.", 4)
    session.submit_read("Cedar", "A hybrid balance respects both sides.", 3)


def test_end_to_end_runs_and_audits():
    s = _new_session()
    _seed(s)
    results = s.deliberate(max_rounds=5)
    assert len(results) >= 1
    debrief = s.debrief()
    assert s.state == State.DONE
    assert len(debrief["audit"]) > 0
    # Every audit event carries a source layer label.
    assert all("actor_type" in e for e in debrief["audit"])


def test_cannot_submit_read_before_start():
    s = _new_session()
    with pytest.raises((RuntimeError, KeyError)):
        s.submit_read("Birch", "x", 3)


def test_deliberate_requires_two_reads():
    s = _new_session()
    s.start([("u1", "human")])
    s.submit_read("Birch", "only one read", 3)
    with pytest.raises(RuntimeError):
        s.deliberate()


def test_decision_is_terminal_value():
    s = _new_session()
    _seed(s)
    results = s.deliberate(max_rounds=5)
    assert results[-1].decision in ("QUORUM_MET", "STALE_REFRESH", "CONTINUE")


def test_debrief_reveals_anonymization_map():
    s = _new_session()
    _seed(s)
    s.deliberate(max_rounds=5)
    debrief = s.debrief()
    handles = {p["handle"] for p in debrief["participants"]}
    assert {"Birch", "Maple", "Cedar"}.issubset(handles)
