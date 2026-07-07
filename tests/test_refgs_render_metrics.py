import unittest

import torch

from render import composite_rgba, compute_image_metrics


class RefGSRenderMetricsTests(unittest.TestCase):
    def test_composite_rgba_uses_alpha_and_background(self):
        image = torch.tensor(
            [
                [[1.0]],  # R
                [[0.0]],  # G
                [[0.0]],  # B
                [[0.25]],  # A
            ]
        )
        background = torch.tensor([0.0, 0.0, 1.0])

        composited = composite_rgba(image, background)

        self.assertTrue(torch.allclose(composited[:, 0, 0], torch.tensor([0.25, 0.0, 0.75])))

    def test_compute_image_metrics_reports_standard_keys(self):
        pred = torch.ones((3, 8, 8))
        gt = torch.ones((3, 8, 8))

        metrics = compute_image_metrics(pred, gt, lpips_fn=None)

        self.assertEqual(set(metrics), {"psnr", "ssim", "lpips"})
        self.assertGreater(metrics["psnr"], 60.0)
        self.assertAlmostEqual(metrics["ssim"], 1.0, places=5)
        self.assertIsNone(metrics["lpips"])


if __name__ == "__main__":
    unittest.main()
