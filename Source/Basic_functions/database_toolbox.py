from datetime import datetime
import Source.Objects.Config as Config
import Source.Objects.Database as DB
import Source.Basic_functions.general_toolbox as gtb
import pandas as pd
import os
from pandas.api.types import is_object_dtype

def check_dtypes(df):
    """
    Funktion für korrektes Typing der Dataframes.
    """
    strings = ["CaseID","Diagnosis","Case_ID"]
    for column in df.columns:
        if is_object_dtype(df[column]):
            if not column in strings:
                df = df.astype({column: 'float64'})
            else:
                df = df.astype({column: 'category'})
    return df

def add_row_to_dataframe(name,df):
    """
    Funktion um eine Zeile zum Dataframe hinzuzufügen.
    """
    df.append(pd.Series(name=name))
    return df

def add_column_to_dataframe(name,df):
    """
    Funktion um eine neue Spalte in ein Dataframe einzufügen.
    """
    df[name] = None
    return df

def add_case(db,df):
    """
    Funktion um einen Fall in eine Datenbank einzutragen.
    """
    for id,row in df.iterrows():
        case_id = str(row["Case_ID"])
        if not case_id in db.columns:
            db = add_row_to_dataframe(id,db)
        for index, value in row.items():
            if not index == "ID":
                if not index in db.columns:
                    db = add_column_to_dataframe(index,db)
                db.at[case_id,index] = value
    return db

def add_cells(db,df):
    """
    Funktion um einzelne Zellen der Datenbank hinzuzufügen.
    """
    for column in df.columns:
        if not column in db.columns:
            db[column] = None
    db = pd.concat([db,df])
    return db

def export(df,imageID,pipeline):
    """
    Funktion um Ergebnisse Bildweise als gepickeltes Dataframe zu speichern.
    """
    now = datetime.now()
    current_time = now.strftime("%d_%m_%Y_%H_%M_%S_%f")
    config = Config.load()
    if len(df.index) > 0:
        df = df.set_index("ID")
    df.to_pickle(get_tmp_workspace(pipeline,imageID)+imageID+"-"+imageID+"_"+pipeline+"_"+current_time+".pkl")

def get_tmp_workspace(pipeline,imageID):
    """
    Funktion um einen temporären Speicherort für den Programmdurchlauf zu erzeugen.
    """
    config = Config.load()
    tmp_path = config.get("tmp")
    workspace_path = tmp_path + imageID + "/" + pipeline + "/"
    return gtb.observe_path_for_existence(workspace_path)
    

def collect_pipeline_export(pipeline,imageID):
    """
    Funktion um Ergebnisse einer parallelisierten Pipeline zu sammeln und in eine Datenbank einzutragen.
    """
    config = Config.load()
    workspace_path = get_tmp_workspace(pipeline,imageID)
    collector = pd.DataFrame()
    database = DB.load()
    for file in os.listdir(workspace_path):
        path = workspace_path+file
        if os.path.isfile(path):
            df = pd.read_pickle(path)
            if len(df.index) > 0:
                if config.get(pipeline+"_result_type") == "case":
                    collector = add_case(collector,df)
                elif config.get(pipeline+"_result_type") == "cell":
                    collector = add_cells(collector,df)
                else:
                    ("[Database toolbox]: Script not found: " +file.split("_")[1])
            os.remove(workspace_path+file)
    if config.get(pipeline+"_pipeline_type") == "image_processing":
        if not config.get(pipeline+"_postprocessing") == "empty":
            for postpipe in config.get(pipeline+"_postprocessing").split(","):
                collector = gtb.postprocessing_pipeline_exector(collector,imageID,postpipe)
    collector.to_pickle(config.get("image_result_storage")+imageID+"_"+pipeline+"-"+config.get(pipeline+"_version")+".pkl")
    database.update_analysed_images(pipeline,imageID)
    return config.get(pipeline+"_result_type")

def filter_df(df):
    """
    Funktion um ein Dataframe auf Basis einer manuellen Annotation zu filtern.
    """
    config = Config.load()
    annotation_df = pd.read_excel(config.get("annotation")+"Annotation_cases.xlsx",engine="openpyxl")
    accepted = annotation_df.loc[annotation_df["Accepted"]=="Yes"]
    accepted_df = pd.DataFrame()
    df = df.astype({"Case_ID": 'string'})
    accepted = accepted.astype({"CaseID": 'string'})
    for caseid in accepted["CaseID"]:
        cur_df = df.loc[df["Case_ID"] == caseid]
        if accepted_df.empty:
            accepted_df = cur_df
        else:
            accepted_df = pd.concat([accepted_df,cur_df])
    return accepted_df