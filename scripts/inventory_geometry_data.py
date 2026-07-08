#!/usr/bin/env python3
"""Inventory geometry-related data for Ref-GS reproduction scenes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Sequence


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

RAW_GLOSSY_SUBDIR = "GlossySynthetic"


def _first_paths(root: Path, patterns: Sequence[str], limit: int = 5) -> List[str]:
    paths: List[Path] = []
    if root.exists():
        for pattern in patterns:
            paths.extend(root.rglob(pattern))
    return [str(path) for path in sorted(set(paths))[:limit]]


def _has_rgba_images(root: Path) -> bool:
    if not root.exists():
        return False
    for image in list(root.rglob("*.png"))[:200]:
        try:
            from PIL import Image

            if Image.open(image).mode == "RGBA":
                return True
        except Exception:
            continue
    return False


def _raw_glossy_scene(scene: str) -> str:
    return scene[:-8] if scene.endswith("_blender") else scene


def inventory_scene(dataset: str, scene: str, scene_root: Path, data_root: Path = None) -> Dict[str, object]:
    data_root = data_root or scene_root.parent.parent
    normal_patterns = ["*normal*.png", "*normal*.jpg", "*normal*.jpeg", "*normal*.exr", "*normal*.npy", "*normal*.npz"]
    depth_patterns = ["*depth*.png", "*depth*.jpg", "*depth*.jpeg", "*depth*.exr", "*depth*.npy", "*depth*.npz"]
    mask_patterns = ["*mask*.png", "*mask*.jpg", "*alpha*.png", "*alpha*.jpg"]
    mesh_patterns = ["*.obj", "*.ply", "*.stl"]

    normal_paths = _first_paths(scene_root, normal_patterns)
    depth_paths = _first_paths(scene_root, depth_patterns)
    mask_paths = _first_paths(scene_root, mask_patterns)
    mesh_paths = _first_paths(scene_root, mesh_patterns)

    if dataset == "glossy_synthetic" and not depth_paths:
        raw_scene = data_root / RAW_GLOSSY_SUBDIR / _raw_glossy_scene(scene)
        depth_paths = _first_paths(raw_scene, depth_patterns)
        if not mesh_paths:
            mesh_paths = _first_paths(raw_scene, ["eval_pts.ply"])

    if dataset == "refnerf":
        gt_mesh = scene_root / f"{scene}_gt_mesh.ply"
        shared_gt = scene_root.parent / "gt" / f"{scene}_gt_mesh.ply"
        for candidate in (gt_mesh, shared_gt):
            if candidate.exists() and str(candidate) not in mesh_paths:
                mesh_paths.insert(0, str(candidate))

    if dataset == "glossy_synthetic":
        eval_pts = scene_root / "eval_pts.ply"
        if eval_pts.exists() and str(eval_pts) not in mesh_paths:
            mesh_paths.insert(0, str(eval_pts))

    gt_normal_available = bool(normal_paths)
    gt_depth_available = bool(depth_paths)
    gt_mesh_available = bool(mesh_paths)
    mask_source = "none"
    if mask_paths:
        mask_source = "alpha_or_mask_file"
    elif _has_rgba_images(scene_root):
        mask_source = "rgba_alpha"
    elif gt_normal_available:
        mask_source = "normal_norm_validity"

    can_measure = dataset == "refnerf" and gt_normal_available
    notes = []
    if dataset == "nerf_synthetic" and gt_mesh_available:
        notes.append("points3d.ply is generated/proxy geometry and is not accepted GT")
    if dataset == "glossy_synthetic" and gt_depth_available:
        notes.append("raw GlossySynthetic depth exists, but converted frame-name alignment must be checked before paper-style depth comparison")
    if not gt_normal_available:
        notes.append("missing_gt_normal")

    return {
        "dataset": dataset,
        "scene": scene,
        "scene_root": str(scene_root),
        "gt_normal_available": gt_normal_available,
        "gt_depth_available": gt_depth_available,
        "gt_mesh_available": gt_mesh_available,
        "normal_patterns": "*normal*" if gt_normal_available else "",
        "depth_patterns": "*depth*" if gt_depth_available else "",
        "normal_examples": normal_paths,
        "depth_examples": depth_paths,
        "mesh_examples": mesh_paths[:5],
        "mask_source": mask_source,
        "transforms_train": str(scene_root / "transforms_train.json") if (scene_root / "transforms_train.json").exists() else "",
        "transforms_test": str(scene_root / "transforms_test.json") if (scene_root / "transforms_test.json").exists() else "",
        "can_measure_paper_normal_mae": can_measure,
        "notes": "; ".join(notes),
    }


def inventory_all(data_root: Path) -> List[Dict[str, object]]:
    rows = []
    for dataset, scenes in DEFAULT_SCENES.items():
        scene_parent = data_root / DATASET_SUBDIRS[dataset]
        for scene in scenes:
            rows.append(inventory_scene(dataset, scene, scene_parent / scene, data_root=data_root))
    return rows


def write_markdown(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Geometry Data Inventory",
        "",
        "This is a read-only inventory of GT normal/depth/mesh availability for the Ref-GS reproduction scenes.",
        "",
        "| Dataset | Scene | GT normal | GT depth | GT mesh/points | Mask source | Paper normal MAE possible | Notes |",
        "|---|---|---:|---:|---:|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {dataset} | {scene} | {normal} | {depth} | {mesh} | {mask} | {mae} | {notes} |".format(
                dataset=row["dataset"],
                scene=row["scene"],
                normal=row["gt_normal_available"],
                depth=row["gt_depth_available"],
                mesh=row["gt_mesh_available"],
                mask=row["mask_source"],
                mae=row["can_measure_paper_normal_mae"],
                notes=row["notes"],
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("/data/liuly/dataset/3DGS"))
    parser.add_argument("--output", type=Path, default=Path("logs/repro/geometry_data_inventory.json"))
    parser.add_argument("--markdown", type=Path, default=Path("logs/repro/geometry_data_inventory.md"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = inventory_all(args.data_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    write_markdown(args.markdown, rows)
    print(f"Wrote {args.output}")
    print(f"Wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
