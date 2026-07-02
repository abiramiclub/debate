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

- **Status:** adapter **built and real** — `constitution/evidence.RTSAdapter` calls
  Slack `assistant.search.context`, parses the top result, and runs it through the
  position-neutrality gate, returning `Evidence(text, source=<permalink>)`. Offline
  parse + neutrality behavior proven in `tests/test_rts.py`. `RTSAdapterStub`
  remains only as the not-configured placeholder (fails loudly).
- **Seam in place:** the constitution calls `EvidenceSource.fetch()` at the
  deadlock and logs the returned `source` to the audit — swapping the fixture
  source for `RTSAdapter` needs **no protocol change**.
- **Auth model (decided):** scope is **`search:read.public`** (public channels only).
  Bot-token calls need a **per-event `action_token`** captured from an `app_mention` /
  `message.channels` event (subscribed in `slack_app/manifest.yaml`) and passed as
  `RTSAdapter(token=…, action_token=…)`. Offline-proven the token is sent + result
  parsed in `tests/test_rts.py::test_action_token_is_sent_and_result_parsed`.
- **Remaining (needs a live workspace token):** run against the sandbox and **confirm
  the live `assistant.search.context` response field names**; fix `_call`/`fetch`
  mapping only if they differ from the defensive defaults (`results`/`messages.matches`,
  `text`/`content`, `permalink`/`url`). The token-gated live test in `tests/test_rts.py`
  runs once `SLACK_RTS_TOKEN` is set.

## 2. MCP server integration — the engine

- **Status:** **BUILT and PROVEN.** `mcp_server/server.py` wraps the frozen engine
  as MCP tools (`start_session`, `submit_read`, `deliberate`, `rank_bridging`,
  `check_quorum`, `inject_evidence`, `get_audit`, `debrief`) with server-side
  session state. `python -m mcp_server.seam_check` passes; `tests/test_mcp_roundtrip.py`
  drives a full 5-person deliberation entirely over MCP to the bridged quorum.
- **Remaining:** connect the Slack app (`slack_app/`) as the MCP **client** to this
  server (stdio) — the agent produces the mediator's language work and passes it
  into `deliberate`. Validate the client connection early; it's the least-documented seam.
