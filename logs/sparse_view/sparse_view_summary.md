# Sparse-View Evaluation Summary

## Coverage

- Sparse rows discovered: 100
- Rows with metrics: 31
- Rows missing metrics: 69
- Rows with checkpoints: 31
- Rows with rendered test images: 31
- Completed: 31
- Running: 2
- Missing: 67
- Failed: 0

## Completion By Dataset/View

| dataset | strategy | views | seed | total | completed | running | missing | failed | completion_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | uniform_pose | 3 | 0 | 6 | 1 | 1 | 4 | 0 | 0.166667 |
| glossy_synthetic | uniform_pose | 6 | 0 | 6 | 0 | 1 | 5 | 0 | 0.000000 |
| glossy_synthetic | uniform_pose | 9 | 0 | 6 | 0 | 0 | 6 | 0 | 0.000000 |
| glossy_synthetic | uniform_pose | 12 | 0 | 6 | 0 | 0 | 6 | 0 | 0.000000 |
| glossy_synthetic | uniform_pose | 24 | 0 | 6 | 0 | 0 | 6 | 0 | 0.000000 |
| nerf_synthetic | uniform_pose | 3 | 0 | 8 | 0 | 0 | 8 | 0 | 0.000000 |
| nerf_synthetic | uniform_pose | 6 | 0 | 8 | 0 | 0 | 8 | 0 | 0.000000 |
| nerf_synthetic | uniform_pose | 9 | 0 | 8 | 0 | 0 | 8 | 0 | 0.000000 |
| nerf_synthetic | uniform_pose | 12 | 0 | 8 | 0 | 0 | 8 | 0 | 0.000000 |
| nerf_synthetic | uniform_pose | 24 | 0 | 8 | 0 | 0 | 8 | 0 | 0.000000 |
| refnerf | uniform_pose | 3 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| refnerf | uniform_pose | 6 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| refnerf | uniform_pose | 9 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| refnerf | uniform_pose | 12 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| refnerf | uniform_pose | 24 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |

## Dataset Averages

| dataset | strategy | views | seed | scenes | completed_scenes | psnr | ssim | lpips | delta_psnr | delta_ssim | delta_lpips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | uniform_pose | 3 | 0 | 6 | 1 | 14.831776 | 0.705753 | 0.386508 | -15.287082 | -0.264170 | 0.363225 |
| glossy_synthetic | uniform_pose | 6 | 0 | 6 | 0 | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 9 | 0 | 6 | 0 | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 12 | 0 | 6 | 0 | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 24 | 0 | 6 | 0 | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 3 | 0 | 8 | 0 | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 6 | 0 | 8 | 0 | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 9 | 0 | 8 | 0 | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 12 | 0 | 8 | 0 | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 24 | 0 | 8 | 0 | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 3 | 0 | 6 | 6 | 16.143194 | 0.771586 | 0.318336 | -14.944158 | -0.199352 | 0.269370 |
| refnerf | uniform_pose | 6 | 0 | 6 | 6 | 20.555772 | 0.850310 | 0.187156 | -10.531579 | -0.120628 | 0.138190 |
| refnerf | uniform_pose | 9 | 0 | 6 | 6 | 22.460150 | 0.876464 | 0.153523 | -8.627202 | -0.094474 | 0.104556 |
| refnerf | uniform_pose | 12 | 0 | 6 | 6 | 23.516961 | 0.892502 | 0.133114 | -7.570390 | -0.078436 | 0.084148 |
| refnerf | uniform_pose | 24 | 0 | 6 | 6 | 26.650752 | 0.929333 | 0.090203 | -4.436600 | -0.041605 | 0.041237 |

## Cross-Seed Averages

| dataset | strategy | views | seeds | psnr_mean | psnr_std | ssim_mean | ssim_std | lpips_mean | lpips_std | delta_psnr_mean | delta_ssim_mean | delta_lpips_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | uniform_pose | 3 | 1 | 14.831776 | NA | 0.705753 | NA | 0.386508 | NA | -15.287082 | -0.264170 | 0.363225 |
| glossy_synthetic | uniform_pose | 6 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 9 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 12 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 24 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 3 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 6 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 9 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 12 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 24 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 3 | 1 | 16.143194 | 4.374744 | 0.771586 | 0.120285 | 0.318336 | 0.169784 | -14.944158 | -0.199352 | 0.269370 |
| refnerf | uniform_pose | 6 | 1 | 20.555772 | 6.008194 | 0.850310 | 0.088568 | 0.187156 | 0.111162 | -10.531579 | -0.120628 | 0.138190 |
| refnerf | uniform_pose | 9 | 1 | 22.460150 | 5.887785 | 0.876464 | 0.078159 | 0.153523 | 0.102971 | -8.627202 | -0.094474 | 0.104556 |
| refnerf | uniform_pose | 12 | 1 | 23.516961 | 5.633019 | 0.892502 | 0.064570 | 0.133114 | 0.084187 | -7.570390 | -0.078436 | 0.084148 |
| refnerf | uniform_pose | 24 | 1 | 26.650752 | 4.849875 | 0.929333 | 0.041811 | 0.090203 | 0.054970 | -4.436600 | -0.041605 | 0.041237 |

