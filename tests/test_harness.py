"""Sanity tests for the harness — guard the most error-prone bits (rank
orientation and selection-rule contracts) without needing the real dataset."""

from harness.loader import Session, _endorsement_from_ranks
from harness.baselines import (
    select_bridging, select_majority, select_last_speaker, select_random,
)
from harness.metrics import session_metrics


def test_rank_zero_is_top_endorsement():
    # rank 0 = most preferred -> endorsement 1.0; worst -> 0.0
    assert _endorsement_from_ranks([0, 1, 2, 3]) == [1.0, 2 / 3, 1 / 3, 0.0]


def _toy_session():
    # 4 participants, 3 candidates.
    # cand 0: loved by a 3-person majority, hated by 1 -> majority pick
    # cand 1: liked by everyone moderately -> bridge
    # cand 2: weak
    E = [
        [1.0, 0.6, 0.2],
        [1.0, 0.6, 0.2],
        [1.0, 0.6, 0.2],
        [0.0, 0.6, 0.2],
    ]
    return Session("toy", ["a", "b", "c"], E, ["p1", "p2", "p3", "p4"], [0, 1, 2], ["", "", ""])


def test_majority_picks_steamroller_bridging_protects_minority():
    s = _toy_session()
    assert select_majority(s) == 0      # highest mean (3 love it)
    assert select_bridging(s) == 1      # broad cross-participant support
    m_maj = session_metrics(s, select_majority(s))
    m_bri = session_metrics(s, select_bridging(s))
    # Bridging's pick leaves the least-satisfied group better off.
    assert m_bri["min_group_support"] > m_maj["min_group_support"]


def test_selection_rules_return_valid_indices():
    s = _toy_session()
    for rule in (select_bridging, select_majority, select_last_speaker, select_random):
        idx = rule(s)
        assert 0 <= idx < s.n_candidates
