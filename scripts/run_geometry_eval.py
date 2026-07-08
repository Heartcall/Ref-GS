#!/usr/bin/env python3
"""Run Ref-GS geometry-buffer export and geometry evaluation."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.refgs_runner import DATASET_CONFIGS, DEFAULT_DATA_ROOT, selected_scenes
from scripts.eval_geometry import summarize_rows, write_csv


def display_command(command: Sequence[str], env: Dict[str, str], log_path: Path) -> str:
    prefix = " ".join(f"{k}={shlex.quote(v)}" for k, v in sorted(env.items()))
    body = " ".join(shlex.quote(str(part)) for part in command)
    if prefix:
        body = f"{prefix} {body}"
    return f"{body} > {shlex.quote(str(log_path))} 2>&1"


def run_logged(command: Sequence[str], env: Dict[str, str], log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    run_env = os.environ.copy()
    run_env.update(env)
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write(display_command(command, env, log_path) + "\n\n")
        handle.flush()
        proc = subprocess.run(list(command), cwd=Path.cwd(), env=run_env, stdout=handle, stderr=subprocess.STDOUT)
    return proc.returncode


def checkpoint_exists(output_root: Path, dataset: str, scene: str, iteration: int) -> bool:
    return (output_root / dataset / scene / "point_cloud" / f"iteration_{iteration}" / "point_cloud.ply").exists()


def geometry_exists(output_root: Path, dataset: str, scene: str, iteration: int, split: str) -> bool:
    geom = output_root / dataset / scene / split / f"ours_{iteration}" / "geometry" / "normal"
    return geom.exists() and any(geom.glob("*.npy"))


def build_render_command(
    python: str,
    dataset_key: str,
    scene_name: str,
    data_root: Path,
    output_root: Path,
    iteration: int,
    split: str,
) -> List[str]:
    config = DATASET_CONFIGS[dataset_key]
    scene = config.scene_map()[scene_name]
    source = data_root / config.data_subdir / scene.source_dir
    model = output_root / config.output_subdir / scene.name
    command = [
        python,
        config.render_script,
        "-s",
        str(source),
        "-m",
        str(model),
        "--iteration",
        str(iteration),
        "--save-geometry",
        "--geometry-only",
        "--split",
        split,
        *config.render_args,
    ]
    return command


def build_eval_command(
    python: str,
    dataset_key: str,
    scene_name: str,
    data_root: Path,
    output_root: Path,
    log_root: Path,
    iteration: int,
    split: str,
) -> List[str]:
    return [
        python,
        "scripts/eval_geometry.py",
        "--dataset",
        dataset_key,
        "--scene",
        scene_name,
        "--data-root",
        str(data_root),
        "--output-root",
        str(output_root),
        "--log-root",
        str(log_root),
        "--iteration",
        str(iteration),
        "--split",
        split,
        "--metrics",
        "all",
    ]


def selected_dataset_keys(dataset: str) -> List[str]:
    if dataset == "all":
        return ["refnerf", "glossy_synthetic", "nerf_synthetic"]
    return [dataset]


def collect_geometry_rows(output_root: Path) -> List[Dict[str, object]]:
    rows = []
    for dataset in ("refnerf", "glossy_synthetic", "nerf_synthetic"):
        for path in sorted((output_root / dataset).glob("*/geometry_metrics.json")):
            with path.open(encoding="utf-8") as handle:
                rows.append(json_load(handle)["aggregate"])
    return rows


def json_load(handle):
    import json

    return json.load(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("refnerf", "glossy_synthetic", "nerf_synthetic", "all"), default="all")
    parser.add_argument("--scene", action="append")
    parser.add_argument("--gpu")
    parser.add_argument("--iteration", type=int, default=31000)
    parser.add_argument("--output-root", type=Path, default=Path("output/repro_paper"))
    parser.add_argument("--log-root", type=Path, default=Path("logs/repro"))
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--save-geometry", action="store_true")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--split", choices=("train", "test"), default="test")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env = {"CUDA_VISIBLE_DEVICES": args.gpu} if args.gpu else {}
    failures = []
    for dataset_key in selected_dataset_keys(args.dataset):
        config = DATASET_CONFIGS[dataset_key]
        scenes = [scene.name for scene in selected_scenes(config, args.scene)]
        for scene in scenes:
            out_dataset = config.output_subdir
            if not checkpoint_exists(args.output_root, out_dataset, scene, args.iteration):
                print(f"[skip] {dataset_key}/{scene}: missing checkpoint iteration {args.iteration}")
                continue
            scene_log_dir = args.log_root / out_dataset / scene
            if args.save_geometry:
                if args.skip_existing and not args.force and geometry_exists(args.output_root, out_dataset, scene, args.iteration, args.split):
                    print(f"[skip] {dataset_key}/{scene}: geometry buffers already exist")
                else:
                    render_command = build_render_command(
                        args.python,
                        dataset_key,
                        scene,
                        args.data_root,
                        args.output_root,
                        args.iteration,
                        args.split,
                    )
                    render_log = scene_log_dir / "geometry_render"
                    if args.dry_run:
                        print(display_command(render_command, env, render_log))
                    else:
                        code = run_logged(render_command, env, render_log)
                        if code != 0:
                            failures.append((dataset_key, scene, "render", code, render_log))
                            print(f"[fail] {dataset_key}/{scene}: render exited {code}; see {render_log}")
                            continue
            if args.eval:
                eval_command = build_eval_command(
                    args.python,
                    out_dataset,
                    scene,
                    args.data_root,
                    args.output_root,
                    args.log_root,
                    args.iteration,
                    args.split,
                )
                eval_log = scene_log_dir / "geometry_eval"
                if args.dry_run:
                    print(display_command(eval_command, {}, eval_log))
                else:
                    code = run_logged(eval_command, {}, eval_log)
                    if code != 0:
                        failures.append((dataset_key, scene, "eval", code, eval_log))
                        print(f"[fail] {dataset_key}/{scene}: eval exited {code}; see {eval_log}")
    if not args.dry_run and args.eval:
        rows = collect_geometry_rows(args.output_root)
        if rows:
            args.log_root.mkdir(parents=True, exist_ok=True)
            summarize_rows(rows, args.log_root)
            by_dataset: Dict[str, List[Dict[str, object]]] = {}
            for row in rows:
                by_dataset.setdefault(str(row["dataset"]), []).append(row)
            for dataset, dataset_rows in by_dataset.items():
                dataset_root = args.output_root / dataset
                write_csv(dataset_root / "geometry_summary.csv", dataset_rows)
                (dataset_root / "geometry_summary.json").write_text(json_loads(dataset_rows), encoding="utf-8")
    if failures:
        return 1
    return 0


def json_loads(rows: List[Dict[str, object]]) -> str:
    import json

    return json.dumps(rows, indent=2) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
