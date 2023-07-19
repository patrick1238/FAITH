# -*- coding: utf-8 -*-
"""
@author: Patrick Wurzel, E-Mail: p.wurzel@bioinformatik.uni-frankfurt.de
"""

import os
import Source.Basic_functions.parser as parser
import Source.Objects.Database as DB
import Source.Objects.Config as Config
import pandas as pd

datahandler = None

def load():
    """
    Funktion um ein Objekt des Typs datahandler nach dem Singletonprinzip zu laden.
    """
    global datahandler
    if datahandler == None:
        datahandler = Datahandler()
    return datahandler

class Datahandler():
    """
    Objekt zur Verwaltung des Speicherns und Ladens der zu analysierenden Bilder, Pipelines und bereits analysierten Bilder.
    """

    __images_by_staining = None
    __images_by_id = None
    __pipes = None

    def __init__(self):
        self.__pipes = {}
        config = Config.load()
        self.__pipes["Imagingpipes"] = []
        for pipeline in config.get("image_analysis_pipelines").split(","):
            if pipeline in config.get("available_pipelines").split(","):
                self.__pipes["Imagingpipes"].append(pipeline)
        self.__pipes["Graphpipes"] = []
        for pipeline in config.get("graph_analysis_pipelines").split(","):
            if pipeline in config.get("available_pipelines").split(","):
                self.__pipes["Graphpipes"].append(pipeline)
        self.__pipes["Evalpipes"] = []
        for pipeline in config.get("evaluation_pipelines").split(","):
            if pipeline in config.get("available_pipelines").split(","):
                self.__pipes["Evalpipes"].append(pipeline)
        if config.get("input_type") == "excel":
            self.load_excel(config.get("input"))
        elif config.get("input_type") == "wsi_single":
            image = parser.parse_image(config.get("input"))
            if not image.get_primary_staining() in self.__images_by_staining:
                self.__images_by_staining[image.get_primary_staining()] = []
            self.__images_by_staining[image.get_primary_staining()].append(image)
            self.__images_by_id[image.get_image_id()] = image
        elif config.get("input_type") == "wsi_folder":
            self.load_images(config.get("input"))
        elif config.get("input_type") == "database":
            pass

    def get_pipes(self,pipeids):
        """
        Funktion um die auszuführenden Pipelines abzufragen.
        """
        return self.__pipes[pipeids]

    def load_excel(self,inputpath):
        """
        Funktion um eine Exzeldatei als Database Objekt zu laden.
        """
        df = pd.read_excel(inputpath,engine="openpyxl")
        db = DB.load()
        for index in df.index:
            db.add_case(df.iloc[[index]])
        
    def load_images(self,inputpath):
        """
        Funktion um alle zu analysierenden Bilder zu laden.
        """
        print("[DataHandler]: Loading all images in " + inputpath)
        self.__images_by_staining = {}
        self.__images_by_id = {}
        for subdir, dirs, files in os.walk(inputpath):
            for file in files:
                image = parser.parse_image(os.path.join(subdir, file))
                if not image.get_primary_staining() in self.__images_by_staining:
                    self.__images_by_staining[image.get_primary_staining()] = []
                self.__images_by_staining[image.get_primary_staining()].append(image)
                self.__images_by_id[image.get_image_id()] = image
        print("[DataHandler]: " + str(len(self.__images_by_id.keys())) + " image(s) loaded!")

    def get_image_by_id(self,imageID):
        """
        Funktion um einzelne Bilder mit einer bestimmten ImageID zu laden.
        """
        return self.__images_by_id[imageID].access()

    def get_all_images(self,pipeline="empty"):
        """
        Funktion um alle Bilder zu laden.
        """
        database = DB.load()
        output = []
        for image in self.__images_by_id.values():
            if not database.contains(imageID=image.get_image_id(),pipeline=pipeline):
                output.append(image.access())
        return output

    def get_all_images_with_primary_staining(self,primary_staining,pipeline="empty"):
        """
        Funktion um alle Bilder mit einer bestimmten Primärfärbung zu laden.
        """
        database = DB.load()
        output = []
        if primary_staining in self.__images_by_staining:
            for image in self.__images_by_staining[primary_staining]:
                if not database.contains(imageID=image.get_image_id(),pipeline=pipeline):
                    output.append(image.access())
        return output

    