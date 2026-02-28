#!/usr/bin/env python3
"""
Run the NFT topological reanalysis pipeline end-to-end or from a chosen step.

Examples:
    python run_pipeline.py
    python run_pipeline.py --from-step preprocess
    python run_pipeline.py --only metrics
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
STEP_FILES = {
    "download": "01_download.py",
    "preprocess": "02_preprocess.py",
    "metrics": "03_compute_metrics.py",
    "ordering": "04_temporal_ordering.py",
}
STEP_ORDER = tuple(STEP_FILES)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the NFT TDA reanalysis pipeline.")
    parser.add_argument("--from-step", choices=STEP_ORDER, default="download")
    parser.add_argument("--only", choices=STEP_ORDER, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.only is not None:
        steps = [args.only]
    else:
        start_index = STEP_ORDER.index(args.from_step)
        steps = list(STEP_ORDER[start_index:])

    print("NFT topological reanalysis pipeline")
    print("----------------------------------")
    print(f"working_dir : {BASE_DIR}")
    print(f"steps       : {', '.join(steps)}")
    print()

    for step in steps:
        script = BASE_DIR / STEP_FILES[step]
        print(f"==> {step}: {script.name}")
        subprocess.run([sys.executable, str(script)], cwd=BASE_DIR, check=True)
        print()


if __name__ == "__main__":
    main()
