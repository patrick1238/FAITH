# -*- coding: utf-8 -*-
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
def warn(*args, **kwargs):
    pass
warnings.warn = warn
import numpy as np
import sys
import os
sys.path.append(os.getcwd()+"/Faith/")
import javabridge as jv
import argparse as ap
import Source.Basic_functions.general_toolbox as gtb
import Source.Basic_functions.parser as parser
import Source.Objects.Config as Config
import warnings

def __parse_csv_to_sublist(dump_path):
    """
    Funktion um die exportierten CSV-Dateien, welche die zu verarbeitenden Kachelkoordinaten enthalten, zu laden.
    """
    image_class_sub_list = {}
    f = open(dump_path)
    for line in f:
        line = line.strip("\n").replace(" ","")
        temp_list     = line.split(",")
        tile_id = temp_list[0]
        x_coord        = int(temp_list[1])
        y_coord        = int(temp_list[2])
        width = int(temp_list[3])
        height = int(temp_list[4])
        image_class_sub_list[tile_id] = (x_coord,y_coord,width,height)
    return image_class_sub_list

def __execute_pipeline(image_class_sub_list,input_path,pipeline):
    """
    Funktion um eine Pipeline auszuführen.
    """
    config = Config.load()
    wsi_object = parser.parse_image(input_path).access()
    for tile in image_class_sub_list:
        coordinates_tuple     = image_class_sub_list[tile]
        layer = int(config.get(pipeline+"_layer"))
        cur_tile = wsi_object.get_image(coordinates_tuple[0], coordinates_tuple[1], coordinates_tuple[2], coordinates_tuple[3], layer)
        prepipe_main = gtb.identify_main(pipeline)
        prepipe_main(cur_tile)

parser_new = ap.ArgumentParser()
parser_new.add_argument("-dump", "--dump_path", help="enter path for csv_path", type=str, default=None)
parser_new.add_argument("-i", "--input_path", help="enter input_path to image file", type=str, default=None)
parser_new.add_argument("-pipe", "--pipeline", help="enter pipeline name", type=str, default=None)
args = parser_new.parse_args()
warnings.filterwarnings("ignore", category=DeprecationWarning) 
input_path = args.input_path
dump_path = args.dump_path
pipeline = args.pipeline
gtb._start_jvm()
image_class_sub_list = __parse_csv_to_sublist(dump_path)
os.remove(dump_path)
__execute_pipeline(image_class_sub_list,input_path,pipeline)
jv.kill_vm()






    

