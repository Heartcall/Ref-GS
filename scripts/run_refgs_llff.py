#!/usr/bin/env python3
import argparse
import datetime
import fcntl
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.refgs_llff_common import (
    LLFF_SCENES,
    RESOLUTIONS,
    finite_metrics,
    file_sha256,
    read_json,
    stage_state,
    validate_manifest_payload,
    write_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = Path("/home/liuly/anaconda3/envs/ref_gs/bin/python")
DEFAULT_DATA_ROOT = Path("/data1/liuly/FSGS_LLFF/dataset/nerf_llff_data")
DEFAULT_AUTHOR_ROOT = Path("/data1/liuly/FSGS_LLFF/author_preprocessed")
DEFAULT_PREPARED_ROOT = Path("/data1/liuly/RefGS_LLFF/prepared")
DEFAULT_OUTPUT_ROOT = Path("/data1/liuly/RefGS_LLFF/output/llff_sparse")
DEFAULT_TMP_ROOT = Path("/data1/liuly/RefGS_LLFF/tmp")
DEFAULT_LOG_ROOT = REPO_ROOT / "logs" / "refgs_llff"
MIN_GPU_FREE_MIB = 22000
MIN_STORAGE_FREE_BYTES = 10 * 1024 ** 3
SMOKE_CERTIFICATION_VERSION = 2


def resolve_runtime_paths(args, launch_cwd):
    launch_cwd = Path(launch_cwd).resolve()
    for name in ("data_root", "author_preprocessed_root", "prepared_root", "output_root", "tmp_root", "log_root"):
        value = Path(getattr(args, name))
        setattr(args, name, value if value.is_absolute() else (launch_cwd / value).resolve())
    python = Path(args.python)
    if not python.is_absolute():
        resolved = shutil.which(str(python))
        python = Path(resolved) if resolved else (launch_cwd / python).resolve()
    args.python = python
    return args


def build_child_env(gpu, base=None):
    env = dict(base if base is not None else os.environ)
    env["CUDA_VISIBLE_DEVICES"] = str(gpu)
    env["REFGS_PHYSICAL_GPU"] = str(gpu)
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    env["MPLCONFIGDIR"] = "/tmp/refgs_llff_mpl"
    return env


def cell_paths(prepared_root, output_root, log_root, resolution, scene):
    return {
        "prepared": Path(prepared_root) / resolution / scene,
        "model": Path(output_root) / resolution / scene,
        "log": Path(log_root) / resolution / scene,
    }


def expected_names_from_manifest(prepared):
    payload = read_json(Path(prepared) / "refgs_llff_manifest.json", {}) or {}
    return {record["image_name"] + ".png" for record in payload.get("test", [])}


def protocol_fingerprint_matches(prepared, model):
    if prepared is None:
        return False
    prepared = Path(prepared)
    model = Path(model)
    source_manifest = prepared / "refgs_llff_manifest.json"
    snapshot = model / "refgs_llff_manifest.json"
    metadata = read_json(model / "llff_protocol.json", {}) or {}
    if not source_manifest.is_file() or not snapshot.is_file():
        return False
    manifest = read_json(source_manifest, {}) or {}
    try:
        validate_manifest_payload(manifest, manifest.get("scene"), manifest.get("resolution"))
    except ValueError:
        return False
    manifest_hash = file_sha256(source_manifest)
    point_hash = manifest.get("pointcloud", {}).get("sha256")
    input_ply = model / "input.ply"
    return (
        file_sha256(snapshot) == manifest_hash
        and metadata.get("manifest_sha256") == manifest_hash
        and metadata.get("pointcloud_sha256") == point_hash
        and input_ply.is_file() and file_sha256(input_ply) == point_hash
    )


def prepared_scene_complete(prepared, audit_path):
    prepared = Path(prepared)
    manifest = read_json(prepared / "refgs_llff_manifest.json", {}) or {}
    audit = read_json(audit_path, {}) or {}
    try:
        validate_manifest_payload(manifest, audit.get("scene"), audit.get("resolution"))
    except ValueError:
        return False
    records = manifest["train"] + manifest["test"]
    expected_links = {record["image_name"] + ".png" for record in records}
    image_dir = prepared / "images"
    actual_links = {path.name for path in image_dir.iterdir()} if image_dir.is_dir() else set()
    if actual_links != expected_links:
        return False
    for record in records:
        link = image_dir / (record["image_name"] + ".png")
        if not link.is_symlink() or link.resolve() != Path(record["image_path"]).resolve():
            return False
    ply_link = prepared / "input" / "fused.ply"
    pointcloud = manifest["pointcloud"]
    if (
        not ply_link.is_symlink()
        or ply_link.resolve() != Path(pointcloud["path"]).resolve()
        or file_sha256(ply_link) != pointcloud["sha256"]
    ):
        return False
    return (
        audit.get("train_images") == [record["source_image_name"] for record in manifest["train"]]
        and audit.get("test_images") == [record["source_image_name"] for record in manifest["test"]]
        and audit.get("pointcloud", {}).get("sha256") == pointcloud["sha256"]
    )


def stage_complete(stage, model, iteration, expected_names, prepared=None, log_dir=None):
    if stage == "prepare":
        return bool(prepared and log_dir and prepared_scene_complete(prepared, Path(log_dir) / "data_audit.json"))
    state = stage_state(model, iteration, expected_names)
    if stage == "train":
        return state["checkpoint_exists"] and protocol_fingerprint_matches(prepared, model)
    if stage == "render":
        return state["render_exists"] and protocol_fingerprint_matches(prepared, model)
    if stage == "eval":
        log_root = Path(log_dir).parents[1] if log_dir else DEFAULT_LOG_ROOT
        return shared_eval_complete(model, iteration, expected_names, log_root)
    raise ValueError("unknown stage: {}".format(stage))


def smoke_certificate_header_valid(payload, runner_sha256):
    certificate = payload.get("smoke_certification", {})
    return (
        payload.get("status") == "completed" and payload.get("smoke_gate_passed") is True
        and payload.get("scene") == "horns" and payload.get("resolution") == "1_8"
        and payload.get("gpu") == 1 and payload.get("iteration") == 10000
        and certificate.get("version") == SMOKE_CERTIFICATION_VERSION
        and certificate.get("runner_sha256") == runner_sha256
    )


def smoke_artifact_checks(log_root, prepared_root, output_root):
    log_root, prepared_root, output_root = Path(log_root), Path(prepared_root), Path(output_root)
    cell_log = log_root / "1_8" / "horns"
    prepared = prepared_root / "1_8" / "horns"
    model = output_root / "1_8" / "horns"
    status = read_json(cell_log / "status.json", {}) or {}
    expected = expected_names_from_manifest(prepared)
    state = stage_state(model, 10000, expected)
    all_logs = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in cell_log.glob("*/*.log"))
    stages = status.get("stages", {})
    return {
        "exact_train_test_counts": len(status.get("train_images") or []) == 3 and len(status.get("test_images") or []) == 8,
        "prepared_complete": prepared_scene_complete(prepared, cell_log / "data_audit.json"),
        "protocol_fingerprint_matches": protocol_fingerprint_matches(prepared, model),
        "checkpoint_complete": state["checkpoint_exists"],
        "render_complete": state["render_exists"] and state["render_count"] == 8 and state["gt_count"] == 8,
        "shared_eval_complete": shared_eval_complete(model, 10000, expected, log_root),
        "all_stage_records_complete": set(stages) == {"prepare", "train", "render", "eval"}
        and all(stages[stage].get("status") == "completed" for stage in stages),
        "train_command_exact": "--iterations 10000" in stages.get("train", {}).get("command", "")
        and stages.get("train", {}).get("physical_gpu") == 1,
        "training_logged_three_views": "Training set length 3" in all_logs,
        "test_cameras_deferred": "REFGS_LLFF_TEST_CAMERAS_DEFERRED count=8" in all_logs,
        "no_traceback": "Traceback" not in all_logs,
        "no_oom": "out of memory" not in all_logs.lower(),
        "no_network_download": not any(token in all_logs.lower() for token in ("download", "urllib", "http://", "https://")),
    }


