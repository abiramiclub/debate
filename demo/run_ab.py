"""A/B demo: the SAME fixture through two pipelines.

  naive        — what Slack does today: reveal everything at once, summarise,
                 go with the majority. No independent reads, no cross-inhibition,
                 no minority steelman, no evidence, no bridging.
  constitution — the full protocol: consent -> reads-before-reveal -> reveal ->
                 cross-inhibition -> deadlock -> evidence injection ->
                 bridging quorum, with a JSONL audit of every step.

Run:  python -m demo.run_ab
"""

import json
import os
import tempfile

from constitution.evidence import Evidence, FixtureEvidenceSource
from constitution.protocol import Session
from mediator.scripted import ScriptedMediator

FIXTURE = os.path.join(os.path.dirname(__file__), "fixture_5p_twocamp.json")


def load_fixture(path: str = FIXTURE) -> dict:
    with open(path) as f:
        return json.load(f)


def run_naive(fx: dict) -> str:
    """Reveal-all + majority. Uses the substantive positions (round 1) as 'what
    is on the table' and picks the one with the highest average agreement."""
    positions = fx["rounds"][1]["candidates"]
    agreement = fx["rounds"][1]["agreement"]
    n_p = len(agreement)
    means = [sum(agreement[p][c] for p in range(n_p)) / n_p for c in range(len(positions))]
    winner = max(range(len(positions)), key=lambda c: means[c])
    return positions[winner]


def run_constitution(fx: dict, audit_path: str):
    mediator = ScriptedMediator(fx["rounds"], fx["steelman_text"])
    ev = fx["evidence"]
    source = FixtureEvidenceSource(Evidence(
        text=ev["text"], source=ev["source"], handle=ev["handle"], label=ev["label"]))

    session = Session("demo-5p-twocamp", mediator, audit_path, evidence_source=source)
    session.start([(p["user_id"], p["actor_type"]) for p in fx["participants"]])
    for p, r in zip(session.participants, fx["reads"]):
        session.submit_read(p.handle, r["text"], r["confidence"])
    results = session.deliberate(max_rounds=6)
    debrief = session.debrief()
    return session, results, debrief


def main():
    fx = load_fixture()
    audit_path = os.path.join(tempfile.gettempdir(), "wiki_ab_audit.jsonl")
    if os.path.exists(audit_path):
        os.remove(audit_path)

    print("=" * 74)
    print("TOPIC:", fx["topic"])
    print("Briefing:", fx["briefing"])
    print("=" * 74)

    naive_outcome = run_naive(fx)
    session, results, debrief = run_constitution(fx, audit_path)

    print("\n### CONSTITUTION PIPELINE — the spine, round by round\n")
    for r in results:
        print(f"-- ROUND {r.round_idx} " + "-" * 56)
        print(f"  mediator candidates : {r.candidates}")
        print(f"  opinion groups      : {r.group_labels}  (minority present: {r.minority_present})")
        print(f"  bridging winner     : {r.winner_text!r}")
        print(f"  weighted support    : {r.winner_support:.2f}  (Q={session.cfg.Q}, V_ci={session.cfg.V_ci})")
        if r.cross_inhibition_fired:
            print("  >> CROSS-INHIBITION fired (resisting premature consensus)")
        if r.steelman:
            print(f"  >> MINORITY STEELMAN: {r.steelman[:80]}...")
        print(f"  echo: {'ECHO' if r.echo_flag else 'ok'} — {r.echo_reason}")
        if r.evidence:
            print(f"  >> EVIDENCE INJECTED via @{r.evidence.handle}: {r.evidence.text[:70]}...")
            print(f"     source: {r.evidence.source}")
        print(f"  decision: {r.decision}")

    print("\n" + "=" * 74)
    print("OUTCOMES ON IDENTICAL INPUT")
    print("-" * 74)
    print(f"  naive (reveal-all + majority): {naive_outcome!r}")
    print(f"  constitution (bridged)       : {debrief['winner']!r}")
    diverged = naive_outcome != debrief["winner"]
    print(f"\n  -> outcomes diverge: {diverged}")
    print("     naive overrides the minority; the constitution surfaces dissent,")
    print("     injects sourced evidence at the deadlock, and lands a compromise")
    print("     both camps endorse (different from either opening line).")

    print("\n" + "=" * 74)
    print("AUDIT TRACE (constitution pipeline — every step is logged)")
    print("-" * 74)
    for e in debrief["audit"]:
        src = f"  source={e['source']}" if e.get("source") else ""
        print(f"  [{e['state']:<16}] {e['actor_handle']:<8} {e['action']}{src}")

    print("\n" + "=" * 74)
    print("DEBRIEF — anonymization map revealed (incl. which were AI):")
    for p in debrief["participants"]:
        flag = "  <-- AI" if p["actor_type"] == "agent" else ""
        print(f"  {p['handle']:<8} = {p['user_id']} ({p['actor_type']}){flag}")
    print(f"\nAudit JSONL: {audit_path}  ({len(debrief['audit'])} events)")


if __name__ == "__main__":
    main()
