"""The Honeybee constitution engine, exposed as an MCP server.

Architecture (locked decision #3): the Slack agent is the MCP host/client; THIS is
the MCP server. The agent calls these tools; the probabilistic mediator runs
agent-side and supplies its language work (candidate statements, agreement
estimates, steelman, evidence) into the deterministic engine.

The constitution logic is FROZEN — this module only *wraps* `constitution/` and
`mediator/` as MCP tools. It reimplements no rule.

Because MCP tool calls are stateless, session state (handles, reads, audit, the
live `Session`) is persisted SERVER-SIDE keyed by `session_id` across calls.

Run as a stdio MCP server:  python -m mcp_server.server
"""

import os
import tempfile
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from constitution.bridging import cluster_participants, rank_candidates
from constitution.config import DEFAULT
from constitution.evidence import Evidence, FixtureEvidenceSource
from constitution.protocol import Session, _minority_present
from constitution.weighting import phase_index, raw_support, weighted_support
from mediator.fake import FakeMediator
from mediator.scripted import ScriptedMediator

mcp = FastMCP("honeybee-constitution")

# Server-side session store — the whole point: MCP calls are stateless, so we
# persist the live engine state keyed by session_id across tool invocations.
_SESSIONS: dict[str, Session] = {}


def _audit_path(session_id: str) -> str:
    return os.path.join(tempfile.gettempdir(), f"honeybee_mcp_{session_id}.jsonl")


def _require(session_id: str) -> Session:
    if session_id not in _SESSIONS:
        raise ValueError(f"unknown session_id {session_id!r}; call start_session first")
    return _SESSIONS[session_id]


# --- stateful session lifecycle -----------------------------------------------

@mcp.tool()
def start_session(session_id: str, participants: list[dict]) -> dict:
    """Create a session, assign neutral handles, record consent. Persists the
    live engine server-side under `session_id`.
    participants: [{"user_id": str, "actor_type": "human"|"agent"}]."""
    path = _audit_path(session_id)
    if os.path.exists(path):
        os.remove(path)
    # A placeholder mediator is set now; the real/scripted one is supplied at
    # deliberate() time (the agent owns the language work).
    session = Session(session_id, FakeMediator(), path)
    session.start([(p["user_id"], p["actor_type"]) for p in participants])
    _SESSIONS[session_id] = session
    return {"session_id": session_id,
            "handles": [p.handle for p in session.participants],
            "state": session.state.value}


@mcp.tool()
def submit_read(session_id: str, handle: str, text: str, confidence: int) -> dict:
    """Store one participant's private read + confidence (before any reveal)."""
    s = _require(session_id)
    s.submit_read(handle, text, confidence)
    return {"stored": True, "n_reads": len(s.reads)}


@mcp.tool()
def deliberate(session_id: str, mediator_script: list[dict], steelman_text: str,
               evidence: Optional[dict] = None, max_rounds: int = 6) -> dict:
    """Run the FROZEN deliberation loop server-side: reveal -> cross-inhibition ->
    steelman -> echo/deadlock -> evidence injection -> bridging quorum.

    The agent supplies the mediator's language work:
      mediator_script: [{"candidates": [str], "agreement": [[float]]}] per round
      steelman_text:   the minority steelman string
      evidence:        {"text","source","handle","label"} injected at the deadlock
    Returns per-round outcomes + the bridged winner.
    """
    s = _require(session_id)
    s.mediator = ScriptedMediator(mediator_script, steelman_text)
    if evidence:
        s.evidence_source = FixtureEvidenceSource(Evidence(
            text=evidence["text"], source=evidence["source"],
            handle=evidence.get("handle", "Linden"), label=evidence.get("label", "fixture")))
    results = s.deliberate(max_rounds=max_rounds)
    return {
        "reached_quorum": s.winner_text is not None,
        "winner": s.winner_text,
        "rounds": [{
            "round_idx": r.round_idx,
            "winner_text": r.winner_text,
            "winner_support": r.winner_support,
            "decision": r.decision,
            "cross_inhibition_fired": r.cross_inhibition_fired,
            "minority_present": r.minority_present,
            "has_steelman": r.steelman is not None,
            "echo_flag": r.echo_flag,
            "injected": r.evidence is not None,
            "source": r.evidence.source if r.evidence else None,
        } for r in results],
    }


@mcp.tool()
def get_audit(session_id: str) -> list[dict]:
    """Return the immutable JSONL audit trail for the debrief."""
    return _require(session_id).audit.read_all()


@mcp.tool()
def debrief(session_id: str) -> dict:
    """Reveal the anonymization map, the outcome, injected evidence, and audit."""
    return _require(session_id).debrief()


# --- stateless deterministic primitives (engine ops, individually callable) ---

@mcp.tool()
def rank_bridging(agreement: list[list[float]]) -> dict:
    """Deterministic bridging selection over a participants×candidates agreement
    matrix. Returns the cross-group winner, bridging score, opinion groups, and
    whether a minority cluster is present (the steelman trigger)."""
    labels = cluster_participants(agreement, DEFAULT.k_max, DEFAULT.min_n_for_clustering)
    scored = rank_candidates(agreement, labels)
    near = raw_support(scored) >= DEFAULT.Q
    support = weighted_support(scored, phase_index(0, near), DEFAULT)
    return {"winner_index": scored[0].index, "bridging_score": scored[0].bridging_score,
            "groups": labels, "minority_present": _minority_present(labels), "support": support}


@mcp.tool()
def check_quorum(support: float, ci_rounds_elapsed: int, cross_inhibition_fired: bool) -> dict:
    """Deterministic quorum test: support ≥ Q AND ≥1 cross-inhibition round AND
    not currently firing cross-inhibition."""
    met = support >= DEFAULT.Q and ci_rounds_elapsed >= 1 and not cross_inhibition_fired
    return {"quorum_met": met, "Q": DEFAULT.Q, "support": support}


@mcp.tool()
def inject_evidence(session_id: str, handle: str, text: str, source: str) -> dict:
    """Log an injected, sourced fact (the deadlock consequence) to the audit."""
    s = _require(session_id)
    s.audit.log("INFO_INJECTION", handle, "agent", "inject_evidence",
                payload={"text": text}, source=source)
    return {"injected": True, "source": source}


if __name__ == "__main__":
    mcp.run()
