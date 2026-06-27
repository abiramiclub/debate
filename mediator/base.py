"""The probabilistic layer — the mediator, defined as an interface.

WHAT THE MEDIATOR IS: the *only* place language/LLM work happens. It reads and
summarizes opinions, proposes common-ground statements, estimates who would
agree, steelmans a minority view, and detects echo.

WHAT THE MEDIATOR IS NOT: it is never trusted to be fair. It does not decide
anything. The deterministic constitution INVOKES these methods, then re-selects
or bounds every output with its own rules (bridging ranking, quorum, neutrality
check). "The mediator proposes; the constitution selects."

This split is the whole thesis. Because the mediator is just this interface, you
can run the entire system with a no-LLM `FakeMediator` for testing, then swap in
a real Claude-backed implementation later with zero changes to the constitution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Read:
    """A participant's private position, collected before any reveal."""
    handle: str
    text: str
    confidence: int  # 1..5


class Mediator(ABC):
    @abstractmethod
    def synthesize_candidates(self, reads: list[Read], n: int) -> list[str]:
        """Generate up to `n` candidate common-ground statements from the reads.
        Habermas-style group statements. Quality is the mediator's job; choosing
        the winner is NOT (that is the constitution's bridging ranker)."""

    @abstractmethod
    def predict_agreement(self, reads: list[Read], candidates: list[str]) -> list[list[float]]:
        """Estimate each participant's agreement with each candidate.

        Returns a matrix[participant][candidate] of values in [0, 1]. This feeds
        the deterministic bridging ranker — the mediator never sees the ranking."""

    @abstractmethod
    def steelman_minority(self, reads: list[Read], group_labels: list[int]) -> str:
        """Produce the strongest version of the least-supported credible view.
        Used as the cross-inhibition payload (counter-pressure against fast
        consensus)."""

    @abstractmethod
    def detect_echo(self, previous_round: list[str], current_round: list[str]) -> tuple[bool, str]:
        """Classify whether the discussion is intensifying without new
        information entering (the arXiv 2506.11825 failure mode). Returns
        (is_echo, reason). The constitution decides what to do with the flag."""
