# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 14:23:35 2019

@author: patri
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Mar  6 11:05:18 2018

@author: patri
"""

import numpy as np
import math
from scipy import ndimage
from skimage.color import rgb2gray
import Source.Imaging_functions.imaging_toolbox as itb
from skimage import filters
from skimage import morphology

__SCRIPT_NAME="[Region of interest]"

def createDefault(image):
    """
    Funktion um ein schwarzes Duplikat eines Bildes zu erzeugen.
    """
    array = np.zeros(image.shape)
    return array

def meanBox(startX,startY,width,height,image):
    """
    Funktion zur Berechnung der Durchschnittsintensität in einem quadratischen Bildausschnitt.
    """
    return int(np.mean(image[startY:startY+height,startX:startX+width]))

def fillRectangle(x,y,width,height,mask): 
    """
    Funktion um eine quadratische Fläche in einem binären, zweidimensionalen Bild zu füllen.
    """
    mask[y:y+height,x:x+width] = 1
    return mask

def detect_roi(image,dimension=1000):
    """
    Funktion zur Gewebedetektion.
    """
    numpy_array = image.get_numpy_array()
    if len(numpy_array.shape) > 2:
        numpy_array = rgb2gray(numpy_array)
    numpy_array = itb.intensity_values_to_byte(numpy_array)
    numpy_array = ndimage.filters.gaussian_filter(numpy_array,5)
    x_length = numpy_array.shape[1]
    y_length = numpy_array.shape[0]
    boxWidth = int(max(x_length/dimension,5))
    boxHeight = int(max(y_length/dimension,5))
    xBorder = x_length%boxWidth
    yBorder = y_length%boxHeight
    mask = createDefault(numpy_array)
    threshold = filters.threshold_multiotsu(numpy_array,3)[-1]
    for x in range(0,x_length-xBorder,boxWidth): 
        for y in range(0,y_length-yBorder,boxHeight): 
            meanVal = meanBox(x,y,boxWidth,boxHeight,numpy_array)
            if meanVal < threshold: 
                mask = fillRectangle(x,y,boxWidth,boxHeight,mask)
    if(xBorder>0): 
        for y in range(0,y_length-yBorder,boxHeight): 
            meanVal = meanBox(x_length-xBorder,y,xBorder,boxHeight,numpy_array)
            if meanVal < threshold:
                mask = fillRectangle(x_length-xBorder,y,xBorder,boxHeight,mask)
    if(yBorder>0): 
        for x in range(0,x_length-xBorder,boxWidth): 
            meanVal = meanBox(x,y_length-yBorder,boxWidth,yBorder,numpy_array)
            if meanVal < threshold: 
                mask = fillRectangle(x,y_length-yBorder,boxWidth,yBorder,mask)
    if(xBorder>0 and yBorder>0): 
        meanVal = meanBox(x_length-xBorder,y_length-yBorder,xBorder,yBorder,numpy_array)
        if meanVal < threshold: 
            mask = fillRectangle(x_length-xBorder,y_length-yBorder,xBorder,yBorder,mask)
    min_thresh = int((np.array(mask).size)/100)
    mask = morphology.remove_small_objects(mask.astype(np.bool), min_size=min_thresh)
    return mask.astype(np.uint8)