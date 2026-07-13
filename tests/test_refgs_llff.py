import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from scripts.refgs_llff_common import (
    LLFF_SCENES,
    RESOLUTIONS,
    finite_metrics,
    list_source_image_names,
    metric_means,
    select_llff_views,
    stage_state,
)
from scripts.prepare_refgs_llff import audit_source_scene, prepare_scene


DATA_ROOT = Path("/data1/liuly/FSGS_LLFF/dataset/nerf_llff_data")
AUTHOR_ROOT = Path("/data1/liuly/FSGS_LLFF/author_preprocessed")


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

    def test_protocol_scene_and_resolution_constants(self):
        self.assertEqual(tuple(self.EXPECTED), LLFF_SCENES)
        self.assertEqual(RESOLUTIONS, {"1_8": "images_8", "1_4": "images_4"})

    @unittest.skipUnless(DATA_ROOT.is_dir(), "LLFF data root unavailable")
    def test_all_splits_match_fsgs(self):
        for scene, (expected_train, expected_test_count) in self.EXPECTED.items():
            split = select_llff_views(list_source_image_names(DATA_ROOT / scene))
            self.assertEqual(split["train"], expected_train, scene)
            self.assertEqual(len(split["test"]), expected_test_count, scene)
            self.assertEqual(set(split["train"]) & set(split["test"]), set(), scene)
            self.assertEqual(len(split["train"]), 3, scene)


class StateTests(unittest.TestCase):
    def test_nan_metrics_are_invalid(self):
        self.assertIsNone(finite_metrics({"PSNR": 1.0, "SSIM": 0.5, "LPIPS": float("nan")}))

    def test_failed_rows_do_not_contribute_to_means(self):
        rows = [
            {"status": "completed", "psnr": 10.0, "ssim": 0.5, "lpips": 0.2},
            {"status": "failed", "psnr": None, "ssim": None, "lpips": None},
        ]
        self.assertEqual(metric_means(rows), {"psnr": 10.0, "ssim": 0.5, "lpips": 0.2})

    def test_incomplete_output_is_not_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory)
            checkpoint = model / "point_cloud" / "iteration_10000" / "point_cloud.ply"
            checkpoint.parent.mkdir(parents=True)
            checkpoint.write_bytes(b"ply")
            state = stage_state(model, 10000, {"test.png"})
            self.assertFalse(state["checkpoint_exists"])
            self.assertFalse(state["render_exists"])
            self.assertFalse(state["metrics_exists"])


