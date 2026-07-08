#!/usr/bin/env python3
"""Diagnostic comparison for GT normal coordinate-space hypotheses."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.eval_geometry import DEFAULT_SCENES, evaluate_scene
from scripts.evaluate_normal_mae_protocol_grid import FLIP_PRESETS


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: List[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("refnerf",), required=True)
    parser.add_argument("--scene", nargs="+")
    parser.add_argument("--iteration", nargs="+", type=int, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("output/normal_mae_protocol_debug"))
    parser.add_argument("--data-root", type=Path, default=Path("/data/liuly/dataset/3DGS"))
    parser.add_argument("--log-root", type=Path, default=Path("logs/repro/normal_mae_protocol_debug"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    existing_grid = args.log_root / "normal_mae_protocol_grid.csv"
    if existing_grid.exists():
        with existing_grid.open(newline="", encoding="utf-8") as handle:
            grid_rows = list(csv.DictReader(handle))
        rows = [
            dict(row, inference_note="Reused protocol grid rows; diagnostic only, not automatic final protocol.")
            for row in grid_rows
            if row.get("scene") != "__average__"
            and row.get("mask_policy") == "auto"
            and row.get("absolute_dot") in ("False", "false", False, "")
        ]
        args.log_root.mkdir(parents=True, exist_ok=True)
        csv_path = args.log_root / "gt_normal_space_inference.csv"
        write_csv(csv_path, rows)
        (args.log_root / "gt_normal_space_inference.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {csv_path}")
        return 0
    scenes = args.scene or DEFAULT_SCENES[args.dataset]
    rows: List[Dict[str, object]] = []
    for scene in scenes:
        for iteration in args.iteration:
            for normal_key in ("surf_normal", "rend_normal"):
                for normal_space in ("as_saved", "camera", "world"):
                    for flip_name, flips in FLIP_PRESETS.items():
                        row = evaluate_scene(
                            dataset=args.dataset,
                            scene=scene,
                            data_root=args.data_root,
                            output_root=args.output_root,
                            iteration=iteration,
                            split="test",
                            metrics=("normal_mae",),
                            normal_space=normal_space,
                            mask_policy="auto",
                            normal_source_key=normal_key,
                            flip_x=flips[0],
                            flip_y=flips[1],
                            flip_z=flips[2],
                            absolute_dot=False,
                            protocol_name="gt_normal_space_inference",
                        )
                        row["flip_preset"] = flip_name
                        row["inference_note"] = (
                            "Diagnostic only; lower MAE is evidence for a convention but is not an automatic final protocol."
                        )
                        rows.append(row)
    args.log_root.mkdir(parents=True, exist_ok=True)
    csv_path = args.log_root / "gt_normal_space_inference.csv"
    write_csv(csv_path, rows)
    (args.log_root / "gt_normal_space_inference.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
