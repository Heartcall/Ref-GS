# Ref-GS : Directional Factorization for 2D Gaussian Splatting

## [Project Page](https://ref-gs.github.io/) | [Paper](https://arxiv.org/pdf/2412.00905) | [arXiv](https://arxiv.org/abs/2412.00905)

> Ref-GS : Directional Factorization for 2D Gaussian Splatting<br>
> [Youjia Zhang](https://youjiazhang.github.io/), [Anpei Chen](https://apchenstu.github.io/), [Yumin Wan](https://ref-gs.github.io/), [Zikai Song](https://skyesong38.github.io/), [Junqing Yu](https://scholar.google.com/citations?hl=zh-CN&user=_UjqBfcAAAAJ), [Yawei Luo](https://scholar.google.com/citations?hl=zh-CN&user=pnVwaGsAAAAJ), [Wei Yang](https://weiyang-hust.github.io/)<br>
> CVPR 2025

![teaser](assets/teaser.jpg)

## ⚙️ Setup

### Install Environment via Anaconda (Recommended)
```bash
conda create -n ref_gs python=3.7.16
conda activate ref_gs
pip install -r requirements.txt

pip install submodules/diff-surfel-rasterization-real
pip install submodules/diff-surfel-rasterization
pip install submodules/diff-surfel-2dgs
pip install submodules/simple-knn

git clone https://github.com/NVlabs/nvdiffrast
pip install .
```

## 📦 Dataset
We mainly test our method on [Shiny Blender Synthetic](https://storage.googleapis.com/gresearch/refraw360/ref.zip), [Shiny Blender Real](https://storage.googleapis.com/gresearch/refraw360/ref_real.zip), [Glossy Synthetic](https://liuyuan-pal.github.io/NeRO/) and [NeRF Synthetic dataset](https://drive.google.com/drive/folders/128yBriW1IG_3NJ5Rp7APSTZsJqdJdfc1). Please run the script `nero2blender.py` to convert the format of the Glossy Synthetic dataset.

Put them under the `data` folder:
```bash
data
└── refnerf
    └── car
    └── toaster
└── nerf_synthetic
    └── hotdog
    └── lego
```

## 🏃 Training
We provide the script to test our code on each scene of datasets. Just run:
```
sh train.sh
```
You may need to modify the path in `train.sh`

## Reproduction

This repository keeps the original Ref-GS training code paths:

- Shiny Blender Synthetic / Ref-NeRF scenes use `train.py`.
- NeRF Synthetic scenes use `train-NeRF.py`.
- Glossy Synthetic scenes use `train-NeRO.py`.
- Shiny Blender Real scenes use `train-real.py`.
- Rendering and evaluation use this repository's `gaussian_renderer`, `Scene`, and `GaussianModel`.

The reproduction scripts only organize commands around those entrypoints. They do not import Ref-DGS model code, priors, dual-Gaussian logic, or losses.

### Data Layout

By default the scripts look under:

```bash
/data/liuly/dataset/3DGS
├── Shiny Blender Synthetic
│   ├── ball
│   ├── car
│   ├── coffee
│   ├── helmet
│   ├── teapot
│   └── toaster
├── NeRF Synthetic
│   ├── chair
│   ├── drums
│   ├── ficus
│   ├── hotdog
│   ├── lego
│   ├── materials
│   ├── mic
│   └── ship
├── GlossySyntheticConverted
│   ├── bell_blender
│   ├── tbell_blender
│   ├── potion_blender
│   ├── teapot_blender
│   ├── luyu_blender
│   └── cat_blender
└── Shiny Blender Real
    ├── gardenspheres
    ├── sedan
    └── toycar
```

Use `--data-root` and `--dataset-subdir` if your local layout differs.

### Convert Glossy Synthetic

Raw NeRO Glossy Synthetic scenes must be converted before Ref-GS can load them:

```bash
python nero2blender.py \
  --path /data/liuly/dataset/3DGS/GlossySynthetic \
  --scene bell \
  --output-root /data/liuly/dataset/3DGS/GlossySyntheticConverted
```

The converter expects the raw scene folder, `<id>-camera.pkl`, `<id>-depth.png`, RGB images, and `synthetic_split_128.pkl`. It writes `transforms_train.json`, `transforms_test.json`, `rgb/*.png`, and copies `eval_pts.ply` when present.

### Dry-Run Commands

Dry-run prints commands without starting training:

```bash
python scripts/run_refnerf.py --scene coffee --gpu 0 --dry-run
python scripts/run_nerf_synthetic.py --scene lego --gpu 0 --dry-run
python scripts/run_glossy_synthetic.py --scene bell --gpu 0 --dry-run
python scripts/run_ref_real.py --scene gardenspheres --gpu 0 --dry-run
```

`train.sh` is now a safe dry-run index over all four runners.

### Single-Scene Train / Render / Eval

Run training explicitly with `--train`:

```bash
python scripts/run_refnerf.py --scene coffee --gpu 0 --train
```

Render the latest saved checkpoint:

```bash
python scripts/run_refnerf.py --scene coffee --gpu 0 --render --iteration -1
```

Evaluate PSNR, SSIM, and LPIPS when LPIPS weights are available:

```bash
python scripts/run_refnerf.py --scene coffee --gpu 0 --eval --iteration -1
```

Rendered images and metrics are written under the model directory, for example:

```bash
output/repro/refnerf/coffee/test/ours_<iter>/renders
output/repro/refnerf/coffee/results.json
output/repro/refnerf/coffee/metrics.csv
```

LPIPS may require local cached weights or network access through `torch.hub`. If LPIPS cannot initialize, `results.json` records `lpips: null` and keeps PSNR/SSIM.

### Batch Runs

Use `--scene all` or omit `--scene` to generate jobs for all known scenes in a dataset:

```bash
python scripts/run_refnerf.py --gpu 0 --train
python scripts/run_refnerf.py --gpu 0 --render --eval --iteration -1
```

The scripts never delete an existing output directory. Logs go to `logs/repro/<dataset>/<scene>/<action>` by default. Use `--output-root` and `--log-root` to separate experiments.

### Geometry Evaluation

RGB reproduction metrics are PSNR, SSIM, and LPIPS. The paper-comparable
geometry metric handled by this repository is normal Mean Angular Error in
degrees (`normal_mae_deg` / MAE°), when both Ref-GS rendered normal buffers and
GT normal maps are available under the evaluated split.

First inventory the dataset geometry assets:

```bash
python scripts/inventory_geometry_data.py \
  --data-root /data/liuly/dataset/3DGS \
  --output logs/repro/geometry_data_inventory.json \
  --markdown logs/repro/geometry_data_inventory.md
```

Then export Ref-GS geometry buffers from existing checkpoints and evaluate:

```bash
python scripts/run_geometry_eval.py \
  --dataset all \
  --gpu 1 \
  --iteration 31000 \
  --output-root output/repro_paper \
  --log-root logs/repro \
  --data-root /data/liuly/dataset/3DGS \
  --save-geometry \
  --eval
```

`render.py --save-geometry --geometry-only` saves `.npy` precision normal/depth
buffers plus visualization PNGs under each split directory. It uses the current
Ref-GS renderer and checkpoint; it does not retrain or modify RGB metrics.

Geometry outputs:

```bash
output/repro_paper/<dataset>/<scene>/geometry_metrics.json
output/repro_paper/<dataset>/<scene>/geometry_metrics.csv
output/repro_paper/<dataset>/geometry_summary.csv
output/repro_paper/<dataset>/geometry_summary.json
logs/repro/geometry_summary.md
logs/repro/geometry_summary.csv
logs/repro/geometry_summary.json
```

Chamfer/F-score values currently use saved Gaussian centers as the prediction
point set unless an extracted surface mesh is explicitly supplied. Those rows
are marked `metric_family=proxy_geometry` or carry notes that the
Chamfer/F-score part is proxy-only, with `paper_comparable=false` for paper
normal-MAE comparisons. Missing GT normal/depth/mesh is recorded as
`missing_gt_*`; no metric is fabricated.

### Hyperparameter Provenance

The runner preserves the important hyperparameters from the original `train.sh` comments:

- Ref-NeRF: `run_dim=256`, `albedo_bias=0`, and `coffee` uses `albedo_lr=0.002`.
- NeRF Synthetic: `run_dim=64` for most scenes, `materials` uses `run_dim=256`, and listed scenes preserve `gsrgb_loss` / `albedo_lr` from `train.sh`.
- Glossy Synthetic: `run_dim=256`, `albedo_bias=2`, `albedo_lr=0.0005`, `init_until_iter=3000`.
- Shiny Blender Real: `run_dim=256`, `albedo_bias=2`, `albedo_lr=0.0005`, plus the scene-specific `env_scope_center`, `env_scope_radius`, `init_until_iter`, resolution, and `xyz_axis` values from `train.sh`.

Still uncertain from the paper/released repo:

- Whether all paper tables used exactly 31k iterations or longer scene-specific schedules.
- Whether real-scene environment sphere parameters were tuned beyond the three released examples.
- Whether LPIPS preprocessing matched the paper implementation beyond the standard Ref-GS image range used here.
- Whether Glossy Synthetic scenes outside the original `train.sh` list should be included in paper-scale reproduction.

## Sparse-View Evaluation

Sparse-view evaluation uses the same Ref-GS training and rendering entrypoints
as the full-view reproduction, but reduces only the training split. The generated
scene keeps `transforms_test.json` byte-for-byte identical to the original full
test split, and writes a new `transforms_train.json` containing the selected
training frames. Original data under `/data/liuly/dataset/3DGS` is not modified.

Generated sparse data is written by default to:

```bash
/data/liuly/dataset/3DGS/SparseViewGenerated/<dataset>/<strategy>/views_<N>/seed_<S>/<scene>/
```

Experiment outputs and logs are kept separate from the full-view reproduction:

```bash
output/sparse_view/<dataset>/<strategy>/views_<N>/seed_<S>/<scene>/
logs/sparse_view/<dataset>/<strategy>/views_<N>/seed_<S>/<scene>/{train,render,eval}
```

Supported datasets are `refnerf`, `glossy_synthetic`, and `nerf_synthetic`.
Supported selection strategies are:

- `random`: seeded random subset, restored to original frame order.
- `uniform_index`: uniformly spaced indices in the original train-frame order.
- `uniform_pose`: uniformly spaced azimuths from camera centers, falling back to
  `uniform_index` if poses are missing.
- `farthest_pose`: seeded farthest-point selection over camera centers, falling
  back to `uniform_index` if poses are missing.

Dry-run a sparse split:

```bash
conda run -n ref_gs python scripts/make_sparse_view_dataset.py \
  --dataset refnerf \
  --scene coffee \
  --views 3 \
  --strategy uniform_pose \
  --seed 0 \
  --data-root /data/liuly/dataset/3DGS \
  --output-root /data/liuly/dataset/3DGS/SparseViewGenerated \
  --dry-run
```

Create that split:

```bash
conda run -n ref_gs python scripts/make_sparse_view_dataset.py \
  --dataset refnerf \
  --scene coffee \
  --views 3 \
  --strategy uniform_pose \
  --seed 0 \
  --data-root /data/liuly/dataset/3DGS \
  --output-root /data/liuly/dataset/3DGS/SparseViewGenerated
```

Run a 10-step smoke test. The train iteration is passed to `train.py` through
`--extra-train-arg`; `--iteration` controls render/eval checkpoint loading:

```bash
conda run -n ref_gs python scripts/run_sparse_view_eval.py \
  --dataset refnerf \
  --scene coffee \
  --views 3 \
  --strategy uniform_pose \
  --seed 0 \
  --gpu 1 \
  --make-data \
  --train --render --eval \
  --iteration 10 \
  --output-root output/sparse_view_smoke \
  --log-root logs/sparse_view_smoke \
  --extra-train-arg=--iterations \
  --extra-train-arg=10
```

Main uniform-pose run:

```bash
conda run -n ref_gs python scripts/run_sparse_view_eval.py \
  --dataset all \
  --views 3 6 9 12 24 \
  --strategy uniform_pose \
  --seed 0 \
  --gpu 1 \
  --make-data \
  --train --render --eval \
  --iteration 31000 \
  --data-root /data/liuly/dataset/3DGS \
  --sparse-data-root /data/liuly/dataset/3DGS/SparseViewGenerated \
  --output-root output/sparse_view \
  --log-root logs/sparse_view \
  --skip-existing
```

Random subsets should be run across multiple seeds because sparse camera choice
can dominate scene quality:

```bash
for seed in 0 1 2; do
  conda run -n ref_gs python scripts/run_sparse_view_eval.py \
    --dataset all \
    --views 3 6 9 12 24 \
    --strategy random \
    --seed ${seed} \
    --gpu 4 \
    --make-data \
    --train --render --eval \
    --iteration 31000 \
    --data-root /data/liuly/dataset/3DGS \
    --sparse-data-root /data/liuly/dataset/3DGS/SparseViewGenerated \
    --output-root output/sparse_view \
    --log-root logs/sparse_view \
    --skip-existing
done
```

Summarize sparse RGB metrics against the full-view baseline in
`output/repro_paper` and `logs/repro/metrics_summary.csv`:

```bash
conda run -n ref_gs python scripts/summarize_sparse_view.py \
  --sparse-output-root output/sparse_view \
  --baseline-output-root output/repro_paper \
  --log-root logs/sparse_view \
  --iteration 31000
```

The summary files are:

```bash
logs/sparse_view/sparse_view_summary.md
logs/sparse_view/sparse_view_summary.csv
logs/sparse_view/sparse_view_summary.json
```

Sparse-view numbers are not directly interchangeable with the paper/full-view
main table unless the same sparse-view protocol, selected views, strategy, seed,
iteration, renderer, and test split are used. Geometry/proxy metrics should stay
separate from the sparse-view RGB summary unless explicitly reported as optional
geometry diagnostics.

## ✍️ Test
We provide simple jupyter notebooks `notebook/test.ipynb` to explore the model.

For mesh extraction, we adopt the same method as used in [2DGS](https://surfsplatting.github.io/).

## 🫡 Acknowledgments

This work is built on many amazing research works and open-source projects,

- [NeRF-Casting: Improved View-Dependent Appearance with Consistent Reflections](https://dorverbin.github.io/nerf-casting/)
- [GaussianShader: 3D Gaussian Splatting with Shading Functions for Reflective Surfaces](https://github.com/Asparagus15/GaussianShader)
- [3D Gaussian Splatting with Deferred Reflection](https://github.com/gapszju/3DGS-DR/tree/main)
- [2DGS: 2D Gaussian Splatting for Geometrically Accurate Radiance Fields](https://surfsplatting.github.io/)

We are grateful to the authors for releasing their code.

## 📜 Citation

If you find our work useful in your research, please consider giving a star :star: and citing the following paper :pencil:.

```
@article{zhang2024ref,
  title={Ref-GS: Directional Factorization for 2D Gaussian Splatting},
  author={Zhang, Youjia and Chen, Anpei and Wan, Yumin and Song, Zikai and Yu, Junqing and Luo, Yawei and Yang, Wei},
  journal={arXiv preprint arXiv:2412.00905},
  year={2024}
}
```

## ✉️ Contact

For feedback, questions, or press inquiries please contact [Youjia Zhang](Youjiazhang@hust.edu.cn).
