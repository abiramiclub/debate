"""Phase A runner: bridging selection vs baselines on real human deliberation data.

One command, fully offline (requires the gitignored Habermas parquet locally):

    python -m harness.run_harness

Emits RESULTS.md and results.csv, and prints the comparison table.
"""

import argparse
import csv
import statistics as stats
from collections import defaultdict

from .baselines import RULES
from .loader import load_sessions
from .metrics import METRIC_KEYS, session_metrics
from constitution.config import DEFAULT


def run(min_participants: int, min_candidates: int, limit: int | None):
    sessions = load_sessions(min_participants=min_participants, min_candidates=min_candidates)
    if limit:
        sessions = sessions[:limit]

    rows = []  # one row per (session, rule)
    # agg[rule][metric] -> list of values
    agg: dict[str, dict[str, list[float]]] = {r: defaultdict(list) for r in RULES}
    # for head-to-head vs majority
    per_session: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)

    for s in sessions:
        for rule_name, rule in RULES.items():
            chosen = rule(s)
            m = session_metrics(s, chosen)
            per_session[s.session_id][rule_name] = m
            for k in METRIC_KEYS:
                agg[rule_name][k].append(m[k])
            rows.append({
                "session_id": s.session_id, "n_participants": s.n_participants,
                "n_candidates": s.n_candidates, "rule": rule_name,
                "chosen": chosen, **{k: round(m[k], 4) for k in METRIC_KEYS},
            })

    return sessions, rows, agg, per_session


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def summarize(sessions, agg, per_session):
    lines = []
    n = len(sessions)
    sizes = defaultdict(int)
    for s in sessions:
        sizes[s.n_participants] += 1

    lines.append(f"Sessions analysed: {n}")
    lines.append(f"Participants/session: " +
                 ", ".join(f"{k}p×{v}" for k, v in sorted(sizes.items())))
    lines.append("")

    header = f"{'rule':<14}" + "".join(f"{k:>20}" for k in METRIC_KEYS)
    lines.append(header)
    lines.append("-" * len(header))
    for rule in RULES:
        row = f"{rule:<14}" + "".join(f"{_mean(agg[rule][k]):>20.4f}" for k in METRIC_KEYS)
        lines.append(row)
    lines.append("")

    # Head-to-head: bridging vs majority (the decisive comparison).
    wins = ties = losses = 0
    deltas_mgs = []
    deltas_mean = []
    for sid, rules in per_session.items():
        b, m = rules["bridging"], rules["majority"]
        deltas_mgs.append(b["min_group_support"] - m["min_group_support"])
        deltas_mean.append(b["mean_endorsement"] - m["mean_endorsement"])
        if b["min_group_support"] > m["min_group_support"] + 1e-9:
            wins += 1
        elif b["min_group_support"] < m["min_group_support"] - 1e-9:
            losses += 1
        else:
            ties += 1
    lines.append("Bridging vs Majority (per session, on min_group_support):")
    lines.append(f"  bridging better: {wins} ({wins/n:.1%}) | "
                 f"tie: {ties} ({ties/n:.1%}) | worse: {losses} ({losses/n:.1%})")
    lines.append(f"  mean Δ min_group_support (bridging−majority): {_mean(deltas_mgs):+.4f}")
    lines.append(f"  mean Δ mean_endorsement  (bridging−majority): {_mean(deltas_mean):+.4f}  "
                 f"(the utilitarian cost, if any)")
    lines.append("")

    # Stratify by participant count: below 5 the frozen constitution makes each
    # participant their own group, so bridging and majority converge more often.
    size_of = {s.session_id: s.n_participants for s in sessions}
    lines.append("Per-participant-count split (bridging vs majority):")
    by_size: dict[int, list[str]] = defaultdict(list)
    for sid in per_session:
        by_size[size_of[sid]].append(sid)
    for size in sorted(by_size):
        sids = by_size[size]
        dmgs = _mean([per_session[s]["bridging"]["min_group_support"]
                      - per_session[s]["majority"]["min_group_support"] for s in sids])
        dmin = _mean([per_session[s]["bridging"]["minority_survival"]
                      - per_session[s]["majority"]["minority_survival"] for s in sids])
        dmean = _mean([per_session[s]["bridging"]["mean_endorsement"]
                       - per_session[s]["majority"]["mean_endorsement"] for s in sids])
        w = sum(1 for s in sids
                if per_session[s]["bridging"]["min_group_support"]
                > per_session[s]["majority"]["min_group_support"] + 1e-9)
        lines.append(f"  {size}p (n={len(sids):>4}): "
                     f"Δmin_group={dmgs:+.4f}  Δminority_surv={dmin:+.4f}  "
                     f"Δmean_end={dmean:+.4f}  bridging-wins={w/len(sids):.1%}")
    return "\n".join(lines)


def write_results_md(summary: str, args):
    md = f"""# RESULTS — Phase A: Bridging selection on real human deliberation data

**Data:** DeepMind Habermas Machine dataset (CC-BY 4.0), `hm_all_candidate_comparisons.parquet`.
Real human participants (`HUMAN_CITIZEN`) ranking sets of candidate group-statements.
Raw data is downloaded locally and **gitignored** (not redistributed).

**What this measures:** given the SAME real human rankings, which *selection rule*
picks the statement with the broadest cross-group support? Endorsement is real
(rank 0 = most preferred, per DeepMind `utils.py`), so this isolates the selection
rule from any prediction error.

**Rules:** `bridging` (the constitution's cross-group ranker), `majority` (highest
mean endorsement), `last_speaker` (recency *proxy* — candidates are generated
simultaneously in this data, so there is no true speaker order; this is a weak
labeled control), `random` (seeded).

**Metrics:** `min_group_support` = the least-satisfied opinion group's mean
endorsement of the chosen statement (the anti-majority-tyranny metric);
`minority_survival` = smaller camp's mean endorsement; `mean_endorsement` =
overall average (utilitarian); `breadth_ratio` = chosen bridging score / best
available, in (0,1].

## Numbers

```
{summary}
```

## How to reproduce (one command)

```bash
# 1. Download the data (~450MB to data/habermas/, gitignored):
bash harness/download_data.sh
# 2. Run:
python -m harness.run_harness
```

Config used: `min_participants={args.min_participants}`, `min_candidates={args.min_candidates}`,
constitution frozen at defaults (`Q={DEFAULT.Q}`,
`min_n_for_clustering={DEFAULT.min_n_for_clustering}`).

## Honest reading

See the head-to-head block above. Where bridging's mean Δ `min_group_support` is
positive, it is protecting the least-satisfied group better than majority rule.
Where `mean_endorsement` Δ is negative, that is the utilitarian price paid for
that protection. Both numbers are reported; neither is hidden. A near-tie on
small (4-participant) sessions is expected, because the frozen constitution treats
each participant as their own group below 5 participants — read the per-size split.
"""
    with open("RESULTS.md", "w") as f:
        f.write(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-participants", type=int, default=4)
    ap.add_argument("--min-candidates", type=int, default=3)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    sessions, rows, agg, per_session = run(args.min_participants, args.min_candidates, args.limit)

    with open("harness/results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    summary = summarize(sessions, agg, per_session)
    print(summary)
    write_results_md(summary, args)
    print("\nWrote RESULTS.md and harness/results.csv")


if __name__ == "__main__":
    main()
