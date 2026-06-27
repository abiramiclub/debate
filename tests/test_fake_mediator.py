"""Pin the FakeMediator candidate mix: bridging (two-theme) statements survive
even when there are many single themes (the former N=8 truncation artifact)."""

from mediator.base import Read
from mediator.fake import FakeMediator


def test_bridge_candidates_survive_with_many_themes():
    reads = [
        Read("Birch", "alpha beta gamma delta epsilon zeta eta theta", 4),
        Read("Cedar", "iota kappa lambda mu nu xicon omicron pius", 4),
    ]
    cands = FakeMediator().synthesize_candidates(reads, n=8)
    assert len(cands) <= 8
    assert any(c.startswith("A shared path respects both") for c in cands), \
        "bridging candidates must not be truncated away"


def test_respects_n_limit():
    reads = [Read("Birch", "one two three four five", 4),
             Read("Cedar", "six seven eight nine ten", 4)]
    assert len(FakeMediator().synthesize_candidates(reads, n=3)) <= 3
