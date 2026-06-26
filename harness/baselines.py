"""Selection rules. Each takes a Session and returns the chosen candidate index.

  * bridging      — the constitution's bridging ranker (cross-group consensus)
  * majority      — highest mean endorsement (utilitarian / what a vote does)
  * last_speaker  — recency proxy (see note); models "defer to the latest"
  * random        — seeded control

The endorsement matrix here is REAL human endorsement (rankings), so no language
model / predictor is involved: Phase A isolates the *selection* rule from any
prediction error. In the live system the same rule runs on predicted endorsement
behind the Mediator interface; here we feed it ground truth.
"""

import random as _random

from constitution.bridging import cluster_participants, rank_candidates
from constitution.config import DEFAULT

from .loader import Session


def select_bridging(session: Session) -> int:
    labels = cluster_participants(session.endorsement, DEFAULT.k_max,
                                  DEFAULT.min_n_for_clustering)
    scored = rank_candidates(session.endorsement, labels)
    return scored[0].index


def select_majority(session: Session) -> int:
    n_c = session.n_candidates
    means = [sum(row[c] for row in session.endorsement) / session.n_participants
             for c in range(n_c)]
    return max(range(n_c), key=lambda c: means[c])


def select_last_speaker(session: Session) -> int:
    """Recency baseline. NOTE: candidates in this dataset are generated
    simultaneously (identical timestamps), so there is no real speaker order.
    We use the last candidate in display order as a positional proxy — a
    deliberately weak control, labeled as such in RESULTS."""
    return session.display_order[-1]


def select_random(session: Session, seed: int = 0) -> int:
    rng = _random.Random(f"{session.session_id}:{seed}")
    return rng.randrange(session.n_candidates)


RULES = {
    "bridging": select_bridging,
    "majority": select_majority,
    "last_speaker": select_last_speaker,
    "random": select_random,
}
