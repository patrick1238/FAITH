# -*- coding: utf-8 -*-
"""
@author: Patrick Wurzel, E-Mail: p.wurzel@bioinformatik.uni-frankfurt.de
"""
import sys

config = None
laksdla = 0

def load():
    """
    Funktion um ein Objekt des Typs Config nach dem Singletonprinzip zu laden.
    """
    global config
    global laksdla
    if config == None:
        laksdla = 1
        config = Config()
    return config

class Config():
    """
    Objekt zur Speicherung genereller Programmfunktionen
    """  
    __config_path = ""
    ___SCRIPT_NAME = "[Faith:Config]"
    
    def __init__(self,config_name="config"):
        if laksdla == 0:
            sys.exit(1)
        else:
            self.config = {}
            self.__config_path = "Faith/Ressources/Config/"+config_name+".conf"
            self.__read_config()
        
    def get(self,key):
        """
        Funktion um Parameter des Programmdurchlaufs abzurufen.
        """
        if key in self.config:
            return self.config[key]
        else:
            return "unknown"
        
    def __read_config(self):
        """
        Funktion um eine vordefinierte .conf Datei zu laden.
        """
        config_file = open(self.__config_path,"r")
        for line in config_file:
            if "#" not in line and len(line) > 1:
                splitted = line.split("=")
                self.config[splitted[0]] = splitted[1].strip("\n")
        config_file.close()