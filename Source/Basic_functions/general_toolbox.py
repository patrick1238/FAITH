import sys
from pathlib import Path
import importlib
import inspect
import os
import javabridge as jv
import bioformats as bf
import Source.Objects.Config as Config
import Source.Objects.Datahandler as Datahandler
import Source.Objects.Database as Database
import warnings
import numpy as np
import os
import shutil
from Source.Basic_functions.Faith_multiprocessing import multiprocess_pipepline
from contextlib import contextmanager
import sys, os

@contextmanager
def suppress_stdout():
    """
    Funktion um möglichen Konsolenoutput temporär zu unterdrücken.
    """
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

def clear_tmp_folder():
    """
    Funktion um den temporären digitalen Arbeitsplatz zu räumen.
    """
    config = Config.load()
    for filename in os.listdir(config.get("tmp")):
        file_path = os.path.join(config.get("tmp"), filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def _init_logger():
    """
    Funktion um das Log-Level des Konsolenoutputs zu kontrollieren.
    """
    rootLoggerName = jv.get_static_field("org/slf4j/Logger",
                                         "ROOT_LOGGER_NAME",
                                         "Ljava/lang/String;")

    rootLogger = jv.static_call("org/slf4j/LoggerFactory",
                                "getLogger",
                                "(Ljava/lang/String;)Lorg/slf4j/Logger;",
                                rootLoggerName)

    logLevel = jv.get_static_field("ch/qos/logback/classic/Level",
                                   "WARN",
                                   "Lch/qos/logback/classic/Level;")

    jv.call(rootLogger,
            "setLevel",
            "(Lch/qos/logback/classic/Level;)V",
            logLevel)

def _start_jvm():
    """
    Funktion zum Starten der Java Virtual Machine, für die Verwendung von Bioformats.
    """
    config = Config.load()
    jv.start_vm(class_path=bf.JARS, max_heap_size=config.get("max_heap_size"))
    _init_logger()

def start():
    """
    Funktion zum Starten aller Backgroundprozesse der Software FAITH.
    """
    warnings.filterwarnings("ignore")
    np.seterr(all="ignore")
    clear_tmp_folder()
    Config.load()
    Datahandler.load()
    Database.load()
    _start_jvm()


def stop():
    """
    Funktion zum Stoppen aller Backgroundprozesse der Software FAITH.
    """
    clear_tmp_folder()
    jv.kill_vm()

def identify_main(pipe,import_path = "./Faith/Source/Pipelines/"):
    """
    Funktion zum Auffinden der main Funktion innerhalb eines Skripts.
    """
    spec = importlib.util.spec_from_file_location("pipeline", os.path.abspath(import_path+pipe+".py"))
    pipeline = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = pipeline
    spec.loader.exec_module(pipeline)
    functionList = inspect.getmembers(pipeline,inspect.isfunction)
    for function in functionList:
        if function[0] == "main":
            return function[1]
        
def observe_path_for_existence(path):
    """
    Funktion um Pfade hinsichtlich ihrer Verfügbarkeit zu prüfen.
    """
    file = Path(path)
    if not file.is_dir():
        os.makedirs(path)
    return path

def imageing_pipeline_executor(pipeline,image):
    """
    Funktion zum Ausführen eine Bildverarbeitungspipeline.
    """
    config = Config.load()
    db = Database.load()
    if not db.contains(image.get_image_id(),pipeline):
        if config.get(pipeline+"_multiprocessing") == "False":
            pipe = identify_main(pipeline)
            pipe(image)
        else:
            multiprocess_pipepline(image,pipeline)

def postprocessing_pipeline_exector(cells,imageID,pipeline):
    """
    Funktion zum Ausführen einer Postprocessingpipeline.
    """
    pipe = identify_main(pipeline)
    cells = pipe(cells,imageID)
    return cells

def pipeline_executor(pipeline):
    """
    Funktion zum Ausführen einer Pipeline.
    """
    pipe = identify_main(pipeline)
    pipe()

def reduce_diagnosis(row):
    """
    Funktion um die Diagnose innerhalb einer Pandas.Series auf einen gemeinsamen Nenner zu reduzieren.
    """
    if "LA" in row['Diagnosis'] and not "HL" in row['Diagnosis']:
        return "LA"
    elif "MT" in row['Diagnosis'] or "Misch" in row['Diagnosis']:
        return "HL(MT)"
    elif "NS" in row['Diagnosis']:
        return "HL(NS)"
    else:
        return "delete"

def reduce_to_binary(row):
    """
    Funktion um die Diagnose innerhalb einer Pandas.Series zu binarisieren.
    """
    if "LA" in row['Diagnosis']:
        return "reactive"
    else:
        return "neoplastic"