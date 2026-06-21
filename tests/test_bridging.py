"""Tests for the fairness guarantee: bridging beats majority, and small-N
clustering falls back safely."""

from constitution.bridging import cluster_participants, rank_candidates


def test_bridging_prefers_cross_group_agreement_over_majority():
    # 5 participants. Candidate 0 is loved by a 3-person majority but hated by
    # the 2-person minority. Candidate 1 is liked moderately by EVERYONE.
    # Bridging should pick candidate 1 (cross-group), not the majority's pick.
    agreement = [
        [1.0, 0.7],  # majority
        [1.0, 0.7],  # majority
        [1.0, 0.7],  # majority
        [0.0, 0.7],  # minority
        [0.0, 0.7],  # minority
    ]
    labels = [0, 0, 0, 1, 1]
    scored = rank_candidates(agreement, labels)
    assert scored[0].index == 1, "bridging winner should be the cross-group candidate"


def test_pure_majority_candidate_loses_to_bridge():
    agreement = [
        [1.0, 0.6],
        [1.0, 0.6],
        [1.0, 0.6],
        [0.0, 0.6],
    ]
    labels = [0, 0, 0, 1]
    scored = rank_candidates(agreement, labels)
    # Candidate 0: P(g0)= (2+3)/(1+3)=1.25 ; P(g1)=(2+0)/(1+1)=1.0 -> 1.25
    # Candidate 1: P(g0)= (2+3)/(1+3)=1.25 ; P(g1)=(2+1)/(1+1)=1.5 -> 1.875
    assert scored[0].index == 1


def test_small_n_each_their_own_group():
    agreement = [[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]]
    labels = cluster_participants(agreement, k_max=4, min_n_for_clustering=5)
    assert labels == [0, 1, 2]


def test_clustering_above_threshold_groups_similar_participants():
    # Two clear camps of agreement vectors.
    agreement = [
        [0.9, 0.1], [0.9, 0.1], [0.85, 0.15],
        [0.1, 0.9], [0.1, 0.9], [0.15, 0.85],
    ]
    labels = cluster_participants(agreement, k_max=4, min_n_for_clustering=5)
    # First three share a label, last three share a (different) label.
    assert labels[0] == labels[1] == labels[2]
    assert labels[3] == labels[4] == labels[5]
    assert labels[0] != labels[3]
