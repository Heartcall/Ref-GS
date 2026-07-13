#!/usr/bin/env python3
"""Read-only, CPU-only audit of cached shared-evaluator results.

This module intentionally uses only the Python standard library.  It hashes PNG
bytes but never decodes images and never imports torch, PIL, or LPIPS.
"""

import argparse
import ast
import datetime
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
from pathlib import Path


SCENES = ("fern", "flower", "fortress", "horns", "leaves", "orchids", "room", "trex")
RESOLUTIONS = ("1_8", "1_4")
EXPECTED_TEST_COUNTS = {
    "fern": 3, "flower": 5, "fortress": 6, "horns": 8,
    "leaves": 4, "orchids": 4, "room": 6, "trex": 7,
}
METRICS = ("PSNR", "SSIM", "LPIPS")
DEFAULT_FSGS_REPO = Path("/home/liuly/Surface_Reconstruction/Sparse/FSGS")
DEFAULT_FSGS_OUTPUT = Path("/data1/liuly/FSGS_LLFF/output/llff_repro")
DEFAULT_CACHE_ROOT = Path("logs/refgs_llff/fsgs_shared_eval_validation")
DEFAULT_FSGS_ENVIRONMENT = DEFAULT_FSGS_REPO / "logs" / "llff_repro" / "environment.json"
REPO_ROOT = Path(__file__).resolve().parents[1]


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def directory_manifest(directory):
    directory = Path(directory)
    records = []
    for path in sorted(directory.glob("*.png")):
        stat = path.stat()
        records.append({
            "name": path.name,
            "size_bytes": stat.st_size,
            "sha256": file_sha256(path),
            "mtime_ns": stat.st_mtime_ns,
        })
    stable_records = [
        {key: record[key] for key in ("name", "size_bytes", "sha256")}
        for record in records
    ]
    return {
        "count": len(records),
        "names": [record["name"] for record in records],
        "files": records,
        "manifest_sha256": canonical_sha256(stable_records),
        "latest_mtime_ns": max((record["mtime_ns"] for record in records), default=None),
    }


