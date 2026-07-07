import csv
import json
from argparse import ArgumentParser
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional

import torch

from arguments import ModelParams, PipelineParams, get_combined_args
from utils.image_utils import psnr
from utils.loss_utils import ssim


def composite_rgba(image: torch.Tensor, background: torch.Tensor) -> torch.Tensor:
    if image.shape[0] < 4:
        return image[:3]
    rgb = image[:3]
    alpha = image[3:4]
    return rgb * alpha + (1.0 - alpha) * background[:, None, None]


def compute_image_metrics(pred: torch.Tensor, gt: torch.Tensor, lpips_fn=None) -> Dict[str, Optional[float]]:
    pred = torch.clamp(pred[:3], 0.0, 1.0)
    gt = torch.clamp(gt[:3], 0.0, 1.0)
    pred_batch = pred.unsqueeze(0)
    gt_batch = gt.unsqueeze(0)
    result = {
        "psnr": float(psnr(pred_batch, gt_batch).mean().item()),
        "ssim": float(ssim(pred_batch, gt_batch).mean().item()),
        "lpips": None,
    }
    if lpips_fn is not None:
        result["lpips"] = float(lpips_fn(pred_batch, gt_batch))
    return result


def _make_lpips_fn(device: torch.device):
    try:
        from lpipsPyTorch.modules.lpips import LPIPS

        model = LPIPS(net_type="alex").to(device)
        model.eval()

        def evaluate(pred: torch.Tensor, gt: torch.Tensor) -> float:
            with torch.no_grad():
                return model(pred.to(device) * 2.0 - 1.0, gt.to(device) * 2.0 - 1.0).mean().item()

        return evaluate, None
    except Exception as exc:  # LPIPS may need unavailable local weights/network.
        return None, str(exc)


def _select_image(render_pkg: dict, image_key: str) -> torch.Tensor:
    if image_key in render_pkg:
        return render_pkg[image_key]
    for fallback in ("pbr_rgb", "render"):
        if fallback in render_pkg:
            return render_pkg[fallback]
    raise KeyError(f"Renderer did not return {image_key!r}, 'pbr_rgb', or 'render'. Keys: {sorted(render_pkg)}")


def _render_function(renderer: str):
    from gaussian_renderer import render, render_nerf, render_real

    if renderer == "nerf":
        return render_nerf
    if renderer == "real":
        return render_real
    return render


def _load_scene(args, model_params, iteration: int):
    from scene import GaussianModel, Scene

    dataset = model_params.extract(args)
    gaussians = GaussianModel(dataset.sh_degree, dataset)
    scene = Scene(dataset, gaussians, load_iteration=iteration, shuffle=False, resolution_scales=[1.0])
    return dataset, scene


def _render_kwargs(renderer: str, args):
    if renderer != "real":
        return {"iteration": -1}
    env_center = torch.tensor([float(c) for c in args.env_scope_center], device="cuda")
    xyz_axis = [int(float(c)) for c in args.xyz_axis]
    return {
        "iteration": -1,
        "ITER": args.init_until_iter,
        "ENV_CENTER": env_center,
        "ENV_RADIUS": args.env_scope_radius,
        "XYZ": xyz_axis,
    }


def _save_image(tensor: torch.Tensor, path: Path) -> None:
    import torchvision

    path.parent.mkdir(parents=True, exist_ok=True)
    torchvision.utils.save_image(torch.clamp(tensor.detach().cpu(), 0.0, 1.0), str(path))


def _write_metrics(output_dir: Path, rows: List[Dict], aggregate: Dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump({"aggregate": aggregate, "images": rows}, handle, indent=2)
    with (output_dir / "metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["split", "image_name", "psnr", "ssim", "lpips"])
        writer.writeheader()
        writer.writerows(rows)


def _evaluate_split(split: str, cameras, scene, render_func, pipe, background, args, lpips_fn):
    split_dir = Path(args.model_path) / split / f"ours_{scene.loaded_iter}"
    render_dir = split_dir / "renders"
    gt_dir = split_dir / "gt"
    rows = []
    render_kwargs = _render_kwargs(args.renderer, args)
    for camera in cameras:
        render_pkg = render_func(camera, scene.gaussians, pipe, background, **render_kwargs)
        pred = _select_image(render_pkg, args.image_key)
        gt = composite_rgba(camera.original_image.to(pred.device), background)
        _save_image(pred, render_dir / f"{camera.image_name}.png")
        _save_image(gt, gt_dir / f"{camera.image_name}.png")
        if args.metrics:
            metrics = compute_image_metrics(pred, gt, lpips_fn=lpips_fn)
            rows.append({"split": split, "image_name": camera.image_name, **metrics})
    if args.metrics and rows:
        aggregate = {
            "split": split,
            "count": len(rows),
            "psnr": mean(row["psnr"] for row in rows),
            "ssim": mean(row["ssim"] for row in rows),
            "lpips": mean(row["lpips"] for row in rows if row["lpips"] is not None)
            if any(row["lpips"] is not None for row in rows)
            else None,
        }
        _write_metrics(split_dir, rows, aggregate)
    return rows


def main(default_renderer: str = "refgs") -> None:
    torch.set_num_threads(4)
    torch.set_num_interop_threads(2)
    parser = ArgumentParser(description="Render and evaluate Ref-GS checkpoints.")
    model = ModelParams(parser, sentinel=True)
    pipeline = PipelineParams(parser)
    parser.add_argument("--iteration", default=-1, type=int)
    parser.add_argument("--renderer", default=default_renderer, choices=("refgs", "nerf", "real"))
    parser.add_argument("--dataset", default=None, help="Optional dataset label for logs; kept for runner compatibility.")
    parser.add_argument("--image-key", default="pbr_rgb", help="Renderer output key to evaluate/save.")
    parser.add_argument("--skip_train", action="store_true")
    parser.add_argument("--skip_test", action="store_true")
    parser.add_argument("--metrics", action="store_true", help="Compute PSNR/SSIM/LPIPS and write results.json/metrics.csv.")
    parser.add_argument("--no-lpips", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = get_combined_args(parser)
    args.renderer = default_renderer if default_renderer == "real" else args.renderer

    from utils.general_utils import safe_state

    safe_state(args.quiet)
    print("Rendering " + args.model_path)

    dataset, scene = _load_scene(args, model, args.iteration)
    pipe = pipeline.extract(args)
    bg_color = [1, 1, 1] if dataset.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")
    render_func = _render_function(args.renderer)
    lpips_fn, lpips_error = (None, None) if args.no_lpips or not args.metrics else _make_lpips_fn(background.device)

    all_rows = []
    if not args.skip_train:
        all_rows.extend(_evaluate_split("train", scene.getTrainCameras(), scene, render_func, pipe, background, args, lpips_fn))
    if not args.skip_test and scene.getTestCameras():
        all_rows.extend(_evaluate_split("test", scene.getTestCameras(), scene, render_func, pipe, background, args, lpips_fn))

    if args.metrics and all_rows:
        aggregate = {
            "iteration": scene.loaded_iter,
            "renderer": args.renderer,
            "count": len(all_rows),
            "psnr": mean(row["psnr"] for row in all_rows),
            "ssim": mean(row["ssim"] for row in all_rows),
            "lpips": mean(row["lpips"] for row in all_rows if row["lpips"] is not None)
            if any(row["lpips"] is not None for row in all_rows)
            else None,
            "lpips_error": lpips_error,
        }
        _write_metrics(Path(args.model_path), all_rows, aggregate)


if __name__ == "__main__":
    main()
