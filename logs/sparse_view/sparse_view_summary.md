# Sparse-View Evaluation Summary

## Coverage

- Sparse rows discovered: 100
- Rows with metrics: 0
- Rows missing metrics: 100
- Rows with checkpoints: 0
- Rows with rendered test images: 0

## Dataset Averages

| dataset | strategy | views | seed | scenes | psnr | ssim | lpips | delta_psnr | delta_ssim | delta_lpips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | uniform_pose | 3 | 0 | 6 | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 6 | 0 | 6 | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 9 | 0 | 6 | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 12 | 0 | 6 | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 24 | 0 | 6 | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 3 | 0 | 8 | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 6 | 0 | 8 | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 9 | 0 | 8 | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 12 | 0 | 8 | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 24 | 0 | 8 | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 3 | 0 | 6 | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 6 | 0 | 6 | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 9 | 0 | 6 | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 12 | 0 | 6 | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 24 | 0 | 6 | NA | NA | NA | NA | NA | NA |

## Cross-Seed Averages

| dataset | strategy | views | seeds | psnr_mean | psnr_std | ssim_mean | ssim_std | lpips_mean | lpips_std | delta_psnr_mean | delta_ssim_mean | delta_lpips_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | uniform_pose | 3 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 6 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 9 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 12 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| glossy_synthetic | uniform_pose | 24 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 3 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 6 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 9 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 12 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nerf_synthetic | uniform_pose | 24 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 3 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 6 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 9 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 12 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| refnerf | uniform_pose | 24 | 1 | NA | NA | NA | NA | NA | NA | NA | NA | NA |

## Per-Scene Table

| dataset | scene | strategy | views | seed | train_views | test_views | psnr | ssim | lpips | baseline_psnr | baseline_ssim | baseline_lpips | delta_psnr | delta_ssim | delta_lpips | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | bell_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 30.118858 | 0.969923 | 0.023283 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 30.920703 | 0.971890 | 0.025718 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 29.274393 | 0.955103 | 0.033163 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 29.926326 | 0.959533 | 0.046309 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 31.215519 | 0.967600 | 0.033669 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 3 | 0 | 3 | 16 | NA | NA | NA | 27.011217 | 0.953340 | 0.037896 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 30.118858 | 0.969923 | 0.023283 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 30.920703 | 0.971890 | 0.025718 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 29.274393 | 0.955103 | 0.033163 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 29.926326 | 0.959533 | 0.046309 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 31.215519 | 0.967600 | 0.033669 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 6 | 0 | 6 | 16 | NA | NA | NA | 27.011217 | 0.953340 | 0.037896 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 30.118858 | 0.969923 | 0.023283 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 30.920703 | 0.971890 | 0.025718 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 29.274393 | 0.955103 | 0.033163 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 29.926326 | 0.959533 | 0.046309 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 31.215519 | 0.967600 | 0.033669 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 9 | 0 | 9 | 16 | NA | NA | NA | 27.011217 | 0.953340 | 0.037896 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 30.118858 | 0.969923 | 0.023283 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 30.920703 | 0.971890 | 0.025718 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 29.274393 | 0.955103 | 0.033163 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 29.926326 | 0.959533 | 0.046309 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 31.215519 | 0.967600 | 0.033669 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 12 | 0 | 12 | 16 | NA | NA | NA | 27.011217 | 0.953340 | 0.037896 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 30.118858 | 0.969923 | 0.023283 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 30.920703 | 0.971890 | 0.025718 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 29.274393 | 0.955103 | 0.033163 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 29.926326 | 0.959533 | 0.046309 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 31.215519 | 0.967600 | 0.033669 | NA | NA | NA | missing_metrics | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 24 | 0 | 24 | 16 | NA | NA | NA | 27.011217 | 0.953340 | 0.037896 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 29.053885 | 0.976026 | 0.028086 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 24.823498 | 0.933557 | 0.060275 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 24.411800 | 0.925269 | 0.074030 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 33.157090 | 0.980351 | 0.029270 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 30.542826 | 0.972603 | 0.027694 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 30.285471 | 0.949973 | 0.050605 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 32.366114 | 0.978492 | 0.030150 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 28.350269 | 0.874557 | 0.130135 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 29.053885 | 0.976026 | 0.028086 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 24.823498 | 0.933557 | 0.060275 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 24.411800 | 0.925269 | 0.074030 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 33.157090 | 0.980351 | 0.029270 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 30.542826 | 0.972603 | 0.027694 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 30.285471 | 0.949973 | 0.050605 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 32.366114 | 0.978492 | 0.030150 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 28.350269 | 0.874557 | 0.130135 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 29.053885 | 0.976026 | 0.028086 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 24.823498 | 0.933557 | 0.060275 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 24.411800 | 0.925269 | 0.074030 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 33.157090 | 0.980351 | 0.029270 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 30.542826 | 0.972603 | 0.027694 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 30.285471 | 0.949973 | 0.050605 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 32.366114 | 0.978492 | 0.030150 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 28.350269 | 0.874557 | 0.130135 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 29.053885 | 0.976026 | 0.028086 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 24.823498 | 0.933557 | 0.060275 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 24.411800 | 0.925269 | 0.074030 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 33.157090 | 0.980351 | 0.029270 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 30.542826 | 0.972603 | 0.027694 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 30.285471 | 0.949973 | 0.050605 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 32.366114 | 0.978492 | 0.030150 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 28.350269 | 0.874557 | 0.130135 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 29.053885 | 0.976026 | 0.028086 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 24.823498 | 0.933557 | 0.060275 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 24.411800 | 0.925269 | 0.074030 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 33.157090 | 0.980351 | 0.029270 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 30.542826 | 0.972603 | 0.027694 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 30.285471 | 0.949973 | 0.050605 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 32.366114 | 0.978492 | 0.030150 | NA | NA | NA | missing_metrics | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 28.350269 | 0.874557 | 0.130135 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | ball | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 30.037854 | 0.971641 | 0.081153 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | car | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 31.196145 | 0.965286 | 0.026168 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | coffee | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 31.923324 | 0.968782 | 0.065987 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | helmet | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 30.502143 | 0.977921 | 0.036616 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | teapot | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 35.109675 | 0.991671 | 0.016388 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | toaster | uniform_pose | 3 | 0 | 3 | 200 | NA | NA | NA | 27.754969 | 0.950328 | 0.067487 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | ball | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 30.037854 | 0.971641 | 0.081153 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | car | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 31.196145 | 0.965286 | 0.026168 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | coffee | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 31.923324 | 0.968782 | 0.065987 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | helmet | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 30.502143 | 0.977921 | 0.036616 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | teapot | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 35.109675 | 0.991671 | 0.016388 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | toaster | uniform_pose | 6 | 0 | 6 | 200 | NA | NA | NA | 27.754969 | 0.950328 | 0.067487 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | ball | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 30.037854 | 0.971641 | 0.081153 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | car | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 31.196145 | 0.965286 | 0.026168 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | coffee | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 31.923324 | 0.968782 | 0.065987 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | helmet | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 30.502143 | 0.977921 | 0.036616 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | teapot | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 35.109675 | 0.991671 | 0.016388 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | toaster | uniform_pose | 9 | 0 | 9 | 200 | NA | NA | NA | 27.754969 | 0.950328 | 0.067487 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | ball | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 30.037854 | 0.971641 | 0.081153 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | car | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 31.196145 | 0.965286 | 0.026168 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | coffee | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 31.923324 | 0.968782 | 0.065987 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | helmet | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 30.502143 | 0.977921 | 0.036616 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | teapot | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 35.109675 | 0.991671 | 0.016388 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | toaster | uniform_pose | 12 | 0 | 12 | 200 | NA | NA | NA | 27.754969 | 0.950328 | 0.067487 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | ball | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 30.037854 | 0.971641 | 0.081153 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | car | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 31.196145 | 0.965286 | 0.026168 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | coffee | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 31.923324 | 0.968782 | 0.065987 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | helmet | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 30.502143 | 0.977921 | 0.036616 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | teapot | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 35.109675 | 0.991671 | 0.016388 | NA | NA | NA | missing_metrics | missing_metrics |
| refnerf | toaster | uniform_pose | 24 | 0 | 24 | 200 | NA | NA | NA | 27.754969 | 0.950328 | 0.067487 | NA | NA | NA | missing_metrics | missing_metrics |

