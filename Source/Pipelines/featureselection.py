import numpy as np
import matplotlib.pyplot as plt
import Source.Objects.Config as Config
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr
from scipy.cluster import hierarchy
from scipy.spatial.distance import squareform
import Source.Objects.Database as db

__SCRIPT_NAME="featureselection"

def hierachical_feature_selection(df,features_to_analyse):
    config = Config.load()
    x = df.loc[:, features_to_analyse].values
    y = df.loc[:,'Diagnosis'].values
    fig, ax1 = plt.subplots(1, 1, figsize=(12, 8))
    corr = spearmanr(x).correlation
    corr = (corr + corr.T) / 2
    np.fill_diagonal(corr, 1)
    distance_matrix = 1 - np.abs(corr)
    dist_linkage = hierarchy.ward(squareform(distance_matrix))
    hierarchy.dendrogram(dist_linkage, labels=features_to_analyse, ax=ax1, leaf_rotation=90)
    plt.axhline(y=0.5)
    plt.title("Feature selection")
    plt.ylabel("Correlation distance")
    fig.tight_layout()
    plt.savefig(config.get("output")+"feature_selection.png")

def main():
    config = Config.load()
    df = db.load().get_database_dataframe()
    features = df.select_dtypes('number').columns
    if not config.get("featureselection_features").lower() == "all":
        features = config.get("featureselection_features").split(",")
    hierachical_feature_selection(df,features)