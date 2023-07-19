from sklearn import preprocessing
from sklearn.model_selection import StratifiedKFold
from sklearn import ensemble
from sklearn import tree
from sklearn.metrics import confusion_matrix,balanced_accuracy_score
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import Source.Objects.Database as db
import Source.Objects.Config as Config
import copy as cp
import matplotlib.pyplot as plt


__SCRIPT_NAME="classification"

def cross_val_predict(model, skf,X, y,outpath):
    scaler = preprocessing.MinMaxScaler()
    X = scaler.fit_transform(X)
    
    model_ = cp.deepcopy(model)    
    actual_classes = np.empty([0], dtype=int)
    predicted_classes = np.empty([0], dtype=int)
    accuracys = []
    for train_ndx, test_ndx in skf.split(X, y):

        train_X, train_y, test_X, test_y = X[train_ndx], y[train_ndx], X[test_ndx], y[test_ndx]

        actual_classes = np.append(actual_classes, test_y)

        model_.fit(train_X, train_y)
        prediction = model_.predict(test_X)
        predicted_classes = np.append(predicted_classes, prediction)
        score = balanced_accuracy_score(test_y,prediction)
        accuracys.append(score)
    matrix = confusion_matrix(actual_classes, predicted_classes, labels=np.unique(y))
    annot = []
    for row in matrix:
        new_row = []
        sum_row = np.sum(row)/100
        for value in row:
            new_row.append(value/sum_row)
        annot.append(new_row)
    plt.figure(figsize=(12.8,6))
    ax = sns.heatmap(matrix, annot=annot, xticklabels=np.unique(y), yticklabels=np.unique(y), cmap=matplotlib.colors.LinearSegmentedColormap.from_list("", ["black","green"]), fmt='.1f', cbar=False,annot_kws={"size":20})
    for t in ax.texts: t.set_text(t.get_text() + " %")
    plt.xlabel('Predicted'); plt.ylabel('Actual')
    mean_acc = np.mean(accuracys)
    std_acc = np.std(accuracys)
    plt.title("Mean balanced accuracy: "+str(mean_acc)+"\n with a standard deviation of "+str(std_acc))
    plt.savefig(outpath+"Crossvalidation.png")
    

def main():
    config = Config.load()
    df = db.load().get_database_dataframe()
    features = df.select_dtypes('number').columns
    group_id = config.get("classification_group")
    outpath = config.get("output")
    skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=1)
    if config.get("classification_classificator")=="Randomforest":
        model = ensemble.RandomForestClassifier()
    elif config.get("classification_classificator")=="DecisionTree":
        model = tree.DecisionTreeClassifier()
    elif config.get("classification_classificator")=="BaggedDecisionTree":
        model = ensemble.BaggingClassifier()
    cross_val_predict(model, skf, df[features].to_numpy(), df[group_id].to_numpy(),outpath)