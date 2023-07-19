import pandas as pd
import networkx as nx
import Source.Graph_functions.init_edges as ie
import tqdm
import numpy as np
import Source.Objects.Database as db
import Source.Basic_functions.database_toolbox as dbt
from timeit import default_timer as timer
import Source.Objects.Config as Config

__SCRIPT_NAME="cellgraphanalysis"

def get_attributedict(header,row):
    cur = {}
    for head in header:
        cur[head.strip(" ").replace(" ","_").replace("=","-")] = row[head]
    return cur

def calculate_graph(df):
    communication_threshold = df["Majoraxislength"].median() * 2
    graph = nx.Graph()
    attribute_dict = {}
    for index, row in df.iterrows():
        graph.add_node(index)
        attribute_dict[index] = {"X":int(row["X"]),"Y":int(row["Y"])}
    nx.set_node_attributes(graph, attribute_dict)
    config = Config.load()
    if config.get("cellgraphanalysis_graphtype") == "deterministic":
        graph = ie.initialize_deterministic_graph(graph,communication_threshold)
    elif config.get("cellgraphanalysis_graphtype") == "waxmann":
        graph = ie.initialize_waxmann_graph(graph,communication_threshold)
    elif config.get("cellgraphanalysis_graphtype") == "extended_waxmann":
        graph = ie.initialize_waxmann_graph_extended(graph,communication_threshold)
    return ie.initialize_deterministic_graph(graph,communication_threshold)

def calculate_average_local_graph_efficiency(graph, output_dict):
    if not "Local communication efficiency" in output_dict:
        output_dict["Local communication efficiency"] = []
    output_dict["Local communication efficiency"].append(nx.local_efficiency(graph))
    return output_dict

def Percentage_of_isolated_points(graph, output_dict):
    if not "Percentage of isolates" in output_dict:
        output_dict["Percentage of isolates"] = []
    output_dict["Percentage of isolates"].append(float(len(list(nx.isolates(graph))))/float(graph.number_of_nodes()))
    return output_dict

def average_degree(graph, output_dict):
    if not "Average connections" in output_dict:
        output_dict["Average connections"] = []
    output_dict["Average connections"].append(np.sum(list(zip(*graph.degree))[1])/float(graph.number_of_nodes()))
    return output_dict

def degree_assortativity(graph, output_dict):
    if not "Degree assortativity" in output_dict:
        output_dict["Degree assortativity"] = []
    output_dict["Degree assortativity"].append(nx.degree_assortativity_coefficient(graph))
    return output_dict

def transitivity(graph, output_dict):
    if not "Transitivity" in output_dict:
        output_dict["Transitivity"] = []
    output_dict["Transitivity"].append(nx.transitivity(graph))
    return output_dict

def average_clustering(graph, output_dict):
    if not "Average clustering" in output_dict:
        output_dict["Average clustering"] = []
    output_dict["Average clustering"].append(nx.average_clustering(graph))
    return output_dict

def main():
    database = db.load()
    cells_df = database.get_cells_dataframe()
    for imageid, group in tqdm.tqdm(cells_df.groupby("Image_ID")):
        graph = calculate_graph(group)
        case = group.Case_ID.unique()[0]
        diagnosis = group.Diagnosis.unique()[0]
        output_dict = {"ID":[case],"Case_ID":[case],"Diagnosis":[diagnosis]}
        output_dict = calculate_average_local_graph_efficiency(graph,output_dict)
        output_dict = Percentage_of_isolated_points(graph, output_dict)
        output_dict = average_degree(graph, output_dict)
        output_dict = average_clustering(graph, output_dict)
        output_dict = transitivity(graph,output_dict)
        output_dict = degree_assortativity(graph, output_dict)
        dbt.get_tmp_workspace(__SCRIPT_NAME,imageid)
        dbt.export(pd.DataFrame.from_dict(output_dict),imageid,__SCRIPT_NAME)
        dbt.collect_pipeline_export(__SCRIPT_NAME,imageid)
