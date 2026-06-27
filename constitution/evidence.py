"""Evidence injection — deterministic gate, sourced content (constitution §5).

The constitution decides WHEN to inject (deadlock/echo consequence) and logs the
source; the CONTENT comes from a swappable `EvidenceSource` so the fact is never
hardcoded into the protocol.

B1 scope: the interface + an offline `FixtureEvidenceSource`, enough to wire the
deadlock consequence and run the demo.
B3 scope (tracked, not built here): an `RTSAdapterStub` for the real Real-Time
Search call, and the pre/post information-uptake metric.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Evidence:
    text: str
    source: str                 # citation / URL — written to the audit
    handle: str = "Linden"      # neutral handle the fact is injected under
    label: str = "fixture"      # provenance of the evidence source itself


class EvidenceSource(ABC):
    """Supplies one vetted, sourced fact when the constitution asks for it."""

    @abstractmethod
    def fetch(self, context: dict) -> Optional[Evidence]:
        ...


class FixtureEvidenceSource(EvidenceSource):
    """Offline source: returns a pre-vetted fact from the demo fixture. Used so
    the demo runs reproducibly without network or a Slack runtime."""

    def __init__(self, evidence: Evidence):
        self._evidence = evidence

    def fetch(self, context: dict) -> Optional[Evidence]:
        return self._evidence


class RTSAdapterStub(EvidenceSource):
    """Adapter for the real Real-Time Search API (one of the two required-tech
    routes). NOT wired yet.

    Finding (tracked in docs/REQUIRED_TECH_TODO.md): the Real-Time Search API is
    a Slack-platform capability that expects the Slack app runtime / token
    context, so it cannot be exercised from this offline harness. We keep this
    adapter as the seam: in the Slack phase, implement `fetch()` to issue the RTS
    query, vet the top result, and return it as `Evidence(text, source=<url>)`.
    Until then it fails loudly rather than silently returning nothing, so the
    required-tech wiring cannot quietly disappear.
    """

    def __init__(self, query_builder=None):
        self._query_builder = query_builder

    def fetch(self, context: dict) -> Optional[Evidence]:
        raise NotImplementedError(
            "RTS real wiring is a tracked must-do for the Slack phase "
            "(see docs/REQUIRED_TECH_TODO.md). Use FixtureEvidenceSource offline."
        )
