#!/usr/bin/env python3
"""Export normal geometry buffers by normal key into an isolated debug root."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.refgs_runner import DATASET_CONFIGS, DEFAULT_DATA_ROOT


def display_command(command: Sequence[str], env: Dict[str, str]) -> str:
    prefix = " ".join(f"{k}={shlex.quote(v)}" for k, v in sorted(env.items()))
    body = " ".join(shlex.quote(str(part)) for part in command)
    return f"{prefix} {body}".strip()


def geometry_exists(output_root: Path, dataset: str, scene: str, iteration: int, normal_key: str, expected_frame_count: int) -> bool:
    normal_dir = output_root / dataset / scene / f"iteration_{iteration}" / normal_key / "test" / f"ours_{iteration}" / "geometry" / "normal"
    return normal_dir.exists() and sum(1 for _ in normal_dir.glob("*.npy")) >= expected_frame_count


def build_command(
    python: str,
    dataset: str,
    scene: str,
    iteration: int,
    normal_key: str,
    output_root: Path,
    source_output_root: Path,
    data_root: Path,
    normal_dtype: str,
    save_depth: bool,
    save_vis: bool,
) -> List[str]:
    config = DATASET_CONFIGS[dataset]
    scene_config = config.scene_map()[scene]
    source = data_root / config.data_subdir / scene_config.source_dir
    model = source_output_root / config.output_subdir / scene_config.name
    geometry_root = output_root / config.output_subdir / scene_config.name / f"iteration_{iteration}" / normal_key
    command = [
        python,
        "render.py",
        "-s",
        str(source),
        "-m",
        str(model),
        "--iteration",
        str(iteration),
        "--save-geometry",
        "--geometry-only",
        "--split",
        "test",
        "--normal-key",
        normal_key,
        "--depth-key",
        "surf_depth",
        "--geometry-output-root",
        str(geometry_root),
        "--geometry-normal-dtype",
        normal_dtype,
        *config.render_args,
    ]
    if not save_depth:
        command.append("--skip-depth-geometry")
    if not save_vis:
        command.append("--skip-geometry-vis")
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("refnerf",), required=True)
    parser.add_argument("--scene", nargs="+", required=True)
    parser.add_argument("--iteration", nargs="+", type=int, required=True)
    parser.add_argument("--normal-key", nargs="+", choices=("surf_normal", "rend_normal"), required=True)
    parser.add_argument("--gpu", default="5")
    parser.add_argument("--output-root", type=Path, default=Path("output/normal_mae_protocol_debug"))
    parser.add_argument("--source-output-root", type=Path, default=Path("output/repro_paper"))
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--expected-frame-count", type=int, default=200)
    parser.add_argument("--normal-dtype", choices=("float32", "float16"), default="float16")
    parser.add_argument("--save-depth", action="store_true")
    parser.add_argument("--save-vis", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = DATASET_CONFIGS[args.dataset]
    scene_map = config.scene_map()
    env = {"CUDA_VISIBLE_DEVICES": str(args.gpu)} if args.gpu else {}
    failures = []
    for scene in args.scene:
        if scene not in scene_map:
            raise ValueError(f"Unknown scene for {args.dataset}: {scene}")
        for iteration in args.iteration:
            checkpoint = args.source_output_root / config.output_subdir / scene / "point_cloud" / f"iteration_{iteration}" / "point_cloud.ply"
            if not checkpoint.exists():
                print(f"[skip] {args.dataset}/{scene} iteration {iteration}: missing checkpoint {checkpoint}")
                continue
            for normal_key in args.normal_key:
                if args.skip_existing and not args.force and geometry_exists(
                    args.output_root,
                    config.output_subdir,
                    scene,
                    iteration,
                    normal_key,
                    args.expected_frame_count,
                ):
                    print(f"[skip] {args.dataset}/{scene} iteration {iteration} {normal_key}: existing buffers")
                    continue
                command = build_command(
                    args.python,
                    args.dataset,
                    scene,
                    iteration,
                    normal_key,
                    args.output_root,
                    args.source_output_root,
                    args.data_root,
                    args.normal_dtype,
                    args.save_depth,
                    args.save_vis,
                )
                if args.dry_run:
                    print(display_command(command, env))
                    continue
                run_env = os.environ.copy()
                run_env.update(env)
                print(f"[run] {args.dataset}/{scene} iteration {iteration} {normal_key}")
                code = subprocess.run(command, cwd=REPO_ROOT, env=run_env).returncode
                if code != 0:
                    failures.append((scene, iteration, normal_key, code))
                    print(f"[fail] {scene} iteration {iteration} {normal_key}: render exited {code}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