def smoke_allows_batch(log_root, prepared_root=DEFAULT_PREPARED_ROOT, output_root=DEFAULT_OUTPUT_ROOT):
    payload = read_json(Path(log_root) / "1_8" / "horns" / "status.json", {}) or {}
    runner_hash = file_sha256(Path(__file__))
    if not smoke_certificate_header_valid(payload, runner_hash):
        return False
    checks = smoke_artifact_checks(log_root, prepared_root, output_root)
    return all(checks.values()) and payload.get("smoke_certification", {}).get("checks") == checks


def certify_existing_smoke(args):
    validate_execution_request(args.scene, args.resolution, args.gpu, args.iteration, False)
    status_path = args.log_root / "1_8" / "horns" / "status.json"
    payload = read_json(status_path, {}) or {}
    checks = smoke_artifact_checks(args.log_root, args.prepared_root, args.output_root)
    if not all(checks.values()):
        raise RuntimeError("existing smoke artifacts fail current certification: {}".format(checks))
    payload.update({
        "scene": "horns", "resolution": "1_8", "gpu": 1, "iteration": 10000,
        "status": "completed", "smoke_gate_passed": True,
        "smoke_certification": {
            "version": SMOKE_CERTIFICATION_VERSION,
            "runner_sha256": file_sha256(Path(__file__)),
            "certified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "checks": checks,
        },
    })
    write_json(status_path, payload)
    print(json.dumps(payload["smoke_certification"], indent=2, sort_keys=True))
    return 0


