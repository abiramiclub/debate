"""Prediction gate (symmetric to the neutrality gate): a mediator message that
forecasts the outcome is blocked, logged `prediction_blocked`, and dropped."""

import os
import tempfile

from constitution.neutrality import forecasts_outcome
from constitution.protocol import Session
from mediator.base import Mediator


class _StubMediator(Mediator):
    """Emits one outcome-forecasting candidate among neutral ones; steelman
    forecasts or not by flag. predict_agreement aligns to the gated candidate
    list and yields two opinion camps."""

    def __init__(self, forecast_steelman: bool = False):
        self.forecast_steelman = forecast_steelman

    def synthesize_candidates(self, reads, n):
        return [
            "This will clear quorum, probably 4 to 1.",        # forecast -> blocked
            "A chatbot is one option to weigh.",                # neutral
            "A wiki is another option to weigh.",               # neutral
        ]

    def predict_agreement(self, reads, candidates):
        rows = []
        n = len(candidates)
        for i in range(len(reads)):
            rows.append([0.9] + [0.1] * (n - 1) if i < 3 else [0.1] + [0.9] * (n - 1))
        return rows

    def steelman_minority(self, reads, labels):
        return ("My money's on the wiki — it probably wins."
                if self.forecast_steelman
                else "The accuracy/audit concern deserves fair weight.")

    def detect_echo(self, previous_round, current_round):
        return False, "new content"


def _session(forecast_steelman=False):
    path = os.path.join(tempfile.mkdtemp(), "audit.jsonl")
    s = Session("prediction", _StubMediator(forecast_steelman), path)
    s.start([(f"u{i}", "human") for i in range(5)])
    for p in s.participants:
        s.submit_read(p.handle, "a generic read about the help bot", 4)
    return s


def test_forecast_marker_detection():
    assert forecasts_outcome("This will clear quorum, probably 4 to 1.")
    assert forecasts_outcome("my money's on the wiki")
    assert forecasts_outcome("it'll be 3-2")
    assert not forecasts_outcome("A wiki is one option to weigh.")
    assert not forecasts_outcome("The accuracy concern deserves fair weight.")


def test_forecasting_candidate_blocked_and_logged():
    s = _session()
    results = s.deliberate(max_rounds=1)
    candidates = results[0].candidates
    assert "This will clear quorum, probably 4 to 1." not in candidates
    assert all(not forecasts_outcome(c) for c in candidates)
    assert "prediction_blocked" in [e["action"] for e in s.audit.read_all()]


def test_forecasting_steelman_dropped():
    s = _session(forecast_steelman=True)
    results = s.deliberate(max_rounds=1)
    assert results[0].steelman is None
    actions = [e["action"] for e in s.audit.read_all()]
    assert "prediction_blocked" in actions
    assert "steelman_minority" not in actions
