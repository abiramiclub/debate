# The Wiki — the deliberation constitution (deterministic rule set)

**Version:** 0.1 (v1 build target)
**Owner:** Abirami Club
**Role in system:** This is **the Wiki** — the DETERMINISTIC constitution. It conducts the process and owns every fairness guarantee. The probabilistic mediator, **Vicky**, only executes language tasks the Wiki invokes; her outputs are always selected/bounded by the rules below.

> **Naming.** The deterministic layer is **the Wiki** (the fixed rule set; originally nicknamed *the Karpaty Wiki*); the probabilistic layer is **Vicky** (the mediator). The pun is deliberate — it began as a voice-dictation mishearing of "Wiki" as "Vicky", which turned out to be a perfect label for *deterministic vs. not*. Code modules are named `constitution/` and `mediator/`; Wiki and Vicky are their nicknames in the docs, audit log, and channel.

> **Positioning.** This is a *mediation* tool grounded in computational-deliberation research (Pol.is, the Habermas Machine, Community Notes) — it works **against** groupthink. It is not a swarm / hive-mind / collective-intelligence system; the design principle is the opposite (preserve dissent, never converge a crowd into one signal).

---

## 0. Invariants (never violate)

1. **Mediate, do not debate.** Vicky never holds or advocates a position on the topic under discussion.
2. **Deterministic conducts, probabilistic executes.** Anything that must be fair, auditable, or reproducible is decided here, in code. The LLM is invoked only for language understanding/generation and never trusted to be fair on its own.
3. **Fairness is a property of the process, not the outcome.** No rule optimizes for any particular conclusion.
4. **Inject information, never steer opinion.** The agent may add vetted information and surface neglected views. It may never nudge participants toward a conclusion. (Hard rule — violating this turns a fairness tool into an astroturfing tool.)
5. **Consensual blind.** Participants opt in to a format where identities — including human vs. AI — are hidden, with a debrief afterward. No covert AI participation.
6. **Everything is logged.** Every state transition and every agent contribution (with source) is appended to an immutable JSONL audit.

---

## 1. The five governing mechanisms (principle → rule)

Each rule encodes a mechanism from computational-deliberation and collective-decision research; the deterministic rule is what the Wiki actually enforces.

| # | Principle (and where it's deployed) | Deterministic system rule |
|---|---|---|
| 1 | **Independent assessment before exposure** — break anchoring (deliberative polling; Pol.is independent voting) | Collect each participant's private position + confidence (1–5) by DM/modal. No participant sees any other position until all reads are in OR `T_read` elapses (default 120s). |
| 2 | **Surface by merit, not volume or recency** (bridging visibility; Pol.is / Community Notes) | A candidate statement's visibility weight = its bridging score (§2), never its post count or how recently it was raised. |
| 3 | **Counter-pressure against premature lock-in** (cross-inhibition / stop-signal dynamics in collective decision-making) | If the leading candidate's weighted support crosses `V_ci` (default 50%) within the first reveal round AND no new information has entered since the last round → inject a minority steelman (§5) and require one more round before any quorum check. |
| 4 | **Decide at a quorum threshold, not forced unanimity** | Decision is reached when a candidate's bridging-adjusted weighted support ≥ `Q` (default 0.66) AND at least one cross-inhibition round has elapsed. Threshold-based ⇒ N-agnostic (works for any participant count). |
| 5 | **Detect stale / failing deliberation and refresh** | If `echo_index` is high AND `information_uptake` is low for `R` consecutive rounds (default 2) → trigger a structural refresh: re-collect independent reads and reframe the question. |

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
- This selection is deterministic given the agreement estimates. The agreement estimates themselves come from Vicky (§ mediator), but the *choice* is made here.

---

## 3. Anti-sycophancy weighting (deterministic)

Directly inverts the failure mode of participant-agents (drift toward last speaker / forming consensus).

- **Recency neutrality (structural):** the ranker's visibility weight is the bridging score (§2) only — it never reads post-count or recency — so the most recent input gets no extra influence *by construction*. (No separate recency down-weight step exists; an explicit `recency_weights()` helper was retired as it had no aggregation step to apply to. `w_recency` is retained in config only as a reserved tunable.)
- **Minority visibility floor:** any credible view held by ≥1 participant is guaranteed surfacing at least once before quorum, regardless of support level.
- **Phase-tuned convergence/dissent balance:** the ratio of convergence-pressure to dissent-preservation adapts by phase.

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

All transitions are pure functions of logged state. No LLM call decides a transition. In the audit, deterministic events are logged under the handle **Wiki**; Vicky's language outputs under **Vicky**.

---

## 5. Information injection (deterministic gate, probabilistic content)

- Source must be **vetted and citable**, retrieved via the Real-Time Search API. The source URL/citation is written to the audit.
- Injected through an anonymous handle so it lands like any other contribution.
- Content may be a fact or a steelman of a neglected view (generated by Vicky), but **must not contain an advocacy of any conclusion** (Invariant 4). A position-neutrality check runs on injected text before posting; if it advocates, it is rejected and regenerated.

---

## 6. Facilitation behaviors (optional, layer on top)

Drawn from Harrison Owen's Open Space Technology — minimal facilitation, not crowd aggregation:

- **Reflective pause** = the independent-read step (`COLLECT_READS`).
- **Cross-pollination** = the mediator may carry one point from a sub-thread into another that lacks it.
- **Law of Two Feet** = disengagement is signal; a dead thread or a performative pile-on is NOT treated as genuine quorum.

---

## 7. Governance & audit (deterministic)

- **Audit (JSONL):** one line per event — `{ts, session_id, state, actor_handle, actor_type, action, payload_hash, source}`. Deterministic events use `actor_handle = "Wiki"`; Vicky's outputs use `"Vicky"`.
- **Position-neutrality check:** every mediator output passes a deterministic gate that rejects topic-position advocacy before it reaches the channel.
- **Anonymization map** (`handle ↔ real user`, `handle ↔ human|agent`) is stored server-side only, access-controlled, and revealed only at DEBRIEF.

---

## 8. Default parameters (all tunable)

| Param | Default | Meaning |
|---|---|---|
| `T_read` | 120s | independent-read collection window |
| `V_ci` | 0.50 | cross-inhibition trigger (fast-consensus velocity) |
| `Q` | 0.66 | quorum threshold (bridging-adjusted weighted support) |
| `R` | 2 | stale-rounds before structural refresh |
| `w_recency` | 0.5 | reserved recency tunable (recency-neutrality is structural; see §3) |
| `N_candidates` | 8 | common-ground statements generated per round |
| `k_max` | 4 | max opinion clusters |
| `confidence_scale` | 1–5 | per-participant confidence |

---

## 9. Sources (the Wiki distils these)

- **AI mediation** — Tessler, Bakker et al., "Habermas Machine," *Science* 2024 (generative + reward model + Schulze-method selection; caucus mediation).
- **Bridging consensus** — Pol.is / The Computational Democracy Project (group-informed consensus); Remesh (elicitation inference, bridging-based ranking); Community Notes (bridging-based ranking in production).
- **Collective decision dynamics** — quorum thresholds and cross-inhibition (stop-signals) as general mechanisms for committing at a threshold while resisting premature lock-in.
- **Facilitation philosophy** — Harrison Owen, Open Space Technology (minimal facilitator; Law of Two Feet).
- **Failure mode being countered** — arXiv 2506.11825 (LLM debate agents form echo chambers and intensify).
