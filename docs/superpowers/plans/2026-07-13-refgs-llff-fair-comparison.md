# Ref-GS LLFF Fair Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a strictly gated `horns` 1/8 smoke of Ref-GS under the completed FSGS LLFF three-view protocol, with deterministic preparation, test-only shared metrics, and complete audit evidence.

**Architecture:** A manifest-backed scene adapter exposes only the approved three training cameras and fixed test cameras, while the author fused PLY remains the only initialization. Focused scripts prepare and audit data, execute resumable stages, evaluate with the FSGS metric definitions, and summarize evidence; existing Ref-GS method code changes are limited to manifest dispatch, RGB target handling, and removal of GPU-related environment hardcoding.

**Tech Stack:** Python 3.7, `argparse`, `unittest`, NumPy, Pillow, plyfile, PyTorch 1.12.1, Ref-GS CUDA extensions, lpipsPyTorch VGG, COLMAP binary readers already in the repository.

---

## File structure

- Create `scripts/refgs_llff_common.py`: protocol constants, split logic, hashes, PLY and manifest validation, stage completeness, status helpers.
- Create `scripts/prepare_refgs_llff.py`: read-only source audit and deterministic prepared-scene construction.
- Create `scripts/evaluate_refgs_llff.py`: exact shared PSNR/SSIM/LPIPS-VGG evaluator with strict image gates.
- Create `scripts/run_refgs_llff.py`: stage commands, GPU provenance, timing/memory monitoring, safe resume, and smoke gate.
- Create `scripts/summarize_refgs_llff.py`: Ref-GS summaries and Ref-GS-minus-FSGS comparisons.
- Create `tests/test_refgs_llff.py`: all protocol, security boundary, state, metric, and summary tests.
- Modify `scene/dataset_readers.py`: manifest scene reader.
- Modify `scene/__init__.py`: manifest reader dispatch before COLMAP/Blender discovery.
- Modify `train.py`: preserve RGBA behavior while accepting opaque RGB LLFF images; remove `CUDA_LAUNCH_BLOCKING` assignment.
- Modify `train-real.py`: remove `CUDA_LAUNCH_BLOCKING` assignment only.
- Create `logs/refgs_llff/environment.md`, `environment.json`, and `protocol.md` from audited facts.

### Task 1: Protocol primitives and exact split tests

**Files:**
- Create: `tests/test_refgs_llff.py`
- Create: `scripts/refgs_llff_common.py`

- [ ] **Step 1: Write failing tests for constants, split selection, and resolution mapping**

```python
class SplitTests(unittest.TestCase):
    EXPECTED = {
        "fern": (["IMG_4027.JPG", "IMG_4036.JPG", "IMG_4045.JPG"], 3),
        "flower": (["IMG_2963.JPG", "IMG_2979.JPG", "IMG_2995.JPG"], 5),
        "fortress": (["IMG_1801.JPG", "IMG_1821.JPG", "IMG_1841.JPG"], 6),
        "horns": (["DJI_20200223_163017_967.jpg", "DJI_20200223_163053_863.jpg", "DJI_20200223_163225_243.jpg"], 8),
        "leaves": (["IMG_2998.JPG", "IMG_3010.JPG", "IMG_3023.JPG"], 4),
        "orchids": (["IMG_4468.JPG", "IMG_4479.JPG", "IMG_4490.JPG"], 4),
        "room": (["DJI_20200226_143851_396.JPG", "DJI_20200226_143918_576.JPG", "DJI_20200226_143946_704.JPG"], 6),
        "trex": (["DJI_20200223_163551_210.jpg", "DJI_20200223_163616_980.jpg", "DJI_20200223_163654_571.jpg"], 7),
    }

    def test_all_splits_match_fsgs(self):
        for scene, (expected_train, expected_test_count) in self.EXPECTED.items():
            names = list_source_image_names(DATA_ROOT / scene)
            split = select_llff_views(names)
            self.assertEqual(split["train"], expected_train)
            self.assertEqual(len(split["test"]), expected_test_count)
            self.assertEqual(set(split["train"]) & set(split["test"]), set())

    def test_resolution_mapping(self):
        self.assertEqual(RESOLUTIONS, {"1_8": "images_8", "1_4": "images_4"})
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.SplitTests -v`

