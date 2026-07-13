#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

import os
import random
import json
import shutil
from utils.system_utils import searchForMaxIteration
from scene.dataset_readers import sceneLoadTypeCallbacks
from scene.gaussian_model import GaussianModel
from arguments import ModelParams
from utils.camera_utils import cameraList_from_camInfos, camera_to_JSON

class Scene:

    gaussians : GaussianModel

    def __init__(self, args : ModelParams, gaussians : GaussianModel, load_iteration=None, shuffle=True, resolution_scales=[1.0]):
        """b
        :param path: Path to colmap scene main folder.
        """
        self.model_path = args.model_path
        self.loaded_iter = None
        self.gaussians = gaussians

        if load_iteration:
            if load_iteration == -1:
                self.loaded_iter = searchForMaxIteration(os.path.join(self.model_path, "point_cloud"))
            else:
                self.loaded_iter = load_iteration
            print("Loading trained model at iteration {}".format(self.loaded_iter))

        self.train_cameras = {}
        self.test_cameras = {}

        if os.path.exists(os.path.join(args.source_path, "refgs_llff_manifest.json")):
            scene_info = sceneLoadTypeCallbacks["RefGSLLFF"](
                args.source_path,
                load_test_cameras=getattr(args, "load_test_cameras", True),
            )
        elif os.path.exists(os.path.join(args.source_path, "sparse")):
            scene_info = sceneLoadTypeCallbacks["Colmap"](args.source_path, args.images, args.eval)
        elif os.path.exists(os.path.join(args.source_path, "transforms_train.json")):
            print("Found transforms_train.json file, assuming Blender data set!")
            scene_info = sceneLoadTypeCallbacks["Blender"](args.source_path, args.white_background, args.eval)
        else:
            assert False, "Could not recognize scene type!"

        if not self.loaded_iter:
            with open(scene_info.ply_path, 'rb') as src_file, open(os.path.join(self.model_path, "input.ply") , 'wb') as dest_file:
                dest_file.write(src_file.read())
            json_cams = []
            camlist = []
            if scene_info.test_cameras:
                camlist.extend(scene_info.test_cameras)
            if scene_info.train_cameras:
                camlist.extend(scene_info.train_cameras)
            for id, cam in enumerate(camlist):
                json_cams.append(camera_to_JSON(id, cam))
            with open(os.path.join(self.model_path, "cameras.json"), 'w') as file:
                json.dump(json_cams, file)
            llff_manifest = os.path.join(args.source_path, "refgs_llff_manifest.json")
            if os.path.isfile(llff_manifest):
                from scripts.refgs_llff_common import file_sha256
                manifest_snapshot = os.path.join(self.model_path, "refgs_llff_manifest.json")
                shutil.copy2(llff_manifest, manifest_snapshot)
                with open(llff_manifest, encoding="utf-8") as file:
                    llff_payload = json.load(file)
                with open(os.path.join(self.model_path, "llff_protocol.json"), "w", encoding="utf-8") as file:
                    json.dump({
                        "manifest_sha256": file_sha256(llff_manifest),
                        "pointcloud_sha256": llff_payload["pointcloud"]["sha256"],
                        "scene": llff_payload["scene"],
                        "resolution": llff_payload["resolution"],
                        "recorded_by": "scene_initialization",
                    }, file, indent=2)

        if shuffle:
            random.shuffle(scene_info.train_cameras)  # Multi-res consistent random shuffling
            random.shuffle(scene_info.test_cameras)   # Multi-res consistent random shuffling

        self.cameras_extent = scene_info.nerf_normalization["radius"]

        print('resolution_scales', resolution_scales)
        
        for resolution_scale in resolution_scales:
            print("Loading Training Cameras")
            self.train_cameras[resolution_scale] = cameraList_from_camInfos(scene_info.train_cameras, resolution_scale, args)
            print("Loading Test Cameras")
            self.test_cameras[resolution_scale] = cameraList_from_camInfos(scene_info.test_cameras, resolution_scale, args)
        
        if self.loaded_iter:
            self.gaussians.load_ply(os.path.join(
                self.model_path,
               "point_cloud",
               "iteration_" + str(self.loaded_iter),
               "point_cloud.ply"
            ))
        else:
            self.gaussians.create_from_pcd(scene_info.point_cloud, self.cameras_extent)

    def save(self, iteration):
        point_cloud_path = os.path.join(self.model_path, "point_cloud/iteration_{}".format(iteration))
        self.gaussians.save_ply(os.path.join(point_cloud_path, "point_cloud.ply"))

    def getTrainCameras(self, scale=1.0):
        return self.train_cameras[scale]

    def getTestCameras(self, scale=1.0):
        return self.test_cameras[scale]
