# Ref-GS Reproduction Geometry Metrics

Generated: 2026-07-08

These metrics compare saved Ref-GS Gaussian point-cloud centers against
available dataset geometry in raw coordinates. No ICP, scale fitting, or
similarity alignment is applied.

Reference protocol:

- Ref-NeRF/Shiny Blender Synthetic: sampled scene GT mesh, accepted GT.
- GlossySynthetic: `eval_pts.ply`, accepted evaluation points.
- NeRF Synthetic: `points3d.ply`, proxy only and not accepted GT.

Normal-angle metrics are `NA` because the Ref-GS saved Gaussian point clouds
do not contain prediction normals.

## Coverage

- Total scenes: 20
- Successful geometry rows: 20
- Accepted-GT rows: 12
- Proxy-only rows: 8
- Failed rows: 0

## Dataset Averages

| Dataset | Rows | Protocol | Chamfer-L1 | Chamfer-L2 | Hausdorff | F@0.5% | F@1% | F@2% |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| refnerf | 6 | accepted GT | 0.021572 | 0.002087 | 0.452548 | 0.6018 | 0.8202 | 0.9237 |
| glossy_synthetic | 6 | accepted GT | 0.010846 | 0.000365 | 0.337523 | 0.7694 | 0.9332 | 0.9796 |
| nerf_synthetic | 8 | proxy/mixed | 0.184408 | 0.084345 | 1.048907 | 0.0736 | 0.1754 | 0.2671 |

## Per-Scene Metrics

| Dataset | Scene | Protocol | Chamfer-L1 | Chamfer-L2 | Hausdorff | F@0.5% | F@1% | F@2% |
|---|---|---|---:|---:|---:|---:|---:|---:|
| refnerf | helmet | accepted_gt | 0.019848 | 0.000785 | 0.448495 | 0.5348 | 0.7917 | 0.9487 |
| refnerf | car | accepted_gt | 0.024137 | 0.003290 | 0.387368 | 0.6935 | 0.8332 | 0.8943 |
| refnerf | ball | accepted_gt | 0.013648 | 0.000492 | 0.680302 | 0.7775 | 0.9589 | 0.9870 |
| refnerf | teapot | accepted_gt | 0.016694 | 0.001071 | 0.283948 | 0.4707 | 0.7922 | 0.9199 |
| refnerf | coffee | accepted_gt | 0.020580 | 0.001131 | 0.334095 | 0.5554 | 0.7843 | 0.9315 |
| refnerf | toaster | accepted_gt | 0.034522 | 0.005756 | 0.581081 | 0.5787 | 0.7612 | 0.8610 |
| glossy_synthetic | bell_blender | accepted_gt | 0.009123 | 0.000163 | 0.352153 | 0.7924 | 0.9567 | 0.9891 |
| glossy_synthetic | tbell_blender | accepted_gt | 0.008822 | 0.000175 | 0.403820 | 0.8416 | 0.9678 | 0.9951 |
| glossy_synthetic | potion_blender | accepted_gt | 0.012275 | 0.000344 | 0.379736 | 0.7294 | 0.9199 | 0.9835 |
| glossy_synthetic | teapot_blender | accepted_gt | 0.012864 | 0.000782 | 0.436378 | 0.7390 | 0.9164 | 0.9711 |
| glossy_synthetic | luyu_blender | accepted_gt | 0.008201 | 0.000134 | 0.196255 | 0.8274 | 0.9591 | 0.9936 |
| glossy_synthetic | cat_blender | accepted_gt | 0.013790 | 0.000594 | 0.256793 | 0.6862 | 0.8790 | 0.9449 |
| nerf_synthetic | ship | proxy_only | 0.157542 | 0.059175 | 1.069701 | 0.1181 | 0.3648 | 0.4773 |
| nerf_synthetic | ficus | proxy_only | 0.223423 | 0.120955 | 1.150695 | 0.0425 | 0.0950 | 0.1805 |
| nerf_synthetic | lego | proxy_only | 0.152001 | 0.056525 | 0.870247 | 0.0932 | 0.2141 | 0.3381 |
| nerf_synthetic | mic | proxy_only | 0.225308 | 0.117233 | 1.223563 | 0.0373 | 0.0676 | 0.1171 |
| nerf_synthetic | hotdog | proxy_only | 0.204857 | 0.098505 | 1.080622 | 0.0851 | 0.2079 | 0.2899 |
| nerf_synthetic | chair | proxy_only | 0.168155 | 0.073513 | 1.192408 | 0.0767 | 0.1693 | 0.2533 |
| nerf_synthetic | materials | proxy_only | 0.193906 | 0.094202 | 0.899656 | 0.0771 | 0.1523 | 0.2371 |
| nerf_synthetic | drums | proxy_only | 0.150073 | 0.054655 | 0.904362 | 0.0590 | 0.1321 | 0.2433 |

Machine-readable files:

- `logs/repro/geometry_metrics.csv`
- `logs/repro/geometry_metrics.json`
