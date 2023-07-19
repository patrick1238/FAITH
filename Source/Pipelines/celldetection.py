import Source.Imaging_functions.color_deconvolution as cd
import Source.Objects.Config as Config
import pandas as pd
import skimage.measure as mes
import scipy.ndimage as ndi
import Source.Basic_functions.database_toolbox as dbt
import numpy as np


__SCRIPT_ID="celldetection"

def measure_objects(segmented, intensity_image, num_labels=0, im_coords=[0, 0], current_name='', lower_thres=700, upper_thres=7000):
    labeled, num_features = ndi.measurements.label(segmented)
    measures = mes.regionprops(labeled,intensity_image=intensity_image)
    border_labels = get_border_object_labels(labeled)
    cells = {"Cell_ID":[],"X":[],"Y":[],"Area":[],"Orientation":[],"Circumference":[],"Perimeter":[],"Roundness":[],"Eccentricity":[],"Solidity":[],"Majoraxislength":[],"Intensity_mean":[]}
    cell_id = 0
    for mes_object in measures:
        if (mes_object.filled_area >= lower_thres)  and (not mes_object.label in border_labels) and (mes_object.filled_area <= upper_thres):
            new_x = mes_object.centroid[1] + im_coords[0]
            new_y = mes_object.centroid[0] + im_coords[1]
            cells["Cell_ID"].append(cell_id)
            cells["X"].append(new_x)
            cells["Y"].append(new_y)
            cells["Area"].append(mes_object.filled_area)
            cells["Orientation"].append(mes_object.orientation)
            cells["Circumference"].append(np.sum(ndi.morphology.distance_transform_edt(mes_object.filled_image) == 1))
            cells["Perimeter"].append(mes_object.perimeter)
            cells["Roundness"].append(4 * np.pi * mes_object.filled_area / (np.sum(ndi.morphology.distance_transform_edt(mes_object.filled_image) == 1) ** 2))
            cells["Eccentricity"].append(mes_object.eccentricity)
            cells["Solidity"].append(mes_object.solidity)
            cells["Majoraxislength"].append(mes_object.major_axis_length)
            cells["Intensity_mean"].append(mes_object.intensity_mean)
            cell_id = cell_id + 1
    return pd.DataFrame.from_dict(cells)
        
def get_border_object_labels(labeled):
    lower = np.unique(labeled[labeled.shape[0] - 1, :])
    if (0 in lower):
        lower = lower[1:]
    upper = np.unique(labeled[0, :])
    if (0 in upper):
        upper = upper[1:]
    left = np.unique(labeled[:, 0])
    if (0 in left):
        left = left[1:]
    right = np.unique(labeled[:, labeled.shape[1] - 1])
    if (0 in right):
        right = right[1:]
    whole = np.concatenate((lower, upper, left, right))
    return whole  

def segment_cv(primary):
    np_array = primary.get_numpy_array()
    binarized = 1.0 * (np_array > 0)
    return ndi.binary_fill_holes(ndi.binary_erosion(ndi.binary_dilation(binarized, iterations=5),iterations=5)).astype(int)



def main(image):
    config = Config.load()
    prim,hem = cd.colour_deconvolution(image)
    segmented = segment_cv(prim)
    cellsizes = config.get(image.get_primary_staining()+"_cellsize").split("-")
    objects = measure_objects(segmented, prim.get_numpy_array(), im_coords=[prim.get_global_x(), prim.get_global_y()],lower_thres=int(cellsizes[0]),upper_thres=int(cellsizes[1]))
    if len(objects.index) > 0:
        objects['Case_ID']=image.get_case_id()
        objects['Image_ID']=image.get_image_id()
        objects['Diagnosis']=image.get_diagnosis()
        objects["Staining"]=image.get_primary_staining()
        objects['ID']=objects['Case_ID'].astype(str)+"-"+objects['Image_ID'].astype(str)+"_"+str(image.get_global_x())+"-"+str(image.get_global_y())+"_"+objects["Cell_ID"].astype(str)
        objects.drop("Cell_ID", axis=1, inplace=True)
        dbt.export(objects,image.get_image_id(),__SCRIPT_ID)
    cd30 = None
    hem = None