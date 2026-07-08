import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.inventory_geometry_data import inventory_scene


class GeometryInventoryTests(unittest.TestCase):
    def test_inventory_detects_normal_depth_mesh_and_mask(self):
        with tempfile.TemporaryDirectory() as tmp:
            scene_root = Path(tmp) / "scene"
            scene_root.mkdir()
            Image.fromarray(np.zeros((2, 2, 3), dtype=np.uint8)).save(scene_root / "r_0_normal.png")
            Image.fromarray(np.zeros((2, 2), dtype=np.uint16)).save(scene_root / "r_0_depth.png")
            Image.fromarray(np.zeros((2, 2), dtype=np.uint8)).save(scene_root / "r_0_alpha.png")
            (scene_root / "scene_gt_mesh.ply").write_text("ply\n", encoding="utf-8")
            (scene_root / "transforms_test.json").write_text('{"frames": []}\n', encoding="utf-8")

            row = inventory_scene("refnerf", "scene", scene_root)

        self.assertTrue(row["gt_normal_available"])
        self.assertTrue(row["gt_depth_available"])
        self.assertTrue(row["gt_mesh_available"])
        self.assertIn("*normal*", row["normal_patterns"])
        self.assertEqual(row["mask_source"], "alpha_or_mask_file")

    def test_inventory_reports_missing_gt_without_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            scene_root = Path(tmp) / "scene"
            scene_root.mkdir()

            row = inventory_scene("nerf_synthetic", "scene", scene_root)

        self.assertFalse(row["gt_normal_available"])
        self.assertFalse(row["gt_depth_available"])
        self.assertFalse(row["can_measure_paper_normal_mae"])


if __name__ == "__main__":
    unittest.main()
