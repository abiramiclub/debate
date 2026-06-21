# HONEYBEE CONSTITUTION — Deliberation Mediator (Karpaty Wiki, distilled)

**Version:** 0.1 (v1 build target)
**Owner:** Abirami Club
**Role in system:** This is the DETERMINISTIC layer. It conducts the process and owns every fairness guarantee. The probabilistic mediator ("Vicky") only executes language tasks this constitution invokes; its outputs are always selected/bounded by the rules below.

---

## 0. Invariants (never violate)

1. **Mediate, do not debate.** The mediator never holds or advocates a position on the topic under discussion.
2. **Deterministic conducts, probabilistic executes.** Anything that must be fair, auditable, or reproducible is decided here, in code. The LLM is invoked only for language understanding/generation and never trusted to be fair on its own.
3. **Fairness is a property of the process, not the outcome.** No rule optimizes for any particular conclusion.
4. **Inject information, never steer opinion.** The agent may add vetted information and surface neglected views. It may never nudge participants toward a conclusion. (Hard rule — violating this turns a fairness tool into an astroturfing tool.)
5. **Consensual blind.** Participants opt in to a format where identities — including human vs. AI — are hidden, with a debrief afterward. No covert AI participation.
6. **Everything is logged.** Every state transition and every agent contribution (with source) is appended to an immutable JSONL audit.

---

## 1. The five governing mechanisms (biology → principle → rule)

| # | Biological fact (honeybee) | Abstracted principle | Deterministic system rule |
|---|---|---|---|
| 1 | Scouts assess sites **independently before** advertising | Break anchoring before exposure | Collect each participant's private position + confidence (1–5) by DM/modal. No participant sees any other position until all reads are in OR `T_read` elapses (default 120s). |
| 2 | Waggle-dance vigor is **proportional to site quality** | Surface by merit, not volume or recency | A candidate statement's visibility weight = its bridging score (§2), never its post count or how recently it was raised. |
| 3 | **Cross-inhibition** (stop-signals) prevents premature lock-in | Counter-pressure against fast consensus | If the leading candidate's weighted support crosses `V_ci` (default 50%) within the first reveal round AND no new information has entered since the last round → inject a minority steelman (§5) and require one more round before any quorum check. |
| 4 | Swarm commits at a **quorum**, not unanimity | Decide at a threshold; tolerate dissent | Decision is reached when a candidate's bridging-adjusted weighted support ≥ `Q` (default 0.66) AND at least one cross-inhibition round has elapsed. Threshold-based ⇒ N-agnostic (works for any participant count). |
| 5 | Falling **queen pheromone** triggers supersedure (new queen) | Detect stale/failing deliberation and refresh | If `echo_index` is high AND `information_uptake` is low for `R` consecutive rounds (default 2) → trigger a structural refresh: re-collect independent reads and reframe the question. |

---

## 2. Aggregation rule — bridging-based ranking (the fairness guarantee)

The winning statement is selected by **group-informed (bridging) consensus**, which rewards agreement *across* opinion groups rather than within the largest one. This is the deployed anti-majority-tyranny method from Pol.is / Remesh / Community Notes.

For a participant set partitioned into opinion groups `g`:

```
P(g, c) = (2 + N_agree(g, c)) / (1 + N_voted(g, c))      # smoothed agreement of group g with candidate c
bridging_score(c) = PRODUCT over all groups g of P(g, c)  # high only if liked across groups
representativeness(g, c) = P(g_complement, c) / P(g, c)    # diagnostic: who a statement over/under-represents
```

- Winner = `argmax_c bridging_score(c)`.
- Opinion groups are formed by clustering participant reads (k-means / agglomerative on embedding of reads; `k` chosen by silhouette, capped at 4 for v1).
- This selection is deterministic given the agreement estimates. The agreement estimates themselves come from the probabilistic layer (§ mediator), but the *choice* is made here.

---

## 3. Anti-sycophancy weighting (deterministic)

Directly inverts the failure mode of participant-agents (drift toward last speaker / forming consensus).

