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
from .evidence import Evidence, EvidenceSource
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
    INFO_INJECTION = "INFO_INJECTION"
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
    minority_present: bool
    steelman: Optional[str]
    echo_flag: bool
    echo_reason: str
    decision: str  # "QUORUM_MET" | "CONTINUE" | "STALE_REFRESH" | "EVIDENCE_INJECTED"
    evidence: Optional[Evidence] = None


def _minority_present(labels: list[int]) -> bool:
    """True when clustering yields more than one opinion group AND at least one
    group is strictly smaller than the largest (a genuine minority cluster).
    Below the clustering floor (each participant their own group) all groups are
    equal-sized singletons, so this is False — no real minority structure."""
    if len(set(labels)) <= 1:
        return False
    sizes: dict[int, int] = {}
    for lab in labels:
        sizes[lab] = sizes.get(lab, 0) + 1
    return min(sizes.values()) < max(sizes.values())


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
        evidence_source: Optional[EvidenceSource] = None,
    ):
        self.session_id = session_id
        self.mediator = mediator
        self.cfg = cfg
        self.evidence_source = evidence_source
        self.audit = AuditLog(audit_path, session_id)
        self.state = State.CONSENT
        self.participants: list[Participant] = []
        self._by_handle: dict[str, Participant] = {}
        self.reads: list[Read] = []
        self._prev_round_msgs: list[str] = []
        self._ci_rounds_elapsed = 0
        self._stale_streak = 0
        self._injected = False
        self.injected_evidence: list[Evidence] = []
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
    def deliberate(self, max_rounds: int = 6,
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
            self.audit.log(State.REVEAL, "mediator", "agent", "synthesize+predict",
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

            # CROSS_INHIBITION stage. Two distinct rules live here:
            self.state = State.CROSS_INHIBITION

            # (a) Minority steelman: fires WHENEVER a minority cluster exists
            #     (constitution §3 minority-visibility floor) — not only as the
            #     cross-inhibition payload.
            minority = _minority_present(labels)
            steelman = None
            if minority:
                steelman = self.mediator.steelman_minority(self.reads, labels)
                self.audit.log(State.CROSS_INHIBITION, "mediator", "agent",
                               "steelman_minority", payload={"text": steelman})

            # (b) Cross-inhibition trigger: counter-pressure against a fast /
            #     premature consensus in the first reveal round (§1 rule 3).
            ci_fired = False
            if round_idx == 0 and support >= self.cfg.V_ci:
                ci_fired = True
                self.audit.log(State.CROSS_INHIBITION, "system", "system",
                               "cross_inhibition", payload={"support": support,
                                                            "v_ci": self.cfg.V_ci})
            self._ci_rounds_elapsed += 1

            # Echo detection measures whether the DELIBERATION content (the
            # positions on the table + any human discussion) brings new
            # information. It deliberately excludes the mediator's own steelman
            # scaffolding, which repeats and would otherwise mask genuine novelty.
            current_msgs = candidates + discussion
            echo_flag, echo_reason = self.mediator.detect_echo(self._prev_round_msgs, current_msgs)
            self._prev_round_msgs = current_msgs
            if echo_flag:
                self._stale_streak += 1
            else:
                self._stale_streak = 0

            # QUORUM_CHECK (deterministic).
            self.state = State.QUORUM_CHECK
            quorum_met = support >= self.cfg.Q and self._ci_rounds_elapsed >= 1 and not ci_fired
            deadlock = self._stale_streak >= self.cfg.R

            evidence: Optional[Evidence] = None
            if quorum_met:
                decision = "QUORUM_MET"
            elif deadlock and self.evidence_source is not None and not self._injected:
                # Deadlock/echo CONSEQUENCE: inject one sourced fact (§5).
                evidence = self._inject_evidence(round_idx)
                decision = "EVIDENCE_INJECTED" if evidence else "STALE_REFRESH"
            elif deadlock:
                decision = "STALE_REFRESH"
            else:
                decision = "CONTINUE"
            self.audit.log(State.QUORUM_CHECK, "system", "system", "check_quorum",
                           payload={"decision": decision, "support": support,
                                    "stale_streak": self._stale_streak})

            results.append(RoundResult(
                round_idx=round_idx, candidates=candidates, winner_text=winner_text,
                winner_support=support, group_labels=labels, cross_inhibition_fired=ci_fired,
                minority_present=minority, steelman=steelman, echo_flag=echo_flag,
                echo_reason=echo_reason, decision=decision, evidence=evidence,
            ))

            if decision in ("QUORUM_MET", "STALE_REFRESH"):
                self.winner_text = winner_text if decision == "QUORUM_MET" else None
                break

        self.state = State.DEBRIEF
        return results

    def _inject_evidence(self, round_idx: int) -> Optional[Evidence]:
        """INFO_INJECTION: pull one vetted, sourced fact and inject it under a
        neutral handle. The source is written to the audit. Resets the echo
        streak because new information has entered the room."""
        self.state = State.INFO_INJECTION
        ev = self.evidence_source.fetch({"reads": self.reads, "round": round_idx})
        if ev is None:
            return None
        self._injected = True
        self.injected_evidence.append(ev)
        self._stale_streak = 0
        # Injected fact lands like any other contribution (anonymous handle).
        self.reads.append(Read(handle=ev.handle, text=ev.text, confidence=3))
        self.audit.log(State.INFO_INJECTION, ev.handle, "agent", "inject_evidence",
                       payload={"text": ev.text}, source=ev.source)
        return ev

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
            "injected_evidence": [
                {"text": e.text, "source": e.source, "handle": e.handle}
                for e in self.injected_evidence
            ],
            "audit": self.audit.read_all(),
        }
