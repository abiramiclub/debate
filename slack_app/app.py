"""Wiki & Vicky — the Slack Bolt surface (Socket Mode).

The app is the MCP host/client; it drives the frozen engine ONLY through
`slack_app.mcp_client` (never imports `constitution/`). Credentials come from env:
SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_RTS_TOKEN, ANTHROPIC_API_KEY.

Flow (DEMO_SCRIPT.md beats): /decide -> consent -> private read modal
(hidden before reveal) -> reveal -> Vicky synthesis + minority steelman ->
Wiki gate strikes (from the audit) -> deadlock -> RTS evidence under @Linden ->
bridged quorum -> Block Kit debrief.

Requires a live Slack sandbox + tokens to run; unrunnable offline. The MCP seam it
renders on is verified offline by `slack_app/run_scripted.py` and tests/test_slack_seam.py.
"""

import asyncio
import json
import os

from slack_app import render
from slack_app.mcp_client import EngineClient, engine_client

SESSION_ID = "slack-demo"
_FIXTURE = os.path.join(os.path.dirname(__file__), "..", "demo", "fixture_5p_twocamp.json")


def _load_fixture() -> dict:
    with open(_FIXTURE) as f:
        return json.load(f)


def _participants(fx: dict) -> list[dict]:
    return [{"user_id": p["user_id"], "actor_type": p["actor_type"], "handle": p["handle"]}
            for p in fx["participants"]]


async def _post(client, channel, blocks, text):
    await client.chat_postMessage(channel=channel, blocks=blocks, text=text)


async def _run_and_post(client, channel, engine: EngineClient, fx: dict):
    """Submit the (reproducible) reads, run the deliberation over MCP, and post
    every DEMO_SCRIPT beat with the real engine data + audit-sourced gate strikes."""
    # Reads are collected privately before reveal (anti-anchoring). For the
    # reproducible recorded demo we submit the fixture reads.
    handles = [p["handle"] for p in fx["participants"]]
    for handle, read in zip(handles, fx["reads"]):
        await engine.submit_read(SESSION_ID, handle, read["text"], read["confidence"])

    delib = await engine.deliberate(SESSION_ID, fx["rounds"], fx["steelman_text"], fx["evidence"])
    debrief = await engine.debrief(SESSION_ID)
    audit = debrief["audit"]
    actions = [e["action"] for e in audit]

    # 1) Reveal — two camps, names withheld.
    await _post(client, channel, render.reveal_blocks(delib["rounds"][0]["candidates"]),
                "Reads are in.")
    # 2) Cross-inhibition (resist premature consensus).
    if any(r["cross_inhibition_fired"] for r in delib["rounds"]):
        await _post(client, channel, render.wiki(
            "cross-inhibition — resisting premature consensus"), "cross-inhibition")
    # 3) Minority steelman.
    await _post(client, channel, render.vicky(
        "Strongest version of the least-supported view, for fair consideration:")
        + [{"type": "section", "text": {"type": "mrkdwn", "text": f"> {fx['steelman_text']}"}}],
        "minority steelman")
    # 4) Gate strikes, sourced from the audit.
    for action in ("neutrality_rejected", "prediction_blocked"):
        if action in actions:
            await _post(client, channel, render.wiki_strike(render.strike_line_for(action)),
                        "gate strike")
    # 5) Deadlock -> evidence via RTS under a neutral handle.
    if debrief.get("injected_evidence"):
        ev = debrief["injected_evidence"][0]
        await _post(client, channel, render.wiki("HOLDING quorum · requesting evidence at deadlock"),
                    "holding")
        await _post(client, channel,
                    render.neutral_evidence(ev["handle"], ev["text"], ev["source"]), "evidence")
    # 6) Bridged quorum.
    if delib["reached_quorum"]:
        await _post(client, channel, render.wiki(
            f"QUORUM MET · cross-group support high · audit: {len(audit)} events"), "quorum")
        await _post(client, channel, render.vicky(
            f"The compromise nobody walked in with:\n> {debrief['winner']}"), "winner")
    # 7) Debrief (Block Kit) + the Willow-was-an-AI reveal.
    await _post(client, channel, render.debrief_blocks(), "Debrief")


def build_app(engine: EngineClient):
    from slack_bolt.async_app import AsyncApp

    app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])
    fx = _load_fixture()

    @app.command("/decide")
    async def decide(ack, body, client):
        await ack()
        question = (body.get("text") or "How should we build our internal knowledge agent?").strip()
        started = await engine.start_session(SESSION_ID, _participants(fx))
        channel = body["channel_id"]
        await _post(client, channel, render.consent_blocks(question), "A decision to make")
        # Stash handles for the consent step.
        app._handles = started["handles"]  # noqa: SLF001 (demo state)
        app._channel = channel

    @app.action("consent_join")
    async def consent(ack, body, client):
        await ack()
        channel = body["container"]["channel_id"]
        await _post(client, channel, render.handles_blocks(getattr(app, "_handles", [])),
                    "Handles assigned")
        # Open a private read modal to the clicker (anti-anchoring demo).
        await client.views_open(
            trigger_id=body["trigger_id"],
            view=render.read_modal(SESSION_ID, getattr(app, "_handles", ["Birch"])[0]))
        # Run the reproducible deliberation and post the beats.
        await _run_and_post(client, channel, engine, fx)

    @app.view("submit_read")
    async def submit_read(ack, body, view):
        meta = json.loads(view["private_metadata"])
        text = view["state"]["values"]["read"]["text"]["value"]
        conf = int(view["state"]["values"]["confidence"]["value"]["selected_option"]["value"])
        await engine.submit_read(meta["session_id"], meta["handle"], text, conf)
        await ack()

    return app


async def _main() -> None:
    from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler

    for var in ("SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"):
        if not os.environ.get(var):
            raise SystemExit(f"missing env var {var}")
    async with engine_client() as engine:  # one persistent MCP connection
        app = build_app(engine)
        handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
        await handler.start_async()


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
