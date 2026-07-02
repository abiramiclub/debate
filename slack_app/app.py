"""Wiki & Vicky — the Slack Bolt surface (Socket Mode).

The app is the MCP host/client; it drives the frozen engine ONLY through
`slack_app.agent` / `slack_app.mcp_client` (never imports `constitution/`).
Credentials from env: SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_RTS_TOKEN,
ANTHROPIC_API_KEY.

Two modes of `/decide`:
  * `/decide <question>`  — LIVE: real reads (modal) -> live Vicky candidates +
    agreement via ClaudeMediator -> Wiki's deterministic selection/gates/quorum ->
    RTS evidence at the deadlock -> Block Kit debrief.
  * `/decide replay`      — the reproducible recorded demo (replays the fixture).

Requires a live Slack sandbox + tokens; unrunnable offline. The seams it renders on
are verified offline by tests/test_slack_seam.py (replay) and tests/test_live_path.py
(live plumbing, stub mediator).
"""

import asyncio
import json
import os

from slack_app import render
from slack_app.agent import run_live_session_over_mcp, run_session_over_mcp

_FIXTURE = os.path.join(os.path.dirname(__file__), "..", "demo", "fixture_5p_twocamp.json")

# Minimal in-memory demo state (single concurrent session).
_STATE: dict = {"action_token": None, "question": None, "channel": None, "reads": []}


def _load_fixture() -> dict:
    with open(_FIXTURE) as f:
        return json.load(f)


async def _post(client, channel, blocks, text):
    await client.chat_postMessage(channel=channel, blocks=blocks, text=text)


async def _post_beats(client, channel, result: dict, steelman_text: str):
    """Post every DEMO_SCRIPT beat from a completed deliberation (replay or live)."""
    delib, debrief = result["delib"], result["debrief"]
    audit = debrief["audit"]
    actions = [e["action"] for e in audit]

    await _post(client, channel, render.reveal_blocks(delib["rounds"][0]["candidates"]),
                "Reads are in.")
    if any(r["cross_inhibition_fired"] for r in delib["rounds"]):
        await _post(client, channel, render.wiki(
            "cross-inhibition — resisting premature consensus"), "cross-inhibition")
    await _post(client, channel, render.vicky(
        "Strongest version of the least-supported view, for fair consideration:")
        + [{"type": "section", "text": {"type": "mrkdwn", "text": f"> {steelman_text}"}}],
        "minority steelman")
    for action in ("neutrality_rejected", "prediction_blocked"):
        if action in actions:
            await _post(client, channel, render.wiki_strike(render.strike_line_for(action)),
                        "gate strike")
    if debrief.get("injected_evidence"):
        ev = debrief["injected_evidence"][0]
        await _post(client, channel, render.wiki("HOLDING quorum · requesting evidence at deadlock"),
                    "holding")
        await _post(client, channel,
                    render.neutral_evidence(ev["handle"], ev["text"], ev["source"]), "evidence")
    if delib["reached_quorum"]:
        await _post(client, channel, render.wiki(
            f"QUORUM MET · cross-group support high · audit: {len(audit)} events"), "quorum")
        await _post(client, channel, render.vicky(
            f"The compromise nobody walked in with:\n> {debrief['winner']}"), "winner")
    await _post(client, channel, render.debrief_blocks(), "Debrief")


def _rts_evidence(question: str, reads: list[dict]) -> dict | None:
    """Fetch sourced evidence via live RTS (needs a token + per-event action_token);
    fall back to the fixture evidence so the demo never dead-ends."""
    fixture_ev = _load_fixture()["evidence"]
    token = os.environ.get("SLACK_RTS_TOKEN")
    if not token or not _STATE.get("action_token"):
        return fixture_ev
    try:
        from constitution.evidence import RTSAdapter
        from mediator.base import Read
        adapter = RTSAdapter(token=token, action_token=_STATE["action_token"])
        ev = adapter.fetch({"query": question,
                            "reads": [Read(r.get("handle", "P"), r["text"], r["confidence"])
                                      for r in reads]})
        return {"text": ev.text, "source": ev.source, "handle": ev.handle, "label": "rts"} \
            if ev else fixture_ev
    except Exception:  # noqa: BLE001 — demo must not dead-end on a live RTS hiccup
        return fixture_ev


def build_app():
    from slack_bolt.async_app import AsyncApp

    app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])
    fx = _load_fixture()

    # Capture the per-event action_token used to authorize bot-token RTS calls.
    @app.event("app_mention")
    async def on_mention(body, ack=None):
        _STATE["action_token"] = body.get("event", {}).get("action_token") or _STATE["action_token"]

    @app.event("message")
    async def on_message(body):
        _STATE["action_token"] = body.get("event", {}).get("action_token") or _STATE["action_token"]

    @app.command("/decide")
    async def decide(ack, body, client):
        await ack()
        channel = body["channel_id"]
        text = (body.get("text") or "").strip()
        _STATE.update(channel=channel, reads=[])

        if text.lower().startswith("replay"):
            await _post(client, channel, render.vicky("Replaying the recorded deliberation…"),
                        "replay")
            result = await run_session_over_mcp(fx, session_id="slack-replay")
            await _post_beats(client, channel, result, fx["steelman_text"])
            return

        _STATE["question"] = text or "How should we build our internal knowledge agent?"
        await _post(client, channel, render.consent_blocks(_STATE["question"]),
                    "A decision to make")

    @app.action("consent_join")
    async def consent(ack, body, client):
        await ack()
        channel = body["container"]["channel_id"]
        cast = [p["handle"] for p in fx["participants"]]
        await _post(client, channel, render.handles_blocks(cast), "Handles assigned")
        await client.views_open(trigger_id=body["trigger_id"],
                                view=render.read_modal("slack-live", cast[0]))
        await _post(client, channel, render.vicky(
            "Once reads are in, run the deliberation with the button… or `/decide replay`.")
            + [{"type": "actions", "elements": [{
                "type": "button", "style": "primary", "action_id": "run_live",
                "text": {"type": "plain_text", "text": "Run deliberation (live)"}}]}],
            "prompt")

    @app.view("submit_read")
    async def submit_read(ack, body, view):
        meta = json.loads(view["private_metadata"])
        text = view["state"]["values"]["read"]["text"]["value"]
        conf = int(view["state"]["values"]["confidence"]["value"]["selected_option"]["value"])
        _STATE["reads"].append({"handle": meta["handle"], "text": text, "confidence": conf})
        await ack()

    @app.action("run_live")
    async def run_live(ack, body, client):
        """Run the LIVE deliberation on the collected reads (real ClaudeMediator)."""
        await ack()
        channel = body["container"]["channel_id"]
        reads = _STATE["reads"] or fx["reads"]  # fall back to fixture reads for a solo demo
        participants = [{"user_id": p["user_id"], "actor_type": p["actor_type"],
                         "handle": p["handle"]} for p in fx["participants"]][:len(reads)]
        evidence = _rts_evidence(_STATE.get("question", ""), reads)
        result = await run_live_session_over_mcp(
            _STATE.get("question", ""), reads, participants=participants, evidence=evidence,
            session_id="slack-live")
        await _post_beats(client, channel, result, result["steelman"])

    return app


async def _main() -> None:
    from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler

    for var in ("SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"):
        if not os.environ.get(var):
            raise SystemExit(f"missing env var {var}")
    app = build_app()
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
