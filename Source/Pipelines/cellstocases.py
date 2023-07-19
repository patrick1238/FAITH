import Source.Basic_functions.database_toolbox as dbt
import pandas as pd
from pandas.api.types import is_numeric_dtype
import Source.Imaging_functions.identify_roi as ir
import Source.Objects.Config as Config
import Source.Objects.Datahandler as DH
import Source.Imaging_functions.imaging_toolbox as itb
import numpy as np


__SCRIPT_NAME = "cellstocases"

def roi_size(imageID):
    config = Config.load()
    handler = DH.load()
    image = handler.get_image_by_id(imageID)
    faith_image = image.get_image(layer=3)
    rf = itb.calculate_downsample(image,int(config.get("celldetection_layer")),3)
    roi = ir.detect_roi(faith_image)
    return (rf**2) * np.count_nonzero(roi)
    

def main(cells,imageID):
    cells["Area"] = pd.to_numeric(cells["Area"])
    case = cells.Case_ID.unique()[0]
    diagnosis = cells.Diagnosis.unique()[0]
    output_dict = {"ID":[case],"Case_ID":[case],"Diagnosis":[diagnosis],"Cell count":[len(cells.index)],"Cell density":[len(cells.index)/roi_size(imageID)]}
    for column in cells.columns:
        if is_numeric_dtype(cells[column]) and not column == "X" and not column == "Y":
            if not column in output_dict:
                output_dict[column] = []
            output_dict[column].append(cells[column].median())
    dbt.get_tmp_workspace(__SCRIPT_NAME,imageID)
    dbt.export(pd.DataFrame.from_dict(output_dict),imageID,__SCRIPT_NAME)
    dbt.collect_pipeline_export(__SCRIPT_NAME,imageID)
    return cells