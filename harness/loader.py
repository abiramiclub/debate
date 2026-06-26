"""Load the Habermas Machine candidate-comparison data and group it into
deliberation *sessions* the engine can consume.

A session = one set of candidate group-statements that several human participants
each ranked. We convert each participant's ranking into an endorsement vector and
stack them into an endorsement matrix (participants x candidates), which is
exactly the input the constitution's bridging ranker expects.

Data source: DeepMind Habermas Machine dataset (CC-BY 4.0), downloaded locally
and gitignored — not redistributed here. See harness/README.md.

Authoritative rank convention (DeepMind habermas_machine/utils.py): rank 0 is the
MOST preferred candidate. So endorsement = (max_rank - rank) / max_rank.
"""

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

HUMAN = "HUMAN_CITIZEN"
DATA_PATH = "data/habermas/hm_all_candidate_comparisons.parquet"


@dataclass
class Session:
    session_id: str
    candidate_ids: list[str]
    endorsement: list[list[float]]   # [participant][candidate] in [0, 1]
    participant_ids: list[str]
    display_order: list[int]         # candidate indices in their display order
    texts: list[str]                 # candidate texts ("" if unavailable)

    @property
    def n_participants(self) -> int:
        return len(self.endorsement)

    @property
    def n_candidates(self) -> int:
        return len(self.candidate_ids)


def _endorsement_from_ranks(ranks: list[int]) -> list[float]:
    max_rank = max(ranks) if ranks else 0
    if max_rank == 0:
        return [1.0] * len(ranks)  # everyone tied at top (degenerate)
    return [(max_rank - r) / max_rank for r in ranks]


@lru_cache(maxsize=1)
def _load_raw() -> pd.DataFrame:
    df = pd.read_parquet(DATA_PATH)
    df = df[df["rankings.metadata.provenance"] == HUMAN]
    df = df[df["rankings.candidate_ids"].notna() & df["rankings.numerical_ranks"].notna()]
    return df


def _build_text_map(df: pd.DataFrame) -> dict[str, str]:
    """Best-effort candidate_id -> text, assembled from each row's own authored
    candidate. Only used for illustrative examples, never for the numbers."""
    text_map: dict[str, str] = {}
    for _, r in df.iterrows():
        authors = r.get("candidates.metadata.participant_id")
        ids = r["candidates.metadata.id"]
        own = r.get("candidates.text")
        rid = r["rankings.metadata.participant_id"]
        if authors is not None and own and ids is not None:
            for cid, author in zip(ids, authors):
                if author == rid and cid not in text_map:
                    text_map[cid] = str(own)
    return text_map


def load_sessions(min_participants: int = 4, min_candidates: int = 3,
                  with_texts: bool = False) -> list[Session]:
    """Group human rankings into sessions keyed by their exact candidate set."""
    df = _load_raw()
    text_map = _build_text_map(df) if with_texts else {}

    df = df.copy()
    df["_ckey"] = df["rankings.candidate_ids"].apply(lambda a: tuple(a))

    sessions: list[Session] = []
    for ckey, sub in df.groupby("_ckey"):
        cand_ids = list(ckey)
        n_c = len(cand_ids)
        if n_c < min_candidates:
            continue
        # One ranking per participant (dedupe; keep first).
        seen: set[str] = set()
        endorsement: list[list[float]] = []
        participant_ids: list[str] = []
        for _, r in sub.iterrows():
            pid = r["rankings.metadata.participant_id"]
            if pid in seen:
                continue
            ranks = list(r["rankings.numerical_ranks"])
            ids = list(r["rankings.candidate_ids"])
            if len(ranks) != n_c or sorted(ids) != sorted(cand_ids):
                continue
            # Align this participant's ranks to the canonical candidate order.
            rank_by_id = dict(zip(ids, ranks))
            aligned = [rank_by_id[cid] for cid in cand_ids]
            endorsement.append(_endorsement_from_ranks(aligned))
            participant_ids.append(pid)
            seen.add(pid)
        if len(endorsement) < min_participants:
            continue
        sessions.append(Session(
            session_id=hash_key(cand_ids),
            candidate_ids=cand_ids,
            endorsement=endorsement,
            participant_ids=participant_ids,
            display_order=list(range(n_c)),
            texts=[text_map.get(cid, "") for cid in cand_ids],
        ))
    return sessions


def hash_key(cand_ids: list[str]) -> str:
    return cand_ids[0][:8] + f"+{len(cand_ids)}c"
