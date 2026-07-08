# Normal MAE Protocol Report

## Executive summary

- Paper Ref-GS ShinyB target used for comparison: 2.21 deg.
- Previous reproduced Ref-NeRF/Shiny normal MAE: 8.826000 deg.
- Lowest 30000-step protocol candidate in this report: rend_normal = 6.354952 deg.
- Final rows keep `absolute_dot=false`; absolute-dot and convention-sweep rows are diagnostic only.
- The public protocol still does not identify the exact normal key/convention, so final status remains `protocol_uncertain` unless separately confirmed.

## Final protocol

| Field | Value |
|---|---|
| normal_key | surf_normal and rend_normal reported separately |
| mask_policy | source_rgba_alpha preferred; gt_normal_alpha/source alpha fallback; gt_normal_nonzero only last fallback |
| normal_space | as_saved (space_hypotheses_not_separable; using as_saved by conservative default) |
| iteration | 30000 for paper candidate; 31000 for current reproduction checkpoint |
| absolute_dot | false |
| flip_preset | none |

## Dataset average

| Checkpoint role | Iteration | Normal key | Avg normal MAE deg | Gap to old 8.826 | Gap to paper 2.21 | Status |
|---|---:|---|---:|---:|---:|---|
| final_paper_candidate | 30000 | surf_normal | 8.160663 | -0.665337 | 5.950663 | protocol_uncertain |
| final_paper_candidate | 30000 | rend_normal | 6.354952 | -2.471048 | 4.144952 | protocol_uncertain |
| final_repro_checkpoint | 31000 | surf_normal | 8.185185 | -0.640814 | 5.975185 | protocol_uncertain |
| final_repro_checkpoint | 31000 | rend_normal | 6.356497 | -2.469503 | 4.146497 | protocol_uncertain |

## Surf normal vs rend normal

| Iteration | surf_normal avg | rend_normal avg | rend - surf |
|---:|---:|---:|---:|
| 30000 | 8.160663 | 6.354952 | -1.805711 |
| 31000 | 8.185185 | 6.356497 | -1.828689 |

## 30000 vs 31000

| Normal key | iter30000 avg | iter31000 avg | iter31000 - iter30000 |
|---|---:|---:|---:|
| surf_normal | 8.160663 | 8.185185 | 0.024523 |
| rend_normal | 6.354952 | 6.356497 | 0.001545 |

## Mask policy ablation

Diagnostic grid rows are sampled by default; they are used for protocol evidence, not as the final full-pixel result.

| Iteration | Normal key | Mask policy | Space | Avg MAE deg | Valid ratio | Notes |
|---:|---|---|---|---:|---:|---|
| 30000 | rend_normal | source_rgba_alpha | as_saved | 6.762136 | 0.326483 | dataset_average_over_6_valid_scenes |
| 30000 | surf_normal | source_rgba_alpha | as_saved | 8.315589 | 0.328083 | dataset_average_over_6_valid_scenes |
| 30000 | rend_normal | gt_normal_alpha | as_saved | 7.521306 | 0.329517 | dataset_average_over_6_valid_scenes |
| 30000 | surf_normal | gt_normal_alpha | as_saved | 9.245121 | 0.331000 | dataset_average_over_6_valid_scenes |
| 30000 | rend_normal | gt_normal_nonzero | as_saved | 7.521306 | 0.329517 | dataset_average_over_6_valid_scenes |
| 30000 | surf_normal | gt_normal_nonzero | as_saved | 9.245121 | 0.331000 | dataset_average_over_6_valid_scenes |
| 30000 | rend_normal | auto | as_saved | 6.762136 | 0.326483 | dataset_average_over_6_valid_scenes |
| 30000 | surf_normal | auto | as_saved | 8.315589 | 0.328083 | dataset_average_over_6_valid_scenes |

## Normal-space and convention ablation

These rows keep mask_policy=source_rgba_alpha and absolute_dot=false. Flip rows are diagnostic only and are not selected as the final protocol.

| Iteration | Normal key | Space | Flip | Avg MAE deg | Notes |
|---:|---|---|---|---:|---|
| 30000 | rend_normal | as_saved | none | 6.762136 | dataset_average_over_6_valid_scenes |
| 30000 | surf_normal | as_saved | none | 8.315589 | dataset_average_over_6_valid_scenes |
| 30000 | rend_normal | camera | none | 6.762094 | dataset_average_over_6_valid_scenes |
| 30000 | surf_normal | camera | none | 8.315558 | dataset_average_over_6_valid_scenes |
| 30000 | rend_normal | world | none | 6.762093 | dataset_average_over_6_valid_scenes |
| 30000 | surf_normal | world | none | 8.315559 | dataset_average_over_6_valid_scenes |
| 30000 | rend_normal | as_saved | flip_y | 81.142653 | dataset_average_over_6_valid_scenes |
| 30000 | surf_normal | as_saved | flip_y | 80.078021 | dataset_average_over_6_valid_scenes |
| 30000 | rend_normal | as_saved | flip_z | 55.818352 | dataset_average_over_6_valid_scenes |
| 30000 | surf_normal | as_saved | flip_z | 57.407037 | dataset_average_over_6_valid_scenes |
| 30000 | rend_normal | as_saved | flip_yz | 122.221031 | dataset_average_over_6_valid_scenes |
| 30000 | surf_normal | as_saved | flip_yz | 121.627505 | dataset_average_over_6_valid_scenes |

