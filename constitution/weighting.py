"""Anti-sycophancy weighting (constitution section 3).

Inverts the failure mode of participant-agents (drift toward the last speaker /
premature consensus):

  * recency is weighted DOWN, never up;
  * dissent is preserved more strongly early, convergence allowed more late
    (phase-tuned, drone boids-style).

All deterministic.
"""

from .bridging import CandidateScore
from .config import Config


def phase_index(round_idx: int, near_quorum: bool) -> int:
    """Map a round to a phase: 0=early, 1=mid, 2=late.

    Round 0 (the first reveal round) is always early. Once the leader is within
    reach of quorum we treat it as late so convergence is allowed to finish.
    """
    if round_idx == 0:
        return 0
    if near_quorum:
        return 2
    return 1


def recency_weights(n_contributions: int, w_recency: float) -> list[float]:
    """Weights for a sequence of contributions, oldest first. The most recent
    input is damped by `w_recency` so it does NOT get extra influence."""
    if n_contributions == 0:
        return []
    weights = [1.0] * n_contributions
    weights[-1] = w_recency
    return weights


def raw_support(scored: list[CandidateScore]) -> float:
    """Cross-group support of the bridging winner, in [0, 1]: the mean fraction
    of agreement across opinion groups. High only when the winner is broadly
    agreed across the room, not within one camp.

    (Mean is used for v0; switching to `min(...)` here makes the quorum gate
    strictly bridging — even the least-agreeing group must mostly agree.)
    """
    if not scored:
        return 0.0
    winner = scored[0]  # already sorted best-first by bridging score
    fractions = winner.per_group_fraction
    return sum(fractions) / len(fractions) if fractions else 0.0


def weighted_support(scored: list[CandidateScore], phase: int, cfg: Config) -> float:
    """Phase-adjusted support of the leader. Mid phase is neutral; early phase
    damps support (preserve dissent), late phase lets it count fully (allow the
    group to commit). This is what the quorum / cross-inhibition checks read.
    """
    conv, _dissent = cfg.phase_weights[phase]
    neutral_conv = cfg.phase_weights[1][0]  # mid-phase convergence weight
    scale = conv / neutral_conv
    return min(1.0, raw_support(scored) * scale)
