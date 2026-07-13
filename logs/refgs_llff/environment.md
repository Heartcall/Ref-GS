# Ref-GS LLFF Environment Audit

- Repository: `/home/liuly/Surface_Reconstruction/Glossy/Ref-GS`
- implementation base commit: `e3e14906cabb9cc74cc8b81deec67cfa1e588173`
- Python: `/home/liuly/anaconda3/envs/ref_gs/bin/python`, Python 3.7.12
- PyTorch/CUDA runtime: PyTorch 1.12.1, CUDA 11.3
- Host-visible GPU-1 probe: CUDA available, one visible device, logical
  `cuda:0`, NVIDIA RTX A5000
- Smoke GPU before launch: physical GPU 1, 24,244 MiB free, 3 MiB used
- Restricted sandbox probe reported no CUDA devices. This is a launch-context
  artifact and is not used as the execution gate.

## Entrypoints

- Training: `train.py`
- Test rendering: `render.py --renderer refgs --image-key pbr_rgb --skip_train`
- Formal shared evaluation: `scripts/evaluate_refgs_llff.py`, using the same
  PSNR/SSIM implementations and LPIPS-VGG backbone as FSGS `metrics.py`
- The native `render.py --metrics` result may be retained but is not the formal
  comparison metric.

## Loader audit

The existing loader dispatch supported COLMAP (`sparse`) and Blender
(`transforms_train.json`). The LLFF adaptation adds
`refgs_llff_manifest.json` as the highest-priority explicit format. It neither
scans candidate images nor calls the existing full-scene COLMAP point reader.

Original LLFF intrinsics are `SIMPLE_RADIAL`, 4032 x 3024. Actual images are
504 x 378 for `images_8` and 1008 x 756 for `images_4`. The manifest records
the original and deterministically scaled focal length, principal point,
dimensions, and unchanged radial coefficient.

The downloaded author preprocessing contains only `images.txt` and
`fused.ply` per scene. It does not contain the anticipated `cameras.txt` or
`points3D.txt`; the approved deterministic adaptation is recorded in
`protocol.md`.

## Hardcoding audit

- `train.py` and `train-real.py` do not set `CUDA_VISIBLE_DEVICES`.
- Their previous top-level `CUDA_LAUNCH_BLOCKING=1` assignments were removed.
- The runner passes an explicit absolute model path, so source defaults cannot
  redirect this experiment into a fixed output directory.
- Generic `train.py` uses the existing black-background setting.
- `train-real.py` requires `env_scope_center`, `env_scope_radius`, and
  `xyz_axis`, but this experiment uses the generic path and therefore requires
  no environment sphere.

## Pre-smoke verification

`py_compile` passed. The exact unit-test gate completed 88 tests with zero
failures and zero errors. No environment package was installed or upgraded.
