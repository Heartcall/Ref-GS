# Geometry Data Inventory

This is a read-only inventory of GT normal/depth/mesh availability for the Ref-GS reproduction scenes.

| Dataset | Scene | GT normal | GT depth | GT mesh/points | Mask source | Paper normal MAE possible | Notes |
|---|---|---:|---:|---:|---|---:|---|
| refnerf | helmet | True | False | True | rgba_alpha | True |  |
| refnerf | car | True | False | True | rgba_alpha | True |  |
| refnerf | ball | True | False | True | alpha_or_mask_file | True |  |
| refnerf | teapot | True | False | True | rgba_alpha | True |  |
| refnerf | coffee | True | False | True | rgba_alpha | True |  |
| refnerf | toaster | True | False | True | rgba_alpha | True |  |
| glossy_synthetic | bell_blender | False | True | True | rgba_alpha | False | raw GlossySynthetic depth exists, but converted frame-name alignment must be checked before paper-style depth comparison; missing_gt_normal |
| glossy_synthetic | tbell_blender | False | True | True | rgba_alpha | False | raw GlossySynthetic depth exists, but converted frame-name alignment must be checked before paper-style depth comparison; missing_gt_normal |
| glossy_synthetic | potion_blender | False | True | True | rgba_alpha | False | raw GlossySynthetic depth exists, but converted frame-name alignment must be checked before paper-style depth comparison; missing_gt_normal |
| glossy_synthetic | teapot_blender | False | True | True | rgba_alpha | False | raw GlossySynthetic depth exists, but converted frame-name alignment must be checked before paper-style depth comparison; missing_gt_normal |
| glossy_synthetic | luyu_blender | False | True | True | rgba_alpha | False | raw GlossySynthetic depth exists, but converted frame-name alignment must be checked before paper-style depth comparison; missing_gt_normal |
| glossy_synthetic | cat_blender | False | True | True | rgba_alpha | False | raw GlossySynthetic depth exists, but converted frame-name alignment must be checked before paper-style depth comparison; missing_gt_normal |
| nerf_synthetic | ship | True | True | True | rgba_alpha | False | points3d.ply is generated/proxy geometry and is not accepted GT |
| nerf_synthetic | ficus | False | True | True | rgba_alpha | False | points3d.ply is generated/proxy geometry and is not accepted GT; missing_gt_normal |
| nerf_synthetic | lego | False | True | True | rgba_alpha | False | points3d.ply is generated/proxy geometry and is not accepted GT; missing_gt_normal |
| nerf_synthetic | mic | False | True | True | rgba_alpha | False | points3d.ply is generated/proxy geometry and is not accepted GT; missing_gt_normal |
| nerf_synthetic | hotdog | False | True | True | rgba_alpha | False | points3d.ply is generated/proxy geometry and is not accepted GT; missing_gt_normal |
| nerf_synthetic | chair | False | True | True | rgba_alpha | False | points3d.ply is generated/proxy geometry and is not accepted GT; missing_gt_normal |
| nerf_synthetic | materials | False | True | True | rgba_alpha | False | points3d.ply is generated/proxy geometry and is not accepted GT; missing_gt_normal |
| nerf_synthetic | drums | False | True | True | rgba_alpha | False | points3d.ply is generated/proxy geometry and is not accepted GT; missing_gt_normal |
