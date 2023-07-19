# -*- coding: utf-8 -*-
"""
@author: Patrick Wurzel, E-Mail: p.wurzel@bioinformatik.uni-frankfurt.de
"""

from cmath import nan
import Source.Objects.Config as Config
import Source.Objects.Datahandler as DataHandler
import Source.Basic_functions.general_toolbox as gtb
import tqdm
import Source.Objects.Database as Database
import Source.Basic_functions.database_toolbox as dbt

__SCRIPT_NAME = "[Faith]"

if __name__ == '__main__':
    """
    Hauptfunktion des Softwaretools FAITH. Es lädt zunächst die Konfigurationsdatei, die auszuführenden Pipelines,
    und die zu untersuchenden Daten. Anschließend werden alle Pipelines vom Typ Bildanalyse, Graphanalyse und
    Evaluation ausgeführt.
    """
    print(__SCRIPT_NAME + ": Faith started!")
    gtb.start()
    config = Config.load()
    datahandler = DataHandler.load()
    db = Database.load()
    if len(datahandler.get_pipes("Imagingpipes")) > 0:
        print(__SCRIPT_NAME + ": Imageanalysis started")
        datahandler.load_images(config.get("images"))
        for pipeline in datahandler.get_pipes("Imagingpipes"):
            print(__SCRIPT_NAME + ": Starting " + pipeline)
            cases = False
            cells = False
            print(__SCRIPT_NAME + ": " + pipeline + " started.")
            stains = config.get(pipeline+"_stains")
            images_to_analyse = []
            if stains == "all":
                images_to_analyse = datahandler.get_all_images(pipeline)
            else:
                for stain in stains.split(","):
                    images_to_analyse = images_to_analyse + datahandler.get_all_images_with_primary_staining(stain,pipeline)
            for image in tqdm.tqdm(images_to_analyse):
                collect = False
                if config.get(pipeline+"_result_type") == "cell" or config.get(pipeline+"_result_type") == "case":
                    collect = True
                if collect:
                    dbt.get_tmp_workspace(pipeline,image.get_image_id())
                gtb.imageing_pipeline_executor(pipeline,image)
                if collect:
                    result_type = dbt.collect_pipeline_export(pipeline,image.get_image_id())
                    if result_type == "case":
                        cases = True
                    elif result_type == "cell":
                        cells = True
            db.update_database(cases,cells)
    if len(datahandler.get_pipes("Graphpipes")) > 0:
        print(__SCRIPT_NAME + ": Graph analysis started")
        for pipeline in datahandler.get_pipes("Graphpipes"):
            print(__SCRIPT_NAME + ": Starting " + pipeline)
            gtb.pipeline_executor(pipeline)
            db.update_database(cases=True,cells=False)
    if len(datahandler.get_pipes("Evalpipes")) > 0:
        print(__SCRIPT_NAME + ": Evaluation started")
        for pipeline in datahandler.get_pipes("Evalpipes"):
            print(__SCRIPT_NAME + ": Starting " + pipeline)
            gtb.pipeline_executor(pipeline)
    gtb.stop()
    print(__SCRIPT_NAME + ": Mission complete!")