## Per-scene final normal MAE

| Role | Iteration | Normal key | Scene | New MAE deg | Old MAE deg | Delta vs old | Valid ratio |
|---|---:|---|---|---:|---:|---:|---:|
| final_paper_candidate | 30000 | surf_normal | ball | 3.721487 | 3.723057 | -0.001570 | 0.505424 |
| final_paper_candidate | 30000 | rend_normal | ball | 1.480987 | 3.723057 | -2.242070 | 0.505424 |
| final_repro_checkpoint | 31000 | surf_normal | ball | 3.723084 | 3.723057 | 0.000027 | 0.505424 |
| final_repro_checkpoint | 31000 | rend_normal | ball | 1.490586 | 3.723057 | -2.232471 | 0.505424 |
| final_paper_candidate | 30000 | surf_normal | car | 11.076353 | 12.495539 | -1.419187 | 0.257426 |
| final_paper_candidate | 30000 | rend_normal | car | 8.337158 | 12.495539 | -4.158381 | 0.257522 |
| final_repro_checkpoint | 31000 | surf_normal | car | 11.153790 | 12.495539 | -1.341750 | 0.257425 |
| final_repro_checkpoint | 31000 | rend_normal | car | 8.326313 | 12.495539 | -4.169226 | 0.257521 |
| final_paper_candidate | 30000 | surf_normal | coffee | 10.461179 | 11.097899 | -0.636720 | 0.352284 |
| final_paper_candidate | 30000 | rend_normal | coffee | 9.311833 | 11.097899 | -1.786066 | 0.352301 |
| final_repro_checkpoint | 31000 | surf_normal | coffee | 10.498158 | 11.097899 | -0.599741 | 0.352292 |
| final_repro_checkpoint | 31000 | rend_normal | coffee | 9.315580 | 11.097899 | -1.782319 | 0.352309 |
| final_paper_candidate | 30000 | surf_normal | helmet | 4.991482 | 5.382109 | -0.390627 | 0.426752 |
| final_paper_candidate | 30000 | rend_normal | helmet | 3.483744 | 5.382109 | -1.898365 | 0.426800 |
| final_repro_checkpoint | 31000 | surf_normal | helmet | 4.986045 | 5.382109 | -0.396064 | 0.426749 |
| final_repro_checkpoint | 31000 | rend_normal | helmet | 3.466449 | 5.382109 | -1.915660 | 0.426797 |
| final_paper_candidate | 30000 | surf_normal | teapot | 7.610184 | 8.420211 | -0.810026 | 0.094941 |
| final_paper_candidate | 30000 | rend_normal | teapot | 7.189588 | 8.420211 | -1.230622 | 0.094942 |
| final_repro_checkpoint | 31000 | surf_normal | teapot | 7.629500 | 8.420211 | -0.790711 | 0.094940 |
| final_repro_checkpoint | 31000 | rend_normal | teapot | 7.192275 | 8.420211 | -1.227936 | 0.094940 |
| final_paper_candidate | 30000 | surf_normal | toaster | 11.103292 | 11.837184 | -0.733891 | 0.495758 |
| final_paper_candidate | 30000 | rend_normal | toaster | 8.326401 | 11.837184 | -3.510783 | 0.495772 |
| final_repro_checkpoint | 31000 | surf_normal | toaster | 11.120536 | 11.837184 | -0.716647 | 0.495765 |
| final_repro_checkpoint | 31000 | rend_normal | toaster | 8.347777 | 11.837184 | -3.489407 | 0.495779 |

## Evidence files

- `normal_mae_protocol_grid.csv` contains sampled surf_normal/rend_normal, 30000/31000, mask-policy, space, flip, and absolute-dot diagnostics.
- `gt_normal_space_inference.csv` is evidence for GT space/convention only; lowest rows are not automatically selected.
- `final_normal_mae.csv` is the selected protocol table. Rows marked `sampled` must not be presented as full-pixel results.
- Reaching the paper value requires both a public protocol match and a comparable MAE near 2.21 deg.

## Paper-level conclusion

This run must not be described as `已复现论文 normal MAE` while the normal key and GT convention remain uncertain or the average remains far from 2.21 deg.

Remaining causes, in priority order:

1. Training geometry quality of the available reproduction checkpoint is still worse than the paper target.
2. The paper protocol does not publicly identify whether `surf_normal` or `rend_normal` is the reported key.
3. GT normal coordinate convention remains uncertain because space hypotheses are not clearly separable.
4. Mask details are now alpha-based and traceable, but the exact paper mask policy is still not public.