def path_access(path, workspace_root=REPO_ROOT):
    path = Path(path)
    exists = path.exists()
    try:
        realpath = str(path.resolve(strict=True))
    except OSError:
        realpath = str(path.resolve(strict=False))
    try:
        external = not Path(realpath).is_relative_to(Path(workspace_root).resolve())
    except AttributeError:  # Python 3.7
        try:
            Path(realpath).relative_to(Path(workspace_root).resolve())
            external = False
        except ValueError:
            external = True
    return {
        "requested_path": str(path),
        "realpath": realpath,
        "exists": exists,
        "readable": exists and os.access(str(path), os.R_OK),
        "outside_workspace": external,
        "sandbox_observation": (
            "readable_from_current_restricted_shell"
            if exists and os.access(str(path), os.R_OK)
            else "external_access_unknown"
        ),
        "codex_direct_file_tool": "not_available_in_this_session",
        "shell_subprocess_access": exists and os.access(str(path), os.R_OK),
    }


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _valid_sha256(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _cache_payload(cache_dir, method):
    cache_dir = Path(cache_dir)
    results = _read_json(cache_dir / "results.json")
    per_view = _read_json(cache_dir / "per_view.json")
    metadata = _read_json(cache_dir / "evaluator_metadata.json")
    if not all(isinstance(item, dict) for item in (results, per_view, metadata)):
        return None, "missing_or_unreadable_cache_files"
    if set(results) != {method} or set(per_view) != {method}:
        return None, "unexpected_cache_method_keys"
    aggregate, views = results[method], per_view[method]
    if not isinstance(aggregate, dict) or not isinstance(views, dict):
        return None, "invalid_cache_schema"
    for metric in METRICS:
        value = aggregate.get(metric)
        metric_views = views.get(metric)
        if (
            not isinstance(value, (int, float)) or not math.isfinite(value)
            or not isinstance(metric_views, dict) or not metric_views
            or any(not isinstance(item, (int, float)) or not math.isfinite(item)
                   for item in metric_views.values())
        ):
            return None, "nonfinite_or_missing_metrics"
        mean = sum(float(item) for item in metric_views.values()) / len(metric_views)
        if abs(float(value) - mean) > 1e-6:
            return None, "aggregate_per_view_mismatch"
    if (
        metadata.get("lpips_backbone") != "vgg"
        or not _valid_sha256(metadata.get("evaluator_sha256"))
        or not _valid_sha256(metadata.get("fsgs_metrics_sha256"))
    ):
        return None, "invalid_evaluator_fingerprint"
    return {"results": results, "per_view": per_view, "metadata": metadata}, None


def audit_cell(resolution, scene, model_dir, cache_dir,
               current_evaluator_sha256, current_fsgs_metrics_sha256,
               previous=None, iteration=10000,
               numeric_evaluator_fingerprint_value=None,
               shared_evaluator_runtime_fingerprint=None,
               lpips_backbone="vgg"):
    model_dir, cache_dir = Path(model_dir), Path(cache_dir)
    base = model_dir / "test" / "ours_{}".format(iteration)
    renders_dir, gt_dir = base / "renders", base / "gt"
    access = {
        "model": path_access(model_dir),
        "renders": path_access(renders_dir),
        "gt": path_access(gt_dir),
        "cache": path_access(cache_dir),
    }
    if not all(access[key]["readable"] for key in ("model", "renders", "gt")):
        return {
            "resolution": resolution, "scene": scene,
            "status": "external_access_unknown",
            "reason": "external_inputs_missing_or_unreadable",
            "access": access,
        }

    renders = directory_manifest(renders_dir)
    gt = directory_manifest(gt_dir)
    expected_count = EXPECTED_TEST_COUNTS.get(scene)
    if (
        not renders["count"] or renders["names"] != gt["names"]
        or (expected_count is not None and renders["count"] != expected_count)
    ):
        return {
            "resolution": resolution, "scene": scene,
            "status": "invalid_inputs", "reason": "render_gt_manifest_mismatch",
            "access": access, "renders": renders, "gt": gt,
        }
    input_fingerprint = canonical_sha256({
        "renders": renders["manifest_sha256"],
        "gt": gt["manifest_sha256"],
    })
    method = "ours_{}".format(iteration)
    payload, error = _cache_payload(cache_dir, method)
    if error:
        return {
            "resolution": resolution, "scene": scene,
            "status": "invalid_cache", "reason": error,
            "access": access, "renders": renders, "gt": gt,
            "input_fingerprint": input_fingerprint,
        }
    metadata = payload["metadata"]
    recorded_evaluator = metadata["evaluator_sha256"]
    recorded_fsgs = metadata["fsgs_metrics_sha256"]
    if numeric_evaluator_fingerprint_value is None:
        dependency_hashes = {
            "refgs_loss_utils": file_sha256(REPO_ROOT / "utils" / "loss_utils.py"),
            "refgs_image_utils": file_sha256(REPO_ROOT / "utils" / "image_utils.py"),
            "refgs_lpips": file_sha256(REPO_ROOT / "lpipsPyTorch" / "modules" / "lpips.py"),
        }
        numeric_evaluator_fingerprint_value = numeric_evaluator_fingerprint(
            REPO_ROOT / "scripts" / "evaluate_refgs_llff.py", dependency_hashes, lpips_backbone
        )
    if shared_evaluator_runtime_fingerprint is None:
        shared_evaluator_runtime_fingerprint = canonical_sha256(shared_evaluator_runtime())
    common = {
        "resolution": resolution, "scene": scene, "status": None, "reason": None,
        "access": access, "renders": renders, "gt": gt,
        "input_fingerprint": input_fingerprint,
        "recorded_evaluator_sha256": recorded_evaluator,
        "current_evaluator_sha256": current_evaluator_sha256,
        "evaluator_file_changed": recorded_evaluator != current_evaluator_sha256,
        "numeric_change_proven": False,
        "recorded_fsgs_metrics_sha256": recorded_fsgs,
        "current_fsgs_metrics_sha256": current_fsgs_metrics_sha256,
        "metrics": payload["results"][method],
        "per_view_count": len(payload["per_view"][method]["PSNR"]),
        "lpips_backbone": metadata["lpips_backbone"],
        "numeric_evaluator_fingerprint": numeric_evaluator_fingerprint_value,
        "shared_evaluator_runtime_fingerprint": shared_evaluator_runtime_fingerprint,
        "cached_runtime": metadata.get("runtime"),
    }
    if recorded_fsgs != current_fsgs_metrics_sha256:
        common.update(status="source_changed", reason="fsgs_metrics_source_hash_changed")
        return common
    expected_names = set(renders["names"])
    if any(set(payload["per_view"][method][metric]) != expected_names for metric in METRICS):
        common.update(status="invalid_cache", reason="per_view_names_do_not_match_inputs")
        return common
    identity = {
        "input_fingerprint": input_fingerprint,
        "numeric_evaluator_fingerprint": numeric_evaluator_fingerprint_value,
        "shared_evaluator_runtime_fingerprint": shared_evaluator_runtime_fingerprint,
        "lpips_backbone": lpips_backbone,
    }
    identity_keys = set(identity)
    if previous and identity_keys.issubset(previous):
        status, reason = cache_identity_status(previous, identity)
        common.update(status=status, reason=reason)
        return common

    latest_input = max(renders["latest_mtime_ns"] or 0, gt["latest_mtime_ns"] or 0)
    cache_paths = [cache_dir / name for name in ("results.json", "per_view.json", "evaluator_metadata.json")]
    cache_not_older = all(path.stat().st_mtime_ns >= latest_input for path in cache_paths)
    common["registration_basis"] = {
        "exact_render_gt_names": True,
        "finite_metrics": True,
        "aggregate_matches_per_view": True,
        "cache_files_not_older_than_inputs": cache_not_older,
    }
    if cache_not_older:
        common.update(status="reusable_registered", reason="legacy_cache_registered_without_recompute")
    else:
        common.update(status="input_provenance_unknown", reason="cache_older_than_current_inputs")
    return common


def _git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _distribution_version(name):
    try:
        import importlib_metadata
        return importlib_metadata.version(name)
    except Exception:
        return None


def _torch_cuda_version():
    version_file = Path(sys.prefix) / "lib" / "python{}.{}".format(
        sys.version_info.major, sys.version_info.minor
    ) / "site-packages" / "torch" / "version.py"
    try:
        match = re.search(r"^cuda\s*=\s*['\"]([^'\"]+)", version_file.read_text(), re.MULTILINE)
        return match.group(1) if match else None
    except OSError:
        return None


def shared_evaluator_runtime():
    return {
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "torch_version": _distribution_version("torch"),
        "torchvision_version": _distribution_version("torchvision"),
        "torch_cuda_version": _torch_cuda_version(),
        "numpy_version": _distribution_version("numpy"),
        "pillow_version": _distribution_version("Pillow"),
        "lpips_version": _distribution_version("lpips"),
    }


def runtime_provenance(fsgs_environment_path=DEFAULT_FSGS_ENVIRONMENT):
    environment = _read_json(fsgs_environment_path) or {}
    original = environment.get("runtime")
    if not isinstance(original, dict):
        original = {
            "status": "external_access_unknown",
            "source": str(Path(fsgs_environment_path).resolve(strict=False)),
        }
    else:
        original = dict(original)
        original["source"] = str(Path(fsgs_environment_path).resolve(strict=False))
    return {
        "original_fsgs_training_runtime": original,
        "shared_evaluator_runtime": shared_evaluator_runtime(),
    }


def numeric_evaluator_fingerprint(evaluator_path, dependency_hashes, lpips_backbone="vgg"):
    """Hash only metric-producing AST and numerical dependencies.

    The evaluator function is truncated before result serialization, so CLI,
    logging, metadata, comments, and output formatting do not affect this key.
    """
    tree = ast.parse(Path(evaluator_path).read_text(encoding="utf-8"))
    evaluate_function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "evaluate"
    )
    numerical_body = []
    for statement in evaluate_function.body:
        if (
            isinstance(statement, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "method"
                    for target in statement.targets)
        ):
            break
        numerical_body.append(statement)
    payload = {
        "evaluate_numeric_ast": ast.dump(ast.Module(body=numerical_body), annotate_fields=True),
        "dependencies": dependency_hashes,
        "lpips_backbone": lpips_backbone,
    }
    return canonical_sha256(payload)


