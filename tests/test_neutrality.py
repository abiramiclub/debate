"""Position-neutrality gate at the constitution↔mediator boundary (Bucket B).

An advocacy-laden candidate / steelman is rejected and logged; neutral output
passes through unchanged.
"""

import os
import tempfile

from constitution.neutrality import advocates_position
from constitution.protocol import Session
from mediator.base import Mediator


class _StubMediator(Mediator):
    """Emits one advocacy candidate among neutral ones; steelman is advocacy or
    neutral depending on the flag. predict_agreement aligns to the (gated)
    candidate list and yields two opinion camps."""

    def __init__(self, advocacy_steelman: bool = False):
        self.advocacy_steelman = advocacy_steelman

    def synthesize_candidates(self, reads, n):
        return [
            "You should adopt the four-day week.",          # advocacy -> rejected
            "A four-day week is one option to weigh.",        # neutral
            "Keeping five days is another option to weigh.",  # neutral
        ]

    def predict_agreement(self, reads, candidates):
        rows = []
        n = len(candidates)
        for i in range(len(reads)):
            rows.append([0.9] + [0.1] * (n - 1) if i < 3 else [0.1] + [0.9] * (n - 1))
        return rows

    def steelman_minority(self, reads, labels):
        return ("We should side with the minority here."
                if self.advocacy_steelman
                else "The minority's coverage concern deserves fair weight.")

    def detect_echo(self, previous_round, current_round):
        return False, "new content"


def _session(advocacy_steelman=False):
    path = os.path.join(tempfile.mkdtemp(), "audit.jsonl")
    s = Session("neutrality", _StubMediator(advocacy_steelman), path)
    s.start([(f"u{i}", "human") for i in range(5)])
    for p in s.participants:
        s.submit_read(p.handle, "a generic read about the four-day week", 4)
    return s


def test_advocacy_marker_detection():
    assert advocates_position("You should adopt the four-day week.")
    assert not advocates_position("A four-day week is one option to weigh.")


def test_advocacy_candidate_rejected_and_logged():
    s = _session()
    results = s.deliberate(max_rounds=1)
    candidates = results[0].candidates
    assert "You should adopt the four-day week." not in candidates
    assert all(not advocates_position(c) for c in candidates)
    assert any("one option" in c for c in candidates)  # neutral one survived
    actions = [e["action"] for e in s.audit.read_all()]
    assert "neutrality_rejected" in actions


def test_neutral_steelman_passes():
    s = _session(advocacy_steelman=False)
    results = s.deliberate(max_rounds=1)
    assert results[0].steelman is not None
    actions = [e["action"] for e in s.audit.read_all()]
    assert "steelman_minority" in actions


def test_advocacy_steelman_dropped_after_retries():
    s = _session(advocacy_steelman=True)
    results = s.deliberate(max_rounds=1)
    assert results[0].steelman is None            # dropped, not posted
    actions = [e["action"] for e in s.audit.read_all()]
    assert "neutrality_rejected" in actions
    assert "steelman_minority" not in actions     # never posted
