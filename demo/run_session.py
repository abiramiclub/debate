"""Very basic end-to-end test of the deliberation loop — no Slack, no LLM.

Run it:  python -m demo.run_session

It seeds a small set of participants with private reads, runs them through the
constitution's state machine using the FakeMediator, and prints each step so you
can SEE the division of labor:

    constitution conducts  ->  invokes mediator for language  ->  constitution selects

Change the reads below and re-run to watch the bridging winner change.
"""

import os
import tempfile

from constitution.protocol import Session
from mediator.fake import FakeMediator


def main() -> None:
    audit_path = os.path.join(tempfile.gettempdir(), "honeybee_demo_audit.jsonl")
    if os.path.exists(audit_path):
        os.remove(audit_path)

    session = Session(session_id="demo-001", mediator=FakeMediator(), audit_path=audit_path)

    # (user_id, actor_type). In a real session some of these could be 'agent'.
    session.start([
        ("alice", "human"),
        ("bob", "human"),
        ("carol", "human"),
        ("dave", "human"),
    ])

    # Private reads (collected before any reveal — anti-anchoring).
    reads = [
        ("Birch", "We should prioritize remote work flexibility for the team.", 4),
        ("Maple", "Remote flexibility matters but office collaboration also matters.", 3),
        ("Cedar", "In-office time builds collaboration and mentorship for juniors.", 5),
        ("Aspen", "A hybrid schedule could balance flexibility and collaboration.", 4),
    ]
    for handle, text, conf in reads:
        session.submit_read(handle, text, conf)

    print("=" * 70)
    print("COLLECT_READS — private positions gathered before any reveal:")
    for handle, text, conf in reads:
        print(f"  {handle} (confidence {conf}): {text}")

    results = session.deliberate(max_rounds=5)

    for r in results:
        print("\n" + "=" * 70)
        print(f"ROUND {r.round_idx}")
        print("-" * 70)
        print("Mediator proposed candidates (language work):")
        for i, c in enumerate(r.candidates):
            mark = "  <-- bridging winner" if c == r.winner_text else ""
            print(f"  [{i}] {c}{mark}")
        print(f"\nOpinion groups (clustered by the constitution): {r.group_labels}")
        print(f"Bridging winner: {r.winner_text!r}")
        print(f"Weighted support: {r.winner_support:.2f}  (quorum Q={session.cfg.Q})")
        if r.cross_inhibition_fired:
            print("\nCross-inhibition FIRED (fast consensus -> counter-pressure):")
            print(f"  {r.steelman}")
        print(f"\nEcho check: {'ECHO' if r.echo_flag else 'ok'} — {r.echo_reason}")
        print(f"Decision: {r.decision}")

    print("\n" + "=" * 70)
    debrief = session.debrief()
    print("DEBRIEF")
    print("-" * 70)
    print(f"Reached quorum: {debrief['reached_quorum']}")
    print(f"Outcome: {debrief['winner']!r}")
    print("Anonymization map revealed:")
    for p in debrief["participants"]:
        print(f"  {p['handle']} = {p['user_id']} ({p['actor_type']})")
    print(f"\nAudit trail: {len(debrief['audit'])} events written to {audit_path}")


if __name__ == "__main__":
    main()
