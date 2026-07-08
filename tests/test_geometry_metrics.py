import tempfile
import unittest
from pathlib import Path

import numpy as np

from scripts.eval_geometry import (
    compute_normal_mae_deg,
    decode_normal_image,
    evaluate_scene,
    normalize_normals,
)


class GeometryMetricsTests(unittest.TestCase):
    def test_identical_normals_have_zero_mae(self):
        pred = np.array([[[0.0, 0.0, 1.0]]], dtype=np.float32)
        gt = np.array([[[0.0, 0.0, 1.0]]], dtype=np.float32)

        result = compute_normal_mae_deg(pred, gt)

        self.assertAlmostEqual(result["normal_mae_deg"], 0.0, places=5)

    def test_orthogonal_normals_have_ninety_degree_mae(self):
        pred = np.array([[[1.0, 0.0, 0.0]]], dtype=np.float32)
        gt = np.array([[[0.0, 1.0, 0.0]]], dtype=np.float32)

        result = compute_normal_mae_deg(pred, gt)

        self.assertAlmostEqual(result["normal_mae_deg"], 90.0, places=5)

    def test_opposite_normals_have_180_degree_mae(self):
        pred = np.array([[[0.0, 0.0, 1.0]]], dtype=np.float32)
        gt = np.array([[[0.0, 0.0, -1.0]]], dtype=np.float32)

        result = compute_normal_mae_deg(pred, gt)

        self.assertAlmostEqual(result["normal_mae_deg"], 180.0, places=5)

    def test_absolute_dot_treats_opposite_normals_as_zero(self):
        pred = np.array([[[0.0, 0.0, 1.0]]], dtype=np.float32)
        gt = np.array([[[0.0, 0.0, -1.0]]], dtype=np.float32)

        result = compute_normal_mae_deg(pred, gt, absolute_dot=True)

        self.assertAlmostEqual(result["normal_mae_deg"], 0.0, places=5)

    def test_non_contiguous_normals_do_not_raise(self):
        base = np.zeros((2, 2, 3), dtype=np.float32)
        base[..., 2] = 1.0
        pred = base.transpose(1, 0, 2)
        gt = base.transpose(1, 0, 2)

        result = compute_normal_mae_deg(pred, gt)

        self.assertEqual(result["valid_pixel_count"], 4)
        self.assertAlmostEqual(result["normal_mae_deg"], 0.0, places=5)

    def test_uint8_normal_encoding_decodes_to_signed_range(self):
        encoded = np.array([[[128, 128, 255]]], dtype=np.uint8)

        decoded = decode_normal_image(encoded)
        decoded = normalize_normals(decoded)

        self.assertAlmostEqual(float(decoded[0, 0, 2]), 1.0, places=3)
        self.assertAlmostEqual(float(decoded[0, 0, 0]), 0.0, places=2)
        self.assertAlmostEqual(float(decoded[0, 0, 1]), 0.0, places=2)

    def test_missing_gt_returns_status_without_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model_dir = root / "output" / "refnerf" / "coffee"
            (model_dir / "test" / "ours_31000" / "geometry" / "normal").mkdir(parents=True)
            np.save(
                model_dir / "test" / "ours_31000" / "geometry" / "normal" / "r_0.npy",
                np.dstack([np.zeros((2, 2)), np.zeros((2, 2)), np.ones((2, 2))]).astype(np.float32),
            )

            row = evaluate_scene(
                dataset="refnerf",
                scene="coffee",
                data_root=root / "data",
                output_root=root / "output",
                iteration=31000,
                split="test",
                metrics=("normal_mae",),
            )

        self.assertEqual(row["status"], "missing_gt_normal")
        self.assertIsNone(row["normal_mae_deg"])


if __name__ == "__main__":
    unittest.main()
