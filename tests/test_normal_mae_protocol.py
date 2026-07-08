import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.normal_mae_protocol import (
    build_eval_mask,
    compute_normal_mae_deg,
    decode_normal_rgb,
    load_gt_normal_alpha,
    load_normal,
    load_rgba_alpha_from_source_image,
    normalize_normals,
    transform_normals,
)
from scripts.select_final_normal_mae_protocol import evaluate_final_protocol_scene


class NormalMaeProtocolTests(unittest.TestCase):
    def test_same_normal_mae_is_zero(self):
        pred = np.array([[[0.0, 0.0, 1.0]]], dtype=np.float32)
        gt = np.array([[[0.0, 0.0, 1.0]]], dtype=np.float32)

        result = compute_normal_mae_deg(pred, gt)

        self.assertAlmostEqual(result["normal_mae_deg"], 0.0, places=5)

    def test_orthogonal_normal_mae_is_ninety(self):
        pred = np.array([[[1.0, 0.0, 0.0]]], dtype=np.float32)
        gt = np.array([[[0.0, 1.0, 0.0]]], dtype=np.float32)

        result = compute_normal_mae_deg(pred, gt)

        self.assertAlmostEqual(result["normal_mae_deg"], 90.0, places=5)

    def test_opposite_normal_mae_is_180(self):
        pred = np.array([[[0.0, 0.0, 1.0]]], dtype=np.float32)
        gt = np.array([[[0.0, 0.0, -1.0]]], dtype=np.float32)

        result = compute_normal_mae_deg(pred, gt)

        self.assertAlmostEqual(result["normal_mae_deg"], 180.0, places=5)

    def test_absolute_dot_treats_opposite_normal_as_zero(self):
        pred = np.array([[[0.0, 0.0, 1.0]]], dtype=np.float32)
        gt = np.array([[[0.0, 0.0, -1.0]]], dtype=np.float32)

        result = compute_normal_mae_deg(pred, gt, absolute_dot=True)

        self.assertAlmostEqual(result["normal_mae_deg"], 0.0, places=5)

    def test_uint8_normal_decode_maps_to_signed_range(self):
        decoded = normalize_normals(decode_normal_rgb(np.array([[[128, 128, 255]]], dtype=np.uint8)))

        self.assertAlmostEqual(float(decoded[0, 0, 0]), 0.0, places=2)
        self.assertAlmostEqual(float(decoded[0, 0, 1]), 0.0, places=2)
        self.assertAlmostEqual(float(decoded[0, 0, 2]), 1.0, places=3)

    def test_alpha_mask_excludes_background(self):
        pred = np.array([[[0.0, 0.0, 1.0], [1.0, 0.0, 0.0]]], dtype=np.float32)
        gt = np.array([[[0.0, 0.0, 1.0], [0.0, 1.0, 0.0]]], dtype=np.float32)
        mask = build_eval_mask(mask_policy="source_rgba_alpha", source_rgba_alpha=np.array([[255, 0]], dtype=np.uint8))

        result = compute_normal_mae_deg(pred, gt, mask=mask)

        self.assertEqual(result["valid_pixel_count"], 1)
        self.assertAlmostEqual(result["normal_mae_deg"], 0.0, places=5)

    def test_non_contiguous_array_does_not_raise(self):
        base = np.zeros((2, 2, 3), dtype=np.float32)
        base[..., 2] = 1.0

        result = compute_normal_mae_deg(base.transpose(1, 0, 2), base.transpose(1, 0, 2))

        self.assertEqual(result["valid_pixel_count"], 4)
        self.assertAlmostEqual(result["normal_mae_deg"], 0.0, places=5)

    def test_load_normal_preserves_alpha(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "normal.png"
            arr = np.array([[[128, 128, 255, 0], [128, 128, 255, 255]]], dtype=np.uint8)
            Image.fromarray(arr, mode="RGBA").save(path)

            normal, alpha = load_normal(path)

        self.assertEqual(normal.shape, (1, 2, 3))
        self.assertIsNotNone(alpha)
        self.assertFalse(bool(alpha[0, 0]))
        self.assertTrue(bool(alpha[0, 1]))

    def test_load_gt_normal_alpha_reads_rgba(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "normal.png"
            Image.fromarray(np.array([[[128, 128, 255, 0]]], dtype=np.uint8), mode="RGBA").save(path)

            alpha = load_gt_normal_alpha(path)

        self.assertIsNotNone(alpha)
        self.assertFalse(bool(alpha[0, 0]))

    def test_load_source_alpha_from_transform_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            scene_dir = Path(tmp)
            image_path = scene_dir / "test" / "r_0.png"
            image_path.parent.mkdir(parents=True)
            Image.fromarray(np.array([[[0, 0, 0, 0], [0, 0, 0, 255]]], dtype=np.uint8), mode="RGBA").save(image_path)
            frame = {"file_path": "test/r_0"}

            alpha = load_rgba_alpha_from_source_image(frame, scene_dir)

        self.assertIsNotNone(alpha)
        self.assertFalse(bool(alpha[0, 0]))
        self.assertTrue(bool(alpha[0, 1]))

    def test_transform_normals_uses_rotation_direction(self):
        normal = np.array([[[1.0, 0.0, 0.0]]], dtype=np.float32)
        # R is the CameraInfo convention used in this repo: world-to-camera rotation is R.T.
        r = np.array(
            [
                [0.0, -1.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float32,
        )

        transformed = transform_normals(normal, r, "world_to_camera")

        np.testing.assert_allclose(transformed[0, 0], np.array([0.0, -1.0, 0.0], dtype=np.float32), atol=1e-6)

    def test_final_protocol_scene_exact_eval_streams_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene_dir = root / "data" / "Shiny Blender Synthetic" / "coffee"
            out_dir = (
                root
                / "output"
                / "refnerf"
                / "coffee"
                / "iteration_30000"
                / "surf_normal"
                / "test"
                / "ours_30000"
                / "geometry"
                / "normal"
            )
            scene_dir.joinpath("test").mkdir(parents=True)
            out_dir.mkdir(parents=True)
            (scene_dir / "transforms_test.json").write_text(
                '{"frames":[{"file_path":"test/r_0","transform_matrix":[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}]}',
                encoding="utf-8",
            )
            Image.fromarray(np.array([[[0, 0, 0, 255], [0, 0, 0, 0]]], dtype=np.uint8), mode="RGBA").save(
                scene_dir / "test" / "r_0.png"
            )
            np.save(scene_dir / "test" / "r_0_normal.npy", np.array([[[0.0, 0.0, 2.0], [0.0, 0.0, 2.0]]], dtype=np.float32))
            np.save(out_dir / "r_0.npy", np.array([[[0.0, 0.0, 1.0], [1.0, 0.0, 0.0]]], dtype=np.float32))

            row = evaluate_final_protocol_scene(
                scene="coffee",
                iteration=30000,
                normal_key="surf_normal",
                mask_policy="source_rgba_alpha",
                normal_space="as_saved",
                data_root=root / "data",
                output_root=root / "output",
                max_frames=0,
                max_pixels_per_frame=0,
            )

        self.assertEqual(row["eval_mode"], "full")
        self.assertEqual(row["frame_count"], 1)
        self.assertEqual(row["valid_pixel_count"], 1)
        self.assertAlmostEqual(row["normal_mae_deg"], 0.0, places=5)

    def test_final_protocol_scene_marks_sampled_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene_dir = root / "data" / "Shiny Blender Synthetic" / "coffee"
            out_dir = (
                root
                / "output"
                / "refnerf"
                / "coffee"
                / "iteration_30000"
                / "surf_normal"
                / "test"
                / "ours_30000"
                / "geometry"
                / "normal"
            )
            scene_dir.joinpath("test").mkdir(parents=True)
            out_dir.mkdir(parents=True)
            (scene_dir / "transforms_test.json").write_text(
                '{"frames":[{"file_path":"test/r_0","transform_matrix":[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}]}',
                encoding="utf-8",
            )
            Image.fromarray(np.array([[[0, 0, 0, 255], [0, 0, 0, 255]]], dtype=np.uint8), mode="RGBA").save(
                scene_dir / "test" / "r_0.png"
            )
            np.save(scene_dir / "test" / "r_0_normal.npy", np.array([[[0.0, 0.0, 2.0], [0.0, 0.0, 2.0]]], dtype=np.float32))
            np.save(out_dir / "r_0.npy", np.array([[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]], dtype=np.float32))

            row = evaluate_final_protocol_scene(
                scene="coffee",
                iteration=30000,
                normal_key="surf_normal",
                mask_policy="source_rgba_alpha",
                normal_space="as_saved",
                data_root=root / "data",
                output_root=root / "output",
                max_frames=1,
                max_pixels_per_frame=1,
            )

        self.assertEqual(row["eval_mode"], "sampled")
        self.assertIn("sampled", row["status"])


if __name__ == "__main__":
    unittest.main()
