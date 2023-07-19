# -*- coding: utf-8 -*-
"""
Impro3000

part of the Impro3000 project to replace shitty Impro stuff. Use with care...
"""
import numpy as np
from skimage.color import rgba2rgb
from skimage.color import separate_stains
import os
from skimage.exposure import rescale_intensity, adjust_log
from skimage import filters
from Source.Imaging_functions import imaging_toolbox as itb
from copy import deepcopy

__SCRIPT_NAME="[Color deconvolution]: "

def load_color_matrix(stain="fuchsin_global"):
    """
    Funktion zum Laden einer vordefinierten Farbmatrix.
    """
    color_matrix_file = os.path.abspath("".join(["./Faith/Ressources/Colorvectorfiles/",str(stain), ".csv"]))
    if not os.path.exists(color_matrix_file):
        print( __SCRIPT_NAME+" File '"+color_matrix_file+"' does not exist...skipping." )
        return None
    csv = np.genfromtxt (color_matrix_file, delimiter=",")
    return csv

def colour_deconvolution(image, roi=None, stain="fuchsin_global"):
    """
    Funktion zur Durchführung einer Colordeconvolution.
    """
    stain1 = image.get_primary_staining()
    stain2 = image.get_tertiary_staining()
    image_numpy = image.get_numpy_array()
    if len(image_numpy[0][0])==4:
        image_numpy = rgba2rgb(image_numpy)
    color_matrix = np.linalg.inv(load_color_matrix(stain))
    three_channel_image = separate_stains(image_numpy,color_matrix)
    three_channel_image = rescale_intensity(three_channel_image,out_range=(0,255))
    three_channel_image = three_channel_image.astype(np.uint8)

    sec = image.get_new_instance()
    sec.set_primary_staining("")
    sec.set_tertiary_staining(stain1)
    sec_channel = itb.intensity_values_to_byte(three_channel_image[:, :, 1])
    if type(roi) is np.ndarray:
        sec_channel = sec_channel * roi
    sec_channel = adjust_log(sec_channel)
    sec_channel = rescale_intensity(sec_channel,out_range=(0,255))
    threshold_sec = filters.threshold_multiotsu(sec_channel,4)
    threshold_sec = threshold_sec[-1]
    sec_channel[sec_channel <= threshold_sec] = 0
    sec.set_numpy_array(sec_channel)
    
    prim = image.get_new_instance()
    prim.set_primary_staining(stain2)
    prim.set_tertiary_staining("")
    prim_channel = itb.intensity_values_to_byte(three_channel_image[:, :, 0])
    if type(roi) is np.ndarray:
        prim_channel = prim_channel * roi
    prim_channel = adjust_log(prim_channel)
    prim_channel = rescale_intensity(prim_channel,out_range=(0,255))
    threshold_prim = filters.threshold_multiotsu(prim_channel,4)
    threshold_prim = threshold_prim[-1]
    prim_channel[prim_channel <= threshold_prim] = 0
    prim.set_numpy_array(prim_channel)

    three_channel_image = None
    image_numpy = None
    
    return prim,sec