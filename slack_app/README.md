# slack_app — the Bolt surface

The Slack surface for **Wiki & Vicky**. It is the MCP **host/client**; it drives the
frozen engine (`mcp_server/server.py`) **only** through MCP tools and never imports
`constitution/`. The mediator (Vicky / `ClaudeMediator`) and the RTS evidence fetch
run agent-side; their outputs go into the deterministic engine as data.

## What runs where

| Piece | File | Runs offline? |
|-------|------|---------------|
| MCP client seam | `mcp_client.py` | ✅ |
| Agent orchestration | `agent.py` | ✅ (replay); live needs creds |
| Block Kit rendering | `render.py` | ✅ |
| Bolt app (Socket Mode) | `app.py` | ❌ needs Slack tokens |
| Scripted MCP acceptance run | `run_scripted.py` | ✅ |

## Verify offline (no tokens)

```bash
python -m slack_app.run_scripted     # full deliberation reaches debrief over MCP
python -m pytest -q                  # 53 passed, 1 skipped
```

## Run live in the sandbox

1. **Create the app** at api.slack.com/apps → *From an app manifest* → paste
   `slack_app/manifest.yaml`. Install to the sandbox workspace.
2. **Tokens** (never commit them; see `.env.example`):
   - `SLACK_BOT_TOKEN` — Bot User OAuth token (`xoxb-…`)
   - `SLACK_APP_TOKEN` — App-Level token with `connections:write` (`xapp-…`)
   - `SLACK_RTS_TOKEN` — token authorized for `assistant.search.context`
   - `ANTHROPIC_API_KEY` — (or point `ANTHROPIC_BASE_URL` at OpenClaw/qwen)
3. **Confirm the two live seams first** (STEP 4/5):
   ```bash
   SLACK_RTS_TOKEN=… python -m pytest tests/test_rts.py -q     # confirm field names
   ANTHROPIC_API_KEY=… python -m mediator.probe_real           # all 4 methods live
   ```
   If the live `assistant.search.context` response field names differ from the
   defensive defaults, fix the mapping in `constitution/evidence.py` **only**.
4. **Start the app**, then `/decide "How should we build our internal knowledge agent?"`
   in a channel the bot is in:
   ```bash
   SLACK_BOT_TOKEN=… SLACK_APP_TOKEN=… python -m slack_app.app
   ```
5. **Judge access (STEP 7):** invite `slackhack@salesforce.com` and
   `testing@devpost.com` to the sandbox; capture the **Slack App ID** for the
   submission form.

## Note on the demo deliberation

The private-read **modal** demonstrates the anti-anchoring guarantee (reads hidden
before reveal). For the reproducible recorded demo, the deliberation replays
`demo/fixture_5p_twocamp.json` through the MCP `deliberate` tool. Fully-live
per-round generation from real reads via `ClaudeMediator` is wired as
`agent.build_live_round0()`; the multi-round live arc is a follow-up.
