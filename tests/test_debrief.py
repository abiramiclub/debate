"""B3 + B4 tests: uptake is computed and non-trivial; the Block Kit debrief
validates; evidence source is present."""

import os
import tempfile

import pytest

from constitution.evidence import RTSAdapterStub
from demo.build_debrief import build_blocks, validate_blockkit
from demo.metrics import final_metrics, uptake
from demo.run_ab import load_fixture, run_constitution


def _run():
    fx = load_fixture()
    path = os.path.join(tempfile.mkdtemp(), "audit.jsonl")
    session, results, debrief = run_constitution(fx, path)
    return fx, session, debrief


def test_uptake_is_nontrivial_and_evidence_moves_the_dismissive_camp():
    fx, _, _ = _run()
    up = uptake(fx)
    assert up["mean_stance_shift"] > 0.05
    assert up["moved_count"] >= 1
    # The evidence (the hallucination postmortem) addresses the minority's
    # concern, so it moves the MAJORITY camp (which had been dismissive) most.
    assert up["majority_mean_shift"] > up["minority_mean_shift"]


def test_bridged_beats_naive_on_minority_support_this_session():
    fx, _, debrief = _run()
    final_candidates = fx["rounds"][-1]["candidates"]
    bridged = final_metrics(fx, final_candidates.index(debrief["winner"]))
    naive = final_metrics(fx, 1)  # majority camp's position on the final slate
    assert bridged["min_group_support"] > naive["min_group_support"]
    assert bridged["minority_survival"] > naive["minority_survival"]


def test_debrief_blockkit_validates():
    fx, session, debrief = _run()
    payload = build_blocks(fx, session, debrief)
    assert validate_blockkit(payload)
    assert payload["blocks"][0]["type"] == "header"


def test_validator_rejects_bad_payload():
    with pytest.raises(AssertionError):
        validate_blockkit({"blocks": [{"type": "nonsense"}]})


def test_rts_adapter_is_stubbed_not_silent():
    # The required-tech route must fail loudly, not silently return nothing.
    with pytest.raises(NotImplementedError):
        RTSAdapterStub().fetch({})
