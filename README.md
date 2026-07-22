# Mouse Brain 3D Morphometric Analysis Pipeline

> **Companion repository for ICPR 2026 paper #564**  
> *"Automatic Segmentation for 3D Morphometric Analysis of the Mouse Brain"*

This repository provides a fully reproducible three-stage pipeline for automated 3D morphometric analysis of the mouse brain:

1. **Segmentation** — nnU-Net predicts anatomical regions from `.nrrd` HREM (High Resolution Episcopic Microscopy) volumes
2. **Landmark Placement** — ALPACA registers template landmarks onto each segmented region
3. **Statistical Analysis** — Geometric Morphometrics (GPA + PCA + ANOVA + LDA) in R

---
## Pipeline Execution Benchmarks

The table below outlines the average processing time required for each stage of the pipeline. 

| Stage | Process | Core Tool / Environment | Avg. Time (Per Sample)* |
| :--- | :--- | :--- | :--- |
| **1. Segmentation** | Automated ROI mask generation from `.nrrd` volumes | nnU-Net (Python / PyTorch) | ~7.5 min |
| **2. Landmark Placement** | Point-cloud registration & landmark transfer | ALPACA (SlicerMorph) | ~1 hour 20 min |
| **3. Statistical Analysis** | Shape analysis (GPA, PCA, ANOVA, LDA) | R Spatial/Morpho Packages | < 5 seconds (Batch total) |

## Table of Contents

