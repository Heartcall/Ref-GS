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


if __name__ == "__main__":
    unittest.main()
