#!/bin/bash
# =============================================================
# PIPELINE PATH CONFIGURATION
# Copy this file to config/paths.sh and fill in your paths.
# config/paths.sh is gitignored — never commit real paths.
#
# Usage: replace /path/to/ngmm-pipeline with the absolute path
#        where you cloned this repository. Everything else
#        resolves automatically from REPO_ROOT.
# =============================================================

# ── Repository root (the only line most users need to edit) ──
REPO_ROOT="/path/to/ngmm-pipeline"

# ── Conda environment ─────────────────────────────────────────
CONDA_ENV_PATH="/path/to/.conda/envs/env_ng"

# ── Stage 1: Segmentation ─────────────────────────────────────
# Raw masked MRI volumes: {ID}_RCL5_masked.nrrd
PROCESSED_FILES_DIR="${REPO_ROOT}/pipeline_data/processed_files_3"

# nnU-Net dataset identifier (must match trained model in nnUNet_results)
DATASET="Dataset004_first"
PRED_CONFIG="3d_fullres"

# nnU-Net data directories
NNUNET_RAW="${REPO_ROOT}/pipeline_data/nnUNet_raw_data"
NNUNET_PREPROCESSED="${REPO_ROOT}/pipeline_data/nnUNet_preprocessed"
NNUNET_RESULTS="${REPO_ROOT}/pipeline_data/nnUNet_results"

# Final segmentation outputs (.seg.nrrd)
SEGMENTATION_OUTPUT_DIR="${REPO_ROOT}/pipeline_data/segmentation_predictions"

# ── Stage 2: ALPACA ───────────────────────────────────────────
# Template assets live inside the repo (versioned)
TEMPLATE_MODEL_DIR="${REPO_ROOT}/2_landmark_placement/template_model"
TEMPLATE_LM_DIR="${REPO_ROOT}/2_landmark_placement/template_landmarks"

# Per-region VTK surfaces (generated from .seg.nrrd, gitignored)
TARGET_MODELS_DIR="${REPO_ROOT}/pipeline_data/target_models"

# ALPACA prediction outputs (gitignored)
ALPACA_OUTPUT_DIR="${REPO_ROOT}/pipeline_data/alpaca_run/output"

# ── Stage 3: R analysis ───────────────────────────────────────
# Reads directly from ALPACA output — no separate copy needed
R_INPUT_ROOT="${REPO_ROOT}/3_morphometrics/input"
R_OUTPUT_DIR="${REPO_ROOT}/3_morphometrics/output"