class PreparationTests(unittest.TestCase):
    @unittest.skipUnless(DATA_ROOT.is_dir() and AUTHOR_ROOT.is_dir(), "LLFF source unavailable")
    def test_manifest_validator_rejects_corrupted_scaled_intrinsics(self):
        from scripts.refgs_llff_common import validate_manifest_payload
        with tempfile.TemporaryDirectory() as directory:
            prepared = Path(directory) / "horns"
            prepare_scene("horns", "1_8", DATA_ROOT, AUTHOR_ROOT, prepared)
            payload = json.loads((prepared / "refgs_llff_manifest.json").read_text())
            payload["train"][0]["intrinsics"]["fx"] = -1.0
            with self.assertRaises(ValueError):
                validate_manifest_payload(payload, "horns", "1_8")
    def test_manifest_validator_rejects_wrong_scene_and_overlap(self):
        from scripts.refgs_llff_common import validate_manifest_payload
        payload = {
            "schema_version": 1, "experiment": "Ref-GS under the FSGS LLFF 3-view protocol",
            "scene": "horns", "resolution": "1_8",
            "train": [{"image_name": name, "source_image_name": name + ".jpg", "pose_provenance": "author_3_views_images_txt"} for name in ("a", "b", "c")],
            "test": [{"image_name": "a", "source_image_name": "a.jpg", "pose_provenance": "original_llff_images_bin_test_only"}] * 8,
            "pointcloud": {"source_kind": "author_fused_ply", "sha256": "0" * 64},
            "full_scene_pointcloud_used": False,
        }
        with self.assertRaises(ValueError):
            validate_manifest_payload(payload, "horns", "1_8")
    @unittest.skipUnless(DATA_ROOT.is_dir() and AUTHOR_ROOT.is_dir(), "LLFF source unavailable")
    def test_all_scene_author_poses_and_pointclouds_are_audited(self):
        for scene in LLFF_SCENES:
            audit = audit_source_scene(scene, "1_8", DATA_ROOT, AUTHOR_ROOT)
            self.assertEqual(len(audit["train_images"]), 3, scene)
            self.assertEqual(len(audit["test_images"]), SplitTests.EXPECTED[scene][1], scene)
            self.assertFalse(audit["full_scene_pointcloud_used"], scene)
            self.assertEqual(audit["pointcloud"]["source_kind"], "author_fused_ply", scene)
            self.assertIn("/author_preprocessed/", audit["pointcloud"]["path"], scene)
            self.assertGreater(audit["pointcloud"]["vertex_count"], 0, scene)
            for pose in audit["training_pose_audit"]:
                self.assertLessEqual(pose["rotation_max_abs"], 1e-12, scene)
                self.assertLessEqual(pose["camera_center_l2"], 1e-12, scene)

    @unittest.skipUnless(DATA_ROOT.is_dir() and AUTHOR_ROOT.is_dir(), "LLFF source unavailable")
    def test_horns_source_audit_matches_fsgs(self):
        audit = audit_source_scene("horns", "1_8", DATA_ROOT, AUTHOR_ROOT)
        self.assertEqual(audit["train_images"], SplitTests.EXPECTED["horns"][0])
        self.assertEqual(len(audit["test_images"]), 8)
        self.assertEqual(audit["pointcloud"]["vertex_count"], 19397)
        self.assertEqual(
            audit["pointcloud"]["sha256"],
            "2adda809bc9aaa71b7d5db51336527e22b4ec2b25dfb1b3090ebb62310253cde",
        )
        self.assertEqual(audit["intrinsics"]["scaled"]["width"], 504)
        self.assertEqual(audit["intrinsics"]["scaled"]["height"], 378)
        for pose in audit["training_pose_audit"]:
            self.assertLessEqual(pose["rotation_max_abs"], 1e-12)
            self.assertLessEqual(pose["camera_center_l2"], 1e-12)

    @unittest.skipUnless(DATA_ROOT.is_dir() and AUTHOR_ROOT.is_dir(), "LLFF source unavailable")
    def test_prepared_manifest_contains_only_train_and_test(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Path(directory) / "prepared"
            audit = prepare_scene("horns", "1_8", DATA_ROOT, AUTHOR_ROOT, prepared)
            manifest = json.loads((prepared / "refgs_llff_manifest.json").read_text())
            expected = {
                Path(name).stem + ".png"
                for name in audit["train_images"] + audit["test_images"]
            }
            self.assertEqual({path.name for path in (prepared / "images").iterdir()}, expected)
            self.assertEqual(len(manifest["train"]), 3)
            self.assertEqual(len(manifest["test"]), 8)
            self.assertFalse((prepared / "sparse").exists())
            self.assertNotIn("points3D.bin", json.dumps(manifest))
            self.assertTrue((prepared / "input" / "fused.ply").is_symlink())

    def test_missing_author_ply_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "blocked_pointcloud"):
                audit_source_scene("horns", "1_8", DATA_ROOT, Path(directory))

    def test_llff_adapter_does_not_call_full_scene_point_reader(self):
        import inspect
        import scripts.prepare_refgs_llff as prepare
        from scene.dataset_readers import readRefGSLLFFManifestInfo
        source = inspect.getsource(prepare) + inspect.getsource(readRefGSLLFFManifestInfo)
        self.assertNotIn("read_points3D_binary", source)
        self.assertNotIn("read_points3D_text", source)


