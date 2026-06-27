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
