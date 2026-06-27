# Required-tech wiring — tracked must-dos for the Slack phase

The hackathon rewards combining two technologies: **MCP server integration** and
the **Real-Time Search (RTS) API**. Both are intentionally *stubbed* in the
offline build so the full story is runnable now; neither may silently disappear.

## 1. Real-Time Search (RTS) API — evidence injection

- **Status:** stubbed. `constitution/evidence.RTSAdapterStub.fetch()` raises
  `NotImplementedError`; the offline demo uses `FixtureEvidenceSource`.
- **Why stubbed:** RTS is a Slack-platform capability that expects the Slack app
  runtime / token context, so it cannot be exercised from this offline harness.
- **Seam is in place:** the constitution already calls `EvidenceSource.fetch()`
  at the deadlock and logs the returned `source` to the audit. Swapping the
  fixture source for a live RTS adapter requires **no protocol change**.
- **Slack-phase task:** implement `RTSAdapterStub.fetch()` to (a) build a query
  from the deadlock context, (b) issue the RTS call, (c) vet the top result and
  run it through the position-neutrality check, (d) return
  `Evidence(text=..., source=<url>)`.

## 2. MCP server integration — the engine

- **Status:** not built this phase (deliberately).
- **Plan:** wrap the deterministic engine (`start_session`, `store_read`,
  `rank_bridging`, `check_quorum`, `inject_evidence`, `get_audit`) as MCP tools
  the Slack agent calls. This is the core required technology.
- **Risk to retire early:** the MCP↔Slack seam is the least-documented part;
  validate the connection first in the Slack phase, not last.