class LoaderTests(unittest.TestCase):
    @unittest.skipUnless(DATA_ROOT.is_dir() and AUTHOR_ROOT.is_dir(), "LLFF source unavailable")
    def test_training_can_defer_all_test_camera_construction(self):
        from scene.dataset_readers import readRefGSLLFFManifestInfo
        with tempfile.TemporaryDirectory() as directory:
            prepared = Path(directory) / "horns"
            prepare_scene("horns", "1_8", DATA_ROOT, AUTHOR_ROOT, prepared)
            info = readRefGSLLFFManifestInfo(str(prepared), load_test_cameras=False)
            self.assertEqual(len(info.train_cameras), 3)
            self.assertEqual(info.test_cameras, [])

    @unittest.skipUnless(DATA_ROOT.is_dir() and AUTHOR_ROOT.is_dir(), "LLFF source unavailable")
    def test_manifest_loader_exposes_only_listed_cameras(self):
        from scene.dataset_readers import readRefGSLLFFManifestInfo
        with tempfile.TemporaryDirectory() as directory:
            prepared = Path(directory) / "horns"
            audit = prepare_scene("horns", "1_8", DATA_ROOT, AUTHOR_ROOT, prepared)
            info = readRefGSLLFFManifestInfo(str(prepared))
            self.assertEqual([camera.image_name for camera in info.train_cameras],
                             [Path(name).stem for name in audit["train_images"]])
            self.assertEqual([camera.image_name for camera in info.test_cameras],
                             [Path(name).stem for name in audit["test_images"]])
            self.assertEqual(info.nerf_normalization["source"], "three_training_cameras_only")

    @unittest.skipUnless(DATA_ROOT.is_dir() and AUTHOR_ROOT.is_dir(), "LLFF source unavailable")
    def test_test_pose_changes_do_not_change_normalization(self):
        from scene.dataset_readers import readRefGSLLFFManifestInfo
        with tempfile.TemporaryDirectory() as directory:
            prepared = Path(directory) / "horns"
            prepare_scene("horns", "1_8", DATA_ROOT, AUTHOR_ROOT, prepared)
            before = readRefGSLLFFManifestInfo(str(prepared)).nerf_normalization
            manifest_path = prepared / "refgs_llff_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["test"][0]["tvec"] = [999.0, 999.0, 999.0]
            manifest_path.write_text(json.dumps(manifest))
            after = readRefGSLLFFManifestInfo(str(prepared)).nerf_normalization
            np.testing.assert_allclose(before["translate"], after["translate"])
            self.assertEqual(before["radius"], after["radius"])

    @unittest.skipUnless(DATA_ROOT.is_dir() and AUTHOR_ROOT.is_dir(), "LLFF source unavailable")
    def test_loader_recomputes_normalization_instead_of_trusting_manifest(self):
        from scene.dataset_readers import readRefGSLLFFManifestInfo
        with tempfile.TemporaryDirectory() as directory:
            prepared = Path(directory) / "horns"
            prepare_scene("horns", "1_8", DATA_ROOT, AUTHOR_ROOT, prepared)
            manifest_path = prepared / "refgs_llff_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            expected = dict(manifest["normalization"])
            manifest["normalization"]["translate"] = [999.0, 999.0, 999.0]
            manifest["normalization"]["radius"] = 999.0
            manifest_path.write_text(json.dumps(manifest))
            info = readRefGSLLFFManifestInfo(str(prepared))
            np.testing.assert_allclose(info.nerf_normalization["translate"], expected["translate"], atol=1e-6)
            self.assertAlmostEqual(info.nerf_normalization["radius"], expected["radius"], places=6)


