import Source.Imaging_functions.color_deconvolution as cd
import Source.Imaging_functions.identify_roi as ir
import Source.Objects.Config as Config
import Source.Basic_functions.database_toolbox as dbt
import pandas as pd
import numpy as np
import mahotas
import math
import gc
from scipy import ndimage
from Source.Imaging_functions.imaging_toolbox import contrast_enhancement
from scipy.spatial import ConvexHull
import skimage.measure as mes

__SCRIPT_NAME="follicledetection"

row = 10 #Width of the row for the mean calculation
iterations = 20 #Shockfilter iterations
white_threshold = 175 #Minimum intensity inside a germinal center
sigma_value = 4 #Sigma value for the gaussian filter
kernel_size = 8 #Kernel size for the closing operation
lower_boundary = 15 #Smallest part width or height of a germinal center in pixel, which will be accepted within the edge detection
upper_boundary = 200 #Biggest width or height of a germinal center in pixel, which will be accepted within the edge detection
form_factor_threshold = 0.71
minimum_area = 340 #Minimum area of a lymphoid follicle
maximum_area = 42000 #Maximum area of a lymphoid follicle

def cross(first,second):
    if(first[0][0]==first[1][0]):
        pair1 = first
        pair2 = second
    else:
        pair1 = second
        pair2 = first
    x = pair2[0][1]
    y = pair1[0][0]
    if(x >= pair1[0][1] and x <= pair1[1][1] and y >= pair2[0][0] and y <= pair2[1][0]):
        return True
    else:
        return False

def check_follicle(array,pair):
    inside = False
    for i in range(0,len(array),2):
        test = cross(pair,(array[i],array[i+1]))
        if(test == True):
            inside = True
            break
    return inside

def collect_edges(array):
    collected = [[],[]]
    collector = 1
    collected[0].append(array[0][0])
    collected[0].append(array[0][1])
    del array[0][0]
    del array[0][0]
    save = []
    while(collector>0):
        collector = 0
        for y in range(0,len(array[1]),2):
            test = check_follicle(collected[0],(array[1][y],array[1][y+1]))
            if(test == True):
                collector += 1
                collected[1].append(array[1][y])
                collected[1].append(array[1][y+1])
                save.append(array[1][y])
                save.append(array[1][y+1])
        while(len(save)>0):
            array[1].remove(save.pop())
        collector = 0
        for x in range(0,len(array[0]),2):
            test = check_follicle(collected[1],(array[0][x],array[0][x+1]))
            if(test == True):
                collector += 1
                collected[0].append(array[0][x])
                collected[0].append(array[0][x+1])
                save.append(array[0][x])
                save.append(array[0][x+1])
        while(len(save)>0):
            array[0].remove(save.pop())
    return (collected,array)

def follicle_separation(array):
    collected = []
    while(len(array[0])>0 and len(array[1])>0):
        tmp = collect_edges(array)
        array = tmp[1]
        collected.append(tmp[0])
    return collected

def mean_x(x,y,image,row):
    meanVal = 0
    count   = 1
    for i in range(y,y+row):
        meanVal  = meanVal+(image[i,x]-meanVal)/count
        count+=1
    return meanVal

def mean_y(x,y,image,row):
    meanVal = 0
    count   = 1
    for i in range(x,x+row):
        meanVal  = meanVal+(image[y,i]-meanVal)/count
        count+=1
    return meanVal

def create_horizontal_meanvalues(image):
    xPlot = []
    counter = 0
    for y in range (0,image.shape[0]-row,int(row/2)):
       xPlot.append([])
       for x in range (0,image.shape[1],1):
           xPlot[counter].append(mean_x(x,y,image,row))
       counter += 1
    return xPlot