def validate_execution_request(scene, resolution, gpu, iteration, prior_smoke_passed):
    if int(iteration) != 10000:
        raise ValueError("formal LLFF protocol requires exactly 10000 iterations")
    if str(gpu) not in {"1", "2"}:
        raise ValueError("only physical GPU 1 or 2 is permitted")
    exact_smoke = scene == "horns" and resolution == "1_8" and str(gpu) == "1"
    if not prior_smoke_passed and not exact_smoke:
        raise RuntimeError("only horns 1/8 on physical GPU 1 may run before the smoke gate")


def can_certify_smoke(scene, resolution, gpu, iteration, stage_results, prior_smoke_passed):
    if prior_smoke_passed:
        return True
    if not (scene == "horns" and resolution == "1_8" and str(gpu) == "1" and int(iteration) == 10000):
        return False
    required = {"prepare", "train", "render", "eval"}
    if set(stage_results) != required:
        return False
    return all(
        stage_results[stage].get("status") == "completed"
        and not stage_results[stage].get("skipped_existing")
        for stage in required
    )


def aggregate_matches_per_view(aggregate, per_view, tolerance=1e-6):
    for metric in ("PSNR", "SSIM", "LPIPS"):
        values = per_view.get(metric, {})
        aggregate_value = aggregate.get(metric)
        if (
            not values or not isinstance(aggregate_value, (int, float))
            or not math.isfinite(aggregate_value)
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values.values())
        ):
            return False
        mean_value = sum(float(value) for value in values.values()) / len(values)
        if abs(float(aggregate_value) - mean_value) > tolerance:
            return False
    return True


