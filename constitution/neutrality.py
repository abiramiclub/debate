"""Deterministic gates at the constitution↔mediator boundary
(constitution §0 invariant 4, §5, §7).

Two symmetric gates. The mediator may phrase and surface; it may never (a) advocate
a conclusion on the topic, nor (b) forecast the outcome (calling the result invites
bandwagon / herding). Both are deterministic checks applied to candidate statements,
the minority steelman, and any mediator message before it can be used or posted.

Conservative on purpose — a false positive merely rejects one phrasing and we
regenerate; a false negative is caught by the audit trail.
"""

import re

_ADVOCACY_MARKERS = [
    "you should", "we should", "i think we should", "must adopt", "vote for",
    "vote to", "the answer is", "clearly the best", "everyone agrees",
    "obviously", "the right choice is", "the best option is", "i recommend",
    "we recommend", "let's go with", "we ought to", "the only sensible",
]

_FORECAST_MARKERS = [
    "will pass", "this'll clear", "this will clear", "clears quorum",
    "clear quorum", "will clear", "we'll hit quorum", "hit quorum",
    "probably wins", "probably win", "will win", "going to pass", "this passes",
    "i predict", "my money is on", "my money's on", "likely to pass", "no scoreboard",
]
# Vote-count predictions like "4 to 1", "4-1", "3–2".
_VOTE_COUNT = re.compile(r"\b\d+\s*(?:to|[-–—])\s*\d+\b")


def advocates_position(text: str) -> bool:
    """True if `text` overtly advocates a topic conclusion (must be rejected)."""
    t = (text or "").lower()
    return any(marker in t for marker in _ADVOCACY_MARKERS)


def forecasts_outcome(text: str) -> bool:
    """True if `text` forecasts/calls the outcome (a red line — predicting the
    result invites bandwagon voting). Used by the prediction gate."""
    t = (text or "").lower()
    if any(marker in t for marker in _FORECAST_MARKERS):
        return True
    return bool(_VOTE_COUNT.search(t))
