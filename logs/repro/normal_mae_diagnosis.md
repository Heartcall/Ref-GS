# Ref-GS Normal MAE Diagnosis

## Executive Summary

- Paper Ref-GS ShinyB normal MAE target used here: 2.21 deg.
- Current reproduced Ref-NeRF/Shiny average: 8.826000 deg.
- Gap: 6.616000 deg.
- This diagnosis uses existing saved geometry buffers and GT normals only; no retraining was run and no existing RGB/geometry metrics were overwritten.

## Current vs Paper

| Scene | Current normal MAE deg | Paper target gap | RGB PSNR |
|---|---:|---:|---:|
| ball | 3.723057 | 1.513057 | 30.0379 |
| car | 12.495539 | 10.285539 | 31.1961 |
| coffee | 11.097899 | 8.887899 | 31.9233 |
| helmet | 5.382109 | 3.172109 | 30.5021 |
| teapot | 8.420211 | 6.210211 | 35.1097 |
| toaster | 11.837184 | 9.627184 | 27.7550 |

## Confirmed Code Issues

- `normal_space_not_implemented`: `True`.
- `auto_convention_sweep_first_frame_only`: `True` in the existing `eval_geometry.py` helper.
- `decode_normal_drops_alpha`: `True`; alpha is not used by `decode_normal_image()`.
- `find_mask_reads_rgba_alpha`: `False`.

## Geometry Export Chain

- `geometry_export_chain_inconsistent`: `False`.
- render supports `--save-geometry`, `--geometry-only`, `--split`, `--normal-key`, `--depth-key`: `True`.
- Existing metadata shows prediction normal source per scene under `geometry/metadata.json`.

## Data/Mask Findings

| Scene | Pred normals | GT normals aligned | Current mask | Current valid px | Alpha frames | Alpha-mask MAE | Background entered |
|---|---:|---:|---|---:|---:|---:|---:|
| ball | 200 | True | explicit_mask_file | 999997 | 0 |  | 0 |
| car | 200 | True | gt_normal_norm_gt_eps | 260031 | 200 | 11.595570 | 95025248 |
| coffee | 200 | True | gt_normal_norm_gt_eps | 354208 | 200 | 10.500437 | 82878572 |
| helmet | 200 | True | gt_normal_norm_gt_eps | 429414 | 200 | 4.927682 | 73352942 |
| teapot | 200 | True | gt_normal_norm_gt_eps | 95830 | 200 | 7.648886 | 115839123 |
| toaster | 200 | True | gt_normal_norm_gt_eps | 499999 | 200 | 11.232731 | 64518349 |

## Convention Sweep Findings

Sweep values are diagnostic only; the best convention is not claimed as a paper reproduction. Alternate-convention MAE uses deterministic sampled pixels per frame: 1000.

| Scene | Current MAE | Best MAE | Gap | Best convention |
|---|---:|---:|---:|---|
| ball | 3.729636 | 3.572870 | 0.156766 | space=as_saved, flip=(False,False,False), absolute_dot=True |
| car | 12.408610 | 11.519678 | 0.888932 | space=as_saved, flip=(False,False,False), absolute_dot=True |
| coffee | 11.142431 | 10.162354 | 0.980077 | space=as_saved, flip=(False,False,False), absolute_dot=True |
| helmet | 5.413085 | 4.944990 | 0.468096 | space=as_saved, flip=(False,False,False), absolute_dot=True |
| teapot | 8.474975 | 7.233602 | 1.241373 | space=as_saved, flip=(False,False,False), absolute_dot=True |
| toaster | 11.852673 | 10.908842 | 0.943830 | space=as_saved, flip=(False,False,False), absolute_dot=True |

## Normal Key Findings

- Current saved normal key: `['surf_normal']`.
- Current saved depth key: `['surf_depth']`.
- `normal_key_protocol_uncertain`: `True`.
- Renderer returns both `rend_normal` and `surf_normal`; their definitions are different.

## Training Quality Findings

- `training_quality_possible_factor`: `True`.
- Existing checkpoints include iteration_31000 for all diagnosed scenes; iteration_30000 also exists for optional offline comparison.

## Ranked Root-Cause Hypotheses

1. **high** - 当前导出的 normal key 为 surf_normal，但论文协议未确认是 surf_normal 还是 rend_normal
   - geometry metadata records normal_key=surf_normal
   - render.py auto key order selects surf_normal before rend_normal
   - renderer also returns rend_normal with a different definition
   - sampled convention sweep remains far above 2.21 deg, so a simple flip alone does not explain the gap
2. **high** - mask/alpha 协议未对齐：GT/source RGBA alpha 存在，但当前 eval 多数场景不读取 RGBA alpha
   - decode_normal_image() drops alpha channels
   - find_mask() searches only separate *_alpha/*_mask files and does not read source RGBA alpha
   - diagnostic found current mask includes large background regions for RGBA scenes; alpha-mask sampled MAE improves but does not fully close the paper gap
3. **medium** - normal-space 参数没有执行真实坐标变换
   - `eval_geometry.py` accepts --normal-space but only writes row['normal_space']
   - sampled camera/world variants in the sweep did not beat the as-saved convention, so this is a confirmed eval-code bug but not sufficient evidence for the whole 8.8 vs 2.21 deg gap
4. **medium** - 训练几何质量或公开复现超参仍可能影响法线质量
   - RGB PSNR is reasonable but not proof of paper-level normals
   - all scenes use saved iteration_31000, and iteration_30000 checkpoints also exist for optional offline comparison

## Recommended Next Experiments/Fixes

- Do not change reported metrics in place; first add an eval-only branch that explicitly converts pred/GT normals to the same declared coordinate space.
- Evaluate both `--normal-key surf_normal` and `--normal-key rend_normal` into a separate debug output root, then compare against GT with the same mask and convention sweep.
- Make mask policy explicit: separate mask file, source RGBA alpha, GT normal alpha, or GT nonzero-normal mask; report valid-pixel ratio for every scene.
- Extend convention sweep to the full test split before selecting a protocol; do not use the best sweep value as a paper result.
- Optionally evaluate existing iteration_30000 geometry buffers in a separate output/log root if paper iteration is suspected, without retraining.
