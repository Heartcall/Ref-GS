# Sparse-View Evaluation Summary

## Coverage

- Sparse rows discovered: 100
- Rows with metrics: 100
- Rows missing metrics: 0
- Rows with checkpoints: 100
- Rows with rendered test images: 100
- Completed: 100
- Running: 0
- Missing: 0
- Failed: 0

## Completion By Dataset/View

| dataset | strategy | views | seed | total | completed | running | missing | failed | completion_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | uniform_pose | 3 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| glossy_synthetic | uniform_pose | 6 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| glossy_synthetic | uniform_pose | 9 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| glossy_synthetic | uniform_pose | 12 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| glossy_synthetic | uniform_pose | 24 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| nerf_synthetic | uniform_pose | 3 | 0 | 8 | 8 | 0 | 0 | 0 | 1.000000 |
| nerf_synthetic | uniform_pose | 6 | 0 | 8 | 8 | 0 | 0 | 0 | 1.000000 |
| nerf_synthetic | uniform_pose | 9 | 0 | 8 | 8 | 0 | 0 | 0 | 1.000000 |
| nerf_synthetic | uniform_pose | 12 | 0 | 8 | 8 | 0 | 0 | 0 | 1.000000 |
| nerf_synthetic | uniform_pose | 24 | 0 | 8 | 8 | 0 | 0 | 0 | 1.000000 |
| refnerf | uniform_pose | 3 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| refnerf | uniform_pose | 6 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| refnerf | uniform_pose | 9 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| refnerf | uniform_pose | 12 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |
| refnerf | uniform_pose | 24 | 0 | 6 | 6 | 0 | 0 | 0 | 1.000000 |

## Dataset Averages

| dataset | strategy | views | seed | scenes | completed_scenes | psnr | ssim | lpips | delta_psnr | delta_ssim | delta_lpips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | uniform_pose | 3 | 0 | 6 | 6 | 15.685350 | 0.673214 | 0.376699 | -14.059153 | -0.289684 | 0.343359 |
| glossy_synthetic | uniform_pose | 6 | 0 | 6 | 6 | 19.976883 | 0.816954 | 0.159549 | -9.767620 | -0.145944 | 0.126209 |
| glossy_synthetic | uniform_pose | 9 | 0 | 6 | 6 | 21.974053 | 0.847900 | 0.120449 | -7.770450 | -0.114998 | 0.087109 |
| glossy_synthetic | uniform_pose | 12 | 0 | 6 | 6 | 22.926368 | 0.864717 | 0.105026 | -6.818135 | -0.098181 | 0.071686 |
| glossy_synthetic | uniform_pose | 24 | 0 | 6 | 6 | 25.729414 | 0.911772 | 0.066220 | -4.015089 | -0.051126 | 0.032880 |
| nerf_synthetic | uniform_pose | 3 | 0 | 8 | 8 | 16.759602 | 0.746840 | 0.265548 | -12.364267 | -0.202014 | 0.211767 |
| nerf_synthetic | uniform_pose | 6 | 0 | 8 | 8 | 20.922114 | 0.832661 | 0.148269 | -8.201755 | -0.116192 | 0.094488 |
| nerf_synthetic | uniform_pose | 9 | 0 | 8 | 8 | 22.893462 | 0.866723 | 0.110989 | -6.230407 | -0.082130 | 0.057209 |
| nerf_synthetic | uniform_pose | 12 | 0 | 8 | 8 | 24.066240 | 0.884015 | 0.095659 | -5.057629 | -0.064838 | 0.041879 |
| nerf_synthetic | uniform_pose | 24 | 0 | 8 | 8 | 26.416942 | 0.916125 | 0.072295 | -2.706927 | -0.032728 | 0.018515 |
| refnerf | uniform_pose | 3 | 0 | 6 | 6 | 16.143194 | 0.771586 | 0.318336 | -14.944158 | -0.199352 | 0.269370 |
| refnerf | uniform_pose | 6 | 0 | 6 | 6 | 20.555772 | 0.850310 | 0.187156 | -10.531579 | -0.120628 | 0.138190 |
| refnerf | uniform_pose | 9 | 0 | 6 | 6 | 22.460150 | 0.876464 | 0.153523 | -8.627202 | -0.094474 | 0.104556 |
| refnerf | uniform_pose | 12 | 0 | 6 | 6 | 23.516961 | 0.892502 | 0.133114 | -7.570390 | -0.078436 | 0.084148 |
| refnerf | uniform_pose | 24 | 0 | 6 | 6 | 26.650752 | 0.929333 | 0.090203 | -4.436600 | -0.041605 | 0.041237 |