Expected: import failure for missing `scripts.refgs_llff_common`.

- [ ] **Step 3: Implement immutable protocol primitives**

```python
LLFF_SCENES = ("fern", "flower", "fortress", "horns", "leaves", "orchids", "room", "trex")
RESOLUTIONS = {"1_8": "images_8", "1_4": "images_4"}
ALLOWED_STATUSES = {"pending", "running", "completed", "failed", "missing", "blocked_cuda", "blocked_data", "blocked_pointcloud"}

def select_llff_views(image_names, n_views=3, llffhold=8):
    ordered = sorted(image_names)
    test = [name for index, name in enumerate(ordered) if index % llffhold == 0]
    candidates = [name for index, name in enumerate(ordered) if index % llffhold != 0]
    indices = [round(value) for value in np.linspace(0, len(candidates) - 1, n_views)]
    train = [candidates[index] for index in indices]
    if len(set(train)) != n_views:
        raise ValueError("three-view selection did not produce distinct images")
    return {"all": ordered, "candidate_train": candidates, "train": train, "test": test}
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.SplitTests -v`

Expected: all split tests pass.

### Task 2: Deterministic prepared manifests and point-cloud audit

**Files:**
- Modify: `tests/test_refgs_llff.py`
- Modify: `scripts/refgs_llff_common.py`
- Create: `scripts/prepare_refgs_llff.py`

- [ ] **Step 1: Add failing preparation tests**

Tests create a tiny temporary LLFF fixture with binary camera records represented through injected reader results, author `images.txt`, downsampled PNGs, and a nine-property PLY. Assert:

```python
self.assertEqual(manifest["train_images"], expected_train)
self.assertEqual(manifest["test_images"], expected_test)
self.assertEqual(set(path.name for path in images_dir.iterdir()), set(expected_train + expected_test))
self.assertFalse((prepared / "sparse").exists())
self.assertNotIn("points3D.bin", json.dumps(manifest))
self.assertEqual(manifest["pointcloud"]["sha256"], file_sha256(author_ply))
self.assertEqual(manifest["pointcloud"]["vertex_count"], 2)
self.assertEqual(manifest["intrinsics"]["scaled"]["width"], 504)
self.assertAlmostEqual(manifest["intrinsics"]["scaled"]["fx"], original_fx / 8)
```

Add separate tests that missing PLY and PLY hash mismatch return
`blocked_pointcloud`, author-image mismatch returns `blocked_data`, and no
fallback path is created.

- [ ] **Step 2: Verify preparation tests fail for missing implementation**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.PreparationTests -v`

Expected: missing `prepare_scene`/PLY audit helpers.

- [ ] **Step 3: Implement hashes, PLY audit, pose audit, image mapping, and intrinsic scaling**

Implement these explicit interfaces in `refgs_llff_common.py`:

```python
def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def camera_center(qvec: np.ndarray, tvec: np.ndarray) -> np.ndarray:
    rotation = qvec2rotmat(qvec)
    return -(rotation.T @ np.asarray(tvec))

def pose_error(author_record, original_record) -> dict:
    author_rotation = qvec2rotmat(author_record.qvec)
    original_rotation = qvec2rotmat(original_record.qvec)
    delta = author_rotation - original_rotation
    return {
        "rotation_frobenius": float(np.linalg.norm(delta)),
        "rotation_max_abs": float(np.max(np.abs(delta))),
        "camera_center_l2": float(np.linalg.norm(
            camera_center(author_record.qvec, author_record.tvec)
            - camera_center(original_record.qvec, original_record.tvec)
        )),
    }

def scaled_simple_radial(camera, actual_size) -> dict:
    width, height = actual_size
    focal, cx, cy, radial = [float(value) for value in camera.params]
    sx, sy = width / camera.width, height / camera.height
    return {
        "model": camera.model,
        "width": width,
        "height": height,
        "fx": focal * sx,
        "fy": focal * sy,
        "cx": cx * sx,
        "cy": cy * sy,
        "radial": radial,
        "scale_x": sx,
        "scale_y": sy,
    }

