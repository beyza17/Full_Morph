# Environment Setup

## Stage 1 — Python / nnU-Net

```bash
conda create -n env_ng python=3.11.13 pytorch==2.6.0 pytorch-cuda=11.8 -c pytorch -c nvidia
conda activate env_ng
pip install -r path/to/ngmm-pipeline/docs/requirements.txt
```

Add to `~/.bashrc`:
```bash
export nnUNet_raw=/path/to/ngmm-pipeline/pipeline_data/nnUNet_raw_data
export nnUNet_preprocessed=/path/to/ngmm-pipeline/pipeline_data/nnUNet_preprocessed
export nnUNet_results=//path/to/ngmm-pipeline/pipeline_data/nnUNet_results
```

## Stage 2 — 3D Slicer + ALPACA

1. Download [3D Slicer 5.6+](https://download.slicer.org/)
2. Open Slicer → Extensions Manager → search **SlicerMorph** → install
3. Restart Slicer
4. Verify: `Modules → SlicerMorph → ALPACA` is visible

## Stage 3 — R

```r
install.packages(c(
  "devtools", "geomorph", "tidyverse", "jsonlite",
  "ggforce", "sp", "ggh4x", "ggnewscale", "MASS", "RRPP"
))
```

Tested on R 4.3.2. If `ggh4x` or `ggnewscale` fail to install from CRAN:
```r
devtools::install_github("teunbrand/ggh4x")
devtools::install_github("eliocamp/ggnewscale")
```
