# Ref-GS Under the FSGS LLFF 3-View Protocol

This experiment is **Ref-GS under the FSGS LLFF 3-view protocol for a fair
cross-method comparison**. It is not a Ref-GS original-paper LLFF reproduction.
The Ref-GS paper did not provide LLFF three-view results; corresponding cells
must say `原论文未提供`.

## Split and image protocol

- Scenes: fern, flower, fortress, horns, leaves, orchids, room, trex.
- Test images are sorted full-resolution image indices 0, 8, 16, and so on.
- After removing tests, three train images are selected with NumPy linspace and
  Python 3 bankers rounding, exactly as in the completed FSGS runner.
- Test counts are 3, 5, 6, 8, 4, 4, 6, and 7 respectively.
- `1_8` uses `images_8` (504 x 378); `1_4` uses `images_4` (1008 x 756).
- Each prepared manifest contains exactly the three train records and fixed
  test records. Other candidate images cannot enter the loader.

## Approved deterministic camera adaptation

- Train extrinsics: author `3_views/triangulated/images.txt`.
- Intrinsics: read-only original LLFF `cameras.bin`.
- Test extrinsics: read-only original LLFF `images.bin`, used only by the test
  camera list after training.
- Every author training pose is compared with the corresponding original
  record. Rotation-matrix Frobenius/max-absolute error and camera-center L2
  error are saved per image.

For original width/height `(W,H)` and actual `(w,h)`:

```text
sx = w/W; sy = h/H
fx' = fx*sx; fy' = fy*sy
cx' = cx*sx; cy' = cy*sy
k' = k
```

Both original and scaled parameters are saved. No new distortion or image
resampling is performed.

## Point-cloud prohibition and initialization

Initialization is strictly the author `3_views/dense/fused.ply`. The PLY is
linked read-only and is not sampled, filtered, recolored, augmented, or
reconstructed. Source path, SHA-256, vertex count, bounding box, properties,
and the loader's actual read event are recorded.

The full-scene `points3D.bin` is forbidden: the LLFF preparation and manifest
loader do not read, copy, convert, hash, or use it. Prepared scenes contain no
full-scene point cloud. Missing, unreadable, or hash-mismatched author PLY is
`blocked_pointcloud`; there is no fallback.

## Training-only normalization

Only the three author training cameras determine Ref-GS normalization:

```text
center = arithmetic mean of the three training camera centers
translate = -center
radius = 1.1 * max_i ||camera_center_i - center||_2
```

Tests prove that changing test poses cannot change normalization. The author
PLY bounding box is recorded but does not replace the repository's existing
training-camera extent.

The generic `train.py`/`gaussian_renderer.render` path does not consume
`env_scope_center`, `env_scope_radius`, or `xyz_axis`, so no environment scope
is needed or tuned. `train-real.py` is not used.

## Ref-GS method and budget

Ref-GS model representation, directional appearance decomposition,
directional encoding, spherical Mip-grid, losses, densification/pruning,
optimizer, learning rates, and other method defaults remain unchanged.

- Iterations: 10,000.
- Saves: 5,000 and 10,000.
- Rendering/evaluation: iteration 10,000, test only.
- RGB LLFF images are opaque RGB targets; existing RGBA compositing and alpha
  loss remain unchanged for RGBA datasets.
- No FSGS MiDaS depth, pseudo views, pseudo interval, depth loss, extra image,
  or test supervision is used.

## GPU and stage protocol

GPU selection is external. The runner sets the physical index in
`CUDA_VISIBLE_DEVICES`; the child correctly sees logical `cuda:0`. Each stage
records both indices, GPU name, free memory before launch, peak memory, and
elapsed time. Each cell has isolated prepared, output, log, and tmp paths.

Stage completion is evidence based:

- train: non-empty point clouds at iterations 5,000 and 10,000;
- render: exact expected filenames in both renders and GT;
- eval: `results.json` with finite PSNR, SSIM, and LPIPS;
- failed/blocked metrics remain null.

The persisted smoke certificate is versioned and bound to the current runner
SHA-256. It revalidates the exact horns/1_8/GPU-2/10,000 tuple, all four stage
records, strict prepared links, model/manifest fingerprint, shared evaluator,
and clean logs before it can unlock another cell. A stale boolean alone cannot
unlock batch execution.

## Formal shared evaluation

Formal comparison uses the FSGS metric definitions: repository PSNR,
repository SSIM, and LPIPS with VGG. Inputs are decoded RGB PNG tensors in
`[0,1]`, with equal dimensions and exact manifest filename sets. No training
PSNR substitutes for final test evaluation.

The existing FSGS renders must reproduce the completed means before Ref-GS
metrics are accepted:

- 1/8: PSNR 20.4619, SSIM 0.699808, LPIPS 0.204037.
- 1/4: PSNR 19.7724, SSIM 0.663966, LPIPS 0.269889.

All comparison deltas are `Ref-GS - FSGS`; higher PSNR/SSIM and lower LPIPS are
better.

## Execution gate

After deterministic preparation and tests, only `horns`, `1_8`, physical GPU
1 may run through prepare, train, render, and shared evaluation. Any failed
smoke predicate stops execution before every other scene.
