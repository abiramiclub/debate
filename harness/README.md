# Phase A — Measurement harness (Habermas Machine dataset)

Evaluates the constitution's **bridging selection** against baselines on **real
human deliberation data**, fully offline.

## Data & license

Source: [DeepMind Habermas Machine dataset](https://github.com/google-deepmind/habermas_machine).
- Code license: Apache-2.0. Data license: **CC-BY 4.0**.
- We use `hm_all_candidate_comparisons.parquet` (human participants ranking sets
  of candidate group-statements).
- The raw data is **downloaded locally and gitignored** — not redistributed in
  this repo. Attribution: Tessler, Bakker et al., "AI can help humans find common
  ground in democratic deliberation," *Science* (2024).

Rank convention (authoritative, from DeepMind `habermas_machine/utils.py`):
**rank 0 = most preferred.** Endorsement = `(max_rank - rank) / max_rank`.

## Reproduce (one command each)

```bash
bash harness/download_data.sh     # ~380MB -> data/habermas/ (gitignored)
python -m harness.run_harness     # prints table; writes RESULTS.md + harness/results.csv
```

Options: `--min-participants` (default 4), `--min-candidates` (default 3), `--limit`.

## What it does

- `loader.py` — groups human rankings into sessions (shared candidate set),
  builds the endorsement matrix.
- `baselines.py` — selection rules: `bridging`, `majority`, `last_speaker`
  (recency *proxy* — candidates are generated simultaneously here, so there is no
  true speaker order; labeled weak control), `random`.
- `metrics.py` — `min_group_support`, `minority_survival`, `mean_endorsement`,
  `breadth_ratio`.
- `run_harness.py` — runs everything, stratifies by participant count, emits results.

The endorsement is **real human ranking** (not predicted), so Phase A isolates the
selection rule from any model/prediction error. The constitution is used **frozen**
at its defaults.