def fsgs_cache_validation_complete(log_root, tolerance=1e-6):
    validation_root = Path(log_root) / "fsgs_shared_eval_validation"
    index = read_json(validation_root / "validation_index.json", {}) or {}
    provenance = read_json(validation_root / "provenance.json", {}) or {}
    summary = read_json(validation_root / "validation_summary.json", {}) or {}
    cells = index.get("cells", {})
    provenance_cells = provenance.get("cells", {})
    expected_keys = {
        "{}/{}".format(resolution, scene)
        for resolution in ("1_8", "1_4") for scene in LLFF_SCENES
    }
    guarantees = provenance.get("guarantees", {})
    numeric_fingerprint = provenance.get("numeric_evaluator_fingerprint")
    runtime_fingerprint = provenance.get("shared_evaluator_runtime_fingerprint")
    if (
        set(cells) != expected_keys or set(provenance_cells) != expected_keys
        or provenance.get("mode") != "cache-status-only"
        or guarantees.get("gpu_used") is not False
        or guarantees.get("metrics_computed") is not False
        or guarantees.get("lpips_imported") is not False
        or not isinstance(provenance.get("original_fsgs_training_runtime"), dict)
        or not isinstance(provenance.get("shared_evaluator_runtime"), dict)
        or len(str(numeric_fingerprint or "")) != 64
        or len(str(runtime_fingerprint or "")) != 64
    ):
        return False
    for key in expected_keys:
        cell = cells[key]
        if (
            cell.get("status") not in {"reusable", "reusable_registered"}
            or provenance_cells[key].get("status") not in {"reusable", "reusable_registered"}
            or len(str(cell.get("input_fingerprint", ""))) != 64
            or len(str(cell.get("recorded_evaluator_sha256", ""))) != 64
            or len(str(cell.get("recorded_fsgs_metrics_sha256", ""))) != 64
            or cell.get("numeric_evaluator_fingerprint") != numeric_fingerprint
            or cell.get("shared_evaluator_runtime_fingerprint") != runtime_fingerprint
            or cell.get("lpips_backbone") != "vgg"
            or finite_metrics(cell.get("metrics", {})) is None
        ):
            return False
    for resolution in ("1_8", "1_4"):
        resolution_cells = [cells["{}/{}".format(resolution, scene)] for scene in LLFF_SCENES]
        computed = {
            metric: sum(float(cell["metrics"][metric]) for cell in resolution_cells) / len(resolution_cells)
            for metric in ("PSNR", "SSIM", "LPIPS")
        }
        recorded = summary.get(resolution, {}).get("mean", {})
        if summary.get(resolution, {}).get("passes_1e-6") is not True:
            return False
        if any(
            not isinstance(recorded.get(metric), (int, float))
            or not math.isfinite(recorded[metric])
            or abs(computed[metric] - float(recorded[metric])) > tolerance
            for metric in ("PSNR", "SSIM", "LPIPS")
        ):
            return False
    return True


def shared_eval_complete(model, iteration, expected_names, log_root):
    model = Path(model)
    method = "ours_{}".format(iteration)
    results = read_json(model / "results.json", {}) or {}
    per_view = read_json(model / "per_view.json", {}) or {}
    metadata = read_json(model / "evaluator_metadata.json", {}) or {}
    if finite_metrics(results) is None or set(results) != {method} or set(per_view) != {method}:
        return False
    per_method = per_view[method]
    expected = set(expected_names)
    for metric in ("PSNR", "SSIM", "LPIPS"):
        values = per_method.get(metric, {})
        if set(values) != expected or any(
                not isinstance(value, (int, float)) or not math.isfinite(value)
                for value in values.values()):
            return False
    if not aggregate_matches_per_view(results[method], per_method):
        return False
    evaluator = REPO_ROOT / "scripts" / "evaluate_refgs_llff.py"
    fsgs_metrics = Path("/home/liuly/Surface_Reconstruction/Sparse/FSGS/metrics.py")
    if (
        metadata.get("lpips_backbone") != "vgg"
        or metadata.get("evaluator_sha256") != file_sha256(evaluator)
        or not fsgs_metrics.is_file()
        or metadata.get("fsgs_metrics_sha256") != file_sha256(fsgs_metrics)
    ):
        return False
    return fsgs_cache_validation_complete(log_root)


def resolve_cell_status(artifact_complete, stage_results, requested):
    failure = next((
        item.get("status") for item in stage_results.values()
        if item.get("status") not in {"completed", "running"}
    ), None)
    if failure:
        return failure
    if artifact_complete:
        return "completed"
    if set(requested) == {"prepare"} and stage_results.get("prepare", {}).get("status") == "completed":
        return "pending"
    return "missing"


def cell_failure_reason(stage_results):
    for item in stage_results.values():
        if item.get("status") not in {"completed", "running"}:
            return item.get("failure_reason") or "{} stage failed".format(item.get("stage", "unknown"))
    return ""


