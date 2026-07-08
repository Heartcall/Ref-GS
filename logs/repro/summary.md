# Ref-GS Reproduction Summary

Generated: 2026-07-08

Commit: `08a459b824e9ac20f7d3643b86fa257f73120206`

## Scope

This summary covers the Ref-GS reproduction runs under `output/repro_paper` and
the matching logs under `logs/repro`.

- Data root: `/data/liuly/dataset/3DGS`
- Shiny Blender Synthetic input: `/data/liuly/dataset/3DGS/Shiny Blender Synthetic`
- GlossySynthetic input: `/data/liuly/dataset/3DGS/GlossySyntheticConverted`
- NeRF Synthetic input: `/data/liuly/dataset/3DGS/NeRF Synthetic`
- Output root: `output/repro_paper`
- Log root: `logs/repro`
- Training iteration summarized here: `31000`

## Verification

Fresh checks were run after the jobs completed:

- Each scene has `point_cloud/iteration_31000/point_cloud.ply`.
- Each scene has rendered test images.
- Each scene has `results.json` and `metrics.csv`.
- Logs were scanned for `Traceback`, `RuntimeError`, `CUDA error`,
  `FileNotFoundError`, `OutOfMemory`, and `No such file`; no matching errors
  were found in the final logs.
- `python -m py_compile scripts/refgs_runner.py scripts/run_refnerf.py scripts/run_glossy_synthetic.py scripts/run_nerf_synthetic.py render.py nero2blender.py utils/image_utils.py`
  completed with exit code 0.

Smoke testing found GPU 7 could report CUDA availability but failed tensor
allocation with `CUDA-capable devices are busy or unavailable`; formal runs were
completed on GPUs 1 and 4.

## Dataset Averages

| Dataset | Scenes | Avg PSNR | Avg SSIM | Avg LPIPS |
|---|---:|---:|---:|---:|
| Shiny Blender Synthetic / Ref-NeRF | 6 | 31.0874 | 0.9709 | 0.0490 |
| GlossySynthetic | 6 | 29.7445 | 0.9629 | 0.0333 |
| NeRF Synthetic | 8 | 29.1239 | 0.9489 | 0.0538 |

## Per-Scene Metrics

| Dataset | Scene | Status | Iter | Renders | PSNR | SSIM | LPIPS |
|---|---|---|---:|---:|---:|---:|---:|
| Ref-NeRF | helmet | ok | 31000 | 200 | 30.5021 | 0.9779 | 0.0366 |
| Ref-NeRF | car | ok | 31000 | 200 | 31.1961 | 0.9653 | 0.0262 |
| Ref-NeRF | ball | ok | 31000 | 200 | 30.0379 | 0.9716 | 0.0812 |
| Ref-NeRF | teapot | ok | 31000 | 200 | 35.1097 | 0.9917 | 0.0164 |
| Ref-NeRF | coffee | ok | 31000 | 200 | 31.9233 | 0.9688 | 0.0660 |
| Ref-NeRF | toaster | ok | 31000 | 200 | 27.7550 | 0.9503 | 0.0675 |
| GlossySynthetic | bell_blender | ok | 31000 | 16 | 30.1189 | 0.9699 | 0.0233 |
| GlossySynthetic | tbell_blender | ok | 31000 | 16 | 31.2155 | 0.9676 | 0.0337 |
| GlossySynthetic | potion_blender | ok | 31000 | 16 | 29.9263 | 0.9595 | 0.0463 |
| GlossySynthetic | teapot_blender | ok | 31000 | 16 | 27.0112 | 0.9533 | 0.0379 |
| GlossySynthetic | luyu_blender | ok | 31000 | 16 | 29.2744 | 0.9551 | 0.0332 |
| GlossySynthetic | cat_blender | ok | 31000 | 16 | 30.9207 | 0.9719 | 0.0257 |
| NeRF Synthetic | ship | ok | 31000 | 200 | 28.3503 | 0.8746 | 0.1301 |
| NeRF Synthetic | ficus | ok | 31000 | 200 | 24.4118 | 0.9253 | 0.0740 |
| NeRF Synthetic | lego | ok | 31000 | 200 | 30.5428 | 0.9726 | 0.0277 |
| NeRF Synthetic | mic | ok | 31000 | 200 | 32.3661 | 0.9785 | 0.0302 |
| NeRF Synthetic | hotdog | ok | 31000 | 200 | 33.1571 | 0.9804 | 0.0293 |
| NeRF Synthetic | chair | ok | 31000 | 200 | 29.0539 | 0.9760 | 0.0281 |
| NeRF Synthetic | materials | ok | 31000 | 200 | 30.2855 | 0.9500 | 0.0506 |
| NeRF Synthetic | drums | ok | 31000 | 200 | 24.8235 | 0.9336 | 0.0603 |

## Geometry Metrics

Geometry metrics were added after the RGB/LPIPS summary. They compare saved
Ref-GS Gaussian point-cloud centers against available dataset geometry in raw
coordinates, with no ICP, scale fitting, or similarity alignment.

Reference protocol:

- Ref-NeRF/Shiny Blender Synthetic: sampled scene GT mesh, accepted GT.
- GlossySynthetic: `eval_pts.ply`, accepted evaluation points.
- NeRF Synthetic: `points3d.ply`, proxy only and not accepted GT.

Normal-angle metrics are reported as `NA` because the saved Ref-GS prediction
point clouds do not contain normals.

| Dataset | Rows | Protocol | Chamfer-L1 | Chamfer-L2 | Hausdorff | F@0.5% | F@1% | F@2% |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| Ref-NeRF | 6 | accepted GT | 0.021572 | 0.002087 | 0.452548 | 0.6018 | 0.8202 | 0.9237 |
| GlossySynthetic | 6 | accepted GT | 0.010846 | 0.000365 | 0.337523 | 0.7694 | 0.9332 | 0.9796 |
| NeRF Synthetic | 8 | proxy only | 0.184408 | 0.084345 | 1.048907 | 0.0736 | 0.1754 | 0.2671 |

Geometry metric files:

- `logs/repro/geometry_summary.md`
- `logs/repro/geometry_metrics.csv`
- `logs/repro/geometry_metrics.json`

## Success And Failure Summary

Successful train/render/eval scenes:

- Ref-NeRF: `helmet`, `car`, `ball`, `teapot`, `coffee`, `toaster`
- GlossySynthetic: `bell_blender`, `tbell_blender`, `potion_blender`,
  `teapot_blender`, `luyu_blender`, `cat_blender`
- NeRF Synthetic: `ship`, `ficus`, `lego`, `mic`, `hotdog`, `chair`,
  `materials`, `drums`

Failed formal scenes: none.

Known runtime caveat:

- GPU 7 was not usable for this run despite being listed as idle; smoke testing
  failed during CUDA tensor allocation. The final full runs avoided GPU 7.

## Paper-Alignment Caveats

- The summary uses the current Ref-GS training entrypoints and renderer in this
  repository.
- GlossySynthetic was evaluated from Blender-style converted data under
  `/data/liuly/dataset/3DGS/GlossySyntheticConverted`; the original raw data was
  not moved or overwritten.
- Exact paper alignment is still limited by missing or unclear details in the
  public paper/repository, including some evaluation-resolution details, LPIPS
  weight/version assumptions, and any unpublished scene-specific tuning.

For machine-readable per-scene values, see `logs/repro/metrics_summary.csv`.
