# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 10:15:36 2019

@author: patri
"""
from ast import dump
import Source.Objects.Config as Config
import Source.Imaging_functions.identify_roi as ir
import math
import numpy as np
import os
import multiprocessing as mp
from functools import partial
from Source.Basic_functions.caller_toolbox import process_tiles


def __drop_dump(image_tile_list,dump_path):
    """
    Funktion um csv Dateien zu speichern, welche die Kachelkoordinaten zur parallelisierten Verarbeitung enthalten.
    """
    config = Config.load()
    image_tile_sub_lists = __divide_image_tiles(image_tile_list, int(config.get("cores")))
    for sub_list in image_tile_sub_lists:
        counter = image_tile_sub_lists.index(sub_list)
        csv_file_path = dump_path + "tile_sublist_no_" + str(counter) + ".csv"
        f = open(csv_file_path,"w")
        for image_string in sub_list:
            f.write(image_string+"\n")
        f.close()

def __divide_image_tiles(image_tile_dict,cores):
    """
    Funktion um eine Liste von Bildkacheln hinsichtlich dem Grad der Parallelisierung aufzuteilen.
    """
    sub_length_temp = len(image_tile_dict) / cores
    sub_length = int(sub_length_temp)
    counter = 0
    pointer = 0
    sublists = [[]]
    for key in image_tile_dict:
        if counter > sub_length:
            counter = 0
            pointer = pointer + 1
            sublists.append([])
        output = str(key)+","+str(image_tile_dict[key]).replace("(","").replace(")","").replace("[","").replace("]","")
        sublists[pointer].append(output)
        counter += 1
    return sublists

def __filter_list_for_roi(coords,layer,roi,resize):
    """
    Funktion um Bildkacheln ohne sichtbares Gewebe von der Liste zu bearbeitender Kacheln zu entfernen.
    """
    drop = []
    for key in coords:
        value = coords[key]            
        x = math.floor(value[0]/resize)
        y = math.floor(value[1]/resize)
        width = math.ceil(value[2]/resize)
        height = math.ceil(value[3]/resize)
        widthroi = len(roi[0])
        heightroi = len(roi)
        x = max(0,x)
        y = max(0,y)
        width = min(width,widthroi-x)
        height = min(height,heightroi-y)
        subarray = roi[y:y+height,x:x+width]
        if np.count_nonzero(subarray) == 0:
            drop.append(key)
    for key in drop:
            coords.pop(key)
    return coords

def __export_image_tiles(image,dump_path,pipeline):
    """
    Funktion um ein Bild bezüglich der Parallelisierung zu Kacheln.
    """
    config = Config.load()
    layer = int(config.get(pipeline+"_layer"))
    resize = image.get_width(layer)/image.get_width(3)
    image_tile_coordinates = {}
    width = image.get_width(layer)
    height = image.get_height(layer)
    coords = {}
    x_count = 0
    y_count = 0
    x_value = 0
    y_value = 0
    tile_size = int(config.get("tile_size"))
    overlap = int(config.get("overlap"))
    while (y_value+tile_size)<height:
        while(x_value+tile_size)<width:
            coords[str(layer)+"_"+str(x_count)+"_"+str(y_count)] = (x_value,y_value,tile_size,tile_size)
            x_value = x_value + tile_size - overlap
            x_count = x_count + 1
        coords[str(layer)+"_"+str(x_count)+"_"+str(y_count)] = (x_value,y_value,width-x_value,tile_size)
        x_value = 0
        x_count = 0
        y_count = y_count + 1
        y_value = y_value + tile_size - overlap
    while(x_value+tile_size)<width:
        coords[str(layer)+"_"+str(x_count)+"_"+str(y_count)] = (x_value,y_value,tile_size,height-y_value)
        x_value = x_value + tile_size - overlap
        x_count = x_count + 1
    coords[str(layer)+"_"+str(x_count)+"_"+str(y_count)] = (x_value,y_value,width-x_value,height-y_value)
    roi = ir.detect_roi(image.get_image(layer=3))
    coords = __filter_list_for_roi(coords,layer,roi,resize)
    image_tile_coordinates[layer] = coords
    __drop_dump(image_tile_coordinates[layer],dump_path)


def multiprocess_pipepline(image,pipeline):
    """
    Funktion für den parallelisierten Aufruf einer Pipeline.
    """
    config = Config.load()
    dump_path = config.get("tmp")+"dump/"
    if not os.path.exists(dump_path):
        os.makedirs(dump_path)
    __export_image_tiles(image,dump_path,pipeline)
    p = mp.Pool(processes=int(config.get("cores")))
    pooled_function = partial(process_tiles,dump_path=dump_path,input_path=image.get_file_path(),pipeline=pipeline)
    dump_list = os.listdir(dump_path)
    p.map(pooled_function,dump_list)
    p.close()
    p.join()