"""Per-session metrics for a chosen candidate.

The headline question: does bridging selection buy broader cross-group support
than the baselines, and at what cost to raw average satisfaction?

  * mean_endorsement   — average endorsement of the chosen candidate (utilitarian)
  * min_group_support  — the LEAST-satisfied opinion group's mean endorsement of
                         the chosen candidate (the anti-majority-tyranny metric)
  * minority_survival  — the smaller of two opinion camps' mean endorsement of the
                         chosen candidate (does the dissenting camp survive?)
  * breadth_ratio      — chosen candidate's bridging score / best possible in the
                         session, in (0, 1]; 1.0 means "the broadest available"
"""

from constitution.bridging import cluster_participants, rank_candidates
from constitution.config import DEFAULT

from .loader import Session


def _agglom_two_camps(endorsement: list[list[float]]) -> list[int]:
    """Split participants into 2 camps for the minority-survival metric. This is
    analysis only (not the constitution's grouping), so it ignores the min-N
    floor and always produces two camps when possible."""
    from constitution.bridging import _agglomerative
    n = len(endorsement)
    if n < 2:
        return [0] * n
    return _agglomerative(endorsement, 2)


def _group_means(endorsement, labels, c):
    groups: dict[int, list[float]] = {}
    for p, lab in enumerate(labels):
        groups.setdefault(lab, []).append(endorsement[p][c])
    return {lab: sum(v) / len(v) for lab, v in groups.items()}


def session_metrics(session: Session, chosen: int) -> dict:
    E = session.endorsement
    P = session.n_participants

    mean_endorsement = sum(row[chosen] for row in E) / P

    # Constitution grouping (same as the bridging rule uses).
    const_labels = cluster_participants(E, DEFAULT.k_max, DEFAULT.min_n_for_clustering)
    gm = _group_means(E, const_labels, chosen)
    min_group_support = min(gm.values())

    # Two-camp split for minority survival.
    camps = _agglom_two_camps(E)
    camp_sizes: dict[int, int] = {}
    for lab in camps:
        camp_sizes[lab] = camp_sizes.get(lab, 0) + 1
    minority_lab = min(camp_sizes, key=lambda k: camp_sizes[k])
    cm = _group_means(E, camps, chosen)
    minority_survival = cm[minority_lab]

    # Breadth ratio vs the best-available bridging score this session.
    scored = rank_candidates(E, const_labels)
    by_index = {s.index: s.bridging_score for s in scored}
    best = max(by_index.values())
    breadth_ratio = by_index[chosen] / best if best > 0 else 0.0

    return {
        "mean_endorsement": mean_endorsement,
        "min_group_support": min_group_support,
        "minority_survival": minority_survival,
        "breadth_ratio": breadth_ratio,
    }


METRIC_KEYS = ["mean_endorsement", "min_group_support", "minority_survival", "breadth_ratio"]