def cache_identity_status(saved, current):
    checks = (
        ("input_fingerprint", "input_hash_changed", "render_or_gt_content_changed"),
        ("numeric_evaluator_fingerprint", "numeric_implementation_changed", "metric_numeric_implementation_changed"),
        ("shared_evaluator_runtime_fingerprint", "critical_dependency_changed", "critical_shared_evaluator_dependency_changed"),
        ("lpips_backbone", "lpips_backbone_changed", "lpips_backbone_changed"),
    )
    for key, status, reason in checks:
        if saved.get(key) != current.get(key):
            return status, reason
    return "reusable", "cache_identity_matches"


def _source_entry(path):
    access = path_access(path)
    access["sha256"] = file_sha256(path) if access["readable"] and Path(path).is_file() else None
    return access


def audit_all(fsgs_repo, fsgs_output_root, cache_root, iteration=10000):
    fsgs_repo, fsgs_output_root, cache_root = map(Path, (fsgs_repo, fsgs_output_root, cache_root))
    evaluator = REPO_ROOT / "scripts" / "evaluate_refgs_llff.py"
    metrics = fsgs_repo / "metrics.py"
    current_evaluator = file_sha256(evaluator)
    current_metrics = file_sha256(metrics) if metrics.is_file() and os.access(str(metrics), os.R_OK) else None
    previous_index = _read_json(cache_root / "validation_index.json") or {}
    previous_provenance = _read_json(cache_root / "provenance.json") or {}
    previous_cells = previous_index.get("cells", {}) if isinstance(previous_index, dict) else {}
    source_paths = {
        "fsgs_metrics": metrics,
        "fsgs_loss_utils": fsgs_repo / "utils" / "loss_utils.py",
        "fsgs_image_utils": fsgs_repo / "utils" / "image_utils.py",
        "fsgs_lpips_init": fsgs_repo / "lpipsPyTorch" / "__init__.py",
        "fsgs_lpips_impl": fsgs_repo / "lpipsPyTorch" / "modules" / "lpips.py",
        "refgs_shared_evaluator": evaluator,
        "refgs_loss_utils": REPO_ROOT / "utils" / "loss_utils.py",
        "refgs_image_utils": REPO_ROOT / "utils" / "image_utils.py",
        "refgs_lpips_init": REPO_ROOT / "lpipsPyTorch" / "__init__.py",
        "refgs_lpips_impl": REPO_ROOT / "lpipsPyTorch" / "modules" / "lpips.py",
    }
    source_entries = {name: _source_entry(path) for name, path in source_paths.items()}
    runtimes = runtime_provenance(fsgs_repo / "logs" / "llff_repro" / "environment.json")
    shared_runtime_fingerprint = canonical_sha256(runtimes["shared_evaluator_runtime"])
    numerical_dependencies = {
        name: source_entries[name]["sha256"]
        for name in (
            "fsgs_metrics", "refgs_loss_utils", "refgs_image_utils",
            "refgs_lpips_init", "refgs_lpips_impl",
        )
    }
    numeric_fingerprint = numeric_evaluator_fingerprint(
        evaluator, numerical_dependencies, lpips_backbone="vgg"
    )
    cells = {}
    for resolution in RESOLUTIONS:
        for scene in SCENES:
            key = "{}/{}".format(resolution, scene)
            cells[key] = audit_cell(
                resolution, scene,
                fsgs_output_root / resolution / scene,
                cache_root / resolution / scene,
                current_evaluator, current_metrics,
                previous=previous_cells.get(key), iteration=iteration,
                numeric_evaluator_fingerprint_value=numeric_fingerprint,
                shared_evaluator_runtime_fingerprint=shared_runtime_fingerprint,
                lpips_backbone="vgg",
            )
    validation_index_before = path_access(cache_root / "validation_index.json")
    provenance_before = path_access(cache_root / "provenance.json")
    provenance = {
        "schema_version": 2,
        "mode": "cache-status-only",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "guarantees": {
            "gpu_used": False,
            "images_decoded": False,
            "metrics_computed": False,
            "torch_imported": False,
            "lpips_imported": False,
        },
        "workspace": str(REPO_ROOT),
        "diagnostic_context": previous_provenance.get("diagnostic_context", {}),
        "path_access": {
            "fsgs_repository": path_access(fsgs_repo),
            "fsgs_metrics": path_access(metrics),
            "fsgs_loss_utils": path_access(fsgs_repo / "utils" / "loss_utils.py"),
            "fsgs_outputs": path_access(fsgs_output_root),
            "shared_cache": path_access(cache_root),
            "validation_index_observed_before_write": validation_index_before,
            "provenance_observed_before_write": provenance_before,
        },
        "fsgs_repository": {
            "requested_path": str(fsgs_repo),
            "realpath": str(fsgs_repo.resolve()),
            "commit": _git(fsgs_repo, "rev-parse", "HEAD"),
            "dirty_status": (_git(fsgs_repo, "status", "--short") or "").splitlines(),
        },
        "metric_sources": source_entries,
        "original_fsgs_training_runtime": runtimes["original_fsgs_training_runtime"],
        "shared_evaluator_runtime": runtimes["shared_evaluator_runtime"],
        "shared_evaluator_runtime_fingerprint": shared_runtime_fingerprint,
        "numeric_evaluator_fingerprint": numeric_fingerprint,
        "cells": cells,
        "summary": {
            status: sum(cell.get("status") == status for cell in cells.values())
            for status in sorted({cell.get("status") for cell in cells.values()})
        },
    }
    index = {
        "schema_version": 2,
        "mode": "cache-status-only",
        "generated_at": provenance["generated_at"],
        "cells": {
            key: {
                "status": cell.get("status"),
                "reason": cell.get("reason"),
                "input_fingerprint": cell.get("input_fingerprint"),
                "render_manifest_sha256": cell.get("renders", {}).get("manifest_sha256"),
                "gt_manifest_sha256": cell.get("gt", {}).get("manifest_sha256"),
                "recorded_evaluator_sha256": cell.get("recorded_evaluator_sha256"),
                "recorded_fsgs_metrics_sha256": cell.get("recorded_fsgs_metrics_sha256"),
                "numeric_evaluator_fingerprint": cell.get("numeric_evaluator_fingerprint"),
                "shared_evaluator_runtime_fingerprint": cell.get("shared_evaluator_runtime_fingerprint"),
                "lpips_backbone": cell.get("lpips_backbone"),
                "metrics": cell.get("metrics"),
            }
            for key, cell in cells.items()
        },
    }
    return provenance, index


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(str(temporary), str(path))


def build_parser():
    parser = argparse.ArgumentParser(
        description="CPU-only cache/provenance audit; never imports LPIPS or computes metrics"
    )
    parser.add_argument("--cache-status-only", action="store_true", required=True)
    parser.add_argument("--fsgs-repo", type=Path, default=DEFAULT_FSGS_REPO)
    parser.add_argument("--fsgs-output-root", type=Path, default=DEFAULT_FSGS_OUTPUT)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--iteration", type=int, default=10000)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    provenance, index = audit_all(
        args.fsgs_repo, args.fsgs_output_root, args.cache_root, args.iteration
    )
    write_json(args.cache_root / "provenance.json", provenance)
    write_json(args.cache_root / "validation_index.json", index)
    print(json.dumps(provenance["summary"], indent=2, sort_keys=True))
    return 3 if provenance["summary"].get("external_access_unknown", 0) else 0


if __name__ == "__main__":
    sys.exit(main())