class TrainingGlueTests(unittest.TestCase):
    def test_rgb_target_is_unchanged(self):
        import torch
        from train import training_target
        rgb = torch.rand(3, 4, 5)
        background = torch.rand(3)
        target, alpha = training_target(rgb, background)
        self.assertTrue(torch.equal(target, rgb))
        self.assertIsNone(alpha)

    def test_rgba_target_preserves_compositing(self):
        import torch
        from train import training_target
        rgba = torch.rand(4, 4, 5)
        background = torch.rand(3)
        target, alpha = training_target(rgba, background)
        expected = rgba[:3] * rgba[3:4] + (1 - rgba[3:4]) * background[:, None, None]
        self.assertTrue(torch.allclose(target, expected))
        self.assertTrue(torch.equal(alpha, rgba[3:4]))

    def test_train_sources_do_not_set_gpu_environment(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("train.py", "train-real.py"):
            text = (root / name).read_text(encoding="utf-8")
            self.assertNotIn("CUDA_VISIBLE_DEVICES", text)
            self.assertNotIn("CUDA_LAUNCH_BLOCKING", text)


class EvaluatorTests(unittest.TestCase):
    def test_missing_fsgs_evaluator_is_blocking(self):
        from scripts.evaluate_refgs_llff import EvaluationError, evaluator_metadata
        with self.assertRaises(EvaluationError):
            evaluator_metadata(Path("/definitely/missing/metrics.py"))

    def test_pair_validation_requires_exact_expected_names(self):
        from PIL import Image
        from scripts.evaluate_refgs_llff import EvaluationError, validate_image_pairs
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            renders, gt = root / "renders", root / "gt"
            renders.mkdir(); gt.mkdir()
            image = Image.new("RGB", (4, 3), (10, 20, 30))
            image.save(str(renders / "a.png")); image.save(str(gt / "a.png"))
            self.assertEqual(validate_image_pairs(renders, gt, {"a.png"}), ["a.png"])
            with self.assertRaises(EvaluationError):
                validate_image_pairs(renders, gt, {"a.png", "b.png"})

    def test_evaluator_metadata_uses_vgg(self):
        from scripts.evaluate_refgs_llff import evaluator_metadata
        metadata = evaluator_metadata()
        self.assertEqual(metadata["lpips_backbone"], "vgg")
        self.assertIn("evaluator_sha256", metadata)


class RunnerTests(unittest.TestCase):
    def test_aggregate_must_match_finite_per_view_mean(self):
        from scripts.run_refgs_llff import aggregate_matches_per_view
        per_view = {metric: {"a.png": value, "b.png": value} for metric, value in (
            ("PSNR", 10.0), ("SSIM", 0.5), ("LPIPS", 0.2)
        )}
        self.assertTrue(aggregate_matches_per_view(
            {"PSNR": 10.0, "SSIM": 0.5, "LPIPS": 0.2}, per_view
        ))
        self.assertFalse(aggregate_matches_per_view(
            {"PSNR": 11.0, "SSIM": 0.5, "LPIPS": 0.2}, per_view
        ))
    def test_weak_or_stale_smoke_certificate_is_rejected(self):
        from scripts.run_refgs_llff import smoke_certificate_header_valid
        weak = {"status": "completed", "smoke_gate_passed": True}
        self.assertFalse(smoke_certificate_header_valid(weak, "abc"))
        current = {
            "status": "completed", "smoke_gate_passed": True,
            "scene": "horns", "resolution": "1_8", "gpu": 1, "iteration": 10000,
            "smoke_certification": {"version": 2, "runner_sha256": "abc"},
        }
        self.assertTrue(smoke_certificate_header_valid(current, "abc"))
        self.assertFalse(smoke_certificate_header_valid(current, "different"))
    @unittest.skipUnless(DATA_ROOT.is_dir() and AUTHOR_ROOT.is_dir(), "LLFF source unavailable")
    def test_prepare_skip_rejects_extra_unlisted_image(self):
        from scripts.run_refgs_llff import prepared_scene_complete
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared = root / "prepared"
            audit_path = root / "logs" / "data_audit.json"
            prepare_scene("horns", "1_8", DATA_ROOT, AUTHOR_ROOT, prepared, audit_path)
            self.assertTrue(prepared_scene_complete(prepared, audit_path))
            (prepared / "images" / "extra.png").symlink_to(next((prepared / "images").iterdir()).resolve())
            self.assertFalse(prepared_scene_complete(prepared, audit_path))
            with self.assertRaisesRegex(RuntimeError, "blocked_data"):
                prepare_scene("horns", "1_8", DATA_ROOT, AUTHOR_ROOT, prepared, audit_path)
    def test_gpu_resource_gate_rejects_busy_or_low_memory_device(self):
        from scripts.run_refgs_llff import gpu_resources_ready
        idle = {"memory_free_mib": 24244}
        self.assertTrue(gpu_resources_ready(idle, []))
        self.assertFalse(gpu_resources_ready(idle, [{"pid": 123}]))
        self.assertFalse(gpu_resources_ready({"memory_free_mib": 1000}, []))
    def test_stage_failure_reason_is_promoted_to_cell(self):
        from scripts.run_refgs_llff import cell_failure_reason
        stages = {"train": {"status": "failed", "failure_reason": "stage exited 2"}}
        self.assertEqual(cell_failure_reason(stages), "stage exited 2")
    def test_train_skip_requires_matching_manifest_fingerprint(self):
        from scripts.run_refgs_llff import protocol_fingerprint_matches
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared, model = root / "prepared", root / "model"
            prepared.mkdir(); model.mkdir()
            manifest = prepared / "refgs_llff_manifest.json"
            manifest.write_text('{"schema_version":1}')
            self.assertFalse(protocol_fingerprint_matches(prepared, model))
    def test_only_exact_horns_smoke_can_run_before_gate(self):
        from scripts.run_refgs_llff import validate_execution_request
        validate_execution_request("horns", "1_8", "1", 10000, False)
        invalid = (
            ("horns", "1_8", "2", 10000),
            ("horns", "1_4", "1", 10000),
            ("horns", "1_8", "1", 5000),
            ("fern", "1_8", "1", 10000),
        )
        for scene, resolution, gpu, iteration in invalid:
            with self.assertRaises((ValueError, RuntimeError)):
                validate_execution_request(scene, resolution, gpu, iteration, False)

    def test_smoke_certification_requires_all_four_fresh_stages(self):
        from scripts.run_refgs_llff import can_certify_smoke
        complete = {stage: {"status": "completed"} for stage in ("prepare", "train", "render", "eval")}
        self.assertTrue(can_certify_smoke("horns", "1_8", "1", 10000, complete, False))
        partial = {"eval": {"status": "completed"}}
        self.assertFalse(can_certify_smoke("horns", "1_8", "1", 10000, partial, False))
        stale = dict(complete)
        stale["train"] = {"status": "completed", "skipped_existing": True}
        self.assertFalse(can_certify_smoke("horns", "1_8", "1", 10000, stale, False))
        self.assertTrue(can_certify_smoke("horns", "1_8", "1", 10000, stale, True))

    def test_shared_eval_requires_provenance_and_fsgs_gate(self):
        from scripts.run_refgs_llff import shared_eval_complete
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model, logs = root / "model", root / "logs"
            model.mkdir(); logs.mkdir()
            expected = {"a.png"}
            (model / "results.json").write_text(json.dumps({"ours_10000": {"PSNR": 1.0, "SSIM": 0.5, "LPIPS": 0.2}}))
            self.assertFalse(shared_eval_complete(model, 10000, expected, logs))
    def test_failed_forced_stage_cannot_be_hidden_by_old_artifacts(self):
        from scripts.run_refgs_llff import resolve_cell_status
        status = resolve_cell_status(
            artifact_complete=True,
            stage_results={"eval": {"status": "failed"}},
            requested={"eval"},
        )
        self.assertEqual(status, "failed")

    def test_relative_roots_are_resolved_before_child_cwd_changes(self):
        from argparse import Namespace
        from scripts.run_refgs_llff import resolve_runtime_paths
        args = Namespace(
            python=Path("python"), data_root=Path("data"),
            author_preprocessed_root=Path("author"), prepared_root=Path("prepared"),
            output_root=Path("output"), tmp_root=Path("tmp"), log_root=Path("logs"),
        )
        resolve_runtime_paths(args, Path("/workspace"))
        self.assertEqual(args.log_root, Path("/workspace/logs"))
        self.assertEqual(args.output_root, Path("/workspace/output"))

    def test_physical_gpu_is_exposed_as_single_logical_device(self):
        from scripts.run_refgs_llff import build_child_env
        env = build_child_env("2", {"PATH": "/bin"})
        self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "2")
        self.assertEqual(env["REFGS_PHYSICAL_GPU"], "2")

    def test_two_cells_have_isolated_paths(self):
        from scripts.run_refgs_llff import cell_paths
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fern = cell_paths(root / "prepared", root / "output", root / "logs", "1_8", "fern")
            flower = cell_paths(root / "prepared", root / "output", root / "logs", "1_8", "flower")
            self.assertNotEqual(fern, flower)
            self.assertNotEqual(fern["model"], flower["model"])

    def test_skip_existing_rejects_incomplete_train(self):
        from scripts.run_refgs_llff import stage_complete
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory)
            point = model / "point_cloud" / "iteration_10000" / "point_cloud.ply"
            point.parent.mkdir(parents=True)
            point.write_bytes(b"ply")
            self.assertFalse(stage_complete("train", model, 10000, {"a.png"}))

    def test_smoke_gate_blocks_batch_without_completed_horns(self):
        from scripts.run_refgs_llff import smoke_allows_batch
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(smoke_allows_batch(Path(directory)))