def resolution_image_mapping(original_records, resolution_dir: Path) -> dict:
    ordered_records = sorted(original_records.values(), key=lambda record: record.id)
    ordered_images = sorted(path for path in Path(resolution_dir).iterdir() if path.is_file())
    if len(ordered_records) != len(ordered_images):
        raise ValueError("COLMAP/image count mismatch")
    return {record.name: image for record, image in zip(ordered_records, ordered_images)}

def audit_ply(path: Path) -> dict:
    vertex = PlyData.read(str(path))["vertex"]
    required = ("x", "y", "z", "nx", "ny", "nz", "red", "green", "blue")
    if any(name not in vertex.data.dtype.names for name in required):
        raise ValueError("author fused PLY lacks required properties")
    xyz = np.column_stack([vertex[name] for name in ("x", "y", "z")])
    return {
        "path": str(Path(path).resolve()),
        "sha256": file_sha256(path),
        "vertex_count": int(len(vertex)),
        "bbox_min": xyz.min(axis=0).tolist(),
        "bbox_max": xyz.max(axis=0).tolist(),
        "properties": list(vertex.data.dtype.names),
    }

def validate_manifest(payload: dict) -> None:
    train = payload.get("train", [])
    test = payload.get("test", [])
    train_names = [record["image_name"] for record in train]
    test_names = [record["image_name"] for record in test]
    if len(train_names) != 3 or set(train_names) & set(test_names):
        raise ValueError("manifest violates three-view disjoint split")
    if payload.get("pointcloud", {}).get("source_kind") != "author_fused_ply":
        raise ValueError("manifest point cloud is not the author fused PLY")
```

`audit_ply` requires `x,y,z,nx,ny,nz,red,green,blue`, reports vertex count and
bounds, and never accepts another source. `pose_error` reports Frobenius
rotation error, max-absolute rotation error, and Euclidean camera-center error.

- [ ] **Step 4: Implement `prepare_scene` and CLI**

The CLI accepts the requested roots, scene, and resolution. `prepare_scene`
reads `cameras.bin` and `images.bin`, reads only author `images.txt` and
`fused.ply`, creates links for manifest entries only, writes
`refgs_llff_manifest.json`, and writes the same audit payload to
`logs/refgs_llff/<resolution>/<scene>/data_audit.json`.

Use a module constant named `FORBIDDEN_FULL_POINTCLOUD_BASENAME = "points3D.bin"`
only for static prohibition checks; do not construct or access its source path.

- [ ] **Step 5: Run preparation tests and verify GREEN**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.PreparationTests -v`

Expected: all preparation tests pass.

### Task 3: Manifest scene loader and training-only normalization

**Files:**
- Modify: `tests/test_refgs_llff.py`
- Modify: `scene/dataset_readers.py`
- Modify: `scene/__init__.py`

- [ ] **Step 1: Add failing loader-boundary tests**

```python
def test_manifest_loader_exposes_only_listed_cameras(self):
    info = readRefGSLLFFManifestInfo(self.prepared)
    self.assertEqual([c.image_name for c in info.train_cameras], self.train_stems)
    self.assertEqual([c.image_name for c in info.test_cameras], self.test_stems)

def test_test_pose_changes_do_not_change_normalization(self):
    before = readRefGSLLFFManifestInfo(self.prepared).nerf_normalization
    mutate_test_poses_only(self.manifest)
    after = readRefGSLLFFManifestInfo(self.prepared).nerf_normalization
    np.testing.assert_allclose(before["translate"], after["translate"])
    self.assertEqual(before["radius"], after["radius"])
```

- [ ] **Step 2: Verify loader tests fail**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.LoaderTests -v`

Expected: missing manifest callback.

- [ ] **Step 3: Implement the manifest reader**

`readRefGSLLFFManifestInfo(path)` validates the manifest, constructs
`CameraInfo` objects directly from its ordered train/test records, calls
`getNerfppNorm(train_cam_infos)` only, calls `fetchPly` on the manifest PLY,
prints `REFGS_LLFF_PLY_READ` with path/hash/count/bounds, and returns
`SceneInfo`.

Register:

```python
sceneLoadTypeCallbacks["RefGSLLFF"] = readRefGSLLFFManifestInfo
```

Dispatch before other formats:

```python
if os.path.exists(os.path.join(args.source_path, "refgs_llff_manifest.json")):
    scene_info = sceneLoadTypeCallbacks["RefGSLLFF"](args.source_path)
