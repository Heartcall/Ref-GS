#!/usr/bin/env bash
set -eu

# Legacy convenience entrypoint. It no longer launches training directly.
# Use the Python runners below for controlled train/render/eval execution.

python scripts/run_refnerf.py --dry-run
python scripts/run_nerf_synthetic.py --dry-run
python scripts/run_glossy_synthetic.py --dry-run
python scripts/run_ref_real.py --dry-run