def create_vertical_meanvalues(image):
    yPlot = []
    counter = 0
    for x in range (0,image.shape[1]-row,(row//2)):
       yPlot.append([])
       for y in range (0,image.shape[0],1):
           yPlot[counter].append(mean_y(x,y,image,row))
       counter += 1
    return yPlot

def shock_filter(curve): 
    for i in range(iterations):
        cur_old_l =  curve[0]
        cur_old   =  curve[0]
        cur_old_r =  curve[1]
        for i in range(1,len(curve)-1): 
            cur_old_l = cur_old
            cur_old = cur_old_r
            cur_old_r = curve[i+1]
            delta = cur_old_r - 2 *cur_old + cur_old_l
            delta_left = cur_old-cur_old_l
            delta_right = cur_old_r-cur_old            
            nabla = min(np.abs(delta_left),np.abs(delta_right))*((np.sign(delta_left)+np.sign(delta_right))/2)
            nabla=-np.sign(delta)*np.abs(nabla)
            curve[i]= curve[i]+nabla
    return curve

def collect_intensity_jumps(horizontal_values,vertical_values): 
    k = 0
    points = []
    for i in range(len(horizontal_values)):
        k = 0
        while(k < len(horizontal_values[i])-1):
            jump = math.fabs(horizontal_values[i][k+1]-horizontal_values[i][k])
            if(jump>2):                    
                points.append(jump)
            k += 1
    for i in range(len(vertical_values)): 
        k = 0
        while(k < len(vertical_values[i])-1): 
            jump = math.fabs(vertical_values[i][k+1]-vertical_values[i][k])
            if(jump>2):                    
                points.append(jump)
            k += 1
    return points

def calculate_auto_intensity_threshold(horizontal_values,vertical_values):
    points = collect_intensity_jumps(horizontal_values,vertical_values)
    lower_quartile = np.percentile(np.array(points),25)
    upper_quartile = np.percentile(np.array(points),75)
    iqr = upper_quartile - lower_quartile
    threshold = upper_quartile + 1.5 * iqr
    return threshold

def edge_detection(horizontal_values, vertical_values, roi, jump_threshold): 
    possible_edges = [[],[]]
    k = 0
    gap = 0
    for i in range(len(horizontal_values)): 
        k = 0
        while(k < len(horizontal_values[i])-1):
            curCoords = (int(max(i*row/2+5,0)),int(k))
            if(roi[curCoords]!=0):
                gap = 0
                if(horizontal_values[i][k+1]-horizontal_values[i][k]>jump_threshold):
                    observer = True
                    save = k
                    k+=1
                    while(np.abs(horizontal_values[i][k]-horizontal_values[i][k+1])<jump_threshold and k < len(horizontal_values[i])-2):
                        curCoords = (int(max(i*row/2+5,0)),int(k))
                        if(horizontal_values[i][k] > white_threshold and horizontal_values[i][k+1]> white_threshold and roi[curCoords]!=0):
                            k += 1
                            gap += 1
                        else:
                            k+=1
                            observer = False
                            gap += 1
                    if(gap > lower_boundary and gap < upper_boundary and observer == True): 
                        possible_edges[0].append((max(i*row/2+5,0),save))
                        possible_edges[0].append((max(i*row/2+5,0),k))
                else: 
                    k += 1
            else:
                k+=1
    for i in range(len(vertical_values)): 
        k = 0
        while(k < len(vertical_values[i])-1):
            if(roi[k,(max(i*row//2+5,0))]!=0):
                gap = 0
                if(vertical_values[i][k+1]-vertical_values[i][k]>jump_threshold):
                    observer = True
                    save = k
                    k+=1
                    while(np.abs(vertical_values[i][k]-vertical_values[i][k+1])<jump_threshold and (k < len(vertical_values[i])-2)):
                        curCoords = (int(k),int(max(i*row/2+5,0)))
                        if((vertical_values[i][k] > white_threshold and vertical_values[i][k+1]> white_threshold) and roi[curCoords]!=0):
                            k += 1
                            gap += 1
                        else:
                            k+= 1
                            observer = False
                            gap += 1
                    if(gap > lower_boundary and gap < upper_boundary and observer == True): 
                        possible_edges[1].append((save,(max(i*row/2+5,0))))
                        possible_edges[1].append((k,(max(i*row/2+5,0))))
                else: 
                    k += 1
            else:
                k+=1
    return possible_edges

def merge_list(array):
    merged = []
    it = 0
    for i in array:
        merged.append([])
        for k in i:
            for l in k:
                merged[it].append(l)
        it += 1
    return merged

def convert_points(edges):
    output = []
    for i in edges:
        tmp = []
        for k in i:
            tmp2 = []
            tmp2.append(float(k[0]))
            tmp2.append(float(k[1]))
            tmp.append(tmp2)
        output.append(np.array(tmp))
    return output

def collect_and_reconvert(hull,edges,follicle_id):
    collector = []
    for i in hull.vertices:
        collector.append((int(edges[follicle_id][i][0]),int(edges[follicle_id][i][1])))
    return collector

def get_convex_hull(edges):
    min_set = []
    edges = convert_points(edges)
    it = 0
    for i in edges: 
        if(len(i)>4): 
            hull = ConvexHull(i)
            formFactor = (4*math.pi*hull.volume)/(hull.area**2)
            if(formFactor >= form_factor_threshold and hull.volume < maximum_area and hull.volume > minimum_area):                
                qhull = collect_and_reconvert(hull,edges,it)
                min_set.append(qhull)
        it += 1
    return min_set

def create_mask(edges,image): 
    mask = np.zeros(image.shape)
    for hull in edges: 
        mahotas.polygon.fill_polygon(hull,image)
        mahotas.polygon.fill_polygon(hull,mask)
    return mask

def preprocess(image):
    nparray = image.get_numpy_array()
    nparray = np.array(ndimage.gaussian_filter(nparray, sigma=sigma_value))
    nparray = contrast_enhancement(nparray)
    nparray = ndimage.grey_closing(nparray, size=(kernel_size,kernel_size))
    nparray = np.array(nparray.astype('uint8'))
    image.set_numpy_array(nparray)
    return image

def measure_objects(segmented):
    labeled, num_features = ndimage.measurements.label(segmented)
    measures = mes.regionprops(labeled)
    cells = {"Cell_ID":[],"X":[],"Y":[],"Area":[],"Orientation":[],"Circumference":[],"Perimeter":[],"Roundness":[],"Eccentricity":[],"Solidity":[],"Majoraxislength":[],"Intensity_mean":[]}
    cell_id = 0
    for mes_object in measures:
        cells["Area"].append(mes_object.filled_area)
        cells["Orientation"].append(mes_object.orientation)
        cells["Circumference"].append(np.sum(ndimage.morphology.distance_transform_edt(mes_object.filled_image) == 1))
        cells["Perimeter"].append(mes_object.perimeter)
        cells["Roundness"].append(4 * np.pi * mes_object.filled_area / (np.sum(ndimage.morphology.distance_transform_edt(mes_object.filled_image) == 1) ** 2))
        cells["Eccentricity"].append(mes_object.eccentricity)
        cells["Solidity"].append(mes_object.solidity)
        cells["Majoraxislength"].append(mes_object.major_axis_length)
        cell_id = cell_id + 1
    output = {}
    for feature in cells:
        output["Median_follicle_"+feature] = np.median(cells[feature])
    return output

def main(image):
    config = Config.load()
    faith_image = image.get_image(layer=int(config.get(__SCRIPT_NAME+"_layer")))
    roi = ir.detect_roi(faith_image)
    actin,haem = cd.colour_deconvolution(faith_image,roi,"Actin")
    actin = preprocess(actin)
    horizontal_values = create_horizontal_meanvalues(actin.get_numpy_array())
    vertical_values = create_vertical_meanvalues(actin.get_numpy_array())
    horizontal_values_flattened = []
    vertical_values_flattened = []
    for curve in horizontal_values:
        horizontal_values_flattened.append(shock_filter(curve))
    for curve in vertical_values:
        vertical_values_flattened.append(shock_filter(curve))
    jump_threshold = calculate_auto_intensity_threshold(horizontal_values_flattened,vertical_values_flattened)
    possible_edges = edge_detection(horizontal_values_flattened, vertical_values_flattened, roi, jump_threshold)
    possible_edges = follicle_separation(possible_edges)
    possible_edges = merge_list(possible_edges)
    edges = get_convex_hull(possible_edges)
    fldetect_mask = create_mask(edges,actin.get_numpy_array())
    result_dict = measure_objects(fldetect_mask)
    cur = {"ID":[image.get_case_id()],"Case_ID":[image.get_case_id()],"Diagnosis":[image.get_diagnosis()]}
    for feature in result_dict:
        cur[feature] =result_dict[feature]
    output = pd.DataFrame.from_dict(cur)
    dbt.export(output,image.get_image_id(),__SCRIPT_NAME)