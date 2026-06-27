"""Deterministic position-neutrality gate (constitution §0 invariant 4, §5, §7).

The mediator may phrase and surface; it may never advocate a conclusion on the
topic. This is the single, shared, deterministic check applied at every
constitution↔mediator boundary: candidate statements, the minority steelman, and
injected evidence all pass through it before they can be used or posted.

Conservative on purpose — a false positive merely rejects one phrasing and we
regenerate; a false negative is caught by the audit trail. It keys on overt
advocacy of *which option to choose*, not on a view being stated for fair
consideration.
"""

_ADVOCACY_MARKERS = [
    "you should", "we should", "i think we should", "must adopt", "vote for",
    "vote to", "the answer is", "clearly the best", "everyone agrees",
    "obviously", "the right choice is", "the best option is", "i recommend",
    "we recommend", "let's go with", "we ought to", "the only sensible",
]


def advocates_position(text: str) -> bool:
    """True if `text` overtly advocates a topic conclusion (and so must be
    rejected at the constitution↔mediator boundary)."""
    t = (text or "").lower()
    return any(marker in t for marker in _ADVOCACY_MARKERS)
