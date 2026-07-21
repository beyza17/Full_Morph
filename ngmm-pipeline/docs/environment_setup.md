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

## Stage 2 — Headless Execution (Automated Pipeline)

1. Download [3D Slicer 5.6+](https://download.slicer.org/) 
2. Instead of pasting code into the Slicer console, the pipeline is now fully automated via the command line.

```bash
/path/to/3dslicer/Slicer-5.10.0-linux-amd64/Slicer --no-splash --no-main-window --python-script "/path/to/2_landmark_placement/run_alpaca_pipeline.py" > output.log 2>&1 &
```

## Stage 3 — R

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

### Manual install (not recommended — versions may drift from what was tested)

If you prefer not to use `renv`, you can install packages manually, but 
compatibility with `geomorph`/`RRPP` is only guaranteed at the pinned 
versions above:

```r
install.packages(c(
  "devtools", "geomorph", "tidyverse", "jsonlite",
  "ggforce", "sp", "ggh4x", "ggnewscale", "MASS", "RRPP"
))
```

If `ggh4x` or `ggnewscale` fail to install from CRAN:
```r
devtools::install_github("teunbrand/ggh4x")
devtools::install_github("eliocamp/ggnewscale")
```