- [Repository Structure](#repository-structure)
- [Hardware & Software Requirements](#hardware--software-requirements)
- [Quick Start](#quick-start)
- [Stage 1 — Segmentation with nnU-Net](#stage-1--segmentation-with-nn-u-net)
- [Stage 2 — Landmark Placement with ALPACA](#stage-2--landmark-placement-with-alpaca)
- [Stage 3 — Statistical Analysis in R](#stage-3--statistical-analysis-in-r)
- [Data Format Reference](#data-format-reference)
- [Reproducing Paper Results](#reproducing-paper-results) 
- [Troubleshooting](#troubleshooting)
- [Citation](#citation)

---

## Repository Structure

```
Full_Morph/ngmm-pipeline/
│
├── README.md                          ← This file
│
├── 1_segmentation/                    ← Stage 1: nnU-Net segmentation
│   ├── run_segmentation.sh            ← Main pipeline script
│   ├── prediction/
│   │   ├── File_name_new.py           ← Renames input files for nnU-Net convention
│   │   ├── Conversion_to_nifti.py     ← Converts .nrrd → NIfTI (.nii.gz)
│   │   ├── Conversion_to_nrrd.py      ← Converts nnU-Net output → .seg.nrrd
│   │   └── Remove_outside_voxels.py   ← Masks predictions to brain volume
│   └── dataset.json                   ← nnU-Net label map (region names ↔ IDs)
│   └── NG4990_Segments.seg.nrrd       ← template of label order for saving predicted output of nnU-Net
│
├── 2_landmark_placement/              ← Stage 2: ALPACA in 3D Slicer
│   ├── run_alpaca_pipeline.py         ← ALPACA multiprocess script (run inside Slicer)
│   ├── template_model/                ← Template surface meshes (.vtk), one per region
│   │   ├── DG/  CC/  HP/  ...
│   ├── template_landmarks/            ← Template landmark files (.mrk.json), one per region
│   │   ├── DG/  CC/  HP/  ...
│   └── convert_seg_to_vtk/
│       └── seg_nrrd_to_vtk.py         ← Converts .seg.nrrd → per-region .vtk files
│
├── 3_morphometrics/                   ← Stage 3: R statistical analysis
│   └── gpa_pca_analysis.R             ← Full GPA + PCA + ANOVA + LDA script
│
├── config/
│   └── paths_template.sh              ← Centralised path configuration (edit before running)
│
└── docs/
    ├── data_format.md                 ← File naming conventions and format specs
    └── environment_setup.md           ← Detailed environment setup instructions
    └── requirements.txt               ← Requirements for segmentation stage
    └── alpaca_requirements.txt        ← Requirements for 3D Slicer
```

---

## Hardware & Software Requirements

### Minimum Hardware
| Component | Requirement |
|-----------|-------------|
| GPU | NVIDIA GPU with ≥ 8 GB VRAM (CUDA 11.8) |
| RAM | ≥ 32 GB system RAM |
| Storage | ≥ 50 GB free disk space |

> **Note:** Stage 1 (nnU-Net inference) was run on a shared HPC cluster. Stage 2 (ALPACA) and Stage 3 (R) can run on a standard workstation without a GPU.

### Software Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11.13 | Stages 1 & 2 |
| nnU-Net v2 | 2.6.0 | Segmentation |
| 3D Slicer | 5.10.0 | ALPACA landmark placement |
| SlicerMorph (Slicer extension) | latest | Landmark registration |
| R | 4.5.2 | Statistical analysis |
| CUDA | 11.8 | GPU inference |
| Conda | any | Environment management |
| GCC | 11.2.0 | C/C++ compilation |

---

## Quick Start

```bash
# 1. Clone this repository
git clone https://github.com/beyza17/Full_Morph.git
cd Full_Morph/ngmm-pipeline

# 2. Configure your paths: "config/paths_template.sh"

# 3. Set up the Python environment (see Stage 1 setup below)
conda create -n env_ng python=3.11.13 pytorch==2.6.0 pytorch-cuda=11.8 -c pytorch -c nvidia
conda activate env_ng
module load gcc/11.2.0
pip install -r path/to/ngmm-pipeline/docs/requirements.txt

# 4. Run the full segmentation pipeline
mkdir -p /path/to/ngmm-pipeline/pipeline_data/logger # create logger output folder
1_segmentation/run_segmentation.sh # it needs input files and model weights to be runned (Check "Reproducing Paper Results" section), also it needs GPU 

# 5. Convert segmentations to .vtk for ALPACA (see Stage 2)
# Edit paths inside of the file. Must be run inside 3D Slicer's Python environment. 
/path/to/3dslicer/Slicer-5.10.0-linux-amd64/Slicer --no-splash --no-main-window --python-script "/path/to/2_landmark_placement/convert_seg_to_vtk/seg_nrrd_to_vtk.py" > output.log 2>&1 &

# 6. Prepare template data for ALPACA (see Stage 2)
cd /path/to/ngmm-pipeline/2_landmark_placement
huggingface-cli download bzayim/Full_Morph --include "template_landmarks/**" --local-dir .
huggingface-cli download bzayim/Full_Morph --include "template_model/**" --local-dir .

# 7. Run the complete ALPACA pipeline
# Edit paths inside of the file. Must be run inside 3D Slicer's Python environment. 
/path/to/3dslicer/Slicer-5.10.0-linux-amd64/Slicer --no-splash --no-main-window --python-script "/path/to/2_landmark_placement/run_alpaca_pipeline.py" > output.log 2>&1 &

# 8. Organize ALPACA outputs for R
python /path/to/ngmm-pipeline/2_landmark_placement/prepare_r_input.py

# 9. Run the R analysis in R terminal(see Stage 3)
source("/path/to/ngmm-pipeline/3_morphometrics/gpa_pca_analysis.R") # Edit paths inside of the file.
```

---

## Stage 1 — Segmentation with nnU-Net

### Overview

The script `1_segmentation/run_segmentation.sh` runs a 4-step prediction pipeline:

| Step | Script | What it does |
|------|--------|--------------|
| 1 | `File_name_new.py` | Renames raw `.nrrd` files to nnU-Net's `_0000` suffix convention |
| 2 | `Conversion_to_nifti.py` | Converts renamed `.nrrd` → `.nii.gz` (NIfTI format required by nnU-Net) |
| 3 | `nnUNetv2_predict` | Runs ensemble inference across 5 folds (`-f 0 1 2 3 4`) |
| 4 | `Conversion_to_nrrd.py` | Converts predicted NIfTI labels → `.seg.nrrd` (3D Slicer compatible) |
| 5 | `Remove_outside_voxels.py` | Removes predicted voxels outside the brain mask |

### Setup

```bash
# Create and activate the conda environment
conda create -n env_ng python=3.11.13 pytorch==2.6.0 pytorch-cuda=11.8 -c pytorch -c nvidia
conda activate env_ng
pip install -r path/to/ngmm-pipeline/docs/requirements.txt

# Set nnU-Net environment variables (or add to your .bashrc)
export nnUNet_raw=/path/to/ngmm-pipeline/nnUNet_raw_data
export nnUNet_preprocessed=/path/to/ngmm-pipeline/nnUNet_preprocessed
export nnUNet_results=/path/to/ngmm-pipeline/nnUNet_results
```

### Input Data Requirements

Create input folder with the bash command of:

```bash
mkdir -p /path/to/ngmm-pipeline/pipeline_data/processed_files_3
```

Place your raw HREM volumes in the `processed_files_3/` folder. 

```bash
cd /path/to/ngmm-pipeline/pipeline_data
huggingface-cli download bzayim/Full_Morph   --include "processed_files_3/**"   --local-dir .
```
Each sample must have a file matching the pattern:

```
{SAMPLE_ID}_RCL5_masked.nrrd
```

Example:
```
processed_files_3/
├── NG4975_RCL5_masked.nrrd
├── NG4976_RCL5_masked.nrrd
└── ...
```

### Running the Segmentation

```bash
# Option A: Process all new samples automatically (skips already-processed ones)
1_segmentation/run_segmentation.sh

# Option B: Process specific samples by name
1_segmentation/run_segmentation.sh NG4975 NG4976 NG4977
```

The script automatically detects which sample IDs already have outputs in `output_dir/` and skips them — making it safe to re-run incrementally.

### Expected Outputs

After running, outputs appear in the configured `output_dir/`:

```
segmentation_predictions/
├── NG4975_RCL5.seg.nrrd    ← Multi-label segmentation (all regions)
├── NG4976_RCL5.seg.nrrd
└── ...
```

Each `.seg.nrrd` file contains all segmented anatomical regions encoded as integer labels defined in `dataset.json`.

<img src="thalamus.png" alt="Segmentation prediction output of nnU-Net visualized on 3D Slicer software" width="500"/>

---

## Stage 2 — Landmark Placement with ALPACA

### Overview

ALPACA (Automated Landmarking through Pointcloud Alignment and Correspondence Analysis) transfers landmarks from a template brain to each target brain by:

- Registering the template surface to the target via RANSAC + ICP.
- Propagating landmarks using Coherent Point Drift (CPD).

This stage consists of two main sub-steps executed from the command line:

1. Convert `.seg.nrrd` segmentations to per-region `.vtk` surface meshes.
2. Run the ALPACA pipeline headlessly using 3D Slicer's background Python engine.

---

## 2a — Convert Segmentations to VTK Surfaces

After Stage 1, each sample contains a single `.seg.nrrd` file with all segmented regions. Before running ALPACA, each region must be extracted into an individual `.vtk` surface mesh and organized into region-specific directories:

```text
target_models/
├── DG/
│   ├── NG4975_DG.vtk
│   ├── NG4976_DG.vtk
│   └── ...
├── HP/
│   ├── NG4975_HP.vtk
│   └── ...
└── CC/
    └── ...
```

### Executing the Pipeline (Terminal)

Run the pipeline directly from the command line. Slicer launches silently in the background, processes every brain region across all subjects, writes the landmark files, and exits automatically.

```bash
/path/to/3dslicer/Slicer \
  --no-splash \
  --no-main-window \
  --python-script "/path/to/ngmm-pipeline/2_landmark_placement/convert_seg_to_vtk/seg_nrrd_to_vtk.py" > output.log 2>&1 &
```

**How it works**

The script reads `dataset.json` to map integer label IDs to region names (for example, label `3` → `DG`), extracts each segmentation using the marching cubes algorithm, and saves each surface mesh as:

```text
{REGION_NAME}/{SAMPLE_ID}_{REGION_NAME}.vtk
```

---

## 2b — Run ALPACA (Headless)

### Prerequisites

Before running the pipeline:

- Install **3D Slicer 5.10.0**.
- Install the **SlicerMorph** extension (includes ALPACA) via **Extension Manager**, then restart Slicer.
- Prepare one template model and one landmark file for each brain region:

```text
2_landmark_placement/
├── template_model/
│   ├── DG/
│   ├── HP/
│   └── CC/
└── template_landmarks/
    ├── DG/
    ├── HP/
    └── CC/
```

(See **Quick Start – Step 6** for template preparation.)

---

## Running the Pipeline

Execute the complete ALPACA workflow from the terminal:

```bash
/path/to/3dslicer/Slicer \
  --no-splash \
  --no-main-window \
  --python-script "/path/to/ngmm-pipeline/2_landmark_placement/run_alpaca_pipeline.py" > output.log 2>&1 &
```

This command:

- Launches Slicer without the graphical interface.
- Executes the ALPACA pipeline.
- Automatically exits after processing all regions and subjects.

---

## Installing Dependencies

If required Python packages are missing, install them into Slicer's Python environment (Python 3.12.10).

### From Terminal

```bash
/path/to/3dslicer/Slicer \
  --python-code "slicer.util.pip_install('-r /path/to/ngmm-pipeline/docs/alpaca_requirements.txt')"
```

### From Slicer's Python Interactor

```python
slicer.util.pip_install(
    "-r /path/to/ngmm-pipeline/docs/alpaca_requirements.txt"
)
```

---

## Key Parameters

Edit the following variables near the top of `run_alpaca_pipeline.py`:

```python
BASE = "/path/to/2_landmark_placement"   # Root directory
REGION = "DG"                            # Region to process specific region (or loop over regions)
```

---

## ALPACA Parameters Used in This Study

| Parameter | Value | Description |
|-----------|------:|-------------|
| projectionFactor | 0.01 | Point projection factor |
| pointDensity | 1.5 | Surface sampling density |
| normalSearchRadius | 2.0 | Normal estimation neighbourhood |
| FPFHNeighbors | 100 | Feature descriptor neighbours |
| FPFHSearchRadius | 5.0 | Feature search radius (mm) |
| distanceThreshold | 3.0 | RANSAC inlier threshold (mm) |
| maxRANSAC | 1,000,000 | Maximum RANSAC iterations |
| ICPDistanceThreshold | 1.5 | ICP refinement threshold (mm) |
| alpha | 2.0 | CPD regularisation |
| beta | 2.0 | CPD motion coherence |
| CPDIterations | 100 | Maximum CPD iterations |
| CPDTolerance | 0.001 | CPD convergence tolerance |

---

## Expected Outputs

```text
alpaca_run/
└── output/
    └── DG/
        └── individualEstimates/
            ├── NG4975_RCL5_DG_template.mrk.json
            ├── NG4976_RCL5_DG_template.mrk.json
            └── ...
```

The pipeline also generates:

```text
ALPACA_RMSE_summary.csv
```

This file contains:

- Per-subject RMSE against any available ground-truth landmarks.
- Total runtime for each processed subject.

---

## Quick Reference

### Run the complete Stage 2 pipeline

```bash
/path/to/3dslicer/Slicer \
  --no-splash \
  --no-main-window \
  --python-script "/path/to/ngmm-pipeline/2_landmark_placement/run_alpaca_pipeline.py" > output.log 2>&1 
``` 

### Install dependencies

```bash
/path/to/3dslicer/Slicer \
  --python-code "slicer.util.pip_install('-r /path/to/ngmm-pipeline/docs/alpaca_requirements.txt')"
```

---

## Example Output

<img src="HP.png" alt="HP Region with landmarks on 3D Slicer Software" width="500"/>
---

## Stage 3 — Statistical Analysis in R

### Overview

The R script `3_morphometrics/gpa_pca_analysis.R` processes landmark files from all regions and produces:

- Generalised Procrustes Analysis (GPA) aligned coordinates
- PCA of shape space with variance explained
- Outlier detection (Mean + 2×SD threshold)
- Procrustes ANOVA with permutation (RRPP, 999 iterations)
- Pairwise group comparisons
- Cross-validated LDA with permutation test (1000 iterations)
- Multi-panel matrix plots (PDF) across all regions

### Setup

Requires R >= 4.4.0 (tested on R 4.5.2).

Exact package versions — including all transitive dependencies — are 
pinned in `renv.lock`. To reproduce the exact working environment:

```r
install.packages("renv")
renv::restore()
```

This will install the following direct dependencies at their pinned 
versions (see `renv.lock` for the complete dependency tree):

| Package     | Version   |
|-------------|-----------|
| geomorph    | 4.0.10    |
| RRPP        | 2.1.2     |
| tidyverse   | 2.0.0     |
| jsonlite    | 2.0.0     |
| ggforce     | 0.5.0     |
| ggh4x       | 0.3.1     |
| ggnewscale  | 0.5.2     |
| MASS        | 7.3-65    |
| sp          | 2.2-0     |
| devtools    | 2.4.6     |


### Input Data Requirements

The script expects one folder per brain region, each containing `.mrk.json` landmark files output by ALPACA:

```
projections_out/
├── DG/
│   ├── NG4975_RCL5_DG_template.mrk.json
│   ├── NG4976_RCL5_DG_template.mrk.json
│   └── ...
├── HP/
│   └── ...
└── CC/
    └── ...
```

**File naming requirement:** Each `.mrk.json` filename must start with the sample ID in the format `NG{NNNN}` (e.g., `NG4975`). The script uses this prefix to match samples to genotype metadata.

### Genotype Table

Edit the `geno_table` at the top of `gpa_pca_analysis.R` to match your sample IDs and genotypes:

```r
geno_table <- tribble(
  ~ID,      ~geno,
  "NG4975", "WT",
  "NG4976", "HOM",
  # Add all your samples here...
)
```

Supported genotype labels: `WT` (wild-type), `HOM` (homozygous), `IT` (heterozygous).

### Running the Analysis

```bash
# Edit the root_dir path at the top of the script first
source("/path/to/ngmm-pipeline/3_morphometrics/gpa_pca_analysis.R")
```

### Expected Outputs

For each region folder, a timestamped subfolder is created:

```
DG/
└── 2024-01-15_10_30_00/
    ├── DG_meanShape.csv              ← GPA consensus shape
    ├── DG_Outlier_Check.png          ← Procrustes distance plot
    ├── DG_outliers.csv               ← Outlier flags per specimen
    ├── DG_eigenvalues.csv            ← PC eigenvalues + variance explained
    ├── DG_eigenvectors.csv           ← PC loadings
    ├── DG_pcScores.csv               ← Per-specimen PC scores + genotype
    ├── DG_outputData.csv             ← Aligned coords + metadata
    ├── DG_pcwise_genotype_effects.csv← ANOVA p-values per PC (FDR corrected)
    ├── DG_pairwise_tests.csv         ← WT vs HOM pairwise Procrustes tests
    ├── DG_stats_results.csv          ← ANOVA p / LDA accuracy / LDA perm-p
    └── DG_PCA_Best_Separation.png    ← PCA scatter plot
```

At the root level:
```
projections_out/
├── FULL_STATISTICS_SUMMARY.csv       ← One row per region: ANOVA-p, LDA%, LDA-p
├── MATRIX_1_PC1_PC2.pdf             ← All regions: PC1 vs PC2 matrix
├── MATRIX_2_BEST_SEPARATION.pdf     ← All regions: best discriminating PCs
└── MATRIX_2_SIGNIFICANT_HULLS.pdf   ← As above, with convex hulls for sig. regions
```
<img src="statistics.png" alt="MATRIX_2_SIGNIFICANT_HULLS.pdf" width="500"/>

---

## Data Format Reference

### File Naming Convention

| Stage | File | Naming Pattern | Example |
|-------|------|----------------|---------|
| Input HREM | `.nrrd` | `{ID}_RCL5_masked.nrrd` | `NG4975_RCL5_masked.nrrd` |
| Segmentation | `.seg.nrrd` | `{ID}_RCL5.seg.nrrd` | `NG4975_RCL5.seg.nrrd` |
| Surface mesh | `.vtk` | `{ID}_{REGION}.vtk` | `NG4975_DG.vtk` |
| Landmarks (pred) | `.mrk.json` | `{ID}_RCL5_{REGION}_template.mrk.json` | `NG4975_RCL5_DG_template.mrk.json` |

### Label Map (`dataset.json`)

The `dataset.json` file defines the mapping between integer labels in nnU-Net predictions and anatomical region names. It follows the standard nnU-Net dataset format:

```json
{
  "labels": {
    "background": 0,
    "DG": 1,
    "HP": 2,
    "CC": 3,
    ...
  }
}
```

---

## Reproducing Paper Results

To reproduce the exact results from the paper:

1. **Obtain the data** — available at [HuggingFace link — [here](https://huggingface.co/bzayim/Full_Morph/tree/main/processed_files_3)]
2. **Download trained model weights** — available at [HuggingFace link — [here](https://huggingface.co/bzayim/Full_Morph/tree/main/Dataset004_first)]
3. **Place "Dataset004_first" folder with model weights** in `/path/to/ngmm-pipeline/pipeline_data/nnUNet_results`

```bash
bash mkdir -p /path/to/ngmm-pipeline/pipeline_data/nnUNet_results
cd /path/to/ngmm-pipeline/pipeline_data/nnUNet_results
huggingface-cli download bzayim/Full_Morph   --include "Dataset004_first/nnUNetTrainer__nnUNetPlans__3d_fullres/**"   --local-dir .
```

4. **Configure paths** in `ngmm-pipeline\config\paths_template.sh`
5. **Run all three stages** as described above

> All random seeds are fixed. RRPP permutation tests use `iter = 999`. LDA permutation uses `n_perm = 1000`.

---

## Troubleshooting

**nnU-Net does not find my dataset**  
→ Ensure `nnUNet_raw`, `nnUNet_preprocessed`, and `nnUNet_results` are exported as environment variables *before* running the script. Check `echo $nnUNet_raw`.

**ALPACA crashes with "no points after subsampling"**  
→ Increase `pointDensity` (try `0.5`) or check that your `.vtk` surface mesh is not empty. Very small structures may need lower density.

**R script error: "Inconsistent landmark counts"**  
→ Uncomment the sanity-check block near line 60 of `gpa_pca_analysis.R` to identify which file has a different landmark count. Regenerate that sample's ALPACA output.

**R error: "system is computationally singular"**  
→ You likely have too few specimens for LDA (< 4 per group). The script will log `Insufficient Data` in the stats summary and skip LDA for that region.

**Segmentation script produces empty output for some samples**  
→ Check that the input file matches `{ID}_RCL5_masked.nrrd` exactly. The auto-selection logic filters on this suffix pattern.

---

## Citation

If you use this pipeline in your research, please cite:

```bibtex
@inproceedings{zayim2026segmentation,
  title     = {Automatic Segmentation for 3D Morphometric Analysis of the Mouse Brain},
  author    = {Beyza Zayim, Emilia Skutunova, Taiabur Rahman, Nida Yardim, Salma Zarfaoui, Hanzala Daud, Alienor Vaudene,  Binnaz Yalcin,   Alain Lalande, Fabrice Meriaudeau1,  and StephanCollins },
  booktitle = {Proceedings of the International Conference on Pattern Recognition (ICPR)},
  year      = {2026}
}
```

---
## References

```bibtex
@article{porto2021alpaca,
  title     = {ALPACA: A fast and accurate computer vision approach for automated landmarking of three-dimensional biological structures},
  author    = {Porto, A. and others},
  journal   = {Methods in Ecology and Evolution},
  volume    = {12},
  pages     = {2129--2144},
  year      = {2021}
}
@article{isensee2021nnuet,
  title     = {nnU-Net: A self-configuring method for deep learning-based biomedical image segmentation},
  author    = {Isensee, F. and others},
  journal   = {Nature Methods},
  volume    = {18},
  pages     = {203--211},
  year      = {2021}
}
```

---
## License

This project is licensed under the MIT License — see `LICENSE` for details.

---

*For questions, open a GitHub Issue or contact [beyzayim17@gmail.com].*