elif os.path.exists(os.path.join(args.source_path, "sparse")):
    scene_info = sceneLoadTypeCallbacks["Colmap"](args.source_path, args.images, args.eval)
elif os.path.exists(os.path.join(args.source_path, "transforms_train.json")):
    scene_info = sceneLoadTypeCallbacks["Blender"](args.source_path, args.white_background, args.eval)
else:
    raise AssertionError("Could not recognize scene type")
```

- [ ] **Step 4: Run loader tests and verify GREEN**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.LoaderTests -v`

Expected: loader tests pass without CUDA initialization.

### Task 4: RGB LLFF targets and GPU hardcoding removal

**Files:**
- Modify: `tests/test_refgs_llff.py`
- Modify: `train.py`
- Modify: `train-real.py`

- [ ] **Step 1: Add failing RGB/RGBA and source-policy tests**

```python
def test_rgb_target_is_unchanged(self):
    rgb = torch.rand(3, 4, 5)
    target, mask = training_target(rgb, torch.rand(3))
    self.assertTrue(torch.equal(target, rgb))
    self.assertIsNone(mask)

def test_rgba_target_preserves_compositing(self):
    rgba = torch.rand(4, 4, 5)
    bg = torch.rand(3)
    target, mask = training_target(rgba, bg)
    expected = rgba[:3] * rgba[3:4] + (1 - rgba[3:4]) * bg[:, None, None]
    self.assertTrue(torch.allclose(target, expected))
    self.assertTrue(torch.equal(mask, rgba[3:4]))

def test_train_sources_do_not_set_gpu_environment(self):
    for name in ("train.py", "train-real.py"):
        text = (REPO_ROOT / name).read_text()
        self.assertNotIn("CUDA_VISIBLE_DEVICES", text)
        self.assertNotIn("CUDA_LAUNCH_BLOCKING", text)
```

- [ ] **Step 2: Verify RED**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.TrainingGlueTests -v`

Expected: missing `training_target` and hardcoding assertion failure.

- [ ] **Step 3: Add `training_target` and condition alpha loss**

```python
def training_target(image, background):
    image = image.cuda()
    if image.shape[0] < 4:
        return image[:3], None
    alpha = image[3:4]
    return image[:3] * alpha + (1 - alpha) * background[:, None, None], alpha
```

Call it once per iteration and add binary cross entropy only when `alpha` is not
`None`. Remove only the two top-level `CUDA_LAUNCH_BLOCKING` assignments.

- [ ] **Step 4: Verify GREEN and existing render-unit compatibility**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.TrainingGlueTests tests.test_refgs_render_metrics -v`

Expected: all selected tests pass.

### Task 5: Shared evaluator and FSGS validation

**Files:**
- Modify: `tests/test_refgs_llff.py`
- Create: `scripts/evaluate_refgs_llff.py`

- [ ] **Step 1: Add failing evaluator tests**

Tests assert exact expected filenames, equal render/GT sets, equal image sizes,
RGB conversion, finite `[0,1]` tensors, VGG backbone metadata, blank output on
NaN/Inf, and arithmetic means from per-view results.

```python
with self.assertRaises(EvaluationError):
    validate_image_pairs(render_dir, gt_dir, expected_names | {"extra.png"})
self.assertEqual(evaluator_metadata()["lpips_backbone"], "vgg")
self.assertIsNone(finite_metrics({"PSNR": float("nan"), "SSIM": 0.5, "LPIPS": 0.2}))
```

- [ ] **Step 2: Verify evaluator tests fail**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.EvaluatorTests -v`

Expected: missing evaluator module.

- [ ] **Step 3: Implement exact shared evaluator**

Use `utils.loss_utils.ssim`, `utils.image_utils.psnr`, and
`lpipsPyTorch.lpips(pred, gt, net_type="vgg")`. Process filenames in sorted
order, save `results.json`, `per_view.json`, and `evaluator_metadata.json`, and
include SHA-256 for this script and FSGS `metrics.py`.

- [ ] **Step 4: Verify evaluator unit tests GREEN**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.EvaluatorTests -v`

