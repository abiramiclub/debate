"""B2 spine test: the 5p two-camp fixture exercises every rule, end to end, and
the two pipelines diverge."""

import os
import tempfile

from demo.run_ab import load_fixture, run_constitution, run_naive


def _run():
    fx = load_fixture()
    path = os.path.join(tempfile.mkdtemp(), "audit.jsonl")
    session, results, debrief = run_constitution(fx, path)
    return fx, session, results, debrief


def test_cross_inhibition_fires_round_zero():
    _, _, results, _ = _run()
    assert results[0].cross_inhibition_fired


def test_steelman_fires_on_minority_cluster():
    _, _, results, _ = _run()
    # The two-camp fixture always has a minority cluster -> steelman present.
    assert any(r.steelman for r in results)
    assert all(r.minority_present for r in results)


def test_deadlock_triggers_evidence_injection_with_source():
    fx, _, results, debrief = _run()
    injected = [r for r in results if r.decision == "EVIDENCE_INJECTED"]
    assert len(injected) == 1
    assert injected[0].evidence.source == fx["evidence"]["source"]
    # Source is written to the audit.
    assert any(e.get("source") == fx["evidence"]["source"] for e in debrief["audit"])


def test_reaches_bridging_quorum_on_a_compromise():
    fx, _, results, debrief = _run()
    assert debrief["reached_quorum"]
    winner = debrief["winner"]
    # The winner differs from either camp's opening line (it's a bridge).
    pro_open = fx["rounds"][1]["candidates"][0]
    con_open = fx["rounds"][1]["candidates"][1]
    assert winner not in (pro_open, con_open)


def test_pipelines_diverge_on_identical_input():
    fx, _, _, debrief = _run()
    assert run_naive(fx) != debrief["winner"]


def test_no_vicky_in_user_facing_audit():
    _, _, _, debrief = _run()
    assert not any("Vicky" in str(e.get("actor_handle", "")) for e in debrief["audit"])
