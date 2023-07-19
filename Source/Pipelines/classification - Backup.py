from statistics import mean, stdev
from sklearn import preprocessing
from sklearn.model_selection import StratifiedKFold
from sklearn import ensemble
from sklearn import tree
from sklearn.metrics import confusion_matrix
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.inspection import permutation_importance
import Source.Objects.Database as db
import pandas as pd
import Source.Objects.Config as Config

__SCRIPT_NAME="classification"

def cm_analysis(y_true, y_pred, labels, ymap=None):
    if ymap is not None:
        y_pred = [ymap[yi] for yi in y_pred]
        y_true = [ymap[yi] for yi in y_true]
        labels = [ymap[yi] for yi in labels]
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_sum = np.sum(cm, axis=1, keepdims=True)
    cm_perc = cm / cm_sum.astype(float) * 100
    annot = np.empty_like(cm).astype(str)
    nrows, ncols = cm.shape
    for i in range(nrows):
        for j in range(ncols):
            c = cm[i, j]
            p = cm_perc[i, j]
            if i == j:
                s = cm_sum[i]
                annot[i, j] = '%.1f%%\n%d/%d' % (p, c, s)
            elif c == 0:
                annot[i, j] = ''
            else:
                annot[i, j] = '%.1f%%\n%d' % (p, c)
    return cm

def inspect_data(df,target,features,outpath,appender):
    # Input_x_Features.
    x = df[features].values
    
    # Input_ y_Target_Variable.
    y = df[target].values                  
    unique_values = len(list(np.unique(y)))
    
    # Feature Scaling for input features.
    scaler = preprocessing.MinMaxScaler()
    x_scaled = scaler.fit_transform(x)
    
    # Create  classifier object.
    config = Config.load()
    if config.get("classification_classificator")=="Randomforest":
        lr = ensemble.RandomForestClassifier()
    elif config.get("classification_classificator")=="DecisionTree":
        lr = tree.DecisionTreeClassifier()
    elif config.get("classification_classificator")=="BaggedDecisionTree":
        lr = ensemble.BaggingClassifier()
    splits = 10
    for tar in df[target].unique():
        cur = df.loc[df[target]== tar]
        splits = min(splits,len(cur.index))
    # Create StratifiedKFold object.
    skf = StratifiedKFold(n_splits=splits, shuffle=True, random_state=1)
    lst_accu_stratified = []
    cm = np.array([])
    forest_importances = pd.Series()
    for train_index, test_index in skf.split(x, y):
        x_train_fold, x_test_fold = x_scaled[train_index], x_scaled[test_index]
        y_train_fold, y_test_fold = y[train_index], y[test_index]
        lr.fit(x_train_fold, y_train_fold)
        y_pred=lr.predict(x_test_fold)
        result_new = permutation_importance(
            lr, x_test_fold, y_test_fold, n_repeats=splits, random_state=42, n_jobs=2
        )
        forest_importances_new = pd.Series(result_new.importances_mean, index=features)
        forest_importances = forest_importances.add(forest_importances_new, fill_value=0)
        
        lst_accu_stratified.append(lr.score(x_test_fold, y_test_fold))
        cur = cm_analysis(y_test_fold, y_pred, lr.classes_, ymap=None)
        if cm.size == 0:
            cm = cur
        elif not cur.shape == (unique_values,unique_values):
            pass
        else:
            cm = cm + cur
    forest_importances = forest_importances.rename("Importances")
    a = pd.Series.to_frame(forest_importances)
    a['ID'] = list(a.index)
    a.to_excel(outpath+appender+"_Feature_importances.xlsx")
    labels = lr.classes_
    cm_sum = np.sum(cm, axis=1, keepdims=True)
    cm_perc = cm / cm_sum.astype(float) * 100
    annot = np.empty_like(cm).astype(str)
    nrows, ncols = cm.shape
    for i in range(nrows):
        for j in range(ncols):
            c = cm[i, j]
            p = cm_perc[i, j]
            if i == j:
                s = cm_sum[i]
                annot[i, j] = '%.1f%%' % (p)
            elif c == 0:
                annot[i, j] = ''
            else:
                annot[i, j] = '%.1f%%' % (p)
    annot2 = np.empty_like(cm)
    nrows, ncols = cm.shape
    for i in range(nrows):
        for j in range(ncols):
            p = cm_perc[i, j]
            if i == j:
                annot2[i, j] = float(p)
            elif c == 0:
                annot2[i, j] = float(0)
            else:
                annot2[i, j] = float(p)

    cm = pd.DataFrame(annot2, index=labels, columns=labels)
    cm.index.name = 'Actual'
    cm.columns.name = 'Predicted'

    fig, ax = plt.subplots(figsize=(10,10))
    size = 20
    res = sns.heatmap(cm, annot=annot, fmt='', ax=ax, cbar=False,cmap=matplotlib.colors.LinearSegmentedColormap.from_list("", ["black","green"]),annot_kws={"size":size})
    res.set_xticklabels(res.get_xmajorticklabels(), fontsize = size)
    res.set_yticklabels(res.get_ymajorticklabels(), fontsize = size)

    plt.xlabel('Predicted', fontsize=size)
    plt.ylabel('Actual', fontsize=size)
    plt.title('Splits for StratifiedKFold: '+str(splits)+'\nMaximum Accuracy That can be obtained from this model is: '+str(max(lst_accu_stratified)*100)+ '%\nMinimum Accuracy: '+str(min(lst_accu_stratified)*100)+ '%\nOverall Accuracy: '+str( mean(lst_accu_stratified)*100)+ '%\nStandard Deviation is: '+str( stdev(lst_accu_stratified)))
    plt.savefig(outpath+appender+"_rf_stratkfold_validation.png")
    return a

def main():
    config = Config.load()
    df = db.load().get_database_dataframe()
    counter = 0
    features = df.select_dtypes('number').columns
    if not config.get("classification_features").lower() == "all":
        features = config.get("classification_features").split(",")
    forest_importances = inspect_data(df,config.get("classification_group"),features,config.get("output"),str(counter))
    if config.get("classification_featuresselection") == "True":
        while (forest_importances["Importances"].values < 0).any():
            counter += 1
            good_features = forest_importances.loc[forest_importances["Importances"]>0]
            pathomic_profile = list(good_features["ID"])
            pathomic_profile.append(config.get("classification_group"))
            df_filtered = df[pathomic_profile]
            pathomic_profile.remove(config.get("classification_group"))
            forest_importances = inspect_data(df_filtered,config.get("classification_group"),pathomic_profile,config.get("output"),str(counter))