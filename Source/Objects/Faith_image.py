# -*- coding: utf-8 -*-
"""
@author: Patrick Wurzel, E-Mail: p.wurzel@bioinformatik.uni-frankfurt.de
""" 

from pathlib import Path
import bioformats as bf
import numpy as np
from PIL import Image

class Faith_image():
    """
    Zu verarbeitendes Bildobjekt. Dieses Objekt enthält lediglich die im Dateipfad kodierten Bildinformationen, jedoch nicht die Pixelinformationen.
    """

    __case_id = None
    __image_id = None
    __diagnosis = None
    __primary_staining = None
    __secondary_staining = None
    __tertiary_staining = None
    __file_path = None

    def __init__(self, case_id, image_id, diagnosis, primary_staining, secondary_staining, tertiary_staining, file_path):
        self.__case_id = case_id
        self.__image_id = image_id
        self.__diagnosis = diagnosis
        self.__primary_staining = primary_staining
        self.__secondary_staining = secondary_staining
        self.__tertiary_staining = tertiary_staining
        self.__file_path = file_path

    def get_case_id(self):
        """
        Funktion um die Fall ID des Bildes abzufragen.
        """
        return self.__case_id

    def set_case_id(self,case_id):
        """
        Funktion um die Fall ID des Bildes zu ändern.
        """
        self.__case_id = case_id

    def get_image_id(self):
        """
        Funktion um die Bild ID des Bildes abzufragen.
        """
        return self.__image_id

    def set_image_id(self,image_id):
        """
        Funktion um die Bild ID des Bildes zu ändern.
        """
        self.__image_id = image_id

    def get_diagnosis(self):
        """
        Funktion um die Diagnose des Bildes abzufragen.
        """
        return self.__diagnosis

    def set_diagnosis(self,diagnosis):
        """
        Funktion um die Diagnose des Bildes zu ändern.
        """
        self.__diagnosis = diagnosis

    def get_primary_staining(self):
        """
        Funktion um die Primärfärbung des Bildes abzufragen.
        """
        return self.__primary_staining

    def get_secondary_staining(self):
        """
        Funktion um die Sekundärfärbung des Bildes abzufragen.
        """
        return self.__secondary_staining

    def get_tertiary_staining(self):
        """
        Funktion um die Tertiärfärbung des Bildes abzufragen.
        """
        return self.__tertiary_staining

    def set_primary_staining(self,primary_staining):
        """
        Funktion um die Primärfärbung des Bildes ab zu ändern.
        """
        self.__primary_staining = primary_staining

    def set_secondary_staining(self,secondary_staining):
        """
        Funktion um die Sekundärfärbung des Bildes ab zu ändern.
        """
        self.__secondary_staining = secondary_staining

    def set_tertiary_staining(self,tertiary_staining):
        """
        Funktion um die Tertiärfärbung des Bildes ab zu ändern.
        """
        self.__tertiary_staining = tertiary_staining

    def get_file_path(self):
        """
        Funktion um den Dateipfad des Bildes abzufragen.
        """
        return self.__file_path

    def access(self):
        """
        Funktion um die Pixelinformationen des Bildes zu laden.
        """
        opened = Accessed2DImage(self)
        opened.read_metadata()
        return opened

class Accessed2DImage(Faith_image):
    """
    Objekt welches Metadaten und Pixeldaten enthält.
    """
    __ome = None

    def __init__(self,image):
        super().__init__(image.get_case_id(), image.get_image_id(), image.get_diagnosis(), image.get_primary_staining(), image.get_secondary_staining(), image.get_tertiary_staining(), image.get_file_path())

    def read_metadata(self):
        """
        Funktion um die Metadaten des Bildes zu laden.
        """
        meta_data = bf.get_omexml_metadata(self.get_file_path())
        self.__ome 	= bf.OMEXML(meta_data)
	
    def get_width(self, layer):
        """
        Funktion um die Breite des Bildes abzufragen.
        """
        iome = self.__ome.image(layer)
        return iome.Pixels.get_SizeX()

    def get_height(self, layer):
        """
        Funktion um die Höhe des Bildes abzufragen.
        """
        iome = self.__ome.image(layer)
        return iome.Pixels.get_SizeY()

    def get_layer_count(self):
        """
        Funktion um die Anzahl vorhandener Layer des Bildes abzufragen.
        """
        return self.__ome.image_count

    def get_image(self, x_coord=0, y_coord=0, width=-1, height=-1, layer=3):
        """
        Funktion um die Pixelinformationen des Bildes zu laden.
        """
        if height == -1:
            height = self.get_height(layer)
        if width == -1:
            width = self.get_width(layer)
        image_reader = bf.ImageReader(path=self.get_file_path(), perform_init=True)
        tmp_nparray = image_reader.read(series=layer, XYWH=(x_coord, y_coord, width, height))
        image_reader.close()		
        tmp_nparray = tmp_nparray * 255
        rgb_numpy_array = tmp_nparray.astype(np.uint8)
        return Tile(self.get_image_id(), self.get_case_id(), self.get_diagnosis(),self.get_primary_staining(),self.get_secondary_staining(), self.get_tertiary_staining(), self.get_file_path(),
                        x_coord, y_coord, width, height, layer ,rgb_numpy_array)