Expected: evaluator tests pass without requiring model-weight download.

- [ ] **Step 5: Re-evaluate existing FSGS renders in a GPU-visible process**

Run the evaluator for all completed FSGS 1/8 and 1/4 outputs, storing validation
under `logs/refgs_llff/fsgs_shared_eval_validation`. Confirm eight-scene means
match 20.4619162083/0.6998081729/0.2040368729 and
19.7723984718/0.6639658622/0.2698891808 within `1e-6`. Any mismatch blocks the
Ref-GS formal metric claim.

### Task 6: Safe runner, GPU provenance, and stage state

**Files:**
- Modify: `tests/test_refgs_llff.py`
- Create: `scripts/run_refgs_llff.py`

- [ ] **Step 1: Add failing runner tests**

Cover command construction, physical-to-logical GPU mapping, two-worker output
isolation, status vocabulary, checkpoint validity at both saves, exact render
sets, finite metrics, incomplete skip behavior, failure metrics remaining null,
and smoke-first refusal.

```python
self.assertEqual(build_child_env("2")["CUDA_VISIBLE_DEVICES"], "2")
self.assertNotEqual(cell_paths(root, "1_8", "fern"), cell_paths(root, "1_8", "flower"))
self.assertFalse(stage_complete("train", model, 10000))  # only iteration_10000 exists
self.assertFalse(stage_complete("eval", model, 10000))   # NaN LPIPS
self.assertRaises(SmokeGateError, assert_batch_launch_allowed, log_root)
```

- [ ] **Step 2: Verify runner tests fail**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.RunnerTests -v`

Expected: missing runner interfaces.

- [ ] **Step 3: Implement CLI and command construction**

Support all requested flags and explicit `--python`. Construct:

```text
train.py -s PREPARED -m MODEL --eval --iterations 10000 --save_iterations 5000 10000
render.py -s PREPARED -m MODEL --iteration 10000 --renderer refgs --image-key pbr_rgb --skip_train
evaluate_refgs_llff.py --model-path MODEL --iteration 10000 --manifest MANIFEST
```

Do not pass environment-scope arguments and do not alter method defaults.

- [ ] **Step 4: Implement stage execution and provenance**

Before each GPU stage, run a child probe under the same environment that prints
`CUDA_VISIBLE_DEVICES`, `torch.cuda.current_device()`, and GPU name. Query
physical free memory with `nvidia-smi`; poll the selected physical GPU while the
stage runs; persist peak used memory and elapsed wall time. Write
`commands.txt`, stage logs, stage `status.json`, and cell `status.json` through
atomic replacement.

- [ ] **Step 5: Verify runner tests GREEN**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.RunnerTests -v`

Expected: runner tests pass.

### Task 7: Summary and cross-method comparison

**Files:**
- Modify: `tests/test_refgs_llff.py`
- Create: `scripts/summarize_refgs_llff.py`

- [ ] **Step 1: Add failing summary tests**

Assert recomputation of eight-scene arithmetic means, status counts, blank
failed metrics, fixed aggregate baselines, per-scene FSGS joins, and
`Ref-GS - FSGS` sign convention.

- [ ] **Step 2: Verify summary tests fail**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.SummaryTests -v`

Expected: missing summarizer.

- [ ] **Step 3: Implement CSV/JSON/Markdown summaries**

Write the five requested summary/comparison files. Publish a resolution mean
only for eight completed cells. Include point source, train/test counts,
checkpoint/render/metric completeness, time, peak memory, and
`Ref-GS original paper = 原论文未提供`.

- [ ] **Step 4: Verify summary tests GREEN**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest tests.test_refgs_llff.SummaryTests -v`

Expected: summary tests pass.

### Task 8: Environment and protocol audit artifacts

**Files:**
- Create: `logs/refgs_llff/environment.md`
- Create: `logs/refgs_llff/environment.json`
- Create: `logs/refgs_llff/protocol.md`

- [ ] **Step 1: Generate audit artifacts from live read-only probes**

Record repository root/commit/dirty paths, absolute Python, Python/PyTorch/CUDA
versions, CLI help-derived entry points, loader dispatch, hardcoding findings,
FSGS commit and evaluator hashes, all roots, actual camera models/sizes, the
missing author camera/point text files, approved deterministic adaptation, and
the claim boundary.

