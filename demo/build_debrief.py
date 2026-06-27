"""Build the Block Kit debrief for the demo session and validate it.

Run:  python -m demo.build_debrief
Writes demo/debrief_blockkit.json (paste into the Slack Block Kit Builder).

The debrief mirrors the harness metrics for THIS session (least-satisfied-group
support, minority survival, average), plus the scenario-only uptake delta, the
AI-handle reveal, and an audit-trail reference.
"""

import json
import os

from demo.metrics import final_metrics, uptake
from demo.run_ab import load_fixture, run_constitution, run_naive

OUT = os.path.join(os.path.dirname(__file__), "debrief_blockkit.json")

_ALLOWED_BLOCKS = {"header", "section", "divider", "context", "actions"}


def validate_blockkit(payload: dict) -> bool:
    """Tiny structural validator for a Block Kit message. Raises AssertionError
    on anything that would fail to render in the Block Kit Builder."""
    assert isinstance(payload, dict) and "blocks" in payload, "top level needs 'blocks'"
    blocks = payload["blocks"]
    assert isinstance(blocks, list) and 1 <= len(blocks) <= 50, "1..50 blocks"
    for b in blocks:
        assert isinstance(b, dict) and b.get("type") in _ALLOWED_BLOCKS, f"bad block: {b}"
        t = b["type"]
        if t == "header":
            txt = b["text"]
            assert txt["type"] == "plain_text" and 0 < len(txt["text"]) <= 150
        elif t == "section":
            assert ("text" in b) or ("fields" in b), "section needs text or fields"
            if "text" in b:
                assert b["text"]["type"] in ("mrkdwn", "plain_text")
                assert 0 < len(b["text"]["text"]) <= 3000
            if "fields" in b:
                assert 1 <= len(b["fields"]) <= 10
                for fld in b["fields"]:
                    assert fld["type"] in ("mrkdwn", "plain_text")
                    assert 0 < len(fld["text"]) <= 2000
        elif t == "context":
            assert 1 <= len(b["elements"]) <= 10
        elif t == "actions":
            assert 1 <= len(b["elements"]) <= 5
            for el in b["elements"]:
                assert el["type"] == "button"
                assert el["text"]["type"] == "plain_text"
    return True


def _md(text: str) -> dict:
    return {"type": "mrkdwn", "text": text}


def build_blocks(fixture: dict, session, debrief: dict) -> dict:
    winner = debrief["winner"]
    final_candidates = fixture["rounds"][-1]["candidates"]
    compromise_idx = final_candidates.index(winner)
    naive_idx = 1  # the majority camp's position on the final slate (what naive picks)

    m_bridge = final_metrics(fixture, compromise_idx)
    m_naive = final_metrics(fixture, naive_idx)
    up = uptake(fixture)

    ai = [p["handle"] for p in debrief["participants"] if p["actor_type"] == "agent"]
    n_events = len(debrief["audit"])
    inj = debrief["injected_evidence"][0] if debrief["injected_evidence"] else None

    def pair(key):
        return f"bridged *{m_bridge[key]:.2f}* · naive *{m_naive[key]:.2f}*"

    blocks = [
        {"type": "header", "text": {"type": "plain_text",
         "text": "⚖️ Deliberation debrief"}},
        {"type": "section", "text": _md(f"*Topic:* {fixture['topic']}")},
        {"type": "section", "text": _md(
            f"*Outcome (bridged consensus):*\n>{winner}\n\n"
            f"*What majority-rule would have picked:*\n>{run_naive(fixture)}")},
        {"type": "divider"},
        {"type": "section", "fields": [
            _md(f"*Least-satisfied group*\n{pair('min_group_support')}"),
            _md(f"*Minority survival*\n{pair('minority_survival')}"),
            _md(f"*Average endorsement*\n{pair('mean_endorsement')}"),
            _md(f"*Bridging breadth*\n{m_bridge['breadth_ratio']:.2f} (1.00 = broadest available)"),
        ]},
        {"type": "section", "text": _md(
            f"*Information uptake (this scenario):* the minority shifted "
            f"*{up['minority_mean_shift']:+.2f}* on average after the evidence; "
            f"the majority *{up['majority_mean_shift']:+.2f}*. "
            f"{up['moved_count']} of {up['n']} participants moved.")},
        {"type": "context", "elements": [_md(
            "⚠️ Uptake is a *scenario demonstration*, not data-validated. The "
            "bridging result IS validated on 6,605 real Habermas sessions (Phase A).")]},
        {"type": "divider"},
        {"type": "section", "text": _md(
            "*Who was AI:* " + (", ".join(ai) + " (revealed only now, at debrief)"
                                if ai else "no AI participants"))},
    ]
    if inj:
        blocks.append({"type": "context", "elements": [_md(
            f"📎 Evidence injected at the deadlock via @{inj['handle']} — source: {inj['source']}")]})
    blocks.append({"type": "context", "elements": [_md(
        f"📜 Every step logged — {n_events} audit events for session `{debrief['session_id']}`")]})

    return {"blocks": blocks}


def main():
    fx = load_fixture()
    import tempfile
    audit_path = os.path.join(tempfile.gettempdir(), "wiki_debrief_audit.jsonl")
    if os.path.exists(audit_path):
        os.remove(audit_path)
    session, results, debrief = run_constitution(fx, audit_path)
    payload = build_blocks(fx, session, debrief)
    validate_blockkit(payload)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Validated ✓ and wrote {OUT} ({len(payload['blocks'])} blocks)")
    # Echo the headline numbers so they can be checked against DEMO_SCRIPT.md.
    m = final_metrics(fx, fx["rounds"][-1]["candidates"].index(debrief["winner"]))
    print("bridged min_group_support={:.2f} minority_survival={:.2f} mean={:.2f}".format(
        m["min_group_support"], m["minority_survival"], m["mean_endorsement"]))
    print("uptake:", uptake(fx))


if __name__ == "__main__":
    main()
