"""Default parameters for the Wiki (the deliberation constitution).

Every fairness-relevant number lives here so it is tunable and auditable in one
place. These mirror the defaults table in docs/WIKI.md (section 8).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    T_read: float = 120.0          # independent-read collection window (seconds)
    V_ci: float = 0.50             # cross-inhibition trigger (fast-consensus velocity)
    Q: float = 0.66               # quorum threshold (bridging-adjusted weighted support)
    R: int = 2                     # stale rounds before structural refresh
    w_recency: float = 0.5         # recency down-weight
    N_candidates: int = 8          # common-ground statements generated per round
    k_max: int = 4                 # max opinion clusters
    confidence_scale: int = 5      # per-participant confidence (1..scale)

    # Below this participant count, clustering is statistically meaningless, so
    # we fall back to "each participant is their own opinion group". This guards
    # the N=3 demo case (see BUILD_PLAN risk note on small-N clustering).
    min_n_for_clustering: int = 5

    # Phase-tuned convergence / dissent balance (drone boids-style). Each tuple
    # is (convergence_weight, dissent_preservation_weight).
    phase_weights: tuple = (
        (0.3, 0.7),  # early: reveal -> first cross-inhibition
        (0.5, 0.5),  # mid: subsequent rounds
        (0.7, 0.3),  # late: approaching quorum
    )


DEFAULT = Config()
