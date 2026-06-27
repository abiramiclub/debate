"""Real LLM mediator behind the frozen 4-method interface.

Implements `Mediator` using an Anthropic-compatible client (Claude in the cloud,
or a qwen endpoint via OpenClaw that speaks the same API). The constitution still
makes every decision; this only does the language work.

Credentials are supplied by the deployment (API key / OpenClaw base_url). The
adapter is backend-agnostic via the injected `client`, so the same code serves
the cloud Claude and local qwen variants (locked decision #2).
"""

import json
import re

from .base import Mediator, Read

_NEUTRALITY = (
    "You are a NEUTRAL deliberation mediator. You never advocate a position on the "
    "topic. You only do language work: summarizing, phrasing common ground, or "
    "steelmanning a view on request. Never push participants toward a conclusion."
)


def _default_client():
    import anthropic
    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL


def _extract_json(text: str):
    """Best-effort: pull the first JSON value out of a model response."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1).strip()
    start = min((i for i in (text.find("["), text.find("{")) if i != -1), default=0)
    return json.loads(text[start:])


class ClaudeMediator(Mediator):
    def __init__(self, client=None, model: str = "claude-opus-4-8"):
        self._client = client
        self._model = model

    def _complete(self, user: str, max_tokens: int = 1024) -> str:
        client = self._client or _default_client()
        msg = client.messages.create(
            model=self._model, max_tokens=max_tokens, system=_NEUTRALITY,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text

    def synthesize_candidates(self, reads: list[Read], n: int) -> list[str]:
        body = "\n".join(f"- {r.text} (confidence {r.confidence})" for r in reads)
        out = self._complete(
            f"Here are participants' private reads on a shared question:\n{body}\n\n"
            f"Propose {n} candidate COMMON-GROUND statements that different camps could "
            f"accept. Neutral, no advocacy. Return a JSON array of strings only.")
        data = _extract_json(out)
        return [str(s) for s in data][:n]

    def predict_agreement(self, reads: list[Read], candidates: list[str]) -> list[list[float]]:
        rlines = "\n".join(f"P{i}: {r.text}" for i, r in enumerate(reads))
        clines = "\n".join(f"C{j}: {c}" for j, c in enumerate(candidates))
        out = self._complete(
            f"Participants:\n{rlines}\n\nCandidate statements:\n{clines}\n\n"
            f"For each participant, estimate agreement with each candidate in [0,1]. "
            f"Return a JSON array of {len(reads)} rows × {len(candidates)} numbers only.",
            max_tokens=2048)
        matrix = _extract_json(out)
        return [[float(x) for x in row] for row in matrix]

    def steelman_minority(self, reads: list[Read], group_labels: list[int]) -> str:
        sizes: dict[int, int] = {}
        for lab in group_labels:
            sizes[lab] = sizes.get(lab, 0) + 1
        minority_lab = min(sizes, key=lambda k: sizes[k])
        minority = "\n".join(f"- {r.text}" for r, lab in zip(reads, group_labels)
                             if lab == minority_lab)
        return self._complete(
            f"These are the least-represented participants' views:\n{minority}\n\n"
            f"Write the STRONGEST, fair statement of this minority view in 2-3 "
            f"sentences, so the group hears it before deciding. Do not advocate "
            f"for it as the answer; present it for fair consideration.").strip()

    def detect_echo(self, previous_round: list[str], current_round: list[str]) -> tuple[bool, str]:
        out = self._complete(
            f"Previous round:\n{previous_round}\n\nCurrent round:\n{current_round}\n\n"
            f"Is the discussion intensifying WITHOUT new information entering? "
            f'Return JSON {{"echo": true|false, "reason": "..."}} only.')
        data = _extract_json(out)
        return bool(data["echo"]), str(data.get("reason", ""))
