# ==========================================================
# run_alpaca_pipeline.py
# ALPACA landmark placement for all brain regions
#
# Must be run inside 3D Slicer's Python environment:
#   1. Open 3D Slicer
#   2. View → Python Interactor
#   3. exec(open("/path/to/run_alpaca_pipeline.py").read())
# ==========================================================

import os
import time
import json
import csv
import numpy as np

# ----------------------------------------------------------
# SAFETY: Ensure ALPACA is available
# ----------------------------------------------------------
try:
    import ALPACA
except ImportError:
    raise RuntimeError("This script must be run inside 3D Slicer with ALPACA installed")

PIPELINE_START_TIME = time.time()

# ==========================================================
# 1. PATH CONFIGURATION — edit these to match your system
# ==========================================================

BASE        = "/path/to/2_landmark_placement"
OUTPUT_ROOT = "/path/to/2_landmark_placement/output"
CSV_OUT_DIR = "/path/to/2_landmark_placement/output"
os.makedirs(OUTPUT_ROOT, exist_ok=True)
# Set to None to auto-discover all region folders under BASE/target_models/
# Or explicitly list regions to process, e.g. ["DG", "HP", "CC"]
REGIONS = None

# Whether to evaluate against ground-truth landmarks (set False if you have none)
EVALUATE = False

# ==========================================================
# 2. ALPACA PARAMETERS
# ==========================================================
PARAMETERS = {
    "projectionFactor":    0.01,
    "pointDensity":        1.5,
    "normalSearchRadius":  2.0,
    "FPFHNeighbors":       100,
    "FPFHSearchRadius":    5.0,
    "distanceThreshold":   3.0,
    "maxRANSAC":           1_000_000,
    "ICPDistanceThreshold": 1.5,
    "alpha":               2.0,
    "beta":                2.0,
    "CPDIterations":       100,
    "CPDTolerance":        0.001,
    "Acceleration":        False,
}

# ==========================================================
# 3. HELPER FUNCTIONS
# ==========================================================
def load_mrk_json(path):
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return np.array([cp["position"] for cp in data["markups"][0]["controlPoints"]])
    except Exception:
        return None

def rmse(a, b):
    return np.sqrt(np.mean(np.sum((a - b) ** 2, axis=1)))

def find_file_by_prefix(directory, prefix):
    if not os.path.exists(directory):
        return None
    for f in os.listdir(directory):
        if f.startswith(prefix) and f.endswith(".mrk.json"):
            return os.path.join(directory, f)
    return None

def discover_regions(base):
    target_models_root = os.path.join(base, "target_models")
    if not os.path.exists(target_models_root):
        raise FileNotFoundError(f"target_models directory not found: {target_models_root}")
    return sorted([
        d for d in os.listdir(target_models_root)
        if os.path.isdir(os.path.join(target_models_root, d))
    ])

# ==========================================================
# 4. RESOLVE REGIONS
# ==========================================================
regions_to_run = REGIONS if REGIONS is not None else discover_regions(BASE)
print(f"\nRegions to process: {regions_to_run}")
os.makedirs(CSV_OUT_DIR, exist_ok=True)

# ==========================================================
# 5. MAIN LOOP OVER REGIONS
# ==========================================================
logic = ALPACA.ALPACALogic()
all_csv_rows = []

for REGION in regions_to_run:
    print(f"\n{'='*50}")
    print(f"Processing region: {REGION}")
    print(f"{'='*50}")

    tmpl_model_dir = os.path.join(BASE, "template_model",    REGION)
    tmpl_lm_dir    = os.path.join(BASE, "template_landmarks", REGION)
    tgt_model_dir  = os.path.join(BASE, "target_models",      REGION)
    gt_lm_dir      = os.path.join(BASE, "target_ground_truths", REGION)
    out_dir        = os.path.join(OUTPUT_ROOT, REGION)

    # Validate required directories
    missing = [p for p in [tmpl_model_dir, tmpl_lm_dir, tgt_model_dir] if not os.path.exists(p)]
    if missing:
        print(f"  [SKIP] Missing directories: {missing}")
        all_csv_rows.append([REGION, "__SKIPPED__", "Missing Dirs", "", ""])
        continue

    os.makedirs(out_dir, exist_ok=True)

    # ── Run ALPACA ──────────────────────────────────────────
    region_start = time.time()

    logic.runLandmarkMultiprocess(
        tmpl_model_dir,
        tmpl_lm_dir,
        tgt_model_dir,
        out_dir,
        True,
        0.01,
        True,
        PARAMETERS
    )

    region_runtime = time.time() - region_start
    print(f"  ALPACA finished in {region_runtime:.2f} seconds")

    # ── Evaluation (optional) ───────────────────────────────
    estimates_dir = os.path.join(out_dir, "individualEstimates")
    rmse_scores = []

    all_csv_rows.append([REGION, "__REGION_TOTAL__", "Runtime", "", f"{region_runtime:.2f}"])

# ==========================================================
# 6. PIPELINE SUMMARY + CSV EXPORT
# ==========================================================
pipeline_runtime = time.time() - PIPELINE_START_TIME
all_csv_rows.append(["ALL", "__PIPELINE_TOTAL__", "Runtime", "", f"{pipeline_runtime:.2f}"])

csv_path = os.path.join(CSV_OUT_DIR, "ALPACA_RMSE_summary.csv")
with open(csv_path, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["region", "subject_id", "status", "rmse_mm", "time_sec"])
    writer.writerows(all_csv_rows)

print(f"\n{'='*50}")
print(f"All regions done in {pipeline_runtime:.2f} seconds")
print(f"Summary CSV saved to:\n  {csv_path}")
print(f"{'='*50}")