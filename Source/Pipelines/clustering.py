import seaborn as sns
import Source.Objects.Config as Config
import Source.Objects.Database as db
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans,AgglomerativeClustering,DBSCAN
import numpy as np    

__SCRIPT_NAME="clustering"

def main():
    config = Config.load()
    df = db.load().get_database_dataframe()
    features = df.select_dtypes('number').columns
    if not config.get("clustering_features").lower() == "all":
        features = config.get("clustering_features").split(",")
    x = np.array(df[features].values)
    x = StandardScaler().fit_transform(x)
    annotation = []
    if config.get("clustering_algorithm") == "KMeans":
        km = KMeans(
            n_clusters=3, init='random',
            n_init=10, max_iter=300, 
            tol=1e-04, random_state=0
        )
        annotation = km.fit_predict(x)
    elif config.get("clustering_algorithm") == "HierarchicalClustering":
        ac = AgglomerativeClustering()
        annotation = ac.fit_predict(x)
    elif config.get("clustering_algorithm") == "DBSCAN":
        dbc = DBSCAN(eps=3, min_samples=2)
        annotation = dbc.fit_predict(x)
    df["Clustering"] = annotation
    df = df.astype({"Clustering": 'category'})
    pca = PCA(n_components=2)
    principalComponents = pca.fit_transform(x)
    df["PCA1"] = [i for i, j in principalComponents]
    df["PCA2"] = [j for i, j in principalComponents]
    sp = sns.scatterplot(data=df, x="PCA1", y="PCA2", style="Clustering",hue=config.get("clustering_group"))
    for line in range(0,df.shape[0]):
        sp.text(df["PCA1"][line]+0.1, df["PCA2"][line]+0.1, 
        df["Case_ID"][line], horizontalalignment='right', 
        size='small', color='black')
    plt.tight_layout()
    plt.savefig(config.get("output")+config.get("clustering_algorithm")+"_PCA.png")
    df.drop(df.select_dtypes('number').columns, axis=1, inplace=True)
    df.to_excel(config.get("output")+config.get("clustering_algorithm")+"_values.xlsx")
    
    
        
