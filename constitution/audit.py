"""Immutable JSONL audit log.

Invariant 6 of the constitution: every state transition and every agent
contribution is appended here, with source. One JSON object per line.

This is both governance (the fairness defense) and demo evidence.
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Optional


def _hash_payload(payload: Any) -> str:
    """Stable short hash of a payload, so the audit can prove what was said
    without necessarily storing the full (possibly sensitive) text inline."""
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


@dataclass
class AuditEvent:
    ts: float
    session_id: str
    state: str
    actor_handle: str
    actor_type: str  # "human" | "agent" | "system"
    action: str
    payload_hash: str
    source: Optional[str] = None  # citation / URL for injected info


class AuditLog:
    def __init__(self, path: str, session_id: str):
        self.path = path
        self.session_id = session_id

    def log(
        self,
        state: str,
        actor_handle: str,
        actor_type: str,
        action: str,
        payload: Any = None,
        source: Optional[str] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            ts=time.time(),
            session_id=self.session_id,
            state=state,
            actor_handle=actor_handle,
            actor_type=actor_type,
            action=action,
            payload_hash=_hash_payload(payload) if payload is not None else "",
            source=source,
        )
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")
        return event

    def read_all(self) -> list[dict]:
        events: list[dict] = []
        try:
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        except FileNotFoundError:
            pass
        return events
