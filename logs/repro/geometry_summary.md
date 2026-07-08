# Ref-GS Geometry Summary

RGB metrics are PSNR/SSIM/LPIPS. The paper-comparable geometry metric is normal MAE in degrees.
Chamfer/F-score values in this report use saved Gaussian centers unless explicitly noted, so they are proxy_geometry and not directly comparable to paper normal MAE.

## Dataset Summary

| Dataset | Rows | normal MAE measured | Avg normal MAE deg | Proxy rows | Missing GT normal |
|---|---:|---:|---:|---:|---:|
| refnerf | 6 | 6 | 8.826000 | 0 | 0 |
| glossy_synthetic | 6 | 0 | nan | 6 | 6 |
| nerf_synthetic | 8 | 1 | 67.142690 | 7 | 7 |

## Per-Scene Summary

| Dataset | Scene | Status | Paper comparable | normal MAE deg | Chamfer-L1 | F-score | Notes |
|---|---|---|---:|---:|---:|---:|---|
| refnerf | ball | ok | True | 3.723057 | 0.013685 | 0.958859 | no matching GT depth files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| refnerf | car | ok | True | 12.495539 | 0.024071 | 0.834613 | no matching GT depth files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| refnerf | coffee | ok | True | 11.097899 | 0.020501 | 0.785955 | no matching GT depth files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| refnerf | helmet | ok | True | 5.382109 | 0.019812 | 0.793321 | no matching GT depth files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| refnerf | teapot | ok | True | 8.420211 | 0.016542 | 0.793605 | no matching GT depth files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| refnerf | toaster | ok | True | 11.837184 | 0.034366 | 0.761414 | no matching GT depth files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| glossy_synthetic | bell_blender | missing_gt_normal | False |  | 0.009123 | 0.956717 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| glossy_synthetic | cat_blender | missing_gt_normal | False |  | 0.013790 | 0.879042 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| glossy_synthetic | luyu_blender | missing_gt_normal | False |  | 0.008201 | 0.959121 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| glossy_synthetic | potion_blender | missing_gt_normal | False |  | 0.012275 | 0.919929 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| glossy_synthetic | tbell_blender | missing_gt_normal | False |  | 0.008822 | 0.967806 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| glossy_synthetic | teapot_blender | missing_gt_normal | False |  | 0.012864 | 0.916358 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| nerf_synthetic | chair | missing_gt_normal | False |  | 0.168152 | 0.169917 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| nerf_synthetic | drums | missing_gt_normal | False |  | 0.150056 | 0.132677 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| nerf_synthetic | ficus | missing_gt_normal | False |  | 0.223423 | 0.095049 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| nerf_synthetic | hotdog | missing_gt_normal | False |  | 0.204883 | 0.207586 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| nerf_synthetic | lego | missing_gt_normal | False |  | 0.151996 | 0.214021 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| nerf_synthetic | materials | missing_gt_normal | False |  | 0.193936 | 0.151977 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| nerf_synthetic | mic | missing_gt_normal | False |  | 0.225299 | 0.067613 | no matching GT normal files; Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |
| nerf_synthetic | ship | ok | False | 67.142690 | 0.157689 | 0.364656 | Chamfer/F-score use saved Gaussian centers, not extracted Ref-GS surface; not comparable to paper normal MAE |

## Paper Comparison

The public repository does not include a machine-readable copy of the paper table values.
Measured Ref-NeRF normal MAE deg rows are paper-comparable in metric family, but exact paper-table comparison remains blocked until the target paper values/protocol are entered.
Proxy Chamfer/F-score rows are not comparable to paper normal MAE deg and are intentionally excluded from this comparison.
