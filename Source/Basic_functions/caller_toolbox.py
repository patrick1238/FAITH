import os

def process_tiles(path,dump_path,input_path,pipeline):
    """
    Funktion für den Konsolenaufruf des Skripts "multiprocessed_pipeline_caller.py". Dies dient der Paralellisierung einzelner Pipelines.
    """
    call = "python -W ignore::DeprecationWarning ./Faith/Source/Basic_functions/multiprocessed_pipeline_caller.py -dump \"" +dump_path+path + "\" -i \""+input_path+"\" -pipe " + pipeline
    os.system(call)