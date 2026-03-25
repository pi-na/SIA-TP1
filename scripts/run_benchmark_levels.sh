#!/usr/bin/env bash
set -euo pipefail

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

"$PYTHON_BIN" -u -m src.main \
  --levels-file levels/benchmark_levels.txt \
  --iterations 1 \
  --seed 42 \
  --output-dir results_benchmark_levels
