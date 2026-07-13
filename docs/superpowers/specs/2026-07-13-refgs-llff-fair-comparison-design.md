# Ref-GS Under the FSGS LLFF 3-View Protocol: Design

## Goal and claim boundary

Implement a reproducible evaluation of Ref-GS under exactly the data, three-view
split, initialization, image resolution, 10,000-iteration budget, and test-only
metric protocol used by the completed FSGS LLFF experiment.

This is a **fair cross-method comparison under the FSGS LLFF 3-view protocol**.
It is not a reproduction of a Ref-GS paper LLFF experiment. Ref-GS paper LLFF
three-view values are unavailable and must be reported as `原论文未提供`.

The first execution phase ends after a successful `horns`, `1_8`, GPU 1 smoke.
No other training may start until every smoke gate passes.

## Immutable protocol

- Scenes: `fern`, `flower`, `fortress`, `horns`, `leaves`, `orchids`, `room`,
  and `trex`.
- Resolutions: `1_8 -> images_8`, `1_4 -> images_4`.
- Test split: sorted full-resolution source image indices `0, 8, 16, ...`.
- Training split: exclude the test images, then select three candidate images
  with `numpy.linspace(0, candidate_count - 1, 3)` and Python 3 bankers
  rounding, exactly as in the audited FSGS runner.
- Iterations: 10,000. Save iterations 5,000 and 10,000. Render and evaluate
  iteration 10,000 only.
- Metrics: PSNR, SSIM, and LPIPS-VGG on the test set only.
- Background: retain the generic Ref-GS entry point's black-background default.
  Opaque LLFF RGB inputs are compared as RGB and receive no synthetic alpha
  supervision.
- No test image may contribute pixels, pose statistics, normalization, point
  initialization, training, or densification.
- No FSGS depth, pseudo-view, pseudo-view interval, or other FSGS method logic
  may enter Ref-GS.

## Audited data facts

The read-only roots are:

- `/data1/liuly/FSGS_LLFF/dataset/nerf_llff_data`
- `/data1/liuly/FSGS_LLFF/author_preprocessed`

The downloaded author subtree contains, per scene, only:

- `3_views/triangulated/images.txt`
- `3_views/dense/fused.ply`

It does not contain the anticipated `cameras.txt` or `points3D.txt`. The
approved deterministic adaptation therefore uses:

- author `images.txt` for the three training extrinsics;
- original read-only LLFF `cameras.bin` for intrinsics;
- original read-only LLFF `images.bin` for fixed test extrinsics;
- author `fused.ply` as the only point initialization.

All eight scenes' author training extrinsics were found to match their original
LLFF records. The implementation must reproduce and persist rotation-matrix and
camera-center errors per training image rather than relying on this preliminary
observation.

The implementation must never read, copy, convert, hash, stat for content, or
otherwise use the original full-scene `points3D.bin`. The prepared scene must
not contain it. Missing or invalid author fused PLY is `blocked_pointcloud`, not
a fallback condition.

## Prepared-scene contract

Each `(resolution, scene)` is represented by a dedicated directory below
`/data1/liuly/RefGS_LLFF/prepared`. It contains:

- `refgs_llff_manifest.json`;
- an `images` directory with read-only symlinks for exactly the three training
  and fixed test images;
- `input/fused.ply`, a read-only symlink to the author PLY;
- no `sparse` directory and no full-scene point cloud.

The manifest is the sole camera-list authority. It includes:

- protocol/version identifiers;
- ordered train and test records;
- source image name and actual resolution-image source path;
- author or original pose provenance;
- quaternion, translation, rotation matrix, and camera center;
- original camera model and parameters;
- actual image dimensions and deterministically scaled intrinsics;
- original-to-scaled width and height factors;
- author/source pose error audit;
- fused PLY source, SHA-256, vertex count, bounding box, and property schema;
- training-only normalization values;
- forbidden original point-cloud path and an assertion that it was unused.

Only train and test manifest entries are linked. Other candidate images do not
appear in the prepared directory and the loader never scans the directory to
discover cameras.

For scenes whose downsampled images are named `imageNNN.png`, source mapping is
the exact FSGS mapping: sorted original COLMAP image records correspond to
sorted files in `images_8` or `images_4`. Prepared links use original image
stems so Ref-GS render names equal FSGS render names.

## Camera and intrinsic adaptation

Original cameras are `SIMPLE_RADIAL`, with original dimensions 4032 by 3024.
For each actual image:

```text
sx = actual_width / original_width
sy = actual_height / original_height
fx' = fx * sx
fy' = fx * sy
cx' = cx * sx
cy' = cy * sy
k'  = k
```

The manifest records both parameter sets. The LLFF loader uses actual width,
actual height, `fx'`, and `fy'` to compute horizontal and vertical fields of
view. Radial distortion is not newly applied: the provided downsampled images
are used as-is, consistent with the completed FSGS data path.

Training records use author extrinsics. Test records use original LLFF
extrinsics and remain inaccessible to the training camera list.

## Normalization and environment scope

The new manifest loader computes Ref-GS camera normalization from the three
training cameras only, using the repository's existing NeRF++ normalization
rule: the mean training camera center supplies translation and 1.1 times the
maximum training-camera distance supplies camera extent. Tests must prove that
changing test poses cannot change these values.

The generic `train.py` and `gaussian_renderer.render` path is used. This path
does not use `env_scope_center`, `env_scope_radius`, or `xyz_axis`, so no
environment sphere is introduced. The author PLY bounding-box center/radius is
recorded for audit only and does not replace the method's existing camera
extent. If later evidence shows that the generic path cannot train LLFF, the
smoke fails and the protocol is reconsidered; it must not silently switch to
`train-real.py` or scene-specific scope values.