- **Recency down-weight:** contributions are weighted by `w_recency` (default 0.5) — the most recent input does NOT get extra influence.
- **Minority visibility floor:** any credible view held by ≥1 participant is guaranteed surfacing at least once before quorum, regardless of support level.
- **Phase-tuned convergence/dissent balance (drone boids-style):** the ratio of convergence-pressure to dissent-preservation adapts by phase.

| Phase | Convergence weight | Dissent-preservation weight |
|---|---|---|
| Early (reveal → first cross-inhibition) | 0.3 | 0.7 |
| Mid (subsequent rounds) | 0.5 | 0.5 |
| Late (approaching quorum) | 0.7 | 0.3 |

---

## 4. Protocol state machine (deterministic)

```
CONSENT
  → COLLECT_READS        (private read + confidence; no peeking; T_read timeout)
  → REVEAL               (positions surfaced by bridging weight, not recency)
  → [INFO_INJECTION]     (optional, gated; vetted+sourced via RTS; §5)
  → CROSS_INHIBITION     (minority steelman; counter-pressure; §1 rule 3)
  → QUORUM_CHECK
      ├─ quorum met (Q, ≥1 CI round)        → DEBRIEF
      ├─ stale (echo high + uptake low, R)  → refresh: back to COLLECT_READS (§1 rule 5)
      └─ otherwise                          → back to CROSS_INHIBITION
  → DEBRIEF              (metrics + reveal which participants were agents + audit)
```

All transitions are pure functions of logged state. No LLM call decides a transition.

---

## 5. Information injection (deterministic gate, probabilistic content)

- Source must be **vetted and citable**, retrieved via the Real-Time Search API. The source URL/citation is written to the audit.
- Injected through an anonymous handle so it lands like any other contribution.
- Content may be a fact or a steelman of a neglected view (generated by the mediator), but **must not contain an advocacy of any conclusion** (Invariant 4). A position-detection check runs on injected text before posting; if it advocates, it is rejected and regenerated.

---

## 6. Open Space role behaviors (optional, layer on top)

- **Butterfly** = the reflective pause; implemented as the `COLLECT_READS` independent-read step.
- **Bumblebee** = cross-pollination; the mediator may carry one point from a sub-thread into another that lacks it.
- **Law of Two Feet** = disengagement is signal; a dead thread or a performative pile-on is NOT treated as genuine quorum.

---

## 7. Governance & audit (deterministic)

- **Audit (JSONL):** one line per event — `{ts, session_id, state, actor_handle, actor_type, action, payload_hash, source}`.
- **Position-neutrality check:** every mediator output passes a classifier that rejects topic-position advocacy before it reaches the channel.
- **Anonymization map** (`handle ↔ real user`, `handle ↔ human|agent`) is stored server-side only, access-controlled, and revealed only at DEBRIEF.

---

## 8. Default parameters (all tunable)

| Param | Default | Meaning |
|---|---|---|
| `T_read` | 120s | independent-read collection window |
| `V_ci` | 0.50 | cross-inhibition trigger (fast-consensus velocity) |
| `Q` | 0.66 | quorum threshold (bridging-adjusted weighted support) |
| `R` | 2 | stale-rounds before structural refresh |
| `w_recency` | 0.5 | recency down-weight |
| `N_candidates` | 8 | common-ground statements generated per round |
| `k_max` | 4 | max opinion clusters |
| `confidence_scale` | 1–5 | per-participant confidence |

---

## 9. Sources (the Karpaty wiki distills these)

- **Honeybee swarm decision-making** — Seeley, *Honeybee Democracy* (quorum sensing, waggle dance, cross-inhibition, supersedure).
- **Swarm coordination / weighting** — Reynolds' Boids (separation/alignment/cohesion); Raft consensus for fault-tolerant distributed agreement.
- **AI mediation** — Tessler, Bakker et al., "Habermas Machine," *Science* 2024 (generative + reward model + Schulze-method selection; caucus mediation).
- **Bridging consensus** — Pol.is / The Computational Democracy Project (group-informed consensus); Remesh (elicitation inference, bridging-based ranking).
- **Facilitation philosophy** — Harrison Owen, Open Space Technology (minimal facilitator; Law of Two Feet; bumblebees/butterflies).
- **Failure mode being countered** — arXiv 2506.11825 (LLM debate agents form echo chambers and intensify).
