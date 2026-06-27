"""Evidence injection — deterministic gate, sourced content (constitution §5).

The constitution decides WHEN to inject (deadlock/echo consequence) and logs the
source; the CONTENT comes from a swappable `EvidenceSource` so the fact is never
hardcoded into the protocol.

B1 scope: the interface + an offline `FixtureEvidenceSource`, enough to wire the
deadlock consequence and run the demo.
B3 scope (tracked, not built here): an `RTSAdapterStub` for the real Real-Time
Search call, and the pre/post information-uptake metric.
"""

import json
import re
import urllib.parse
import urllib.request
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


def _advocates_position(text: str) -> bool:
    """Minimal deterministic position-neutrality gate (constitution §5/§7): reject
    injected text that pushes a conclusion rather than informing. Conservative on
    purpose — a false positive just rejects one candidate fact and we try again."""
    t = text.lower()
    advocacy = [
        "you should", "we should", "must adopt", "vote for", "the answer is",
        "clearly the best", "everyone agrees", "obviously", "the right choice is",
    ]
    return any(p in t for p in advocacy)


class RTSAdapter(EvidenceSource):
    """Real Real-Time Search evidence source (one of the two required-tech routes).

    Calls Slack's `assistant.search.context` Web API method — a standard Web API
    method, so it is callable from the backend with a bot/user token (it does NOT
    require the event runtime). Returns the top vetted result as sourced Evidence.

    NOTE: `assistant.search.context` response field names are mapped defensively
    (`results` / `messages.matches`, `text`/`content`, `permalink`/`url`) and
    must be confirmed against the live API with the sandbox token — docs.slack.dev
    is unreachable from this build environment. The request shape (POST + Bearer
    token + `query`) follows Slack Web API conventions.
    """

    BASE = "https://slack.com/api"

    def __init__(self, token: str, base_url: Optional[str] = None,
                 handle: str = "Linden", limit: int = 5):
        if not token:
            raise ValueError("RTSAdapter requires a Slack token (xoxb/xoxp).")
        self._token = token
        self._base = base_url or self.BASE
        self._handle = handle
        self._limit = limit

    def _build_query(self, context: dict) -> str:
        if context.get("query"):
            return str(context["query"])
        reads = context.get("reads", [])
        terms = " ".join(getattr(r, "text", "") for r in reads)[:256]
        return terms or "background evidence"

    def _call(self, query: str) -> list[dict]:
        data = urllib.parse.urlencode({"query": query, "limit": self._limit}).encode()
        req = urllib.request.Request(
            f"{self._base}/assistant.search.context", data=data,
            headers={"Authorization": f"Bearer {self._token}",
                     "Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
        if not body.get("ok"):
            raise RuntimeError(f"RTS error: {body.get('error', 'unknown')}")
        # Defensive: accept whichever result container the API returns.
        return (body.get("results")
                or body.get("messages", {}).get("matches")
                or [])

    def fetch(self, context: dict) -> Optional[Evidence]:
        for item in self._call(self._build_query(context)):
            text = (item.get("text") or item.get("content") or "").strip()
            source = item.get("permalink") or item.get("url") or ""
            if not text or not source:
                continue
            if _advocates_position(text):  # neutrality gate
                continue
            return Evidence(text=text, source=source, handle=self._handle, label="rts")
        return None


class RTSAdapterStub(EvidenceSource):
    """Not-configured placeholder. Fails loudly so the required-tech wiring cannot
    silently disappear; use `RTSAdapter` (with a token) for the real call, or
    `FixtureEvidenceSource` offline."""

    def fetch(self, context: dict) -> Optional[Evidence]:
        raise NotImplementedError(
            "RTS not configured. Use RTSAdapter(token=...) live, or "
            "FixtureEvidenceSource offline. See docs/REQUIRED_TECH_TODO.md."
        )