- [ ] **Step 2: Validate audit files parse and contain mandatory fields**

Run:

```bash
/home/liuly/anaconda3/envs/ref_gs/bin/python -c 'import json; p=json.load(open("logs/refgs_llff/environment.json")); assert p["git"]["commit"]; assert p["python"]["executable"]'
rg -n "公平对比|不是.*复现|points3D.bin|CUDA_VISIBLE_DEVICES|CUDA_LAUNCH_BLOCKING" logs/refgs_llff/environment.md logs/refgs_llff/protocol.md
```

Expected: JSON assertion succeeds and every protocol boundary is documented.

### Task 9: Full static and unit-test gate

**Files:**
- All changed Python files

- [ ] **Step 1: Compile every changed Python file**

Run:

```bash
/home/liuly/anaconda3/envs/ref_gs/bin/python -m py_compile scripts/refgs_llff_common.py scripts/prepare_refgs_llff.py scripts/evaluate_refgs_llff.py scripts/run_refgs_llff.py scripts/summarize_refgs_llff.py tests/test_refgs_llff.py scene/dataset_readers.py scene/__init__.py train.py train-real.py
```

Expected: exit 0 and no output.

- [ ] **Step 2: Run the exact repository test gate**

Run: `/home/liuly/anaconda3/envs/ref_gs/bin/python -m unittest discover -s tests`

Expected: exit 0 with zero failures and zero errors.

- [ ] **Step 3: Run repository hygiene and forbidden-access scans**

Run:

```bash
git diff --check
rg -n "open\(.*points3D\.bin|read_points3D_binary|copy.*points3D\.bin" scripts/refgs_llff_common.py scripts/prepare_refgs_llff.py scene/dataset_readers.py
rg -n "CUDA_VISIBLE_DEVICES|CUDA_LAUNCH_BLOCKING" train.py train-real.py
```

Expected: `git diff --check` succeeds and both scans produce no matches.

### Task 10: Prepare and audit all eight manifests without training

**Files:**
- Create per-cell prepared data and `logs/refgs_llff/<resolution>/<scene>/data_audit.json`

- [ ] **Step 1: Run preparation for all eight scenes and both resolutions**

This is data adaptation only, not experimental execution. Use the approved
read-only roots and `/data1/liuly/RefGS_LLFF/prepared`.

- [ ] **Step 2: Run the manifest audit test against real prepared outputs**

Verify exact split names/counts, pose errors, intrinsic scaling, source links,
PLY hashes/counts/bounds, absence of candidate images, and absence of any
`points3D.bin` in prepared roots. Any failed scene is `blocked_data` or
`blocked_pointcloud` and stops before smoke training.

### Task 11: Horns 1/8 smoke only

**Files:**
- Create: `/data1/liuly/RefGS_LLFF/output/llff_sparse/1_8/horns/*`
- Create: `logs/refgs_llff/1_8/horns/{status.json,commands.txt,train,render,eval}/*`

- [ ] **Step 1: Confirm GPU 1 and storage gates in the exact child environment**

Require physical GPU 1, child logical device 0, CUDA available, no other
training task on GPU 1, sufficient free memory/storage, and no network action.
Failure writes `blocked_cuda` or the corresponding data/point status and stops.

- [ ] **Step 2: Execute exactly one cell**

Run `prepare -> train -> render -> eval` for `horns`, `1_8`, GPU 1,
iteration 10,000. Do not include any other scene in the command.

- [ ] **Step 3: Verify every smoke gate from fresh artifacts**

Check manifest train/test names, PLY source/hash/count, actual loader log,
iteration 5,000 and 10,000 point clouds, exact eight render/GT names,
`results.json`, finite PSNR/SSIM/LPIPS, no OOM/traceback/network/full-point-cloud
evidence, peak memory, and elapsed training time.

- [ ] **Step 4: Generate phase summary without launching full 1/8**

Run `scripts/summarize_refgs_llff.py`, report the requested environment, data,
checkpoint, metric, timing, and memory evidence, and state GO only if every
smoke predicate is true. Stop before the eight-scene 1/8 commands.