def _gpu_snapshot(gpu):
    command = [
        "nvidia-smi", "--query-gpu=index,name,memory.free,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        fields = [field.strip() for field in line.split(",")]
        if len(fields) == 5 and fields[0] == str(gpu):
            return {
                "physical_index": int(fields[0]), "name": fields[1],
                "memory_free_mib": int(fields[2]), "memory_used_mib": int(fields[3]),
                "utilization_percent": int(fields[4]),
            }
    return None


def _gpu_compute_processes(gpu):
    inventory = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader,nounits"],
        text=True, capture_output=True,
    )
    uuid = None
    if inventory.returncode == 0:
        for line in inventory.stdout.splitlines():
            fields = [field.strip() for field in line.split(",")]
            if len(fields) == 2 and fields[0] == str(gpu):
                uuid = fields[1]
                break
    if uuid is None:
        return None
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
         "--format=csv,noheader,nounits"], text=True, capture_output=True,
    )
    if result.returncode != 0:
        return None
    processes = []
    for line in result.stdout.splitlines():
        fields = [field.strip() for field in line.split(",", 3)]
        if len(fields) == 4 and fields[0] == uuid:
            processes.append({"pid": int(fields[1]), "process_name": fields[2], "used_memory_mib": int(fields[3])})
    return processes


def gpu_resources_ready(snapshot, compute_processes, minimum_free_mib=MIN_GPU_FREE_MIB):
    return bool(
        snapshot and snapshot.get("memory_free_mib", 0) >= minimum_free_mib
        and compute_processes is not None and len(compute_processes) == 0
    )


def _probe_cuda(python, env):
    code = (
        "import json,os,torch; "
        "print(json.dumps({'cuda_visible_devices':os.environ.get('CUDA_VISIBLE_DEVICES'),"
        "'physical_gpu':os.environ.get('REFGS_PHYSICAL_GPU'),"
        "'cuda_available':torch.cuda.is_available(),'device_count':torch.cuda.device_count(),"
        "'current_device':torch.cuda.current_device() if torch.cuda.is_available() else None,"
        "'gpu_name':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))"
    )
    result = subprocess.run([str(python), "-c", code], env=env, text=True, capture_output=True)
    try:
        payload = json.loads(result.stdout.strip())
    except ValueError:
        payload = {}
    payload.update({"returncode": result.returncode, "stderr": result.stderr.strip()})
    payload["passes"] = (
        result.returncode == 0 and payload.get("cuda_available") is True
        and payload.get("device_count") == 1 and payload.get("current_device") == 0
    )
    return payload


def _display(command, env):
    prefix = "CUDA_VISIBLE_DEVICES={} REFGS_PHYSICAL_GPU={}".format(
        env["CUDA_VISIBLE_DEVICES"], env["REFGS_PHYSICAL_GPU"]
    )
    return prefix + " " + " ".join(shlex.quote(str(item)) for item in command)


def _run_stage(stage, command, stage_dir, env, cwd, gpu, python, require_cuda):
    stage_dir.mkdir(parents=True, exist_ok=True)
    log_path = stage_dir / "stage.log"
    snapshot_before = _gpu_snapshot(gpu) if require_cuda else None
    compute_processes = _gpu_compute_processes(gpu) if require_cuda else []
    probe = _probe_cuda(python, env) if require_cuda else None
    base = {
        "stage": stage, "status": "running", "command": _display(command, env),
        "cuda_visible_devices": env["CUDA_VISIBLE_DEVICES"],
        "physical_gpu": int(gpu), "cuda_probe": probe,
        "gpu_before": snapshot_before, "competing_compute_processes": compute_processes,
    }
    if require_cuda and not (probe and probe["passes"] and gpu_resources_ready(snapshot_before, compute_processes)):
        base.update(status="blocked_cuda", failure_reason="GPU visibility, free-memory, or exclusivity preflight failed")
        write_json(stage_dir / "status.json", base)
        return base
    start = time.monotonic()
    peak_used = snapshot_before["memory_used_mib"] if snapshot_before else None
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write("CUDA_PROBE " + json.dumps(probe, sort_keys=True) + "\n" if probe else "")
        handle.write("$ " + _display(command, env) + "\n")
        handle.flush()
        process = subprocess.Popen(
            [str(item) for item in command], cwd=str(cwd), env=env,
            stdout=handle, stderr=subprocess.STDOUT, text=True,
        )
        while process.poll() is None:
            if require_cuda:
                snapshot = _gpu_snapshot(gpu)
                if snapshot is not None:
                    peak_used = max(peak_used, snapshot["memory_used_mib"])
            time.sleep(1.0)
        returncode = process.returncode
    elapsed = time.monotonic() - start
    status = "completed" if returncode == 0 else "failed"
    base.update({
        "status": status, "returncode": returncode,
        "elapsed_seconds": elapsed, "peak_memory_used_mib": peak_used,
        "peak_increment_mib": (peak_used - snapshot_before["memory_used_mib"])
        if peak_used is not None and snapshot_before else None,
        "failure_reason": "" if returncode == 0 else "stage exited {}".format(returncode),
    })
    write_json(stage_dir / "status.json", base)
    return base


