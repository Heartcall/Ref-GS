# Sparse-View Evaluation Summary

## Coverage

- Sparse rows discovered: 1
- Rows with metrics: 1
- Rows missing metrics: 0
- Rows with checkpoints: 1
- Rows with rendered test images: 1

## Dataset Averages

| dataset | strategy | views | seed | scenes | psnr | ssim | lpips | delta_psnr | delta_ssim | delta_lpips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| refnerf | uniform_pose | 3 | 0 | 1 | 7.156135 | 0.341582 | 0.890565 | -24.767189 | -0.627200 | 0.824578 |

## Cross-Seed Averages

| dataset | strategy | views | seeds | psnr_mean | psnr_std | ssim_mean | ssim_std | lpips_mean | lpips_std | delta_psnr_mean | delta_ssim_mean | delta_lpips_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| refnerf | uniform_pose | 3 | 1 | 7.156135 | NA | 0.341582 | NA | 0.890565 | NA | -24.767189 | -0.627200 | 0.824578 |

## Per-Scene Table

| dataset | scene | strategy | views | seed | train_views | test_views | psnr | ssim | lpips | baseline_psnr | baseline_ssim | baseline_lpips | delta_psnr | delta_ssim | delta_lpips | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| refnerf | coffee | uniform_pose | 3 | 0 | 3 | 200 | 7.156135 | 0.341582 | 0.890565 | 31.923324 | 0.968782 | 0.065987 | -24.767189 | -0.627200 | 0.824578 | ok |  |

## Failure Summary

No sparse rows with failed or missing metrics were found.

## Paper/Full-View Alignment Caveats

- Sparse-view rows reduce only `transforms_train.json`; `transforms_test.json` remains the full test split.
- Full-view baselines are read from `output/repro_paper` and/or `logs/repro/metrics_summary.csv`; they are not overwritten by this summary.
- Sparse-view RGB metrics are protocol-specific and should not be mixed into the paper full-view table unless the paper uses the same sparse protocol.
- Random sparse-view rows should be interpreted across seeds because individual camera subsets can have high variance.
- Geometry/proxy metrics are intentionally excluded from the main sparse-view RGB summary.
