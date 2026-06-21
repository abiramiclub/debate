"""A deterministic, no-LLM mediator for testing.

Implements the `Mediator` interface with simple, explainable heuristics (token
overlap) instead of a language model. It lets you run the whole constitution
loop offline — no API key, no network, fully reproducible — so you can see the
mediator's *role* in the pipeline before wiring up a real LLM backend.

It is intentionally dumb. The point is the seam, not the language quality.
"""

import re

from .base import Mediator, Read

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "to", "of", "in", "on", "for",
    "is", "are", "be", "we", "i", "it", "this", "that", "with", "as", "at", "by",
    "should", "would", "could", "can", "will", "not", "no", "do", "does", "than",
    "more", "less", "about", "our", "their", "they", "you", "he", "she", "them",
}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# Templating boilerplate that carries no opinion content; stripped before we
# decide what a candidate is "about".
_BOILERPLATE = {
    "agree", "real", "consideration", "shared", "path", "respects", "both",
    "share", "appears", "first", "here", "matters", "matter", "consider",
}


def _theme_tokens(text: str) -> set[str]:
    return _tokens(text) - _BOILERPLATE


class FakeMediator(Mediator):
    def synthesize_candidates(self, reads: list[Read], n: int) -> list[str]:
        # Frequency-rank content tokens across all reads, then template a mix of
        # single-theme and bridged (two-theme) statements.
        freq: dict[str, int] = {}
        for r in reads:
            for t in _tokens(r.text):
                freq[t] = freq.get(t, 0) + 1
        themes = [t for t, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))]
        candidates: list[str] = []
        for t in themes:
            candidates.append(f"We can agree that {t} is a real consideration here.")
            if len(candidates) >= n:
                break
        # Add a couple of explicitly bridging statements pairing the top themes.
        for i in range(0, min(len(themes), 4) - 1, 2):
            if len(candidates) >= n:
                break
            candidates.append(
                f"A shared path respects both {themes[i]} and {themes[i + 1]}."
            )
        return candidates[:n] if candidates else ["We share more than it first appears."]

    def predict_agreement(self, reads: list[Read], candidates: list[str]) -> list[list[float]]:
        # A read "agrees" with a candidate to the extent the read covers the
        # candidate's theme(s). Recall over theme tokens, so a two-theme bridging
        # statement is partially endorsed by BOTH camps (each covers one theme),
        # which is exactly how a bridge should behave.
        cand_themes = [_theme_tokens(c) for c in candidates]
        matrix: list[list[float]] = []
        for r in reads:
            rt = _tokens(r.text)
            conf = max(1, min(5, r.confidence)) / 5.0
            row = []
            for theme in cand_themes:
                recall = len(rt & theme) / len(theme) if theme else 0.0
                agreement = min(1.0, (0.2 + 0.8 * recall) * (0.85 + 0.15 * conf))
                row.append(agreement)
            matrix.append(row)
        return matrix

    def steelman_minority(self, reads: list[Read], group_labels: list[int]) -> str:
        if not reads:
            return "No minority view to steelman."
        # Least-supported credible view = the read whose themes overlap least with
        # everyone else's (the most isolated position).
        all_tokens = [_tokens(r.text) for r in reads]
        isolation: list[float] = []
        for i, ti in enumerate(all_tokens):
            others = [_jaccard(ti, all_tokens[j]) for j in range(len(reads)) if j != i]
            isolation.append(sum(others) / len(others) if others else 0.0)
        minority = reads[isolation.index(min(isolation))]
        return (
            f"The strongest case for the least-represented view: {minority.text} "
            f"This deserves a fair hearing before the group commits."
        )

    def detect_echo(self, previous_round: list[str], current_round: list[str]) -> tuple[bool, str]:
        prev = set().union(*[_tokens(m) for m in previous_round]) if previous_round else set()
        curr = set().union(*[_tokens(m) for m in current_round]) if current_round else set()
        if not curr:
            return False, "No current-round content to assess."
        novel = curr - prev
        novel_ratio = len(novel) / len(curr)
        if novel_ratio < 0.2:
            return True, (
                f"Only {novel_ratio:.0%} of this round's content is new "
                f"({len(novel)}/{len(curr)} tokens). Discussion is intensifying "
                f"without new information."
            )
        return False, f"{novel_ratio:.0%} new content; information is still entering."
