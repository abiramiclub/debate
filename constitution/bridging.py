"""Bridging-based ranking — the fairness guarantee (constitution section 2).

The winning common-ground statement is selected by *group-informed* consensus:
a statement scores high only if it is liked ACROSS opinion groups, not within the
single largest one. This is the deployed anti-majority-tyranny method from
Pol.is / Remesh / Community Notes.

The agreement *estimates* come from the probabilistic mediator. The *selection*
(everything in this file) is deterministic and lives in the constitution.
"""

import math
from dataclasses import dataclass

# agreement_matrix[participant_index][candidate_index] -> float in [0, 1]
AgreementMatrix = list[list[float]]

AGREE_THRESHOLD = 0.5  # an estimated agreement >= this counts as "agrees"


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _silhouette(vectors: list[list[float]], labels: list[int]) -> float:
    """Mean silhouette score for a labeling. Higher is a cleaner clustering."""
    n = len(vectors)
    clusters: dict[int, list[int]] = {}
    for i, lab in enumerate(labels):
        clusters.setdefault(lab, []).append(i)
    if len(clusters) < 2:
        return -1.0
    total = 0.0
    for i in range(n):
        own = clusters[labels[i]]
        if len(own) == 1:
            # Singleton: silhouette is conventionally 0, so over-splitting into
            # many singletons is not rewarded.
            continue
        a = sum(_distance(vectors[i], vectors[j]) for j in own if j != i) / (len(own) - 1)
        b = math.inf
        for lab, members in clusters.items():
            if lab == labels[i]:
                continue
            mean_d = sum(_distance(vectors[i], vectors[j]) for j in members) / len(members)
            b = min(b, mean_d)
        denom = max(a, b)
        total += 0.0 if denom == 0 else (b - a) / denom
    return total / n


def cluster_participants(
    agreement_matrix: AgreementMatrix,
    k_max: int = 4,
    min_n_for_clustering: int = 5,
) -> list[int]:
    """Partition participants into opinion groups by clustering their agreement
    vectors. Returns a group label per participant.

    Small-N fallback: below `min_n_for_clustering`, clustering is meaningless, so
    each participant becomes their own group (maximally preserves dissent). This
    keeps the N=3 case sane instead of inventing fake clusters.
    """
    n = len(agreement_matrix)
    if n == 0:
        return []
    if n < min_n_for_clustering:
        return list(range(n))

    # Agglomerative (single-linkage) merge order, then pick k by best silhouette.
    best_labels = [0] * n
    best_score = -2.0
    for k in range(2, min(k_max, n - 1) + 1):
        labels = _agglomerative(agreement_matrix, k)
        score = _silhouette(agreement_matrix, labels)
        if score > best_score:
            best_score, best_labels = score, labels
    return best_labels


def _agglomerative(vectors: list[list[float]], k: int) -> list[int]:
    clusters: list[list[int]] = [[i] for i in range(len(vectors))]
    while len(clusters) > k:
        best = None
        best_pair = (0, 1)
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = min(
                    _distance(vectors[a], vectors[b])
                    for a in clusters[i]
                    for b in clusters[j]
                )
                if best is None or d < best:
                    best, best_pair = d, (i, j)
        i, j = best_pair
        clusters[i].extend(clusters[j])
        del clusters[j]
    labels = [0] * len(vectors)
    for label, members in enumerate(clusters):
        for m in members:
            labels[m] = label
    return labels


def _smoothed_agreement(n_agree: int, n_voted: int) -> float:
    """P(g, c): smoothed agreement of a group with a candidate."""
    return (2 + n_agree) / (1 + n_voted)


@dataclass
class CandidateScore:
    index: int
    bridging_score: float           # PRODUCT of smoothed group agreement (for ranking)
    per_group_agreement: list[float]  # smoothed P(g, c) per group
    per_group_fraction: list[float]   # raw agree-fraction per group (for the support gate)


def rank_candidates(
    agreement_matrix: AgreementMatrix,
    group_labels: list[int],
) -> list[CandidateScore]:
    """Score every candidate by bridging consensus and return them sorted best
    first. bridging_score(c) = PRODUCT over groups of P(g, c).

    The product is what ranks candidates (it is high only when liked across ALL
    groups). The raw per-group agree fractions are kept separately so the quorum
    gate can read an interpretable cross-group support level in [0, 1].
    """
    if not agreement_matrix:
        return []
    n_candidates = len(agreement_matrix[0])
    groups: dict[int, list[int]] = {}
    for participant, lab in enumerate(group_labels):
        groups.setdefault(lab, []).append(participant)

    scored: list[CandidateScore] = []
    for c in range(n_candidates):
        per_group: list[float] = []
        per_fraction: list[float] = []
        product = 1.0
        for members in groups.values():
            n_agree = sum(1 for p in members if agreement_matrix[p][c] >= AGREE_THRESHOLD)
            p_gc = _smoothed_agreement(n_agree, len(members))
            per_group.append(p_gc)
            per_fraction.append(n_agree / len(members) if members else 0.0)
            product *= p_gc
        scored.append(CandidateScore(
            index=c, bridging_score=product,
            per_group_agreement=per_group, per_group_fraction=per_fraction,
        ))

    scored.sort(key=lambda s: s.bridging_score, reverse=True)
    return scored