def build_commands(args, paths):
    python = str(args.python)
    prepared, model = paths["prepared"], paths["model"]
    return {
        "prepare": [
            python, str(REPO_ROOT / "scripts" / "prepare_refgs_llff.py"),
            "--scene", args.scene, "--resolution", args.resolution,
            "--data-root", str(args.data_root),
            "--author-preprocessed-root", str(args.author_preprocessed_root),
            "--prepared-root", str(args.prepared_root), "--log-root", str(args.log_root),
        ],
        "train": [
            python, str(REPO_ROOT / "train.py"), "-s", str(prepared), "-m", str(model),
            "--eval", "--iterations", str(args.iteration),
            "--save_iterations", "5000", str(args.iteration),
        ],
        "render": [
            python, str(REPO_ROOT / "render.py"), "-s", str(prepared), "-m", str(model),
            "--iteration", str(args.iteration), "--renderer", "refgs",
            "--image-key", "pbr_rgb", "--skip_train",
        ],
        "eval": [
            python, str(REPO_ROOT / "scripts" / "evaluate_refgs_llff.py"),
            "--model-path", str(model), "--iteration", str(args.iteration),
            "--manifest", str(prepared / "refgs_llff_manifest.json"),
        ],
    }


def requested_stages(args):
    selected = [stage for stage in ("prepare", "train", "render", "eval") if getattr(args, stage)]
    if not selected:
        raise ValueError("select at least one stage")
    return selected


