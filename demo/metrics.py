"""Single-session metrics for the demo debrief.

Reuses the EXACT harness metric functions (least-satisfied-group support,
minority survival, average) so the debrief reports the same three numbers Phase A
reports — measured here on the final positions of this one session. Adds the
scenario-only information-uptake number computed from the fixture's stipulated
pre/post positions.
"""

from dataclasses import dataclass

from harness.metrics import session_metrics


@dataclass
class _FinalState:
    """Duck-typed stand-in for a harness Session (the metric functions only need
    these three attributes)."""
    endorsement: list[list[float]]

    @property
    def n_participants(self) -> int:
        return len(self.endorsement)

    @property
    def n_candidates(self) -> int:
        return len(self.endorsement[0]) if self.endorsement else 0


def final_metrics(fixture: dict, chosen_index: int) -> dict:
    """The three harness metrics for `chosen_index`, on the final round's
    endorsement matrix."""
    final = fixture["rounds"][-1]["agreement"]
    return session_metrics(_FinalState(final), chosen_index)


def uptake(fixture: dict) -> dict:
    """Information uptake from the fixture's pre/post positions (scenario only)."""
    pos = fixture["positions"]["by_participant"]
    deltas = [p["post"]["stance"] - p["pre"]["stance"] for p in pos]
    conf_deltas = [p["post"]["confidence"] - p["pre"]["confidence"] for p in pos]
    minority = [d for p, d in zip(pos, deltas) if p["camp"] == "con"]
    majority = [d for p, d in zip(pos, deltas) if p["camp"] == "pro"]
    return {
        "mean_stance_shift": sum(deltas) / len(deltas),
        "minority_mean_shift": sum(minority) / len(minority) if minority else 0.0,
        "majority_mean_shift": sum(majority) / len(majority) if majority else 0.0,
        "moved_count": sum(1 for d in deltas if d > 0.05),
        "n": len(pos),
        "mean_confidence_delta": sum(conf_deltas) / len(conf_deltas),
    }