## Cross-Seed Averages

| dataset | strategy | views | seeds | psnr_mean | psnr_std | ssim_mean | ssim_std | lpips_mean | lpips_std | delta_psnr_mean | delta_ssim_mean | delta_lpips_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | uniform_pose | 3 | 1 | 15.685350 | 0.828204 | 0.673214 | 0.065127 | 0.376699 | 0.081349 | -14.059153 | -0.289684 | 0.343359 |
| glossy_synthetic | uniform_pose | 6 | 1 | 19.976883 | 1.342352 | 0.816954 | 0.026754 | 0.159549 | 0.041185 | -9.767620 | -0.145944 | 0.126209 |
| glossy_synthetic | uniform_pose | 9 | 1 | 21.974053 | 1.978641 | 0.847900 | 0.029724 | 0.120449 | 0.021782 | -7.770450 | -0.114998 | 0.087109 |
| glossy_synthetic | uniform_pose | 12 | 1 | 22.926368 | 1.854010 | 0.864717 | 0.027621 | 0.105026 | 0.029688 | -6.818135 | -0.098181 | 0.071686 |
| glossy_synthetic | uniform_pose | 24 | 1 | 25.729414 | 1.926732 | 0.911772 | 0.020866 | 0.066220 | 0.016493 | -4.015089 | -0.051126 | 0.032880 |
| nerf_synthetic | uniform_pose | 3 | 1 | 16.759602 | 2.449463 | 0.746840 | 0.084003 | 0.265548 | 0.077988 | -12.364267 | -0.202014 | 0.211767 |
| nerf_synthetic | uniform_pose | 6 | 1 | 20.922114 | 2.780095 | 0.832661 | 0.072985 | 0.148269 | 0.056067 | -8.201755 | -0.116192 | 0.094488 |
| nerf_synthetic | uniform_pose | 9 | 1 | 22.893462 | 2.592564 | 0.866723 | 0.068482 | 0.110989 | 0.048258 | -6.230407 | -0.082130 | 0.057209 |
| nerf_synthetic | uniform_pose | 12 | 1 | 24.066240 | 2.520447 | 0.884015 | 0.060135 | 0.095659 | 0.041354 | -5.057629 | -0.064838 | 0.041879 |
| nerf_synthetic | uniform_pose | 24 | 1 | 26.416942 | 2.908889 | 0.916125 | 0.055509 | 0.072295 | 0.041339 | -2.706927 | -0.032728 | 0.018515 |
| refnerf | uniform_pose | 3 | 1 | 16.143194 | 4.374744 | 0.771586 | 0.120285 | 0.318336 | 0.169784 | -14.944158 | -0.199352 | 0.269370 |
| refnerf | uniform_pose | 6 | 1 | 20.555772 | 6.008194 | 0.850310 | 0.088568 | 0.187156 | 0.111162 | -10.531579 | -0.120628 | 0.138190 |
| refnerf | uniform_pose | 9 | 1 | 22.460150 | 5.887785 | 0.876464 | 0.078159 | 0.153523 | 0.102971 | -8.627202 | -0.094474 | 0.104556 |
| refnerf | uniform_pose | 12 | 1 | 23.516961 | 5.633019 | 0.892502 | 0.064570 | 0.133114 | 0.084187 | -7.570390 | -0.078436 | 0.084148 |
| refnerf | uniform_pose | 24 | 1 | 26.650752 | 4.849875 | 0.929333 | 0.041811 | 0.090203 | 0.054970 | -4.436600 | -0.041605 | 0.041237 |

