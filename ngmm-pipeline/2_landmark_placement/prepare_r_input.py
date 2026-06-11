#!/usr/bin/env python3
# =============================================================
# prepare_r_input.py
# Copies .mrk.json landmark files from ALPACA's individualEstimates
# subfolders up one level so the R script can read them directly.
#
# ALPACA output structure (input):
#   pipeline_data/alpaca_run/output/
#   ├── DG/
#   │   └── individualEstimates/
#   │       ├── NG4975_DG_template.mrk.json
#   │       └── ...
#   ├── HP/
#   │   └── individualEstimates/
#   │       └── ...
#
# R-ready structure (output):
#   3_morphometrics/input/
#   ├── DG/
#   │   ├── NG4975_DG_template.mrk.json
#   │   └── ...
#   ├── HP/
#   │   └── ...
#
# Usage:
#   python 2_landmark_placement/prepare_r_input.py
#   Or with explicit paths:
#   python 2_landmark_placement/prepare_r_input.py \
#       --input  /path/to/2_landmark_placement/output \
#       --output /path/to/ngmm-pipeline/3_morphometrics/input
# =============================================================

import os
import shutil
import argparse

# =============================================================
# CONFIGURATION — edit if not using command-line arguments
# =============================================================
DEFAULT_INPUT  = "/path/to/2_landmark_placement/output" # edit
DEFAULT_OUTPUT = "/path/to/ngmm-pipeline/3_morphometrics/input" # edit
os.makedirs(DEFAULT_OUTPUT, exist_ok=True)
# =============================================================

def prepare_r_input(alpaca_output_dir, r_input_dir):
    if not os.path.exists(alpaca_output_dir):
        raise FileNotFoundError(f"ALPACA output directory not found:\n  {alpaca_output_dir}")

    os.makedirs(r_input_dir, exist_ok=True)

    region_folders = [
        d for d in os.listdir(alpaca_output_dir)
        if os.path.isdir(os.path.join(alpaca_output_dir, d))
    ]

    if not region_folders:
        print(f"[WARNING] No region subfolders found in:\n  {alpaca_output_dir}")
        return

    total_copied = 0
    total_skipped = 0

    for region in sorted(region_folders):
        estimates_dir = os.path.join(alpaca_output_dir, region, "individualEstimates")

        if not os.path.exists(estimates_dir):
            print(f"[SKIP] No individualEstimates folder found for region: {region}")
            continue

        mrk_files = [f for f in os.listdir(estimates_dir) if f.endswith(".mrk.json")]

        if not mrk_files:
            print(f"[SKIP] No .mrk.json files found in: {estimates_dir}")
            continue

        region_out = os.path.join(r_input_dir, region)
        os.makedirs(region_out, exist_ok=True)

        copied  = 0
        skipped = 0

        for fname in sorted(mrk_files):
            src = os.path.join(estimates_dir, fname)
            dst = os.path.join(region_out, fname)

            if os.path.exists(dst):
                skipped += 1
                continue

            shutil.copy2(src, dst)
            copied += 1

        print(f"  {region}: {copied} file(s) copied, {skipped} already existed")
        total_copied  += copied
        total_skipped += skipped

    print(f"\nDone. {total_copied} file(s) copied, {total_skipped} already existed.")
    print(f"R input directory:\n  {r_input_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flatten ALPACA individualEstimates folders for R/GPA analysis."
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help="Path to ALPACA output directory (contains per-region subfolders)"
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Path to R input directory (will be created if it doesn't exist)"
    )
    args = parser.parse_args()

    prepare_r_input(args.input, args.output)