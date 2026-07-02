"""Block Kit rendering — the two voices, kept distinct.

  Wiki  = the deterministic chair: terse, monospace, procedural.
  Vicky = the probabilistic voice: warm, plain-language.

The gate strikes only read as gates because there are two voices. During the
debate the options stay generic ("a chatbot" vs "a wiki"); the Wiki/Vicky
parallel is only detonated at the closer.
"""

import json
import os

_DEBRIEF_JSON = os.path.join(os.path.dirname(__file__), "..", "demo", "debrief_blockkit.json")

CONSENT_NOTICE = (
    "This is a *consensual-blind* deliberation. You'll post under an anonymous "
    "tree-handle. Some participants may be AI — you won't know which until the "
    "debrief. Every step is logged to an immutable audit. Opt in to join."
)


def _section(md: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": md}}


def _context(md: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": md}]}


# --- the two voices ----------------------------------------------------------

def vicky(text: str) -> list[dict]:
    """Warm, plain-language mediator voice."""
    return [_section(f"💬 *Vicky*  {text}")]


def wiki(text: str, code: bool = True) -> list[dict]:
    """Terse, procedural deterministic chair. Procedural output is monospace."""
    body = f"```{text}```" if code else f"`{text}`"
    return [_section(f"🔒 *Wiki*\n{body}")]


def wiki_strike(line: str) -> list[dict]:
    """A visible gate strike from the audit (neutrality / prediction)."""
    return [_section(f"🔒 *Wiki*  ⨯ `{line}`")]


def neutral_evidence(handle: str, text: str, source: str) -> list[dict]:
    """A sourced fact injected under a neutral handle (via Real-Time Search)."""
    return [
        _section(f"*@{handle}*  _(neutral evidence · via Real-Time Search)_\n{text}"),
        _context(f"source: <{source}|#incidents-postmortem thread>"),
    ]


# --- flow blocks -------------------------------------------------------------

def consent_blocks(question: str, action_id: str = "consent_join") -> list[dict]:
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "🗳️ A decision to make"}},
        _section(f"*Question:* {question}"),
        _section(CONSENT_NOTICE),
        {"type": "actions", "elements": [{
            "type": "button", "style": "primary",
            "text": {"type": "plain_text", "text": "Consent & join"},
            "action_id": action_id,
        }]},
    ]


def handles_blocks(handles: list[str]) -> list[dict]:
    joined = " · ".join(f"`{h}`" for h in handles)
    return [_section(f"*Neutral handles assigned:* {joined}\nYou'll be DM'd a private "
                     f"card for your read — nobody sees another's until reveal.")]


def read_modal(session_id: str, handle: str) -> dict:
    """A private modal: read text + confidence. Hidden before reveal."""
    return {
        "type": "modal",
        "callback_id": "submit_read",
        "private_metadata": json.dumps({"session_id": session_id, "handle": handle}),
        "title": {"type": "plain_text", "text": "Your private read"},
        "submit": {"type": "plain_text", "text": "Submit"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            _section(f"You are *{handle}*. Nobody sees this until all reads are in."),
            {"type": "input", "block_id": "read", "label":
                {"type": "plain_text", "text": "How should we build it? (your honest read)"},
             "element": {"type": "plain_text_input", "action_id": "text", "multiline": True}},
            {"type": "input", "block_id": "confidence", "label":
                {"type": "plain_text", "text": "Confidence (1–5)"},
             "element": {"type": "static_select", "action_id": "value",
                         "options": [{"text": {"type": "plain_text", "text": str(i)},
                                      "value": str(i)} for i in range(1, 6)]}},
        ],
    }


def reveal_blocks(candidates: list[str]) -> list[dict]:
    lines = "\n".join(f"• {c}" for c in candidates)
    return vicky("Reads are in. Two camps on the table — names withheld so nobody "
                 "defers to the biggest stock grants:") + [_section(lines)]


def debrief_blocks() -> list[dict]:
    """Render the validated Block Kit debrief (demo/debrief_blockkit.json)."""
    with open(_DEBRIEF_JSON) as f:
        return json.load(f)["blocks"]


def strike_line_for(action: str, payload_hint: str = "") -> str:
    """Map an audit gate action to its on-screen strike line."""
    if action == "neutrality_rejected":
        return "mediator output rejected — advocacy detected · neutrality gate"
    if action == "prediction_blocked":
        return "forecast suppressed — calling the outcome is a red line (bandwagon risk)"
    return action
