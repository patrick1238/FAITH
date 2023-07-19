# -*- coding: utf-8 -*-
"""
Created on Wed Nov 28 14:43:55 2018

@author: patri
"""
import numpy as np

def intensity_values_to_byte(data, cmin=None, cmax=None, high=255, low=0):
    """
    Funktion um Intensitätswerte des Typ float in Byte values zu transformieren.
    """
    if cmin is None:
        cmin = data.min()
    if cmax is None:
        cmax = data.max()

    cscale = cmax - cmin
    if cscale < 0:
        raise ValueError("`cmax` should be larger than `cmin`.")
    elif cscale == 0:
        cscale = 1

    scale = float(high - low) / cscale
    bytedata = (data - cmin) * scale + low
    return (bytedata.clip(low, high) + 0.5).astype(np.uint8)
    
def __logTransform(image): 
    """
    Funktion für die logarithmische Transformation eines Bildes.
    """
    val = 0
    image = np.array(image,float)
    for y in range(0,image.shape[0],1): 
        for x in range(0,image.shape[1],1):
            val = float(np.log2(float(image[y,x])+1.0))
            image[y,x] = val
    return image

def __shift(image): 
    """
    Funktion um das Intensitätsspektrum auf 0 bis 255 zu spreizen.
    """
    minVal = image.min()
    maxVal = image.max()
    for y in range(0,image.shape[0],1): 
        for x in range(0,image.shape[1],1):
            image[y,x] = int(((image[y,x] - minVal)/(maxVal-minVal))*255)
    return image

def contrast_enhancement(image):
    """
    Funktion um des Kontrast eines Bildes zu verstärken.
    """
    return __shift(__logTransform(image))

def calculate_percentage(image,mask):
    """
    Funktion um den Anteil positiver Pixel an einer gegebenen Maske zu berechnen.
    """
    image = np.multiply(image, mask)
    image_pixel = np.count_nonzero(image)
    mask_pixel = np.count_nonzero(mask)
    return image_pixel/(mask_pixel/100)

def calculate_downsample(image,layer_1,layer_2):
    """
    Funktion um die downsample Rate zwischen zwei Auflösungsstufen zu berechnen.
    """
    initial_size = image.get_width(layer_1)
    cur_size = image.get_width(layer_2)
    return initial_size/cur_size
