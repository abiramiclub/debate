# Honeybee Deliberation Mediator

A Slack agent that makes group deliberation **fairer and groupthink-resistant**.
It does not debate — it **mediates**. A deterministic "constitution" (rules
distilled from collective decision-making in honeybee swarms) conducts the
process, and a probabilistic **mediator** performs only the language work the
constitution invokes.

> Humans deliberate. The constitution owns every fairness guarantee (auditable).
> The mediator owns understanding and phrasing (never trusted to be fair on its own).

See `docs/` for the full constitution, build plan, architecture diagram, and project spec.

## The two layers — and what the mediator actually does

This is the whole thesis, and the thing most worth being clear on:

| | Deterministic — **Constitution** (`constitution/`) | Probabilistic — **Mediator** (`mediator/`) |
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

Phase 0–2 logic, runnable offline. **Not yet built:** Slack app + Block Kit,
the MCP server wrapper, the real Claude mediator, and Real-Time Search info
injection. See `docs/BUILD_PLAN_v1.md`.
