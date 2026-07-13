#!/usr/bin/env python3
import argparse
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import PIL
from PIL import Image
import torch

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.refgs_llff_common import file_sha256, write_json


DEFAULT_FSGS_METRICS = Path("/home/liuly/Surface_Reconstruction/Sparse/FSGS/metrics.py")


class EvaluationError(RuntimeError):
    pass


def _png_names(directory):
    directory = Path(directory)
    return {path.name for path in directory.glob("*.png")} if directory.is_dir() else set()


def validate_image_pairs(renders_dir, gt_dir, expected_names):
    render_names = _png_names(renders_dir)
    gt_names = _png_names(gt_dir)
    expected = set(expected_names)
    if not expected or render_names != expected or gt_names != expected:
        raise EvaluationError(
            "render/GT/expected filename mismatch: renders={} gt={} expected={}".format(
                sorted(render_names), sorted(gt_names), sorted(expected)
            )
        )
    for name in sorted(expected):
        with Image.open(str(Path(renders_dir) / name)) as render_image, Image.open(str(Path(gt_dir) / name)) as gt_image:
            if render_image.size != gt_image.size:
                raise EvaluationError("image size mismatch for {}".format(name))
    return sorted(expected)


def evaluator_metadata(fsgs_metrics_path=DEFAULT_FSGS_METRICS):
    path = Path(__file__)
    fsgs = Path(fsgs_metrics_path)
    if not fsgs.is_file():
        raise EvaluationError("FSGS evaluator source is missing: {}".format(fsgs))
    return {
        "protocol": "shared FSGS LLFF evaluator",
        "lpips_backbone": "vgg",
        "image_range": "[0,1]",
        "color_space": "PIL decoded RGB, no linearization",
        "alpha_handling": "first three channels; LLFF inputs are opaque RGB",
        "clipping": "none before metrics; decoded PNG values are in [0,1]",
        "evaluator_path": str(path.resolve()),
        "evaluator_sha256": file_sha256(path),
        "fsgs_metrics_path": str(fsgs.resolve()),
        "fsgs_metrics_sha256": file_sha256(fsgs),
        "runtime": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "numpy": np.__version__,
            "pillow": PIL.__version__,
        },
    }


def _expected_from_manifest(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {record["image_name"] + ".png" for record in payload["test"]}


def evaluate(model_path, iteration=10000, manifest=None, output_dir=None):
    import torch
    import torchvision.transforms.functional as tf
    from lpipsPyTorch import lpips
    from utils.image_utils import psnr
    from utils.loss_utils import ssim

    model_path = Path(model_path)
    base = model_path / "test" / "ours_{}".format(iteration)
    expected = _expected_from_manifest(manifest) if manifest else _png_names(base / "gt")
    names = validate_image_pairs(base / "renders", base / "gt", expected)
    per_view = {"SSIM": {}, "PSNR": {}, "LPIPS": {}}
    for name in names:
        with Image.open(str(base / "renders" / name)) as source:
            render = tf.to_tensor(source.convert("RGB")).unsqueeze(0).cuda()
        with Image.open(str(base / "gt" / name)) as source:
            gt = tf.to_tensor(source.convert("RGB")).unsqueeze(0).cuda()
        if render.shape != gt.shape or not torch.isfinite(render).all() or not torch.isfinite(gt).all():
            raise EvaluationError("non-finite or mismatched tensors for {}".format(name))
        values = {
            "SSIM": float(ssim(render, gt).item()),
            "PSNR": float(psnr(render, gt).item()),
            "LPIPS": float(lpips(render, gt, net_type="vgg").item()),
        }
        if not all(math.isfinite(value) for value in values.values()):
            raise EvaluationError("non-finite metric for {}".format(name))
        for metric, value in values.items():
            per_view[metric][name] = value
    aggregate = {metric: sum(values.values()) / len(values) for metric, values in per_view.items()}
    method = "ours_{}".format(iteration)
    destination = Path(output_dir or model_path)
    destination.mkdir(parents=True, exist_ok=True)
    write_json(destination / "results.json", {method: aggregate})
    write_json(destination / "per_view.json", {method: per_view})
    write_json(destination / "evaluator_metadata.json", evaluator_metadata())
    return aggregate


def build_parser():
    parser = argparse.ArgumentParser(description="Shared FSGS-protocol evaluator for Ref-GS LLFF renders")
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--iteration", type=int, default=10000)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        result = evaluate(args.model_path, args.iteration, args.manifest, args.output_dir)
    except EvaluationError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