class Tile(Faith_image):
    """
    Objekt welches ein Teilbild eines Faith Image Objekts enthält
    """
    
    __primary_staining = None
    __secondary_staining = None
    __tertiary_staining = None

    __x_coord = None
    __y_coord = None
    __layer = None
    __width = None
    __height = None
    __numpy_array = None

    def __init__(self, image_id, case_id, diagnosis, primary_staining, secondary_staining, tertiary_staining, file_path,  x_coord, y_coord, width, height,layer, numpy_array):

        super().__init__(case_id, image_id, diagnosis, primary_staining, secondary_staining, tertiary_staining, file_path)
        
        self.__x_coord = x_coord
        self.__y_coord = y_coord
        self.__layer = layer
        self.__width = width
        self.__height = height
        self.__numpy_array = numpy_array

    def get_layer(self):
        """
        Funktion um den Layer des Ausschnitss abzufragen.
        """
        return self.__layer
    
    def set_layer(self, layer):
        """
        Funktion um den Layer des Ausschnitss zu ändern.
        """
        self.__layer = layer
    
    def get_width(self):
        """
        Funktion um die Breite des Ausschnitss abzufragen.
        """
        return self.__width
    
    def set_width(self, width):
        """
        Funktion um die Breite des Ausschnitss zu ändern.
        """
        self.__width = width

    def get_height(self):
        """
        Funktion um die Höhe des Ausschnitss abzufragen.
        """
        return self.__height
    
    def set_height(self, height):
        """
        Funktion um die Höhe des Ausschnitss zu ändern.
        """
        self.__height = height

    def get_global_x(self):
        """
        Funktion um die globale X Koordinate bezogen auf das Gesamtbild abzufragen.
        """
        return self.__x_coord
    
    def set_global_x(self, global_x):
        """
        Funktion um die globale X Koordinate bezogen auf das Gesamtbild zu ändern.
        """
        self.__x_coord = global_x

    def get_global_y(self):
        """
        Funktion um die globale Y Koordinate bezogen auf das Gesamtbild abzufragen.
        """
        return self.__y_coord
    
    def set_global_y(self, global_y):
        """
        Funktion um die globale Y Koordinate bezogen auf das Gesamtbild zu ändern.
        """
        self.__y_coord = global_y

    def get_numpy_array(self):
        """
        Funktion um die Pixelinformationen des Bildes abzufragen.
        """
        return self.__numpy_array

    def set_numpy_array(self, numpy_array):
        """
        Funktion um die Pixelinformationen des Bildes abzuändern.
        """
        self.__numpy_array = numpy_array

    def save(self,output_path,add=""):
        """
        Funktion um den Teilausschnitt zu speichern.
        """
        im = Image.fromarray(self.__numpy_array)
        if add != "":
            add = "_" + add
        im.save(output_path+self.get_case_id()+"_"+self.get_image_id()+add+".png")
        
    def get_new_instance(self):
        """
        Funktion um eine Kopie des Ausschnitts zu erhalten.
        """
        return Tile(self.get_image_id(), self.get_case_id(), self.get_diagnosis(),self.get_primary_staining(),self.get_secondary_staining(), self.get_tertiary_staining(), self.get_file_path(),
                        self.get_global_x(), self.get_global_y(), self.get_width(), self.get_height(), self.get_layer(), self.get_numpy_array())