## Minimal Ref-GS changes

1. Add a manifest scene reader and make `Scene` choose it before COLMAP or
   Blender detection.
2. Make `train.py` accept opaque RGB input: RGB is used directly; RGBA retains
   existing alpha compositing and alpha loss behavior.
3. Remove top-level `CUDA_LAUNCH_BLOCKING=1` assignments from `train.py` and
   `train-real.py`. Do not introduce `CUDA_VISIBLE_DEVICES` in source. The
   runner exclusively controls the physical GPU through its child environment.
4. Keep Ref-GS representation, appearance modules, encoding, Mip-grid, losses,
   densification/pruning, optimizer, learning rates, and other defaults
   unchanged except the explicit 10,000-iteration and save schedule.

## Tools and responsibilities

### `scripts/refgs_llff_common.py`

Owns immutable scene lists, split selection, manifest schema validation, PLY
audit, finite-metric validation, render-set completeness, status vocabulary,
and helpers shared by preparation, running, evaluation, and summarization.

### `scripts/prepare_refgs_llff.py`

Creates one deterministic prepared scene, writes the manifest and
`data_audit.json`, verifies author/source poses, verifies point-cloud identity,
and refuses every unapproved fallback.

### `scripts/run_refgs_llff.py`

Supports the requested stage and root flags. It runs stages independently,
writes `commands.txt` plus stage logs/status, and skips only when the requested
stage's full validity predicate passes. It sets `CUDA_VISIBLE_DEVICES` to the
physical GPU, verifies that the child sees logical `cuda:0`, and records GPU
name, free memory before launch, peak physical memory, elapsed time, and child
environment. One runner process represents one cell; later batch orchestration
may run one sequential worker per physical GPU.

The runner never invokes training for a non-horns cell unless the persisted
horns `1_8` smoke status passes every gate.

### `scripts/evaluate_refgs_llff.py`

Evaluates already-rendered PNGs with the same functions as FSGS `metrics.py`:
repository PSNR, repository SSIM, and `lpipsPyTorch` with VGG. It requires exact
render/GT filename equality, expected test-name equality, RGB conversion,
matching dimensions, finite `[0,1]` tensors, and finite results. It records its
own SHA-256, FSGS evaluator SHA-256, LPIPS backbone, package/runtime versions,
per-view metrics, and aggregate metrics.

It can also evaluate existing FSGS renders. Before Ref-GS metrics are accepted,
the existing FSGS eight-scene means must be reproducible within a documented
floating-point tolerance.

### `scripts/summarize_refgs_llff.py`

Produces the requested Ref-GS summary and Ref-GS-versus-FSGS tables. Metrics
remain empty for failed, missing, or blocked cells. Full eight-scene means are
published only when all eight cells for a resolution are complete. Per-scene
FSGS differences use actual completed FSGS per-scene results; aggregate fixed
baselines are 20.4619/0.699808/0.204037 and
19.7724/0.663966/0.269889. All differences are `Ref-GS - FSGS`.

## Stage state and failure handling

Allowed cell states are:

- `pending`
- `running`
- `completed`
- `failed`
- `missing`
- `blocked_cuda`
- `blocked_data`
- `blocked_pointcloud`

Training completeness requires non-empty iteration 5,000 and 10,000 point
clouds. Render completeness requires exactly the expected test filenames in
both `renders` and `gt`. Evaluation completeness requires `results.json` and
finite PSNR, SSIM, and LPIPS. Directory existence alone never permits a skip.

All failures retain logs and empty metrics. NaN or infinity is never complete.

## Automated tests

Tests are written before production behavior and cover:

- all eight splits match the audited FSGS split;
- exactly three training images and the specified test counts;
- no train/test overlap and no unlisted loader images;
- author `images.txt` names equal manifest training names;
- source/author rotation and camera-center error auditing;
- resolution mapping and exact intrinsic scaling;
- PLY source, schema, point count, bounding box, and hash validation;
- missing/invalid PLY becomes `blocked_pointcloud` with no fallback;
- prepared output contains no original `points3D.bin`;
- test poses cannot affect training normalization;
- physical GPU to logical `cuda:0` provenance;
- output isolation for two workers;
- incomplete stage artifacts are not skipped;
- NaN/Inf cannot produce `completed`;
- eight-scene means are recomputable;
- failure metric fields are empty;
- forbidden full-scene point-cloud access is absent from preparation and loader
  code paths;
- generic RGB training target behavior and preserved RGBA behavior;
- source GPU hardcoding is removed from `train.py` and `train-real.py`.

Required gates before any real experiment are:

```bash
/home/liuly/anaconda3/envs/ref_gs/bin/python -m py_compile <changed Python files>
/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest discover -s tests
```

## Horns 1/8 smoke

After the compile and unit-test gates pass, run exactly:

```text
scene=horns, resolution=1_8, physical_gpu=1, iterations=10000
prepare -> train -> render test only -> shared eval
```

The smoke is complete only if all user-specified gates pass, including exact
3/8 camera sets, author PLY identity, checkpoints at 5,000 and 10,000, eight
renders and eight GT files, exact names, finite metrics, no OOM, no traceback,
no network access, no test supervision, no full-scene point cloud, and no
scene-specific tuning. Failure stops execution before any other scene.

The phase report states the repository commit, runtime versions, actual entry
point, loader changes, GPU-control change, camera names, PLY audit, environment
scope decision, artifact counts, shared metrics, peak memory, training time,
and an evidence-based GO/NO-GO for full `1_8` execution.