## Failure Summary

| dataset | scene | strategy | views | seed | status | notes |
| --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | bell_blender | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | bell_blender | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | cat_blender | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | luyu_blender | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | potion_blender | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | tbell_blender | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| glossy_synthetic | teapot_blender | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | chair | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | drums | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | ficus | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | hotdog | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | lego | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | materials | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | mic | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| nerf_synthetic | ship | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| refnerf | ball | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| refnerf | car | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| refnerf | coffee | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| refnerf | helmet | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| refnerf | teapot | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| refnerf | toaster | uniform_pose | 3 | 0 | missing_metrics | missing_metrics |
| refnerf | ball | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| refnerf | car | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| refnerf | coffee | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| refnerf | helmet | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| refnerf | teapot | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| refnerf | toaster | uniform_pose | 6 | 0 | missing_metrics | missing_metrics |
| refnerf | ball | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| refnerf | car | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| refnerf | coffee | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| refnerf | helmet | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| refnerf | teapot | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| refnerf | toaster | uniform_pose | 9 | 0 | missing_metrics | missing_metrics |
| refnerf | ball | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| refnerf | car | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| refnerf | coffee | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| refnerf | helmet | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| refnerf | teapot | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| refnerf | toaster | uniform_pose | 12 | 0 | missing_metrics | missing_metrics |
| refnerf | ball | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| refnerf | car | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| refnerf | coffee | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| refnerf | helmet | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| refnerf | teapot | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |
| refnerf | toaster | uniform_pose | 24 | 0 | missing_metrics | missing_metrics |

## Paper/Full-View Alignment Caveats

- Sparse-view rows reduce only `transforms_train.json`; `transforms_test.json` remains the full test split.
- Full-view baselines are read from `output/repro_paper` and/or `logs/repro/metrics_summary.csv`; they are not overwritten by this summary.
- Sparse-view RGB metrics are protocol-specific and should not be mixed into the paper full-view table unless the paper uses the same sparse protocol.
- Random sparse-view rows should be interpreted across seeds because individual camera subsets can have high variance.
- Geometry/proxy metrics are intentionally excluded from the main sparse-view RGB summary.
