# -*- coding: utf-8 -*-
"""
@author: Patrick Wurzel, E-Mail: p.wurzel@bioinformatik.uni-frankfurt.de
"""

import Source.Objects.Config as Config
import Source.Objects.Faith_image as Faith_image
import os

def parse_image(input_path):
    """
    Funktion um den Dateinamen nach dem DTMS Schema zu parsen.
    """
    config = Config.load()
    head, tail = os.path.split(input_path)
    splitted = tail.split("_")
    case_id = splitted[0].split("-")[0]
    image_id = splitted[0].split("-")[1]
    diagnosis = splitted[2].split(".")[0]
    stains = splitted[1].split("-")
    primary_staining = ""
    secondary_staining = ""
    tertiary_staining = ""
    if(len(stains)==1):
        primary_staining = stains[0]
    if(len(stains)==2):
        tertiary_staining = stains[0]
        primary_staining = stains[1]
    if(len(stains)==3):
        tertiary_staining = stains[0]
        secondary_staining = stains[1]
        primary_staining = stains[2]
    image = Faith_image.Faith_image(case_id,image_id,diagnosis,primary_staining,secondary_staining,tertiary_staining,input_path)
    return image