## Per-Scene Table

| dataset | scene | strategy | views | seed | train_views | test_views | psnr | ssim | lpips | baseline_psnr | baseline_ssim | baseline_lpips | delta_psnr | delta_ssim | delta_lpips | status | failure_reason | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| glossy_synthetic | bell_blender | uniform_pose | 3 | 0 | 3 | 16 | 14.831776 | 0.705753 | 0.386508 | 30.118858 | 0.969923 | 0.023283 | -15.287082 | -0.264170 | 0.363225 | completed |  |  |
| glossy_synthetic | cat_blender | uniform_pose | 3 | 0 | 3 | 16 | 14.513207 | 0.656219 | 0.423452 | 30.920703 | 0.971890 | 0.025718 | -16.407496 | -0.315671 | 0.397734 | completed |  |  |
| glossy_synthetic | luyu_blender | uniform_pose | 3 | 0 | 3 | 16 | 15.851377 | 0.653345 | 0.372223 | 29.274393 | 0.955103 | 0.033163 | -13.423016 | -0.301759 | 0.339060 | completed |  |  |
| glossy_synthetic | potion_blender | uniform_pose | 3 | 0 | 3 | 16 | 16.112568 | 0.563507 | 0.493296 | 29.926326 | 0.959533 | 0.046309 | -13.813757 | -0.396026 | 0.446988 | completed |  |  |
| glossy_synthetic | tbell_blender | uniform_pose | 3 | 0 | 3 | 16 | 16.614932 | 0.708690 | 0.330860 | 31.215519 | 0.967600 | 0.033669 | -14.600587 | -0.258910 | 0.297191 | completed |  |  |
| glossy_synthetic | teapot_blender | uniform_pose | 3 | 0 | 3 | 16 | 16.188240 | 0.751769 | 0.253856 | 27.011217 | 0.953340 | 0.037896 | -10.822977 | -0.201572 | 0.215959 | completed |  |  |
| glossy_synthetic | bell_blender | uniform_pose | 6 | 0 | 6 | 16 | 19.424870 | 0.828779 | 0.164298 | 30.118858 | 0.969923 | 0.023283 | -10.693988 | -0.141144 | 0.141015 | completed |  |  |
| glossy_synthetic | cat_blender | uniform_pose | 6 | 0 | 6 | 16 | 21.949278 | 0.862704 | 0.120340 | 30.920703 | 0.971890 | 0.025718 | -8.971425 | -0.109186 | 0.094622 | completed |  |  |
| glossy_synthetic | luyu_blender | uniform_pose | 6 | 0 | 6 | 16 | 19.971264 | 0.792285 | 0.126237 | 29.274393 | 0.955103 | 0.033163 | -9.303129 | -0.162818 | 0.093074 | completed |  |  |
| glossy_synthetic | potion_blender | uniform_pose | 6 | 0 | 6 | 16 | 21.154302 | 0.799033 | 0.207327 | 29.926326 | 0.959533 | 0.046309 | -8.772023 | -0.160499 | 0.161018 | completed |  |  |
| glossy_synthetic | tbell_blender | uniform_pose | 6 | 0 | 6 | 16 | 18.865757 | 0.797131 | 0.210343 | 31.215519 | 0.967600 | 0.033669 | -12.349762 | -0.170469 | 0.176674 | completed |  |  |
| glossy_synthetic | teapot_blender | uniform_pose | 6 | 0 | 6 | 16 | 18.495825 | 0.821793 | 0.128750 | 27.011217 | 0.953340 | 0.037896 | -8.515393 | -0.131547 | 0.090853 | completed |  |  |
| glossy_synthetic | bell_blender | uniform_pose | 9 | 0 | 9 | 16 | 22.854769 | 0.869260 | 0.104016 | 30.118858 | 0.969923 | 0.023283 | -7.264089 | -0.100664 | 0.080733 | completed |  |  |
| glossy_synthetic | cat_blender | uniform_pose | 9 | 0 | 9 | 16 | 24.349994 | 0.892065 | 0.099073 | 30.920703 | 0.971890 | 0.025718 | -6.570709 | -0.079824 | 0.073355 | completed |  |  |
| glossy_synthetic | luyu_blender | uniform_pose | 9 | 0 | 9 | 16 | 21.090343 | 0.815849 | 0.104093 | 29.274393 | 0.955103 | 0.033163 | -8.184050 | -0.139254 | 0.070929 | completed |  |  |
| glossy_synthetic | potion_blender | uniform_pose | 9 | 0 | 9 | 16 | 23.358887 | 0.843364 | 0.144861 | 29.926326 | 0.959533 | 0.046309 | -6.567439 | -0.116169 | 0.098552 | completed |  |  |
| glossy_synthetic | tbell_blender | uniform_pose | 9 | 0 | 9 | 16 | 21.398076 | 0.849927 | 0.148347 | 31.215519 | 0.967600 | 0.033669 | -9.817443 | -0.117673 | 0.114678 | completed |  |  |
| glossy_synthetic | teapot_blender | uniform_pose | 9 | 0 | 9 | 16 | 18.792246 | 0.816935 | 0.122303 | 27.011217 | 0.953340 | 0.037896 | -8.218971 | -0.136405 | 0.084406 | completed |  |  |
| glossy_synthetic | bell_blender | uniform_pose | 12 | 0 | 12 | 16 | 23.898506 | 0.881039 | 0.094681 | 30.118858 | 0.969923 | 0.023283 | -6.220352 | -0.088884 | 0.071398 | completed |  |  |
| glossy_synthetic | cat_blender | uniform_pose | 12 | 0 | 12 | 16 | 25.747784 | 0.911528 | 0.074355 | 30.920703 | 0.971890 | 0.025718 | -5.172919 | -0.060361 | 0.048637 | completed |  |  |
| glossy_synthetic | luyu_blender | uniform_pose | 12 | 0 | 12 | 16 | 21.885583 | 0.838108 | 0.082048 | 29.274393 | 0.955103 | 0.033163 | -7.388810 | -0.116995 | 0.048885 | completed |  |  |
| glossy_synthetic | potion_blender | uniform_pose | 12 | 0 | 12 | 16 | 23.144076 | 0.846264 | 0.147122 | 29.926326 | 0.959533 | 0.046309 | -6.782250 | -0.113269 | 0.100814 | completed |  |  |
| glossy_synthetic | tbell_blender | uniform_pose | 12 | 0 | 12 | 16 | 22.611348 | 0.864199 | 0.136213 | 31.215519 | 0.967600 | 0.033669 | -8.604171 | -0.103400 | 0.102544 | completed |  |  |
| glossy_synthetic | teapot_blender | uniform_pose | 12 | 0 | 12 | 16 | 20.270912 | 0.847165 | 0.095735 | 27.011217 | 0.953340 | 0.037896 | -6.740306 | -0.106176 | 0.057838 | completed |  |  |
| glossy_synthetic | bell_blender | uniform_pose | 24 | 0 | 24 | 16 | 26.469224 | 0.920928 | 0.060969 | 30.118858 | 0.969923 | 0.023283 | -3.649634 | -0.048995 | 0.037686 | completed |  |  |
| glossy_synthetic | cat_blender | uniform_pose | 24 | 0 | 24 | 16 | 27.965874 | 0.941041 | 0.047897 | 30.920703 | 0.971890 | 0.025718 | -2.954829 | -0.030849 | 0.022179 | completed |  |  |
| glossy_synthetic | luyu_blender | uniform_pose | 24 | 0 | 24 | 16 | 25.002220 | 0.897138 | 0.050524 | 29.274393 | 0.955103 | 0.033163 | -4.272173 | -0.057965 | 0.017361 | completed |  |  |
| glossy_synthetic | potion_blender | uniform_pose | 24 | 0 | 24 | 16 | 26.340409 | 0.903443 | 0.091845 | 29.926326 | 0.959533 | 0.046309 | -3.585917 | -0.056090 | 0.045537 | completed |  |  |
| glossy_synthetic | tbell_blender | uniform_pose | 24 | 0 | 24 | 16 | 26.301910 | 0.924454 | 0.072467 | 31.215519 | 0.967600 | 0.033669 | -4.913608 | -0.043146 | 0.038798 | completed |  |  |
| glossy_synthetic | teapot_blender | uniform_pose | 24 | 0 | 24 | 16 | 22.296846 | 0.883628 | 0.073617 | 27.011217 | 0.953340 | 0.037896 | -4.714371 | -0.069712 | 0.035721 | completed |  |  |
| nerf_synthetic | chair | uniform_pose | 3 | 0 | 3 | 200 | 14.800869 | 0.768090 | 0.232068 | 29.053885 | 0.976026 | 0.028086 | -14.253016 | -0.207936 | 0.203982 | completed |  |  |
| nerf_synthetic | drums | uniform_pose | 3 | 0 | 3 | 200 | 13.771075 | 0.673761 | 0.346647 | 24.823498 | 0.933557 | 0.060275 | -11.052423 | -0.259796 | 0.286372 | completed |  |  |
| nerf_synthetic | ficus | uniform_pose | 3 | 0 | 3 | 200 | 15.788276 | 0.792583 | 0.197719 | 24.411800 | 0.925269 | 0.074030 | -8.623525 | -0.132687 | 0.123689 | completed |  |  |
| nerf_synthetic | hotdog | uniform_pose | 3 | 0 | 3 | 200 | 18.819591 | 0.837543 | 0.213123 | 33.157090 | 0.980351 | 0.029270 | -14.337499 | -0.142808 | 0.183853 | completed |  |  |
| nerf_synthetic | lego | uniform_pose | 3 | 0 | 3 | 200 | 16.456987 | 0.728242 | 0.235141 | 30.542826 | 0.972603 | 0.027694 | -14.085838 | -0.244361 | 0.207448 | completed |  |  |
| nerf_synthetic | materials | uniform_pose | 3 | 0 | 3 | 200 | 15.284429 | 0.681393 | 0.360094 | 30.285471 | 0.949973 | 0.050605 | -15.001042 | -0.268580 | 0.309489 | completed |  |  |
| nerf_synthetic | mic | uniform_pose | 3 | 0 | 3 | 200 | 21.294186 | 0.866249 | 0.175911 | 32.366114 | 0.978492 | 0.030150 | -11.071928 | -0.112242 | 0.145761 | completed |  |  |
| nerf_synthetic | ship | uniform_pose | 3 | 0 | 3 | 200 | 17.861407 | 0.626856 | 0.363679 | 28.350269 | 0.874557 | 0.130135 | -10.488863 | -0.247700 | 0.233543 | completed |  |  |
| nerf_synthetic | chair | uniform_pose | 6 | 0 | 6 | 200 | 18.897372 | 0.857781 | 0.128026 | 29.053885 | 0.976026 | 0.028086 | -10.156513 | -0.118245 | 0.099940 | completed |  |  |
| nerf_synthetic | drums | uniform_pose | 6 | 0 | 6 | 200 | 18.248149 | 0.817945 | 0.153392 | 24.823498 | 0.933557 | 0.060275 | -6.575349 | -0.115612 | 0.093117 | completed |  |  |
| nerf_synthetic | ficus | uniform_pose | 6 | 0 | 6 | 200 | 19.794234 | 0.856676 | 0.127020 | 24.411800 | 0.925269 | 0.074030 | -4.617567 | -0.068593 | 0.052990 | completed |  |  |
| nerf_synthetic | hotdog | uniform_pose | 6 | 0 | 6 | 200 | 25.130031 | 0.910370 | 0.103379 | 33.157090 | 0.980351 | 0.029270 | -8.027058 | -0.069981 | 0.074109 | completed |  |  |
| nerf_synthetic | lego | uniform_pose | 6 | 0 | 6 | 200 | 20.819773 | 0.808776 | 0.141464 | 30.542826 | 0.972603 | 0.027694 | -9.723053 | -0.163827 | 0.113770 | completed |  |  |
| nerf_synthetic | materials | uniform_pose | 6 | 0 | 6 | 200 | 18.835380 | 0.794156 | 0.173426 | 30.285471 | 0.949973 | 0.050605 | -11.450090 | -0.155817 | 0.122821 | completed |  |  |
| nerf_synthetic | mic | uniform_pose | 6 | 0 | 6 | 200 | 25.301846 | 0.922978 | 0.089047 | 32.366114 | 0.978492 | 0.030150 | -7.064268 | -0.055514 | 0.058897 | completed |  |  |
| nerf_synthetic | ship | uniform_pose | 6 | 0 | 6 | 200 | 20.350129 | 0.692608 | 0.270397 | 28.350269 | 0.874557 | 0.130135 | -8.000141 | -0.181949 | 0.140262 | completed |  |  |
| nerf_synthetic | chair | uniform_pose | 9 | 0 | 9 | 200 | 21.861414 | 0.904068 | 0.081740 | 29.053885 | 0.976026 | 0.028086 | -7.192471 | -0.071957 | 0.053654 | completed |  |  |
| nerf_synthetic | drums | uniform_pose | 9 | 0 | 9 | 200 | 20.596946 | 0.867205 | 0.106269 | 24.823498 | 0.933557 | 0.060275 | -4.226552 | -0.066351 | 0.045994 | completed |  |  |
| nerf_synthetic | ficus | uniform_pose | 9 | 0 | 9 | 200 | 21.664382 | 0.883965 | 0.100426 | 24.411800 | 0.925269 | 0.074030 | -2.747419 | -0.041304 | 0.026397 | completed |  |  |
| nerf_synthetic | hotdog | uniform_pose | 9 | 0 | 9 | 200 | 27.413777 | 0.932053 | 0.074949 | 33.157090 | 0.980351 | 0.029270 | -5.743312 | -0.048298 | 0.045678 | completed |  |  |
| nerf_synthetic | lego | uniform_pose | 9 | 0 | 9 | 200 | 22.724220 | 0.854435 | 0.099020 | 30.542826 | 0.972603 | 0.027694 | -7.818606 | -0.118168 | 0.071327 | completed |  |  |
| nerf_synthetic | materials | uniform_pose | 9 | 0 | 9 | 200 | 20.805982 | 0.831852 | 0.131233 | 30.285471 | 0.949973 | 0.050605 | -9.479489 | -0.118121 | 0.080628 | completed |  |  |
| nerf_synthetic | mic | uniform_pose | 9 | 0 | 9 | 200 | 26.464244 | 0.936919 | 0.073496 | 32.366114 | 0.978492 | 0.030150 | -5.901870 | -0.041572 | 0.043346 | completed |  |  |
| nerf_synthetic | ship | uniform_pose | 9 | 0 | 9 | 200 | 21.616735 | 0.723286 | 0.220783 | 28.350269 | 0.874557 | 0.130135 | -6.733534 | -0.151271 | 0.090647 | completed |  |  |
| nerf_synthetic | chair | uniform_pose | 12 | 0 | 12 | 200 | 23.749696 | 0.916609 | 0.067413 | 29.053885 | 0.976026 | 0.028086 | -5.304189 | -0.059417 | 0.039327 | completed |  |  |
| nerf_synthetic | drums | uniform_pose | 12 | 0 | 12 | 200 | 21.215765 | 0.874316 | 0.099050 | 24.823498 | 0.933557 | 0.060275 | -3.607733 | -0.059241 | 0.038774 | completed |  |  |
| nerf_synthetic | ficus | uniform_pose | 12 | 0 | 12 | 200 | 22.105695 | 0.889637 | 0.095956 | 24.411800 | 0.925269 | 0.074030 | -2.306106 | -0.035633 | 0.021926 | completed |  |  |
| nerf_synthetic | hotdog | uniform_pose | 12 | 0 | 12 | 200 | 28.023419 | 0.940494 | 0.070070 | 33.157090 | 0.980351 | 0.029270 | -5.133671 | -0.039857 | 0.040800 | completed |  |  |
| nerf_synthetic | lego | uniform_pose | 12 | 0 | 12 | 200 | 24.644348 | 0.891001 | 0.076685 | 30.542826 | 0.972603 | 0.027694 | -5.898478 | -0.081602 | 0.048992 | completed |  |  |
| nerf_synthetic | materials | uniform_pose | 12 | 0 | 12 | 200 | 22.268600 | 0.857327 | 0.105864 | 30.285471 | 0.949973 | 0.050605 | -8.016870 | -0.092646 | 0.055259 | completed |  |  |
| nerf_synthetic | mic | uniform_pose | 12 | 0 | 12 | 200 | 27.532606 | 0.946350 | 0.060671 | 32.366114 | 0.978492 | 0.030150 | -4.833508 | -0.032142 | 0.030521 | completed |  |  |
| nerf_synthetic | ship | uniform_pose | 12 | 0 | 12 | 200 | 22.989789 | 0.756388 | 0.189565 | 28.350269 | 0.874557 | 0.130135 | -5.360480 | -0.118169 | 0.059430 | completed |  |  |
| nerf_synthetic | chair | uniform_pose | 24 | 0 | 24 | 200 | 27.145494 | 0.957685 | 0.039401 | 29.053885 | 0.976026 | 0.028086 | -1.908391 | -0.018340 | 0.011316 | completed |  |  |
| nerf_synthetic | drums | uniform_pose | 24 | 0 | 24 | 200 | 22.512641 | 0.901713 | 0.079076 | 24.823498 | 0.933557 | 0.060275 | -2.310857 | -0.031844 | 0.018800 | completed |  |  |
| nerf_synthetic | ficus | uniform_pose | 24 | 0 | 24 | 200 | 23.452131 | 0.907720 | 0.082986 | 24.411800 | 0.925269 | 0.074030 | -0.959669 | -0.017550 | 0.008957 | completed |  |  |
| nerf_synthetic | hotdog | uniform_pose | 24 | 0 | 24 | 200 | 30.361996 | 0.960792 | 0.044784 | 33.157090 | 0.980351 | 0.029270 | -2.795093 | -0.019559 | 0.015514 | completed |  |  |
| nerf_synthetic | lego | uniform_pose | 24 | 0 | 24 | 200 | 28.065531 | 0.941912 | 0.043883 | 30.542826 | 0.972603 | 0.027694 | -2.477294 | -0.030691 | 0.016190 | completed |  |  |
| nerf_synthetic | materials | uniform_pose | 24 | 0 | 24 | 200 | 25.493711 | 0.896676 | 0.084001 | 30.285471 | 0.949973 | 0.050605 | -4.791760 | -0.053296 | 0.033396 | completed |  |  |
| nerf_synthetic | mic | uniform_pose | 24 | 0 | 24 | 200 | 29.840199 | 0.965194 | 0.041948 | 32.366114 | 0.978492 | 0.030150 | -2.525915 | -0.013298 | 0.011798 | completed |  |  |
| nerf_synthetic | ship | uniform_pose | 24 | 0 | 24 | 200 | 24.463835 | 0.797308 | 0.162284 | 28.350269 | 0.874557 | 0.130135 | -3.886434 | -0.077249 | 0.032149 | completed |  |  |
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

No sparse rows with failed or missing metrics were found.

## Paper/Full-View Alignment Caveats

- Sparse-view rows reduce only `transforms_train.json`; `transforms_test.json` remains the full test split.
- Full-view baselines are read from `output/repro_paper` and/or `logs/repro/metrics_summary.csv`; they are not overwritten by this summary.
- Sparse-view RGB metrics are protocol-specific and should not be mixed into the paper full-view table unless the paper uses the same sparse protocol.
- Random sparse-view rows should be interpreted across seeds because individual camera subsets can have high variance.
- Geometry/proxy metrics are intentionally excluded from the main sparse-view RGB summary.
