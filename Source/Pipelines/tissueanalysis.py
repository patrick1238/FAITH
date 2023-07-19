#import sys
#sys.path.append("..")
import Source.Imaging_functions.color_deconvolution as cd
import Source.Imaging_functions.identify_roi as ir
import Source.Objects.Config as Config
import Source.Imaging_functions.imaging_toolbox as itb
import Source.Basic_functions.database_toolbox as dbt
import pandas as pd
import matplotlib.pyplot as plt

__SCRIPT_NAME="tissueanalysis"

def main(image):
    config = Config.load()
    faith_image = image.get_image(layer=int(config.get(__SCRIPT_NAME+"_layer")))
    roi = ir.detect_roi(faith_image)
    fuchsin,haem = cd.colour_deconvolution(faith_image,roi)
    proportion = itb.calculate_percentage(fuchsin.get_numpy_array(),roi)
    cur = {"ID":[image.get_case_id()],"Case_ID":[image.get_case_id()],"Diagnosis":[image.get_diagnosis()],image.get_primary_staining()+"_propotion":[proportion]}
    output = pd.DataFrame.from_dict(cur)
    dbt.export(output,image.get_image_id(),__SCRIPT_NAME)