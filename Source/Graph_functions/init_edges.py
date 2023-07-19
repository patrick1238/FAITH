# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 13:37:33 2018

@author: patri
"""

import math
import numpy as np
import random

def __get_graph_width(nxgraph):
    """
    Funktion zur Bestimmung des Durchmessers des Graphens.
    """
    nodes = nxgraph.nodes(data=True)
    minX = 1000000000
    maxX = 0
    for node in nodes:
        minX = min(minX,node[1]["X"])
        maxX = max(maxX,node[1]["X"])
    return (maxX+1)#-minX

def __get_graph_height(nxgraph):
    """
    Funktion zur Bestimmung der Höhe des Graphens.
    """
    nodes = nxgraph.nodes(data=True)
    minY = 1000000000
    maxY = 0
    for node in nodes:
        minY = min(minY,node[1]["Y"])
        maxY = max(maxY,node[1]["Y"])
    return (maxY+1)#-minY

def get_corresponding_bins(x,y,binned):
    """
    Funktion zur Detektion korrespondierender Bins.
    """
    bins = []
    bins += binned[y][x]
    if y < len(binned)-1:
        bins+=binned[y+1][x]
        if x > 0:
            bins += binned[y+1][x-1]
        if x < len(binned[y])-1:
            bins+=binned[y+1][x+1]
    if x < len(binned[y])-1:
        bins+=binned[y][x+1]
    return bins

def bin_cellgraph(nxgraph,bin_size):
    """
    Funktion um einen Graphen nach gegebener Größe zu binnen.
    """
    width = __get_graph_width(nxgraph)
    height = __get_graph_height(nxgraph)
    binnedCoordinates = [[[]for x in range(int(width/bin_size)+2)]for y in range(int(height/bin_size)+2)]
    nodes = nxgraph.nodes(data=True)
    for node in nodes:
        x = int((node[1]["X"])/bin_size)
        y = int((node[1]["Y"])/bin_size)
        binnedCoordinates[y][x].append(node[0])
    return binnedCoordinates

def __get_distance(point1,point2):
    """
    Funktion zur Bestimmung der Distanz zwischen zwei Punkten.
    """
    return math.sqrt(((point1["X"]-point2["X"])**2+(point1["Y"]-point2["Y"])**2))

def initialize_deterministic_graph(nxgraph,communication_threshold):
    """
    Funktion zur Berechnung eines deterministischen Zellgraphen.
    """
    binsize = int(round(10*communication_threshold))
    binned = bin_cellgraph(nxgraph,binsize)
    nodes = dict(nxgraph.nodes.data())
    x = 0
    y = 0
    for perpendicular in binned:
        x = 0
        for horizontal in perpendicular:
            coordinates = get_corresponding_bins(x,y,binned)
            for key in horizontal:
                for key2 in coordinates:
                    if key != key2:
                        distance = __get_distance(nodes[key],nodes[key2])
                        if distance < communication_threshold:
                            nxgraph.add_edge(key,key2,Distance=distance)
            x += 1
        y += 1
    return nxgraph    

def __edge_prob(distance,communication_threshold,n=0):
    """
    Funktion zur probabilistischen Evaluation des Vorhandenseins einer Kante nach dem Waxmann und dem erweiterten Waxmannmodell.
    """
    prob = np.exp((-distance)/(communication_threshold*0.01))*pow((1/5),n)
    if random.random() < prob:
        return True
    else:
        return False

def initialize_waxmann_graph(nxgraph,communication_threshold):
    """
    Funktion zur Berechnung eines probabilstischen Zellgraphen nach Waxmann.
    """
    binsize = int(round(10*communication_threshold))
    binned = bin_cellgraph(nxgraph,binsize)
    nodes = dict(nxgraph.nodes.data())
    x = 0
    y = 0
    for perpendicular in binned:
        x = 0
        for horizontal in perpendicular:
            coordinates = get_corresponding_bins(x,y,binned)
            for key in horizontal:
                for key2 in coordinates:
                    if key != key2:
                        distance = __get_distance(nodes[key],nodes[key2])
                        if __edge_prob(distance,communication_threshold):
                            nxgraph.add_edge(key,key2,Distance=distance)
            x += 1
        y += 1
    return nxgraph

def __calculate_cellnumber(key,key2,possible_nodes, nodes):
    """
    Funktion zur Bestimmung der intrazellulären Zelldichte.
    """
    counter = 0
    node1 = nodes[key]
    node2 = nodes[key2]
    minx = min(node1["X"],node2["X"])
    miny = min(node1["Y"],node2["Y"])
    maxx = max(node1["X"],node2["X"])
    maxy = max(node1["Y"],node2["Y"])
    for observe in possible_nodes:
        if not observe == key and not observe == key2:
            if nodes[observe]["X"] <maxx and nodes[observe]["X"] > minx:
                if nodes[observe]["Y"] < maxy and nodes[observe]["Y"] > miny:
                    counter += 1
    return counter


def initialize_waxmann_graph_extended(nxgraph,communication_threshold):
    """
    Funktion zur Berechnung eines probabilstischen Zellgraphen nach dem erweiterten Waxmannmodell.
    """
    binsize = int(round(10*communication_threshold))
    binned = bin_cellgraph(nxgraph,binsize)
    nodes = dict(nxgraph.nodes.data())
    x = 0
    y = 0
    for perpendicular in binned:
        x = 0
        for horizontal in perpendicular:
            coordinates = get_corresponding_bins(x,y,binned)
            for key in horizontal:
                for key2 in coordinates:
                    if key != key2:
                        distance = __get_distance(nodes[key],nodes[key2])
                        cell_number = __calculate_cellnumber(key,key2,coordinates,nodes)
                        if __edge_prob(distance,communication_threshold,cell_number):
                            nxgraph.add_edge(key,key2,Distance=distance)
            x += 1
        y += 1
    return nxgraph