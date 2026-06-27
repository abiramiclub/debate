"""The Honeybee constitution engine, exposed as an MCP server.

Architecture (locked decision #3): the Slack agent is the MCP host/client; THIS is
the MCP server. The agent calls these deterministic tools; the probabilistic
mediator runs agent-side and feeds its outputs (candidates, agreement) in.

The constitution logic is FROZEN — this module only *wraps* the existing
functions in `constitution/` as MCP tools. It does not reimplement any rule.

Run as a stdio MCP server:  python -m mcp_server.server
"""

import os
import tempfile

from mcp.server.fastmcp import FastMCP

from constitution.audit import AuditLog
from constitution.bridging import cluster_participants, rank_candidates
from constitution.config import DEFAULT
from constitution.protocol import NEUTRAL_HANDLES, _minority_present
from constitution.weighting import phase_index, raw_support, weighted_support

mcp = FastMCP("honeybee-constitution")

# Server-side session state (the deterministic half of the engine). Keyed by id.
_SESSIONS: dict[str, dict] = {}


def _audit_path(session_id: str) -> str:
    return os.path.join(tempfile.gettempdir(), f"honeybee_mcp_{session_id}.jsonl")


@mcp.tool()
def start_session(session_id: str, participants: list[dict]) -> dict:
    """Create a session, assign neutral handles, record consent.
    participants: [{"user_id": str, "actor_type": "human"|"agent"}]."""
    handles = {}
    for i, p in enumerate(participants):
        handles[NEUTRAL_HANDLES[i % len(NEUTRAL_HANDLES)]] = p
    audit = AuditLog(_audit_path(session_id), session_id)
    audit.log("CONSENT", "system", "system", "consent_recorded",
              payload={"n": len(participants)})
    _SESSIONS[session_id] = {"handles": handles, "audit": audit, "reads": []}
    return {"session_id": session_id, "handles": list(handles.keys()), "state": "COLLECT_READS"}


@mcp.tool()
def store_read(session_id: str, handle: str, text: str, confidence: int) -> dict:
    """Store one participant's private read + confidence (pre-reveal)."""
    s = _SESSIONS[session_id]
    s["reads"].append({"handle": handle, "text": text, "confidence": confidence})
    s["audit"].log("COLLECT_READS", handle, "human", "store_read",
                   payload={"confidence": confidence, "text": text})
    return {"stored": True, "n_reads": len(s["reads"])}


@mcp.tool()
def rank_bridging(agreement: list[list[float]]) -> dict:
    """Deterministic bridging selection over a participants×candidates agreement
    matrix. Returns the cross-group winner, its bridging score, opinion groups,
    and whether a minority cluster is present (steelman trigger)."""
    labels = cluster_participants(agreement, DEFAULT.k_max, DEFAULT.min_n_for_clustering)
    scored = rank_candidates(agreement, labels)
    near = raw_support(scored) >= DEFAULT.Q
    support = weighted_support(scored, phase_index(0, near), DEFAULT)
    return {
        "winner_index": scored[0].index,
        "bridging_score": scored[0].bridging_score,
        "groups": labels,
        "minority_present": _minority_present(labels),
        "support": support,
    }


@mcp.tool()
def check_quorum(support: float, ci_rounds_elapsed: int, cross_inhibition_fired: bool) -> dict:
    """Deterministic quorum test: support ≥ Q AND ≥1 cross-inhibition round AND
    not currently firing cross-inhibition."""
    met = support >= DEFAULT.Q and ci_rounds_elapsed >= 1 and not cross_inhibition_fired
    return {"quorum_met": met, "Q": DEFAULT.Q, "support": support}


@mcp.tool()
def inject_evidence(session_id: str, handle: str, text: str, source: str) -> dict:
    """Log an injected, sourced fact (the deadlock consequence). Source is
    written to the immutable audit."""
    s = _SESSIONS[session_id]
    s["audit"].log("INFO_INJECTION", handle, "agent", "inject_evidence",
                   payload={"text": text}, source=source)
    return {"injected": True, "source": source}


@mcp.tool()
def get_audit(session_id: str) -> list[dict]:
    """Return the immutable JSONL audit trail for the debrief."""
    return _SESSIONS[session_id]["audit"].read_all()


if __name__ == "__main__":
    mcp.run()
