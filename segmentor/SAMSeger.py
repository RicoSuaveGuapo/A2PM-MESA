'''
Author: EasonZhang
Date: 2023-05-17 15:57:27
LastEditors: EasonZhang
LastEditTime: 2024-07-19 20:43:14
FilePath: /SA2M/hydra-mesa/segmentor/SAMSeger.py
Description: SAM-based Image Segmenter

Copyright (c) 2023 by EasonZhang, All Rights Reserved. 
'''

import sys 
sys.path.append("..")

import os
import os.path as osp  
import numpy as np
import cv2
from loguru import logger
from .seg_utils import MaskViewer

# TODO: Modify to your SAM path
from SAM.segment_anything import sam_model_registry, SamAutomaticMaskGenerator

class SAMSeger(object):
    """
    """
    def __init__(self, configs={}) -> None:
        """
        Args:
            W
            H
            sam_model_type
            sam_model_path
            save_folder
            points_per_side
        """
        self.W = configs["W"]
        self.H = configs["H"]
        self.sam_model_type = configs["sam_model_type"]
        self.sam_model_path = configs["sam_model_path"]
        self.save_folder = configs["save_folder"]
        self.points_per_side = configs["points_per_side"]

        self.sam_model = sam_model_registry[self.sam_model_type](checkpoint=self.sam_model_path)
        self.sam_mask_generator = SamAutomaticMaskGenerator(
            model=self.sam_model,
            points_per_side=self.points_per_side,
        )

        self.viewer = MaskViewer(self.save_folder)

    def img_loader(self, path):
        """
        """
        image = cv2.imread(path, -1)
        image = cv2.resize(image, (self.W, self.H))
        logger.info(f"load image as {image.shape}, {image.dtype}")
        return image

    def segment(self, img_path, sort_flag=True, save_flag=True, save_img_flag=False, save_name=""):
        """
        Args:
            img_path
            save_name
        Returns:
            masks : a list of mask
            mask = {
                segmentation : the mask
                area : the area of the mask in pixels
                bbox : the boundary box of the mask in XYWH format
                predicted_iou : the model's own prediction for the quality of the mask
                point_coords : the sampled input point that generated this mask
                stability_score : an additional measure of mask quality
                crop_box : the crop of the image used to generate this mask in XYWH format
            }
        """
        img = self.img_loader(img_path)

        masks = self.sam_mask_generator.generate(img)

        if sort_flag:
            masks.sort(key=lambda x: x["area"], reverse=True)

        if save_flag:
            if save_name == "":
                save_name = osp.splitext(osp.basename(img_path))[0]
            save_full_name = osp.join(self.save_folder, save_name)
            if not osp.exists(self.save_folder):
                os.makedirs(self.save_folder)

            np.save(save_full_name, masks)
            logger.info(f"save masks to {save_full_name}.npy")
        
        logger.info(f"segment {img_path} as {len(masks)} masks")

        if save_img_flag:
            self.viewer.draw_multi_masks_in_one(masks, self.W, self.H, name=save_name, key="segmentation")

        return masks
    
    def draw_masks(self, masks):
        """
        """
        for i, mask in enumerate(masks):
            self._draw_single_mask(mask["segmentation"], f"{i}")

    def _draw_single_mask(self, mask, name, flag=False):
        """
        """
        if not flag: return
        
        img = np.zeros((self.H, self.W), dtype=np.uint8)
        img[mask] = 255
        save_name = osp.join(self.save_folder, f"filtered_{name}.jpg")
        cv2.imwrite(save_name, img)