def execute(args):
    prior_smoke_passed = smoke_allows_batch(args.log_root, args.prepared_root, args.output_root)
    validate_execution_request(args.scene, args.resolution, args.gpu, args.iteration, prior_smoke_passed)
    stages_requested = requested_stages(args)
    paths = cell_paths(args.prepared_root, args.output_root, args.log_root, args.resolution, args.scene)
    paths["log"].mkdir(parents=True, exist_ok=True)

    def persist_preflight_block(status, reason):
        payload = {
            "scene": args.scene, "resolution": args.resolution, "gpu": int(args.gpu),
            "iteration": args.iteration, "status": status, "failure_reason": reason,
            "checkpoint_exists": False, "render_exists": False,
            "metrics_exists": False, "metrics": None, "smoke_gate_passed": False,
        }
        write_json(paths["log"] / "status.json", payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    for storage_path in (args.prepared_root, args.output_root, args.tmp_root):
        storage_path.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(str(storage_path)).free < MIN_STORAGE_FREE_BYTES:
            return persist_preflight_block("blocked_data", "less than 10 GiB free at {}".format(storage_path))
    gpu_lock = None
    if any(stage in {"train", "render", "eval"} for stage in stages_requested):
        lock_path = args.tmp_root / "gpu_locks" / "gpu_{}.lock".format(args.gpu)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        gpu_lock = lock_path.open("a+")
        try:
            fcntl.flock(gpu_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return persist_preflight_block(
                "blocked_cuda", "another Ref-GS LLFF worker owns physical GPU {}".format(args.gpu)
            )
    paths["model"].mkdir(parents=True, exist_ok=True)
    cell_tmp = Path(args.tmp_root) / args.resolution / args.scene
    (cell_tmp / "result").mkdir(parents=True, exist_ok=True)
    env = build_child_env(args.gpu)
    commands = build_commands(args, paths)
    with (paths["log"] / "commands.txt").open("a", encoding="utf-8") as handle:
        for stage in stages_requested:
            handle.write(stage + ": " + _display(commands[stage], env) + "\n")
    previous_cell = read_json(paths["log"] / "status.json", {}) or {}
    stage_results = {}
    for stage in stages_requested:
        if stage != "prepare" and not prepared_scene_complete(
                paths["prepared"], paths["log"] / "data_audit.json"):
            result = {
                "stage": stage, "status": "blocked_data",
                "failure_reason": "prepared manifest, links, or audit failed strict validation",
            }
            write_json(paths["log"] / stage / "status.json", result)
            stage_results[stage] = result
            break
        expected = expected_names_from_manifest(paths["prepared"])
        forced = stage in args.force_stage
        if args.skip_existing and not forced and stage_complete(
                stage, paths["model"], args.iteration, expected,
                prepared=paths["prepared"], log_dir=paths["log"]):
            stage_results[stage] = {"stage": stage, "status": "completed", "skipped_existing": True}
            continue
        result = _run_stage(
            stage, commands[stage], paths["log"] / stage, env, cell_tmp,
            args.gpu, args.python, require_cuda=stage in {"train", "render", "eval"},
        )
        stage_results[stage] = result
        if result["status"] != "completed":
            break
    expected = expected_names_from_manifest(paths["prepared"])
    final = stage_state(paths["model"], args.iteration, expected)
    audit = read_json(paths["log"] / "data_audit.json", {}) or {}
    fingerprint_matches = protocol_fingerprint_matches(paths["prepared"], paths["model"])
    final["protocol_fingerprint_matches"] = fingerprint_matches
    final["checkpoint_exists"] = final["checkpoint_exists"] and fingerprint_matches
    final["render_exists"] = final["render_exists"] and fingerprint_matches
    final["metrics_exists"] = shared_eval_complete(paths["model"], args.iteration, expected, args.log_root) and fingerprint_matches
    prepared_complete = prepared_scene_complete(paths["prepared"], paths["log"] / "data_audit.json")
    final["prepared_complete"] = prepared_complete
    artifact_complete = prepared_complete and all(final[key] for key in ("checkpoint_exists", "render_exists", "metrics_exists"))
    status = resolve_cell_status(artifact_complete, stage_results, set(stages_requested))
    completed = status == "completed"
    smoke_gate = completed and can_certify_smoke(
        args.scene, args.resolution, args.gpu, args.iteration, stage_results, prior_smoke_passed
    )
    persisted_stages = dict(previous_cell.get("stages", {}))
    persisted_stages.update(stage_results)
    payload = dict(final, scene=args.scene, resolution=args.resolution, gpu=int(args.gpu),
                   iteration=args.iteration, status=status, smoke_gate_passed=smoke_gate,
                   stages=persisted_stages, failure_reason=cell_failure_reason(stage_results),
                   train_images=audit.get("train_images"),
                   test_images=audit.get("test_images"), pointcloud=audit.get("pointcloud"))
    write_json(paths["log"] / "status.json", payload)
    if smoke_gate:
        checks = smoke_artifact_checks(args.log_root, args.prepared_root, args.output_root)
        if all(checks.values()):
            payload["smoke_certification"] = {
                "version": SMOKE_CERTIFICATION_VERSION,
                "runner_sha256": file_sha256(Path(__file__)),
                "certified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "checks": checks,
            }
            write_json(paths["log"] / "status.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if completed else 1


def build_parser():
    parser = argparse.ArgumentParser(description="Run Ref-GS under the FSGS LLFF three-view protocol")
    parser.add_argument("--scene", required=True, choices=LLFF_SCENES)
    parser.add_argument("--resolution", required=True, choices=tuple(RESOLUTIONS))
    parser.add_argument("--gpu", required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--iteration", type=int, default=10000)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--force-stage", action="append", choices=("prepare", "train", "render", "eval"), default=[])
    parser.add_argument("--certify-existing-smoke", action="store_true")
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--author-preprocessed-root", type=Path, default=DEFAULT_AUTHOR_ROOT)
    parser.add_argument("--prepared-root", type=Path, default=DEFAULT_PREPARED_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--tmp-root", type=Path, default=DEFAULT_TMP_ROOT)
    parser.add_argument("--log-root", type=Path, default=DEFAULT_LOG_ROOT)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    resolve_runtime_paths(args, Path.cwd())
    try:
        if args.certify_existing_smoke:
            return certify_existing_smoke(args)
        return execute(args)
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
