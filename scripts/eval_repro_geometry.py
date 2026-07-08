#!/usr/bin/env python3
"""Evaluate reproduction geometry from saved Ref-GS point clouds.

The Ref-GS reproduction outputs contain Gaussian point clouds, not extracted
surfaces. This evaluator therefore computes raw-coordinate point-set metrics
against the best available dataset reference:

- Ref-NeRF/Shiny Blender Synthetic: scene GT mesh sampled to points.
- GlossySyntheticConverted: eval_pts.ply.
- NeRF Synthetic: points3d.ply, reported as proxy only.

No ICP, scale fitting, or coordinate alignment is applied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from plyfile import PlyData
from scipy.spatial import cKDTree


DEFAULT_SCENES = {
    "refnerf": ["helmet", "car", "ball", "teapot", "coffee", "toaster"],
    "glossy_synthetic": [
        "bell_blender",
        "tbell_blender",
        "potion_blender",
        "teapot_blender",
        "luyu_blender",
        "cat_blender",
    ],
    "nerf_synthetic": ["ship", "ficus", "lego", "mic", "hotdog", "chair", "materials", "drums"],
}

DATASET_SUBDIRS = {
    "refnerf": "Shiny Blender Synthetic",
    "glossy_synthetic": "GlossySyntheticConverted",
    "nerf_synthetic": "NeRF Synthetic",
}


@dataclass(frozen=True)
class Reference:
    path: Path
    kind: str
    accepted_gt: bool


def read_ply(path: Path) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
    ply = PlyData.read(str(path))
    vertex = ply["vertex"]
    points = np.stack(
        [
            np.asarray(vertex["x"], dtype=np.float64),
            np.asarray(vertex["y"], dtype=np.float64),
            np.asarray(vertex["z"], dtype=np.float64),
        ],
        axis=1,
    )

    normals = None
    names = set(vertex.data.dtype.names or ())
    if {"nx", "ny", "nz"}.issubset(names):
        normals = np.stack(
            [
                np.asarray(vertex["nx"], dtype=np.float64),
                np.asarray(vertex["ny"], dtype=np.float64),
                np.asarray(vertex["nz"], dtype=np.float64),
            ],
            axis=1,
        )

    faces = None
    if "face" in ply:
        faces = np.asarray(ply["face"].data["vertex_indices"], dtype=object)
        faces = np.asarray([np.asarray(face, dtype=np.int64)[:3] for face in faces], dtype=np.int64)

    return points, normals, faces


def stable_sample_indices(count: int, limit: int, rng: np.random.Generator) -> np.ndarray:
    if count <= limit:
        return np.arange(count)
    return np.sort(rng.choice(count, size=limit, replace=False))


def sample_mesh_points(
    vertices: np.ndarray,
    faces: np.ndarray,
    sample_count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if faces is None or len(faces) == 0:
        return vertices[stable_sample_indices(len(vertices), sample_count, rng)]

    tri = vertices[faces]
    cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    areas = np.linalg.norm(cross, axis=1) * 0.5
    valid = np.isfinite(areas) & (areas > 0)
    tri = tri[valid]
    areas = areas[valid]
    if len(tri) == 0:
        return vertices[stable_sample_indices(len(vertices), sample_count, rng)]

    probs = areas / areas.sum()
    face_idx = rng.choice(len(tri), size=sample_count, replace=True, p=probs)
    chosen = tri[face_idx]
    uv = rng.random((sample_count, 2))
    flip = uv.sum(axis=1) > 1.0
    uv[flip] = 1.0 - uv[flip]
    return chosen[:, 0] + uv[:, :1] * (chosen[:, 1] - chosen[:, 0]) + uv[:, 1:] * (
        chosen[:, 2] - chosen[:, 0]
    )


def reference_for(data_root: Path, dataset: str, scene: str) -> Optional[Reference]:
    scene_root = data_root / DATASET_SUBDIRS[dataset] / scene
    if dataset == "refnerf":
        candidates = [
            scene_root / f"{scene}_gt_mesh.ply",
            data_root / DATASET_SUBDIRS[dataset] / "gt" / f"{scene}_gt_mesh.ply",
        ]
        for path in candidates:
            if path.exists():
                return Reference(path=path, kind="accepted_gt_mesh", accepted_gt=True)
        return None

    if dataset == "glossy_synthetic":
        eval_pts = scene_root / "eval_pts.ply"
        if eval_pts.exists():
            return Reference(path=eval_pts, kind="accepted_eval_points", accepted_gt=True)
        points = scene_root / "points.ply"
        if points.exists():
            return Reference(path=points, kind="candidate_points_proxy", accepted_gt=False)
        return None

    if dataset == "nerf_synthetic":
        points = scene_root / "points3d.ply"
        if points.exists():
            return Reference(path=points, kind="proxy_points_not_accepted_gt", accepted_gt=False)
        return None

    raise ValueError(f"Unknown dataset: {dataset}")


def latest_point_cloud(model_dir: Path) -> Tuple[Optional[int], Optional[Path]]:
    pc_root = model_dir / "point_cloud"
    if not pc_root.exists():
        return None, None
    candidates: List[Tuple[int, Path]] = []
    for path in pc_root.glob("iteration_*/point_cloud.ply"):
        try:
            iteration = int(path.parent.name.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            continue
        candidates.append((iteration, path))
    if not candidates:
        return None, None
    return max(candidates, key=lambda item: item[0])


def bbox_diag(points: np.ndarray) -> float:
    if len(points) == 0:
        return math.nan
    extent = points.max(axis=0) - points.min(axis=0)
    return float(np.linalg.norm(extent))


def fscore(precision: float, recall: float) -> float:
    denom = precision + recall
    if denom == 0:
        return 0.0
    return float(2.0 * precision * recall / denom)


def compute_metrics(
    pred: np.ndarray,
    ref: np.ndarray,
    thresholds_pct: Sequence[float],
) -> Dict[str, Optional[float]]:
    tree_ref = cKDTree(ref)
    pred_to_ref, _ = tree_ref.query(pred, k=1, workers=-1)
    tree_pred = cKDTree(pred)
    ref_to_pred, _ = tree_pred.query(ref, k=1, workers=-1)

    diag = bbox_diag(ref)
    metrics: Dict[str, Optional[float]] = {
        "bbox_diag": diag,
        "accuracy_mean": float(np.mean(pred_to_ref)),
        "accuracy_median": float(np.median(pred_to_ref)),
        "accuracy_rmse": float(np.sqrt(np.mean(np.square(pred_to_ref)))),
        "completeness_mean": float(np.mean(ref_to_pred)),
        "completeness_median": float(np.median(ref_to_pred)),
        "completeness_rmse": float(np.sqrt(np.mean(np.square(ref_to_pred)))),
        "chamfer_l1": float((np.mean(pred_to_ref) + np.mean(ref_to_pred)) * 0.5),
        "chamfer_l2": float((np.mean(np.square(pred_to_ref)) + np.mean(np.square(ref_to_pred))) * 0.5),
        "hausdorff": float(max(np.max(pred_to_ref), np.max(ref_to_pred))),
    }

    for pct in thresholds_pct:
        threshold = diag * pct
        precision = float(np.mean(pred_to_ref < threshold))
        recall = float(np.mean(ref_to_pred < threshold))
        key = f"{pct * 100:g}pct".replace(".", "p")
        metrics[f"threshold_{key}"] = float(threshold)
        metrics[f"precision_{key}"] = precision
        metrics[f"recall_{key}"] = recall
        metrics[f"fscore_{key}"] = fscore(precision, recall)

    return metrics


def evaluate_scene(
    dataset: str,
    scene: str,
    data_root: Path,
    output_root: Path,
    max_pred_points: int,
    max_ref_points: int,
    mesh_sample_points: int,
    thresholds_pct: Sequence[float],
    seed: int,
) -> Dict[str, object]:
    model_dir = output_root / dataset / scene
    iteration, pred_path = latest_point_cloud(model_dir)
    ref = reference_for(data_root, dataset, scene)
    row: Dict[str, object] = {
        "dataset": dataset,
        "scene": scene,
        "status": "ok",
        "iteration": iteration,
        "model_dir": str(model_dir),
        "pred_path": str(pred_path) if pred_path else "",
        "reference_path": str(ref.path) if ref else "",
        "reference_kind": ref.kind if ref else "",
        "accepted_gt": ref.accepted_gt if ref else False,
        "alignment": "raw_coordinates_no_icp",
        "normal_angle_error_deg": None,
        "normal_metric_reason": "prediction_point_cloud_has_no_normals",
    }

    if pred_path is None:
        row.update(status="missing_prediction", error="point_cloud/iteration_*/point_cloud.ply not found")
        return row
    if ref is None:
        row.update(status="missing_reference", error="reference geometry not found")
        return row

    scene_digest = hashlib.sha256(f"{dataset}/{scene}".encode("utf-8")).hexdigest()
    scene_seed = seed + int(scene_digest[:12], 16) % 1_000_000
    rng = np.random.default_rng(scene_seed)
    pred_points, pred_normals, _ = read_ply(pred_path)
    ref_points, ref_normals, ref_faces = read_ply(ref.path)
    if ref_faces is not None and ref.kind.endswith("_mesh"):
        ref_points = sample_mesh_points(ref_points, ref_faces, mesh_sample_points, rng)

    pred_points = pred_points[stable_sample_indices(len(pred_points), max_pred_points, rng)]
    ref_points = ref_points[stable_sample_indices(len(ref_points), max_ref_points, rng)]

    row.update(
        pred_points=int(len(pred_points)),
        reference_points=int(len(ref_points)),
        pred_normals=pred_normals is not None,
        reference_normals=ref_normals is not None,
    )

    if len(pred_points) == 0 or len(ref_points) == 0:
        row.update(status="empty_geometry", error="prediction or reference contains no points")
        return row

    row.update(compute_metrics(pred_points, ref_points, thresholds_pct))
    return row


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    keys: List[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def mean(values: Iterable[object]) -> Optional[float]:
    nums = [float(v) for v in values if v is not None and v != ""]
    if not nums:
        return None
    return float(sum(nums) / len(nums))


def write_markdown(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    ok_rows = [row for row in rows if row.get("status") == "ok"]
    accepted = [row for row in ok_rows if row.get("accepted_gt") is True]
    proxy = [row for row in ok_rows if row.get("accepted_gt") is not True]

    lines = [
        "# Ref-GS Reproduction Geometry Metrics",
        "",
        "Generated: 2026-07-08",
        "",
        "These metrics compare saved Ref-GS Gaussian point-cloud centers against",
        "available dataset geometry in raw coordinates. No ICP, scale fitting, or",
        "similarity alignment is applied.",
        "",
        "Reference protocol:",
        "",
        "- Ref-NeRF/Shiny Blender Synthetic: sampled scene GT mesh, accepted GT.",
        "- GlossySynthetic: `eval_pts.ply`, accepted evaluation points.",
        "- NeRF Synthetic: `points3d.ply`, proxy only and not accepted GT.",
        "",
        "Normal-angle metrics are `NA` because the Ref-GS saved Gaussian point clouds",
        "do not contain prediction normals.",
        "",
        "## Coverage",
        "",
        f"- Total scenes: {len(rows)}",
        f"- Successful geometry rows: {len(ok_rows)}",
        f"- Accepted-GT rows: {len(accepted)}",
        f"- Proxy-only rows: {len(proxy)}",
        f"- Failed rows: {len(rows) - len(ok_rows)}",
        "",
        "## Dataset Averages",
        "",
        "| Dataset | Rows | Protocol | Chamfer-L1 | Chamfer-L2 | Hausdorff | F@0.5% | F@1% | F@2% |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]

    for dataset in DEFAULT_SCENES:
        ds_rows = [row for row in ok_rows if row["dataset"] == dataset]
        protocol = "accepted GT" if all(row.get("accepted_gt") for row in ds_rows) else "proxy/mixed"
        vals = {
            "chamfer_l1": mean(row.get("chamfer_l1") for row in ds_rows),
            "chamfer_l2": mean(row.get("chamfer_l2") for row in ds_rows),
            "hausdorff": mean(row.get("hausdorff") for row in ds_rows),
            "fscore_0p5pct": mean(row.get("fscore_0p5pct") for row in ds_rows),
            "fscore_1pct": mean(row.get("fscore_1pct") for row in ds_rows),
            "fscore_2pct": mean(row.get("fscore_2pct") for row in ds_rows),
        }
        lines.append(
            "| {dataset} | {count} | {protocol} | {cl1:.6f} | {cl2:.6f} | {haus:.6f} | {f05:.4f} | {f1:.4f} | {f2:.4f} |".format(
                dataset=dataset,
                count=len(ds_rows),
                protocol=protocol,
                cl1=vals["chamfer_l1"] or math.nan,
                cl2=vals["chamfer_l2"] or math.nan,
                haus=vals["hausdorff"] or math.nan,
                f05=vals["fscore_0p5pct"] or math.nan,
                f1=vals["fscore_1pct"] or math.nan,
                f2=vals["fscore_2pct"] or math.nan,
            )
        )

    lines.extend(
        [
            "",
            "## Per-Scene Metrics",
            "",
            "| Dataset | Scene | Protocol | Chamfer-L1 | Chamfer-L2 | Hausdorff | F@0.5% | F@1% | F@2% |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        if row.get("status") != "ok":
            lines.append(
                f"| {row['dataset']} | {row['scene']} | failed: {row.get('error', '')} | NA | NA | NA | NA | NA | NA |"
            )
            continue
        protocol = "accepted_gt" if row.get("accepted_gt") else "proxy_only"
        lines.append(
            "| {dataset} | {scene} | {protocol} | {cl1:.6f} | {cl2:.6f} | {haus:.6f} | {f05:.4f} | {f1:.4f} | {f2:.4f} |".format(
                dataset=row["dataset"],
                scene=row["scene"],
                protocol=protocol,
                cl1=float(row["chamfer_l1"]),
                cl2=float(row["chamfer_l2"]),
                haus=float(row["hausdorff"]),
                f05=float(row["fscore_0p5pct"]),
                f1=float(row["fscore_1pct"]),
                f2=float(row["fscore_2pct"]),
            )
        )

    lines.extend(
        [
            "",
            "Machine-readable files:",
            "",
            "- `logs/repro/geometry_metrics.csv`",
            "- `logs/repro/geometry_metrics.json`",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("/data/liuly/dataset/3DGS"))
    parser.add_argument("--output-root", type=Path, default=Path("output/repro_paper"))
    parser.add_argument("--log-root", type=Path, default=Path("logs/repro"))
    parser.add_argument("--dataset", choices=sorted(DEFAULT_SCENES), action="append")
    parser.add_argument("--scene", action="append", help="Scene name; may be repeated.")
    parser.add_argument("--max-pred-points", type=int, default=200_000)
    parser.add_argument("--max-ref-points", type=int, default=200_000)
    parser.add_argument("--mesh-sample-points", type=int, default=200_000)
    parser.add_argument("--threshold-pct", type=float, nargs="*", default=[0.005, 0.01, 0.02])
    parser.add_argument("--seed", type=int, default=20260708)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    datasets = args.dataset or list(DEFAULT_SCENES)
    rows: List[Dict[str, object]] = []
    for dataset in datasets:
        scenes = args.scene or DEFAULT_SCENES[dataset]
        for scene in scenes:
            if scene not in DEFAULT_SCENES[dataset]:
                continue
            rows.append(
                evaluate_scene(
                    dataset=dataset,
                    scene=scene,
                    data_root=args.data_root,
                    output_root=args.output_root,
                    max_pred_points=args.max_pred_points,
                    max_ref_points=args.max_ref_points,
                    mesh_sample_points=args.mesh_sample_points,
                    thresholds_pct=args.threshold_pct,
                    seed=args.seed,
                )
            )

    args.log_root.mkdir(parents=True, exist_ok=True)
    csv_path = args.log_root / "geometry_metrics.csv"
    json_path = args.log_root / "geometry_metrics.json"
    md_path = args.log_root / "geometry_summary.md"
    write_csv(csv_path, rows)
    json_path.write_text(json.dumps(rows, indent=2) + "\n")
    write_markdown(md_path, rows)

    failures = [row for row in rows if row.get("status") != "ok"]
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Rows: {len(rows)}, failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
