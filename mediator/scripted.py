"""A fixture-driven mediator for the controlled demo.

Unlike `FakeMediator` (token heuristics), `ScriptedMediator` returns exactly the
candidates and agreement matrix the fixture specifies for each round. This lets
the demo engineer a precise deliberation arc that exercises every constitution
rule (cross-inhibition, minority steelman, echo/deadlock, evidence injection,
bridging quorum) — while the constitution still makes every decision itself.

The mediator does language work; it never decides transitions. Here the "language
work" is simply pre-written, so the run is deterministic and inspectable.
"""

import re

from .base import Mediator, Read


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zA-Z']+", text.lower()) if len(w) > 2}


class ScriptedMediator(Mediator):
    def __init__(self, rounds: list[dict], steelman_text: str):
        # rounds[i] = {"candidates": [str], "agreement": [[float]]}
        self._rounds = rounds
        self._steelman = steelman_text
        self._ptr = 0
        self._cur: dict = rounds[0] if rounds else {"candidates": [], "agreement": []}

    def synthesize_candidates(self, reads: list[Read], n: int) -> list[str]:
        idx = min(self._ptr, len(self._rounds) - 1)
        self._cur = self._rounds[idx]
        self._ptr += 1
        return list(self._cur["candidates"])

    def predict_agreement(self, reads: list[Read], candidates: list[str]) -> list[list[float]]:
        return [list(row) for row in self._cur["agreement"]]

    def steelman_minority(self, reads: list[Read], group_labels: list[int]) -> str:
        return self._steelman

    def detect_echo(self, previous_round: list[str], current_round: list[str]) -> tuple[bool, str]:
        prev = set().union(*[_tokens(m) for m in previous_round]) if previous_round else set()
        curr = set().union(*[_tokens(m) for m in current_round]) if current_round else set()
        if not curr:
            return False, "No current-round content to assess."
        novel = curr - prev
        ratio = len(novel) / len(curr)
        if ratio < 0.2:
            return True, (f"Only {ratio:.0%} new content ({len(novel)}/{len(curr)} tokens); "
                          f"the thread is repeating without new information.")
        return False, f"{ratio:.0%} new content; information is still entering."
