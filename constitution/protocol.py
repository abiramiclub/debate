"""The protocol state machine — the conductor (constitution section 4).

This is the deterministic core. It drives the deliberation through its states,
INVOKES the mediator for every language task, and makes every fairness decision
itself. No LLM call decides a state transition.

State flow:
    CONSENT -> COLLECT_READS -> REVEAL
        -> CROSS_INHIBITION -> QUORUM_CHECK
            -> quorum met            -> DEBRIEF
            -> stale (echo+low uptake) -> refresh (back to COLLECT_READS)
            -> otherwise             -> next round (CROSS_INHIBITION)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from mediator.base import Mediator, Read

from .audit import AuditLog
from .bridging import cluster_participants, rank_candidates
from .config import DEFAULT, Config
from .weighting import phase_index, raw_support, weighted_support

NEUTRAL_HANDLES = [
    "Birch", "Maple", "Cedar", "Aspen", "Willow", "Hazel",
    "Rowan", "Linden", "Alder", "Hawthorn", "Spruce", "Elm",
]


class State(str, Enum):
    CONSENT = "CONSENT"
    COLLECT_READS = "COLLECT_READS"
    REVEAL = "REVEAL"
    CROSS_INHIBITION = "CROSS_INHIBITION"
    QUORUM_CHECK = "QUORUM_CHECK"
    DEBRIEF = "DEBRIEF"
    DONE = "DONE"


@dataclass
class RoundResult:
    round_idx: int
    candidates: list[str]
    winner_text: str
    winner_support: float
    group_labels: list[int]
    cross_inhibition_fired: bool
    steelman: Optional[str]
    echo_flag: bool
    echo_reason: str
    decision: str  # "QUORUM_MET" | "CONTINUE" | "STALE_REFRESH"


@dataclass
class Participant:
    user_id: str
    handle: str
    actor_type: str  # "human" | "agent"


class Session:
    """One deliberation. Drive it: start() -> submit_read()* -> deliberate() -> debrief()."""

    def __init__(
        self,
        session_id: str,
        mediator: Mediator,
        audit_path: str,
        cfg: Config = DEFAULT,
    ):
        self.session_id = session_id
        self.mediator = mediator
        self.cfg = cfg
        self.audit = AuditLog(audit_path, session_id)
        self.state = State.CONSENT
        self.participants: list[Participant] = []
        self._by_handle: dict[str, Participant] = {}
        self.reads: list[Read] = []
        self._prev_round_msgs: list[str] = []
        self._ci_rounds_elapsed = 0
        self._stale_streak = 0
        self.winner_text: Optional[str] = None

    # --- CONSENT -------------------------------------------------------------
    def start(self, participants: list[tuple[str, str]]) -> None:
        """participants: list of (user_id, actor_type) where actor_type is
        'human' or 'agent'. Assigns neutral handles and records consent."""
        for i, (user_id, actor_type) in enumerate(participants):
            handle = NEUTRAL_HANDLES[i % len(NEUTRAL_HANDLES)]
            p = Participant(user_id=user_id, handle=handle, actor_type=actor_type)
            self.participants.append(p)
            self._by_handle[handle] = p
        self.audit.log(self.state, "system", "system", "consent_recorded",
                       payload={"n": len(participants)})
        self.state = State.COLLECT_READS

    # --- COLLECT_READS -------------------------------------------------------
    def submit_read(self, handle: str, text: str, confidence: int) -> None:
        if self.state != State.COLLECT_READS:
            raise RuntimeError(f"Cannot submit read in state {self.state}")
        if handle not in self._by_handle:
            raise KeyError(f"Unknown handle {handle}")
        self.reads.append(Read(handle=handle, text=text, confidence=confidence))
        self.audit.log(self.state, handle, self._by_handle[handle].actor_type,
                       "store_read", payload={"confidence": confidence, "text": text})

    # --- REVEAL + rounds -----------------------------------------------------
    def deliberate(self, max_rounds: int = 5,
                   discussion_by_round: Optional[list[list[str]]] = None) -> list[RoundResult]:
        """Run reveal + cross-inhibition + quorum rounds until a decision."""
        if self.state != State.COLLECT_READS:
            raise RuntimeError(f"Cannot deliberate in state {self.state}")
        if len(self.reads) < 2:
            raise RuntimeError("Need at least 2 reads to deliberate")
        self.state = State.REVEAL
        results: list[RoundResult] = []

        for round_idx in range(max_rounds):
            discussion = (discussion_by_round[round_idx]
                          if discussion_by_round and round_idx < len(discussion_by_round)
                          else [])

            # 1-2. Mediator proposes (the ONLY language work).
            candidates = self.mediator.synthesize_candidates(self.reads, self.cfg.N_candidates)
            agreement = self.mediator.predict_agreement(self.reads, candidates)
            self.audit.log(State.REVEAL, "Vicky", "agent", "synthesize+predict",
                           payload={"n_candidates": len(candidates)})

            # 3-4. Constitution selects (deterministic).
            labels = cluster_participants(agreement, self.cfg.k_max,
                                          self.cfg.min_n_for_clustering)
            scored = rank_candidates(agreement, labels)
            winner = scored[0]
            winner_text = candidates[winner.index]

            near = raw_support(scored) >= self.cfg.Q
            phase = phase_index(round_idx, near)
            support = weighted_support(scored, phase, self.cfg)
            self.audit.log(State.REVEAL, "system", "system", "rank_bridging",
                           payload={"winner": winner_text, "support": support,
                                    "groups": labels})

            # CROSS_INHIBITION: counter-pressure against fast consensus.
            self.state = State.CROSS_INHIBITION
            ci_fired = False
            steelman = None
            if round_idx == 0 and support >= self.cfg.V_ci and self._ci_rounds_elapsed == 0:
                steelman = self.mediator.steelman_minority(self.reads, labels)
                ci_fired = True
                self.audit.log(State.CROSS_INHIBITION, "Vicky", "agent",
                               "steelman_minority", payload={"text": steelman})
            self._ci_rounds_elapsed += 1

            # Echo detection on what was surfaced this round (+ any discussion).
            current_msgs = candidates + ([steelman] if steelman else []) + discussion
            echo_flag, echo_reason = self.mediator.detect_echo(self._prev_round_msgs, current_msgs)
            self._prev_round_msgs = current_msgs
            if echo_flag:
                self._stale_streak += 1
            else:
                self._stale_streak = 0

            # QUORUM_CHECK (deterministic).
            self.state = State.QUORUM_CHECK
            quorum_met = support >= self.cfg.Q and self._ci_rounds_elapsed >= 1 and not ci_fired
            stale = self._stale_streak >= self.cfg.R
            if quorum_met:
                decision = "QUORUM_MET"
            elif stale:
                decision = "STALE_REFRESH"
            else:
                decision = "CONTINUE"
            self.audit.log(State.QUORUM_CHECK, "system", "system", "check_quorum",
                           payload={"decision": decision, "support": support,
                                    "stale_streak": self._stale_streak})

            results.append(RoundResult(
                round_idx=round_idx, candidates=candidates, winner_text=winner_text,
                winner_support=support, group_labels=labels, cross_inhibition_fired=ci_fired,
                steelman=steelman, echo_flag=echo_flag, echo_reason=echo_reason,
                decision=decision,
            ))

            if decision in ("QUORUM_MET", "STALE_REFRESH"):
                self.winner_text = winner_text if decision == "QUORUM_MET" else None
                break

        self.state = State.DEBRIEF
        return results

    # --- DEBRIEF -------------------------------------------------------------
    def debrief(self) -> dict:
        """Reveal the anonymization map, the outcome, and the audit trail."""
        self.audit.log(State.DEBRIEF, "system", "system", "debrief")
        self.state = State.DONE
        return {
            "session_id": self.session_id,
            "winner": self.winner_text,
            "reached_quorum": self.winner_text is not None,
            "participants": [
                {"handle": p.handle, "user_id": p.user_id, "actor_type": p.actor_type}
                for p in self.participants
            ],
            "audit": self.audit.read_all(),
        }
