# Required-tech wiring — tracked must-dos for the Slack phase

The hackathon rewards combining two technologies: **MCP server integration** and
the **Real-Time Search (RTS) API**.

## Seam-slice results (STEP 0)

| Seam | Status | Evidence |
|------|--------|----------|
| **MCP** | ✅ **PROVEN here** | `python -m mcp_server.seam_check`: engine runs as a real MCP server (stdio), a client round-trip returns the identical frozen `rank_bridging` result, stateful tools + audit round-trip. |
| **Real mediator** | ⚙️ adapter built, live call **needs creds** | `mediator/claude.py` implements all 4 methods; offline-proven in `tests/test_real_mediator.py` with a stub client. `python -m mediator.probe_real` reports BLOCKED (no `ANTHROPIC_API_KEY`/OpenClaw endpoint in this env). |
| **RTS** | ⚙️ adapter built, live call **needs token** | Method confirmed: `assistant.search.context` (Slack **Web API**, so backend-callable). `constitution/evidence.RTSAdapter` issues the call + neutrality-vets the result; offline-proven in `tests/test_rts.py`. Live test runs when `SLACK_RTS_TOKEN` is set. |

What only you can supply (not available in this build env): a Slack **sandbox +
workspace token** (RTS), and an **OpenClaw endpoint / API key** (mediator).

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
