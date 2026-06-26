#!/usr/bin/env bash
# Download the Habermas Machine dataset (CC-BY 4.0) into data/habermas/ (gitignored).
# Source: https://github.com/google-deepmind/habermas_machine
set -euo pipefail
DIR="data/habermas"
mkdir -p "$DIR"
BASE="https://storage.googleapis.com/habermas_machine/datasets"
# Only the table the harness needs (multi-candidate human rankings, ~380MB):
curl -fSL -o "$DIR/hm_all_candidate_comparisons.parquet" \
  "$BASE/hm_all_candidate_comparisons.parquet"
echo "Downloaded to $DIR (gitignored)."
