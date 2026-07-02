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
4. **Start the app** in a channel the bot is in:
   ```bash
   SLACK_BOT_TOKEN=… SLACK_APP_TOKEN=… python -m slack_app.app
   ```
5. **Judge access (STEP 7):** invite `slackhack@salesforce.com` and
   `testing@devpost.com` to the sandbox; capture the **Slack App ID** for the
   submission form.

## Two modes of `/decide`

- **`/decide <question>` — LIVE (default):** posts consent → collects real reads via
  the private modal (hidden before reveal) → `/decide-run` runs the deliberation on
  those reads: **Vicky** (`ClaudeMediator`, default model `claude-sonnet-5`) produces
  candidates + agreement, **Wiki** (the engine) does the deterministic selection,
  gates, and quorum, and RTS evidence is fetched at the deadlock. Every step is
  audited. Verified offline (stub mediator) by `tests/test_live_path.py`.
- **`/decide replay` — the reproducible recorded demo:** replays
  `demo/fixture_5p_twocamp.json` through the MCP `deliberate` tool. Use this for the
  on-camera run. Verified by `tests/test_slack_seam.py`.

## RTS (assistant.search.context) specifics

- Scope: **`search:read.public`** (evidence is searched in **public** channels only).
- Bot-token calls need a **per-event `action_token`**, captured from an
  `app_mention` / `message.channels` event (subscribed in `manifest.yaml`) and
  passed into `RTSAdapter(token=…, action_token=…)`. If it's missing, the app falls
  back to the fixture evidence so the demo never dead-ends.
- Confirm the live response field names against the sandbox; fix the mapping in
  `constitution/evidence.py` only if they differ from the defensive defaults.

## Gate (per the July 6 decision)

The live path is demo-ready by **July 6** or we freeze and ship `/decide replay`.
