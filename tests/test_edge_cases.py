"""Offline hardening: edge cases must not crash and must yield a sensible
winner (a string) or None. Plus a determinism check on the demo fixture."""

import os
import tempfile

from constitution.protocol import Session
from mediator.base import Mediator


class _CfgMediator(Mediator):
    """Fully controllable mediator: fixed neutral candidates + agreement matrix,
    configurable echo and steelman."""

    def __init__(self, candidates, agreement, echo=False,
                 steelman="A minority view to weigh fairly."):
        self._candidates = candidates
        self._agreement = agreement
        self._echo = echo
        self._steelman = steelman

    def synthesize_candidates(self, reads, n):
        return list(self._candidates)

    def predict_agreement(self, reads, candidates):
        return [list(r) for r in self._agreement]

    def steelman_minority(self, reads, labels):
        return self._steelman

    def detect_echo(self, previous_round, current_round):
        return self._echo, "cfg"


def _run(mediator, n_participants, texts=None, evidence_source=None, max_rounds=4):
    path = os.path.join(tempfile.mkdtemp(), "audit.jsonl")
    s = Session("edge", mediator, path, evidence_source=evidence_source)
    s.start([(f"u{i}", "human") for i in range(n_participants)])
    n_reads = len(texts) if texts is not None else n_participants
    for i in range(n_reads):
        s.submit_read(s.participants[i].handle, (texts[i] if texts else f"read {i}"), 4)
    results = s.deliberate(max_rounds=max_rounds)
    return s, results


def _assert_sane(s, results):
    assert results, "should produce at least one round"
    assert s.winner_text is None or isinstance(s.winner_text, str)


# Two neutral candidates used across several cases.
AB = ["Option A is on the table.", "Option B is on the table."]


def test_small_n_each_own_group():
    med = _CfgMediator(AB, [[0.9, 0.1], [0.8, 0.2], [0.2, 0.9]])
    s, results = _run(med, 3)
    _assert_sane(s, results)
    assert results[0].group_labels == [0, 1, 2]  # below clustering floor


def test_unanimous_reads():
    med = _CfgMediator(AB, [[0.95, 0.1]] * 5)
    s, results = _run(med, 5)
    _assert_sane(s, results)


def test_all_disagree_polarized():
    med = _CfgMediator(AB, [[0.9, 0.1]] * 3 + [[0.1, 0.9]] * 2)
    s, results = _run(med, 5)
    _assert_sane(s, results)


def test_tied_candidates():
    med = _CfgMediator(AB, [[0.7, 0.7]] * 5)
    s, results = _run(med, 5)
    _assert_sane(s, results)
    if s.winner_text is not None:
        assert s.winner_text in AB


def test_single_candidate():
    med = _CfgMediator(["One option on the table."], [[0.9]] * 5)
    s, results = _run(med, 5)
    _assert_sane(s, results)
    assert s.winner_text in ("One option on the table.", None)


def test_empty_and_partial_reads():
    # 5 participants started, only 2 (empty-text) reads submitted.
    med = _CfgMediator(AB, [[0.9, 0.1], [0.1, 0.9]])
    s, results = _run(med, 5, texts=["", ""])
    _assert_sane(s, results)


def test_quorum_never_reached():
    # Polarized + perpetual echo, no evidence -> deadlock -> no quorum.
    med = _CfgMediator(AB, [[0.9, 0.1]] * 3 + [[0.1, 0.9]] * 2, echo=True)
    s, results = _run(med, 5, max_rounds=6)
    assert s.winner_text is None
    assert results[-1].decision in ("STALE_REFRESH", "CONTINUE")


def test_determinism_same_fixture_same_outcome():
    from demo.run_ab import load_fixture, run_constitution
    fx = load_fixture()
    p1 = os.path.join(tempfile.mkdtemp(), "a.jsonl")
    p2 = os.path.join(tempfile.mkdtemp(), "b.jsonl")
    _, _, d1 = run_constitution(fx, p1)
    _, _, d2 = run_constitution(fx, p2)
    assert d1["winner"] == d2["winner"]
    assert [e["action"] for e in d1["audit"]] == [e["action"] for e in d2["audit"]]
