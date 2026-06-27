# Wiki & Vicky — a deliberation mediator

A Slack agent that makes group deliberation **fairer and groupthink-resistant**.
It does not debate — it **mediates**. A deterministic constitution — **the Wiki** —
conducts the process, and a probabilistic mediator — **Vicky** — performs only the
language work the Wiki invokes. Grounded in computational-deliberation research
(Pol.is, the Habermas Machine, Community Notes); it works *against* groupthink —
not a swarm / hive-mind system.

> **Wiki vs. Vicky** is the joke and the thesis: the Wiki is the fixed, auditable
> rule set (deterministic); Vicky is the language model (not). Code modules are
> `constitution/` and `mediator/`; Wiki and Vicky are their nicknames in the docs,
> audit log, and channel.

> Humans deliberate. The Wiki owns every fairness guarantee (auditable). Vicky
> owns understanding and phrasing (never trusted to be fair on her own).

See `docs/WIKI.md` for the full constitution, plus the build plan, architecture
diagram, and project spec in `docs/`.

## The two layers — and what Vicky actually does

This is the whole thesis, and the thing most worth being clear on:

| | Deterministic — **the Wiki** (`constitution/`) | Probabilistic — **Vicky** (`mediator/`) |
|---|---|---|
| Role | **Conducts.** Decides everything. | **Executes.** Does language work on request. |
| Owns | state machine, bridging ranking, quorum, anti-sycophancy weighting, audit | reading opinions, proposing statements, estimating agreement, steelmanning, echo detection |
| Trusted to be fair? | Yes — it is the fairness guarantee | **No, never** |

**The mediator is just an interface** (`mediator/base.py`) with four methods:

- `synthesize_candidates` — propose common-ground statements
- `predict_agreement` — estimate who would agree with each
- `steelman_minority` — argue the least-supported credible view
- `detect_echo` — flag a thread intensifying with no new information

The constitution calls these, then **re-selects or bounds every result** with its
own deterministic rules. The mediator *proposes*; the constitution *selects*. It
never decides a state transition or picks the winner.

Because the mediator is only this interface, the entire system runs offline with
a no-LLM `FakeMediator` (`mediator/fake.py`) for testing. A real Claude-backed
mediator drops in later with **zero changes** to the constitution.

## Run the basic test (no Slack, no API key)

```bash
python -m demo.run_session
```

You'll watch a small session go through `COLLECT_READS → REVEAL →
CROSS_INHIBITION → QUORUM_CHECK → DEBRIEF`, see the mediator's proposed
candidates, and see the constitution pick the bridging winner. Edit the reads in
`demo/run_session.py` and re-run to watch the outcome change.

```bash
pip install -r requirements.txt   # only needed for the tests
pytest -q
```

## Layout

```
constitution/   deterministic core
  config.py       tunable parameters (Q, V_ci, R, weights, ...)
  protocol.py     the state machine (the conductor)
  bridging.py     bridging-based ranking + opinion-group clustering
  weighting.py    anti-sycophancy / phase-tuned dissent preservation
  audit.py        immutable JSONL audit log
mediator/       probabilistic layer
  base.py         the Mediator interface (the contract)
  fake.py         deterministic no-LLM implementation for testing
demo/           runnable end-to-end session
tests/          unit tests for the fairness math + state machine
docs/           constitution, build plan, architecture, project spec
```

## Status

Engine + full offline story runnable and tested. **Built:** the deliberation
spine, bridging harness (validated on 6,605 real Habermas sessions), the
position-neutrality gate, the engine wrapped as an **MCP server** (`mcp_server/`,
full round-trip), and the **Vicky** (`mediator/claude.py`) + **RTS**
(`constitution/evidence.py`) adapters (offline-tested; live calls need
credentials). **Not yet built:** the live Slack surface (Block Kit app) wiring
it all together. See `docs/BUILD_PLAN_v1.md` and `docs/REQUIRED_TECH_TODO.md`.