## Per-Scene Table

| dataset | scene | strategy | views | seed | train_views | test_views | psnr | ssim | lpips | baseline_psnr | baseline_ssim | baseline_lpips | delta_psnr | delta_ssim | delta_lpips | status | failure_reason | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | bell_blender | uniform_pose | 3 | 0 | 3 | 16 | 14.831776 | 0.705753 | 0.386508 | 30.118858 | 0.969923 | 0.023283 | -15.287082 | -0.264170 | 0.363225 | completed |  |  |
| glossy_synthetic | cat_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 30.920703 | 0.971890 | 0.025718 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 29.274393 | 0.955103 | 0.033163 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 29.926326 | 0.959533 | 0.046309 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 31.215519 | 0.967600 | 0.033669 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 27.011217 | 0.953340 | 0.037896 | NA | NA | NA | running |  | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 30.118858 | 0.969923 | 0.023283 | NA | NA | NA | running |  | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 30.920703 | 0.971890 | 0.025718 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 29.274393 | 0.955103 | 0.033163 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 29.926326 | 0.959533 | 0.046309 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 31.215519 | 0.967600 | 0.033669 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 27.011217 | 0.953340 | 0.037896 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 30.118858 | 0.969923 | 0.023283 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 30.920703 | 0.971890 | 0.025718 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 29.274393 | 0.955103 | 0.033163 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 29.926326 | 0.959533 | 0.046309 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 31.215519 | 0.967600 | 0.033669 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 27.011217 | 0.953340 | 0.037896 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 30.118858 | 0.969923 | 0.023283 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 30.920703 | 0.971890 | 0.025718 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 29.274393 | 0.955103 | 0.033163 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 29.926326 | 0.959533 | 0.046309 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 31.215519 | 0.967600 | 0.033669 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 27.011217 | 0.953340 | 0.037896 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 30.118858 | 0.969923 | 0.023283 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 30.920703 | 0.971890 | 0.025718 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 29.274393 | 0.955103 | 0.033163 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 29.926326 | 0.959533 | 0.046309 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 31.215519 | 0.967600 | 0.033669 | NA | NA | NA | missing |  | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 27.011217 | 0.953340 | 0.037896 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 29.053885 | 0.976026 | 0.028086 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 24.823498 | 0.933557 | 0.060275 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 24.411800 | 0.925269 | 0.074030 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 33.157090 | 0.980351 | 0.029270 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 30.542826 | 0.972603 | 0.027694 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 30.285471 | 0.949973 | 0.050605 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 32.366114 | 0.978492 | 0.030150 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 28.350269 | 0.874557 | 0.130135 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 29.053885 | 0.976026 | 0.028086 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 24.823498 | 0.933557 | 0.060275 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 24.411800 | 0.925269 | 0.074030 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 33.157090 | 0.980351 | 0.029270 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 30.542826 | 0.972603 | 0.027694 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 30.285471 | 0.949973 | 0.050605 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 32.366114 | 0.978492 | 0.030150 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 28.350269 | 0.874557 | 0.130135 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 29.053885 | 0.976026 | 0.028086 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 24.823498 | 0.933557 | 0.060275 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 24.411800 | 0.925269 | 0.074030 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 33.157090 | 0.980351 | 0.029270 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 30.542826 | 0.972603 | 0.027694 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 30.285471 | 0.949973 | 0.050605 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 32.366114 | 0.978492 | 0.030150 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 28.350269 | 0.874557 | 0.130135 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 29.053885 | 0.976026 | 0.028086 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 24.823498 | 0.933557 | 0.060275 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 24.411800 | 0.925269 | 0.074030 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 33.157090 | 0.980351 | 0.029270 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 30.542826 | 0.972603 | 0.027694 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 30.285471 | 0.949973 | 0.050605 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 32.366114 | 0.978492 | 0.030150 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 28.350269 | 0.874557 | 0.130135 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 29.053885 | 0.976026 | 0.028086 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 24.823498 | 0.933557 | 0.060275 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 24.411800 | 0.925269 | 0.074030 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 33.157090 | 0.980351 | 0.029270 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 30.542826 | 0.972603 | 0.027694 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 30.285471 | 0.949973 | 0.050605 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 32.366114 | 0.978492 | 0.030150 | NA | NA | NA | missing |  | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 28.350269 | 0.874557 | 0.130135 | NA | NA | NA | missing |  | missing_metrics |
| refnerf | ball | uniform_pose | 3 | 0 | 3 | 200 | 11.829082 | 0.660491 | 0.541012 | 30.037854 | 0.971641 | 0.081153 | -18.208772 | -0.311150 | 0.459858 | completed |  |  |
| refnerf | car | uniform_pose | 3 | 0 | 3 | 200 | 18.054066 | 0.801862 | 0.169408 | 31.196145 | 0.965286 | 0.026168 | -13.142079 | -0.163424 | 0.143239 | completed |  |  |
| refnerf | coffee | uniform_pose | 3 | 0 | 3 | 200 | 17.841351 | 0.816676 | 0.291644 | 31.923324 | 0.968782 | 0.065987 | -14.081973 | -0.152106 | 0.225657 | completed |  |  |
| refnerf | helmet | uniform_pose | 3 | 0 | 3 | 200 | 14.357655 | 0.773803 | 0.363751 | 30.502143 | 0.977921 | 0.036616 | -16.144487 | -0.204118 | 0.327136 | completed |  |  |
| refnerf | teapot | uniform_pose | 3 | 0 | 3 | 200 | 23.056637 | 0.956396 | 0.091382 | 35.109675 | 0.991671 | 0.016388 | -12.053038 | -0.035275 | 0.074994 | completed |  |  |
| refnerf | toaster | uniform_pose | 3 | 0 | 3 | 200 | 11.720373 | 0.620290 | 0.452820 | 27.754969 | 0.950328 | 0.067487 | -16.034596 | -0.330038 | 0.385333 | completed |  |  |
| refnerf | ball | uniform_pose | 6 | 0 | 6 | 200 | 15.988120 | 0.802616 | 0.321006 | 30.037854 | 0.971641 | 0.081153 | -14.049734 | -0.169025 | 0.239852 | completed |  |  |
| refnerf | car | uniform_pose | 6 | 0 | 6 | 200 | 21.587629 | 0.848174 | 0.098278 | 31.196145 | 0.965286 | 0.026168 | -9.608515 | -0.117112 | 0.072110 | completed |  |  |
| refnerf | coffee | uniform_pose | 6 | 0 | 6 | 200 | 21.848452 | 0.885513 | 0.181208 | 31.923324 | 0.968782 | 0.065987 | -10.074872 | -0.083268 | 0.115222 | completed |  |  |
| refnerf | helmet | uniform_pose | 6 | 0 | 6 | 200 | 18.536541 | 0.867244 | 0.196767 | 30.502143 | 0.977921 | 0.036616 | -11.965602 | -0.110677 | 0.160152 | completed |  |  |
| refnerf | teapot | uniform_pose | 6 | 0 | 6 | 200 | 31.164317 | 0.982224 | 0.031197 | 35.109675 | 0.991671 | 0.016388 | -3.945358 | -0.009447 | 0.014809 | completed |  |  |
| refnerf | toaster | uniform_pose | 6 | 0 | 6 | 200 | 14.209573 | 0.716089 | 0.294482 | 27.754969 | 0.950328 | 0.067487 | -13.545396 | -0.234239 | 0.226995 | completed |  |  |
| refnerf | ball | uniform_pose | 9 | 0 | 9 | 200 | 17.366939 | 0.819699 | 0.298335 | 30.037854 | 0.971641 | 0.081153 | -12.670915 | -0.151942 | 0.217182 | completed |  |  |
| refnerf | car | uniform_pose | 9 | 0 | 9 | 200 | 22.362517 | 0.873252 | 0.073747 | 31.196145 | 0.965286 | 0.026168 | -8.833627 | -0.092034 | 0.047579 | completed |  |  |
| refnerf | coffee | uniform_pose | 9 | 0 | 9 | 200 | 24.547222 | 0.914602 | 0.139919 | 31.923324 | 0.968782 | 0.065987 | -7.376103 | -0.054180 | 0.073932 | completed |  |  |
| refnerf | helmet | uniform_pose | 9 | 0 | 9 | 200 | 22.135418 | 0.905257 | 0.134156 | 30.502143 | 0.977921 | 0.036616 | -8.366725 | -0.072663 | 0.097540 | completed |  |  |
| refnerf | teapot | uniform_pose | 9 | 0 | 9 | 200 | 32.452116 | 0.984800 | 0.026571 | 35.109675 | 0.991671 | 0.016388 | -2.657559 | -0.006871 | 0.010183 | completed |  |  |
| refnerf | toaster | uniform_pose | 9 | 0 | 9 | 200 | 15.896687 | 0.761176 | 0.248409 | 27.754969 | 0.950328 | 0.067487 | -11.858282 | -0.189152 | 0.180923 | completed |  |  |
| refnerf | ball | uniform_pose | 12 | 0 | 12 | 200 | 19.331461 | 0.855944 | 0.236851 | 30.037854 | 0.971641 | 0.081153 | -10.706393 | -0.115697 | 0.155697 | completed |  |  |
| refnerf | car | uniform_pose | 12 | 0 | 12 | 200 | 23.362938 | 0.882798 | 0.067981 | 31.196145 | 0.965286 | 0.026168 | -7.833207 | -0.082487 | 0.041813 | completed |  |  |
| refnerf | coffee | uniform_pose | 12 | 0 | 12 | 200 | 24.567674 | 0.917762 | 0.138106 | 31.923324 | 0.968782 | 0.065987 | -7.355650 | -0.051020 | 0.072119 | completed |  |  |
| refnerf | helmet | uniform_pose | 12 | 0 | 12 | 200 | 23.148718 | 0.916059 | 0.110339 | 30.502143 | 0.977921 | 0.036616 | -7.353425 | -0.061862 | 0.073723 | completed |  |  |
| refnerf | teapot | uniform_pose | 12 | 0 | 12 | 200 | 33.505935 | 0.986670 | 0.023524 | 35.109675 | 0.991671 | 0.016388 | -1.603740 | -0.005001 | 0.007136 | completed |  |  |
| refnerf | toaster | uniform_pose | 12 | 0 | 12 | 200 | 17.185042 | 0.795779 | 0.221885 | 27.754969 | 0.950328 | 0.067487 | -10.569927 | -0.154549 | 0.154398 | completed |  |  |
| refnerf | ball | uniform_pose | 24 | 0 | 24 | 200 | 24.930064 | 0.922822 | 0.143654 | 30.037854 | 0.971641 | 0.081153 | -5.107790 | -0.048819 | 0.062500 | completed |  |  |
| refnerf | car | uniform_pose | 24 | 0 | 24 | 200 | 25.617334 | 0.908021 | 0.051115 | 31.196145 | 0.965286 | 0.026168 | -5.578811 | -0.057264 | 0.024947 | completed |  |  |
| refnerf | coffee | uniform_pose | 24 | 0 | 24 | 200 | 27.828950 | 0.943725 | 0.096447 | 31.923324 | 0.968782 | 0.065987 | -4.094374 | -0.025057 | 0.030460 | completed |  |  |
| refnerf | helmet | uniform_pose | 24 | 0 | 24 | 200 | 26.601677 | 0.946232 | 0.070214 | 30.502143 | 0.977921 | 0.036616 | -3.900466 | -0.031689 | 0.033598 | completed |  |  |
| refnerf | teapot | uniform_pose | 24 | 0 | 24 | 200 | 34.908607 | 0.989831 | 0.018185 | 35.109675 | 0.991671 | 0.016388 | -0.201068 | -0.001840 | 0.001797 | completed |  |  |
| refnerf | toaster | uniform_pose | 24 | 0 | 24 | 200 | 20.017881 | 0.865369 | 0.161605 | 27.754969 | 0.950328 | 0.067487 | -7.737088 | -0.084960 | 0.094119 | completed |  |  |

## Failure Summary

| dataset | scene | strategy | views | seed | status | failure_reason | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | cat_blender | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 3 | 0 | running |  | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 6 | 0 | running |  | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 3 | 0 | missing |  | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 6 | 0 | missing |  | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 9 | 0 | missing |  | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 12 | 0 | missing |  | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 24 | 0 | missing |  | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 24 | 0 | missing |  | missing_metrics |

## Paper/Full-View Alignment Caveats

- Sparse-view rows reduce only `transforms_train.json`; `transforms_test.json` remains the full test split.
- Full-view baselines are read from `output/repro_paper` and/or `logs/repro/metrics_summary.csv`; they are not overwritten by this summary.
- Sparse-view RGB metrics are protocol-specific and should not be mixed into the paper full-view table unless the paper uses the same sparse protocol.
- Random sparse-view rows should be interpreted across seeds because individual camera subsets can have high variance.
- Geometry/proxy metrics are intentionally excluded from the main sparse-view RGB summary.
