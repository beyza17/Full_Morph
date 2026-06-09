# Environment Setup

## Stage 1 — Python / nnU-Net

```bash
conda create -n env_ng python=3.9
conda activate env_ng
pip install nnunetv2
pip install SimpleITK pynrrd numpy
```

Add to `~/.bashrc`:
```bash
export nnUNet_raw=/path/to/nnUNet_raw_data
export nnUNet_preprocessed=/path/to/nnUNet_preprocessed
export nnUNet_results=/path/to/nnUNet_results
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
