# DEMO SCRIPT — the full story, on screen

**The pitch in one line:** most agents make Slack faster at *answering*; this makes
a room better at *deciding* — bridging consensus, in a real deliberation, with
mid-debate evidence and an audit trail for every move.

This is **not** a voting widget. It is a facilitated process: people deliberate,
a deterministic constitution conducts, and a mediator does only the language work
it's told to. Everything below is produced by `python -m demo.run_ab` and
`python -m demo.build_debrief` — offline, no Slack, no API key.

## The 3-minute arc (foil → mediated → debrief)

| # | On screen | Rule it shows | Audit-log line (action) |
|---|-----------|---------------|--------------------------|
| 1 | **Foil first:** "what Slack does today" — reveal everyone at once, summarise, go with the majority. Outcome: *"Adopt a four-day week"* — the 2-person minority is simply overruled. | (no constitution) | — (naive pipeline is not audited) |
| 2 | Switch on the constitution. Session opens with a consent gate and neutral tree-handles (Birch, Maple, …). | Consent gate · anonymization | `CONSENT / consent_recorded` |
| 3 | Each person submits a **private read + confidence before anyone sees another** (breaks anchoring). | Independent reads before reveal | `COLLECT_READS / store_read` ×5 |
| 4 | Reveal. The mediator proposes candidate statements; the constitution clusters the room into two camps and ranks by **cross-group** support. | Mediator proposes / constitution selects · bridging | `REVEAL / synthesize+predict` then `REVEAL / rank_bridging` |
| 5 | Round 0 jumps to a feel-good platitude ("we all want the team to thrive"). The constitution **fires cross-inhibition** — resist the premature consensus. | Cross-inhibition (anti-premature-lock-in) | `CROSS_INHIBITION / cross_inhibition` |
| 6 | The minority's view is **steelmanned** into the channel, every round it exists — coverage is a real obligation. | Minority steelman on any minority cluster | `CROSS_INHIBITION / steelman_minority` |
| 7 | The two camps repeat themselves — no new information. The echo signal trips into a **deadlock**. | Echo / deadlock detection | `QUORUM_CHECK / check_quorum` (decision shows the stall) |
| 8 | **Consequence:** at the deadlock the agent injects one **sourced fact** via a neutral handle — coverage rotas kept output up in real trials. The source URL is written to the log. | Evidence injection (RTS route) | `INFO_INJECTION / inject_evidence` (with `source=…`) |
| 9 | With the coverage concern addressed, a **compromise** both camps endorse crosses quorum: *"Pilot a four-day week with a Friday on-call rota."* — different from either opening line. | Bridging quorum (N-agnostic) | `QUORUM_CHECK / check_quorum` (decision `QUORUM_MET`) |
| 10 | **Debrief** (Block Kit): least-satisfied-group support **0.81 vs 0.15**, minority survival **0.81 vs 0.15**, average **0.84 vs 0.60**; the minority moved **+0.40** after the evidence; and Maple is revealed to have been an AI all along. | Debrief · metrics · AI reveal · audit link | `DEBRIEF / debrief` |

## What each number means (and what's proven vs shown)

- **Least-satisfied group / minority survival / average** — the *same three metrics*
  the Phase A harness reports, computed here for this one session. Bridging keeps
  the minority at **0.81**; majority rule leaves them at **0.15**.
- **Bridging is data-proven** on 6,605 real human Habermas sessions (Phase A).
- **Information uptake is a scenario demonstration only** — the Habermas data has
  no evidence dimension, so the pre/post positions are stipulated by the fixture.
  The debrief says this in-line. Never present uptake as data-validated.

## Run it

```bash
python -m demo.run_ab          # the spine + audit trace, naive vs constitution
python -m demo.build_debrief   # writes & validates demo/debrief_blockkit.json
```

Paste `demo/debrief_blockkit.json` into the Slack **Block Kit Builder** to see the
debrief render. The on-camera Slack version and the real RTS/MCP wiring are the
next phase (tracked in `docs/REQUIRED_TECH_TODO.md`).
