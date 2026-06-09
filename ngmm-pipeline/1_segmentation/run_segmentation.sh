#!/bin/bash
# =============================================================
# run_segmentation.sh
# Full nnU-Net inference pipeline for mouse brain segmentation
#
# Usage:
#   bash run_segmentation.sh                      # auto-selects new samples
#   bash run_segmentation.sh NG4975 NG4976        # process specific samples
# =============================================================

set -e
trap 'echo "[ERROR] Script failed at step above. Exiting."' ERR

# ── Load configuration ────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/../config/paths.sh"

if [ ! -f "$CONFIG" ]; then
    echo "[ERROR] Config file not found: $CONFIG"
    echo "        Copy config/paths_template.sh to config/paths.sh and fill in your paths."
    exit 1
fi

source "$CONFIG"

# ── Activate conda environment ────────────────────────────────
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV_PATH"

# ── Export nnU-Net environment variables ──────────────────────
export nnUNet_raw="$NNUNET_RAW"
export nnUNet_preprocessed="$NNUNET_PREPROCESSED"
export nnUNet_results="$NNUNET_RESULTS"

# ── Internal temp paths (relative to segmentation script dir) ─
SOURCE_DIR="${SCRIPT_DIR}"
TEMP_DIR="${REPO_ROOT}/pipeline_data/temp"
CONVERTED_FILE_PATH="${TEMP_DIR}/1.File_Name_Modification"
INPUT="${TEMP_DIR}/2.imagesTs"
OUTPUT="${TEMP_DIR}/3.labelsTs"

mkdir -p "$CONVERTED_FILE_PATH" "$INPUT" "$OUTPUT" "$SEGMENTATION_OUTPUT_DIR"

# ── Step 1: File renaming ─────────────────────────────────────
echo "======================================================="
echo "Step 1: File name modification"
echo "======================================================="

if [ "$#" -gt 0 ]; then
    echo "Processing provided sample IDs: $@"
    python "${SOURCE_DIR}/prediction/File_name_new.py" \
        --folder_path "$PROCESSED_FILES_DIR" \
        --output_path "$CONVERTED_FILE_PATH" \
        --names "$@"
else
    echo "No sample IDs provided — auto-selecting unprocessed samples..."

    existing_names=()
    for f in "$SEGMENTATION_OUTPUT_DIR"/*; do
        [ -e "$f" ] || continue
        fname=$(basename "$f")
        base=${fname%%_*}
        existing_names+=("$base")
    done

    all_candidates=()
    for f in "$PROCESSED_FILES_DIR"/*_RCL5_masked.nrrd; do
        [ -e "$f" ] || continue
        fname=$(basename "$f")
        base=${fname%%_*}
        all_candidates+=("$base")
    done

    names_to_process=()
    for name in "${all_candidates[@]}"; do
        if [[ ! " ${existing_names[*]} " =~ " ${name} " ]]; then
            names_to_process+=("$name")
        fi
    done

    if [ ${#names_to_process[@]} -eq 0 ]; then
        echo "No new samples to process. All outputs already exist in:"
        echo "  $SEGMENTATION_OUTPUT_DIR"
        exit 0
    fi

    echo "New samples to process: ${names_to_process[@]}"
    python "${SOURCE_DIR}/prediction/File_name_new.py" \
        --folder_path "$PROCESSED_FILES_DIR" \
        --output_path "$CONVERTED_FILE_PATH" \
        --names "${names_to_process[@]}"
fi

echo "Step 1 done."

# ── Step 2: Convert to NIfTI ──────────────────────────────────
echo "======================================================="
echo "Step 2: Convert .nrrd → .nii.gz"
echo "======================================================="

python "${SOURCE_DIR}/prediction/Conversion_to_nifti.py" \
    --folder_path "$CONVERTED_FILE_PATH" \
    --output_path "$INPUT" \
    --clean_path "$OUTPUT"

echo "Step 2 done."

# ── Step 3: nnU-Net inference ─────────────────────────────────
echo "======================================================="
echo "Step 3: nnU-Net prediction (5-fold ensemble)"
echo "======================================================="

nnUNetv2_predict \
    -d "$DATASET" \
    -i "$INPUT" \
    -o "$OUTPUT" \
    -f 0 1 2 3 4 \
    -tr nnUNetTrainer \
    -c "$PRED_CONFIG" \
    -p nnUNetPlans

echo "Step 3 done."

# ── Step 4: Convert predictions to .seg.nrrd ─────────────────
echo "======================================================="
echo "Step 4: Convert predictions → .seg.nrrd"
echo "======================================================="

python "${SOURCE_DIR}/prediction/Conversion_to_nrrd.py" \
    --label_json_path "${SOURCE_DIR}/dataset.json" \
    --input_dir "$OUTPUT" \
    --output_dir "$SEGMENTATION_OUTPUT_DIR" \
    --original_folder "$CONVERTED_FILE_PATH" \
    --example_seg_path "${SOURCE_DIR}/NG2561_Segments.seg.nrrd"

echo "Step 4 done."

# ── Step 5: Remove outside-brain voxels ──────────────────────
echo "======================================================="
echo "Step 5: Mask predictions to brain volume"
echo "======================================================="

python "${SOURCE_DIR}/prediction/Remove_outside_voxels.py" \
    --volume_dir "$CONVERTED_FILE_PATH" \
    --seg_dir "$SEGMENTATION_OUTPUT_DIR" \
    --output_path "$SEGMENTATION_OUTPUT_DIR"

echo "Step 5 done."

# ── Summary ───────────────────────────────────────────────────
echo "======================================================="
echo "Pipeline complete."
echo "Segmentation outputs saved to:"
echo "  $SEGMENTATION_OUTPUT_DIR"
echo "======================================================="