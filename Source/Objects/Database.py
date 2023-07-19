import pandas as pd
import Source.Objects.Config as Config
import os
import Source.Basic_functions.database_toolbox as dtb
import numpy as np
from copy import deepcopy
import Source.Basic_functions.general_toolbox as gtb

database = None

def load():
    """
    Funktion um ein Objekt des Typs Database nach dem Singletonprinzip zu laden.
    """
    global database
    if database == None:
        database = Database()
    return database

class Database():
    """
    Objekt zur Speicherung der Bildinformationen.
    """
    per_case = pd.DataFrame()
    per_cell = pd.DataFrame()
    analysed_images = None

    def __init__(self):
        config = Config.load()
        analysed_images_tmp = {"Run ID":[],"Plugin Version":[],"Plugin ID":[],"Image ID":[]}
        runid = 0
        for file in os.listdir(config.get("image_result_storage")):
            splitted = file.replace(".pkl","").split("_")
            imageid = splitted[0]
            pid = splitted[1].split("-")[0]
            pv = splitted[1].split("-")[1]
            analysed_images_tmp["Run ID"].append(runid)
            analysed_images_tmp["Plugin Version"].append(pv)
            analysed_images_tmp["Plugin ID"].append(pid)
            analysed_images_tmp["Image ID"].append(imageid)
            runid += 1
        self.analysed_images = pd.DataFrame.from_dict(analysed_images_tmp)
        self.analysed_images.set_index("Run ID")

    def load_cases(self):
        """
        Funktion um bereits berechnete Fälle zu laden.
        """
        config = Config.load()
        for file in os.listdir(config.get("image_result_storage")):
            pipeline = file.replace(".pkl","").split("_")[1].split("-")[0]
            if config.get(pipeline+"_result_type") == "case":
                cur = pd.read_pickle(config.get("image_result_storage")+file)
                self.add_case(cur)

    def load_cells(self):
        """
        Funktion um bereits berechnete Zellen zu laden.
        """
        self.per_cell = pd.DataFrame()
        config = Config.load()
        folder_path = config.get("image_result_storage")
        for file in os.listdir(folder_path):
            if file.endswith(".pkl"):
                pipeline = file.replace(".pkl","").split("_")[1].split("-")[0]
                if config.get(pipeline+"_result_type") == "cell":
                    cur = pd.read_pickle(folder_path+file)
                    self.add_cells(cur)
                
    def add_case(self,df):
        """
        Funktion um einen Falle der Datenbank hinzuzufügen.
        """
        self.per_case = dtb.add_case(self.per_case,df)

    def add_cells(self,df):
        """
        Funktion um Zellen eines Bildes der Datenbank hinzuzufügen.
        """
        self.per_cell = dtb.add_cells(self.per_cell,df)

    def contains(self,imageID,pipeline):
        """
        Funktion zur Abfrage ob ein bestimmtes Bild bereits mit der gewählten Pipeline analysiert wurde.
        """
        contain = False
        config = Config.load()
        if imageID in list(self.analysed_images["Image ID"].values):
            plugins = self.analysed_images.loc[self.analysed_images["Image ID"] == imageID]
            if pipeline in list(plugins["Plugin ID"].values):
                versions = plugins.loc[plugins["Plugin ID"] == pipeline]
                version = int(list(versions["Plugin Version"].values)[0])
                if int(config.get(pipeline+"_version")) <= version:
                    contain = True
                else:
                    self.analysed_images.drop(versions.index[0],inplace=True)
        return contain

    def update_analysed_images(self,pipeline,imageID):
        """
        Funktion um die interne Datenbank gespeicherter Bilder upzudaten.
        """
        config = Config.load()
        cur = {"Run ID":[],"Plugin Version":[],"Plugin ID":[],"Image ID":[]}
        runID = 0
        if len(self.analysed_images.index) > 0:
            runID = np.amax(np.array(list(self.analysed_images.index)).astype(int))+1
        cur["Run ID"].append(runID)
        cur["Plugin Version"].append(config.get(pipeline+"_version"))
        cur["Plugin ID"].append(pipeline)
        cur["Image ID"].append(imageID)
        runID = runID + 1
        cur_df = pd.DataFrame.from_dict(cur)
        cur_df = cur_df.set_index("Run ID")
        self.analysed_images = pd.concat([cur_df,self.analysed_images])

    def update_database(self,cases=True,cells=True):
        """
        Funktion um die Datenbank neu zu laden.
        """
        if cells:
            self.load_cells()
        if cases:
            self.load_cases()

    def get_database_dataframe(self,filter=True,reduced_diagnosis=True,binary_diagnosis=False):
        """
        Funktion um die gespeicherten Fälle abzufragen.
        """
        if len(self.per_case.index)==0:
            self.load_cases()
        return_df = deepcopy(self.per_case)
        if filter:
            return_df = dtb.filter_df(return_df)
        if reduced_diagnosis:
            return_df["Diagnosis"] = return_df.apply(lambda row: gtb.reduce_diagnosis(row), axis=1)
            return_df = return_df.drop(return_df[return_df["Diagnosis"]=="delete"].index)
        if binary_diagnosis:
            return_df["Diagnosis"] = return_df.apply(lambda row: gtb.reduce_to_binary(row), axis=1)
            return_df = return_df.drop(return_df[return_df["Diagnosis"]=="delete"].index)
        return dtb.check_dtypes(return_df)

    def get_cells_dataframe(self,filter=False):
         """
        Funktion um die gespeicherten Zellen abzufragen.
        """
        if len(self.per_cell.index)==0:
            self.load_cells()
        return_df = deepcopy(self.per_cell)
        if filter:
            return_df = dtb.filter_df(return_df)
        return dtb.check_dtypes(return_df)