class SummaryTests(unittest.TestCase):
    def test_summary_script_runs_as_a_direct_entrypoint(self):
        import subprocess
        import sys
        script = Path(__file__).resolve().parents[1] / "scripts" / "summarize_refgs_llff.py"
        result = subprocess.run([sys.executable, str(script), "--help"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_summary_writes_markdown_without_duplicate_format_keys(self):
        from scripts.summarize_refgs_llff import summarize
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for resolution in RESOLUTIONS:
                for scene in LLFF_SCENES:
                    path = root / resolution / scene / "status.json"
                    path.parent.mkdir(parents=True)
                    path.write_text(json.dumps({"status": "pending"}))
            summarize(root, root / "missing_fsgs.json")
            self.assertTrue((root / "refgs_llff_summary.md").is_file())

    def test_eight_scene_mean_and_delta_are_recomputed(self):
        from scripts.summarize_refgs_llff import aggregate_resolution
        rows = []
        for index, scene in enumerate(LLFF_SCENES):
            rows.append({
                "scene": scene, "resolution": "1_8", "status": "completed",
                "psnr": 20.0 + index, "ssim": 0.6 + index * 0.01,
                "lpips": 0.3 - index * 0.01,
            })
        result = aggregate_resolution(rows, "1_8")
        self.assertEqual(result["completed"], 8)
        self.assertAlmostEqual(result["mean"]["psnr"], 23.5)
        self.assertAlmostEqual(result["refgs_minus_fsgs"]["psnr"], 23.5 - 20.4619)
        self.assertAlmostEqual(result["refgs_minus_fsgs"]["lpips"], result["mean"]["lpips"] - 0.204037)

    def test_failed_metric_cells_are_blank(self):
        from scripts.summarize_refgs_llff import row_from_status
        row = row_from_status("fern", "1_8", {"status": "failed"})
        self.assertIsNone(row["psnr"])
        self.assertIsNone(row["ssim"])
        self.assertIsNone(row["lpips"])


if __name__ == "__main__":
    unittest.main()
