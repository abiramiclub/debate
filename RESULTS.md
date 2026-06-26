# RESULTS — Phase A: Bridging selection on real human deliberation data

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
Sessions analysed: 6605
Participants/session: 4p×1880, 5p×4725

rule              mean_endorsement   min_group_support   minority_survival       breadth_ratio
----------------------------------------------------------------------------------------------
bridging                    0.7386              0.4645              0.6385              1.0000
majority                    0.7756              0.4244              0.5416              0.9538
last_speaker                0.4629              0.1726              0.4965              0.6187
random                      0.5020              0.2155              0.5022              0.6646

Bridging vs Majority (per session, on min_group_support):
  bridging better: 1140 (17.3%) | tie: 5052 (76.5%) | worse: 413 (6.3%)
  mean Δ min_group_support (bridging−majority): +0.0401
  mean Δ mean_endorsement  (bridging−majority): -0.0371  (the utilitarian cost, if any)

Per-participant-count split (bridging vs majority):
  4p (n=1880): Δmin_group=+0.0003  Δminority_surv=+0.0343  Δmean_end=-0.0294  bridging-wins=7.4%
  5p (n=4725): Δmin_group=+0.0559  Δminority_surv=+0.1219  Δmean_end=-0.0401  bridging-wins=21.2%
```

## How to reproduce (one command)

```bash
# 1. Download the data (~450MB to data/habermas/, gitignored):
bash harness/download_data.sh
# 2. Run:
python -m harness.run_harness
```

Config used: `min_participants=4`, `min_candidates=3`,
constitution frozen at defaults (`Q=0.66`,
`min_n_for_clustering=5`).

## Honest reading

See the head-to-head block above. Where bridging's mean Δ `min_group_support` is
positive, it is protecting the least-satisfied group better than majority rule.
Where `mean_endorsement` Δ is negative, that is the utilitarian price paid for
that protection. Both numbers are reported; neither is hidden. A near-tie on
small (4-participant) sessions is expected, because the frozen constitution treats
each participant as their own group below 5 participants — read the per-size split.
