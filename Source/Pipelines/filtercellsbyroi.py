import Source.Imaging_functions.identify_roi as ir
import Source.Objects.Config as Config
import Source.Objects.Datahandler as DH
import Source.Imaging_functions.imaging_toolbox as itb

__SCRIPT_NAME="filtercellsbyroi"

def is_in_roi(point,roi):
    inside = False
    if roi[int(point[2]),int(point[1])] == 1:
        inside = True
    return inside

def main(cells,imageID):
    config = Config.load()
    handler = DH.load()
    image = handler.get_image_by_id(imageID)
    faith_image = image.get_image(layer=int(config.get(__SCRIPT_NAME+"_layer")))
    rf = itb.calculate_downsample(image,int(config.get("celldetection_layer")),int(config.get(__SCRIPT_NAME+"_layer")))
    roi = ir.detect_roi(faith_image)
    for point in zip(cells.index,cells["X"]/rf,cells["Y"]/rf):
        if not is_in_roi(point,roi):
            cells = cells.drop(point[0])
    roi = None
    return cells