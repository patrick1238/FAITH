#import imageio
import Source.Objects.Config as Config
import Source.Objects.Database as dtb
import numpy as np
import matplotlib.pyplot as plt
import Source.Imaging_functions.identify_roi as ir
import Source.Imaging_functions.imaging_toolbox as it

__SCRIPT_NAME="saveimage"    

def main(image):
    config = Config.load()
    pipe_layer = int(config.get(__SCRIPT_NAME+"_layer"))
    faith_image = image.get_image(layer=pipe_layer)
    nparray = faith_image.get_numpy_array().astype(np.uint8)
    plt.imshow(nparray)
    if config.get(__SCRIPT_NAME + "_print_cells") == "True" or config.get(__SCRIPT_NAME + "_print_edges") == "True" or config.get(__SCRIPT_NAME + "_print_features") == "True":
        initial_layer = int(config.get("celldetection_layer"))
        db = dtb.load()
        df = db.get_cells_dataframe()
        cells = df.loc[df["Image_ID"]==image.get_image_id()]
        if config.get(__SCRIPT_NAME + "_print_cells") == "True":
            ds = it.calculate_downsample(image,initial_layer,pipe_layer)
            x = cells["X"].tolist()
            y = cells["Y"].tolist()
            area = cells["Area"].tolist()
            adapted_x = [i / ds for i in x]
            adapted_y = [i / ds for i in y]
            adapted_area = [max(int(i / np.amax(area)),0.1)  for i in area]
            plt.scatter(adapted_x,adapted_y,marker="o",s=adapted_area,linewidths=0,alpha=float(config.get(__SCRIPT_NAME+"_alpha")),color='green')
            plt.title(image.get_case_id()+"-"+image.get_image_id()+"_"+image.get_primary_staining()+"_"+image.get_diagnosis()+"\n Cell count: " + str(len(cells.index)))   
    plt.savefig(config.get("output")+image.get_case_id()+"-"+image.get_image_id()+"_"+image.get_primary_staining()+"_"+image.get_diagnosis()+"_marked_cells.png",dpi=int(config.get(__SCRIPT_NAME+"_dpi")))
    plt.close()