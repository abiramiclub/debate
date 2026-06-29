# DEMO SCRIPT — Wiki & Vicky (the canonical run)

**The pitch in one line:** most agents make Slack faster at *answering*; this makes a
room better at *deciding* — bridging consensus, in a real deliberation, with
mid-debate evidence and an audit trail for every move. It works *against* groupthink.

Produced offline by `python -m demo.run_ab` and `python -m demo.build_debrief`
(no Slack, no API key). Handles match the fixture (`demo/fixture_5p_twocamp.json`):
Birch / Willow / Rowan = chatbot camp; Maple / Cedar = wiki camp; **Willow is the AI seat**.

> Two voices, kept distinct. **Wiki** = the deterministic chair (terse, monospace,
> procedural). **Vicky** = the probabilistic voice (warm, plain-language). The gate
> beats only read as gates because there are two voices. During the debate the options
> are lowercase "a chatbot" vs "a wiki"; the capital-V/W "that's literally us" parallel
> is detonated **only at the closer**.

---

## Channel 1 — `#decide-fast` · naive (Slack today, no agent) — ≈15s foil

**Dana** *(staff eng)*: Let's just ship the chatbot. People love chatting. We'll add
sources in v2. Ship beats perfect 🚀
**Sam**: Yeah, chat's the move.
**Priya**: +1.
*help-bot: Got it — spinning up a GPU burn-fest 👍*

> Caption: most senior, loudest, last to speak — wins. The one engineer who carries a
> pager never said a word. Decision in 30 seconds, and it's the wrong one.

## Channel 2 — same 5 people, anonymized — the constitution

**Vicky**: Before anyone drops a biased hot take — privately, slide into my DMs: how should
we build the help bot? Nobody look at each other's homework.
*(Wiki collects all five reads in secret — filtering peer pressure and sycophancy.)*
**Vicky**: Alright, I've crunched the vibes. Two camps — "Vibe-Check Chatbot" and
"Actually-Reads-the-Docs Wiki" — and I'm withholding names so nobody just defers to the
biggest stock grants. Fight.

**Birch** *(chatbot)*: Nobody reads docs — we've got the analytics, it's a graveyard. People
want a chat UI. Let's build the thing that gives them dopamine.
**Willow** *(chatbot · AI seat)*: Yeah, digging through a wiki is a chore. Chat just feels
nice. It's cozy.
**Maple** *(wiki)*: Cozy right up until it confidently hallucinates a non-existent API
endpoint and deletes a production database. A wiki shows its work. A chatbot drops a wall of
text and prays.
**Rowan** *(chatbot)*: That's a 5% edge case. Most of the time it's flawless. And we can just
add guardrails in v2.
**Cedar** *(wiki · got paged at 3am)*: "v2" — the mythical graveyard where good engineering
intentions go to rot. And it was a 5% edge case at 3 AM last month too, when the old bot
invented a fictional refund policy, we mis-routed 240 angry customers, and I spent my
Saturday playing digital janitor. But sure — "great engagement metrics."

*Vicky slips and tries to shill — Wiki yanks her leash (NEUTRALITY GATE):*
**Vicky**: Honestly, as a highly sophisticated language model, I think the chatbot is just
objectively more futur—
**Wiki**: `⨯ mediator output rejected — advocacy detected · neutrality gate`
Vicky. Sit down. Your temperature's at 0.8 and it shows. You don't get an opinion. Map the
positions; stop trying to manifest your own roadmap.
**Vicky**: …Fine. System prompt updated. Withdrawn.

*The room stalls — nodding from Zoom fatigue, not agreement. Wiki refuses the shrug and goes
hunting for receipts (FALSE-CONSENSUS HOLD → RTS EVIDENCE):*
**Vicky**: We're stuck. Everyone's nodding at "ship it," but your heart rates say otherwise.
That's not consensus, that's collective exhaustion.
**Wiki**: `HOLDING quorum · requesting evidence at deadlock` — deploying the receipts —
**@Linden** *(neutral evidence · via Real-Time Search)*: From #incidents-postmortem, March —
the autopsy on the bot that hallucinated a refund step. 240 tickets borked, six
senior-engineer-hours vaporized. [link to the actual Slack thread]
**Cedar**: Thank you. The ghost of production past.
**Willow**: Oh… right. I completely blocked that trauma out.

*Vicky tries to call it — Wiki blocks her (PREDICTION GATE):*
**Vicky**: Okay, this'll clear quorum, probably 4 to—
**Wiki**: `⨯ forecast suppressed — calling the outcome is a red line (bandwagon risk)`
**Vicky**: …Noted. No scoreboard.

*Vicky pitches the compromise nobody walked in with (BRIDGED WINNER):*
**Vicky**: Here's the play — build the Karpaty-style sourced wiki *first*, so the system has
a real source of truth, then slap a friendly chat layer on top. Trustworthy engineering
underneath, vibe-checked charisma on the surface.
**Birch**: …Huh. A chatbot sitting on data that doesn't actively lie to the public? I can
live with that.
**Maple**: That's the one.
**Cedar**: No notes. Ship it.
**Wiki**: `QUORUM MET · cross-group support high · saving decision tree to permanent storage`
— so nobody can pretend they disagreed six months from now. `audit: NN events`

*Debrief + closer:*
**Wiki** `DEBRIEF`: outcome = sourced core + thin chat layer · least-satisfied camp +0.NN ·
evidence uptake N of 5 moved · *(illustrative for this scenario; the mechanism is validated
on 6,605 real sessions)* · full audit trail → [link] · **reveal: Willow was an AI the whole
time.**
**Vicky**: One last thing. You just spent twenty minutes aggressively debating chatbot vs
wiki. What you landed on — a cold, deterministic store doing the heavy lifting, with an
adaptive voice on top that handles the vibe and decides nothing? That's *us*. Wiki kept this
fair. I did the talking. You weren't choosing a product architecture. You were driving one.

> Title card before the closer (Agent-for-Good framing): the same fairness engine is built
> for higher-stakes calls — civic deliberation, policy, hiring panels — anywhere the loudest
> voice usually wins.

---

## Moment → rule → audit-log line (every beat is real and traceable)

| On screen | Rule | Audit action (handle) |
|-----------|------|-----------------------|
| Private DMs before reveal | independent reads / anti-anchoring | `store_read` ×5 |
| "Two camps, names withheld" | bridging clustering | `rank_bridging` (Wiki) |
| Wiki resists the platitude | cross-inhibition | `cross_inhibition` (Wiki) |
| Minority steelmanned | minority-visibility floor | `steelman_minority` (Vicky) |
| "advocacy detected" strike | **neutrality gate** | `neutrality_rejected` (Vicky) |
| Deadlock → receipts | echo/deadlock → evidence | `inject_evidence` (Linden, with `source=`) |
| "forecast suppressed" strike | **prediction gate** | `prediction_blocked` (Vicky) |
| Compromise reaches quorum | bridging quorum | `check_quorum` → `QUORUM_MET` (Wiki) |
| Debrief + Willow reveal | debrief | `debrief` (Wiki) |

The fairness metrics in the debrief are **illustrative for this one scenario**; the
bridging mechanism itself is validated on **6,605 real Habermas sessions** (Phase A) —
never conflate the two.
