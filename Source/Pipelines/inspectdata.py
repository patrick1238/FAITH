# -*- coding: utf-8 -*-

import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import scikit_posthocs as scp
from statannotations.Annotator import Annotator
import Source.Objects.Config as Config
import Source.Objects.Database as db
import matplotlib.pyplot as plt
import Source.Basic_functions.general_toolbox as gtp

__SCRIPT_NAME="inspectdata"

def plot_box_with_star(df,column,group):
    ax = sns.boxplot(data=df, x=group, y=column, showfliers = False)
    dunn_df = scp.posthoc_dunn(
        df, val_col=column, group_col=group, p_adjust="bonferroni"
    )
    remove = np.tril(np.ones(dunn_df.shape), k=0).astype("bool")
    dunn_df[remove] = np.nan

    molten_df = dunn_df.melt(ignore_index=False).reset_index().dropna()
    pairs = [(i[1]["index"], i[1]["variable"]) for i in molten_df.iterrows()]
    p_values = [i[1]["value"] for i in molten_df.iterrows()]
    annotator = Annotator(
        ax, pairs, data=df, x=group, y=column
    )
    annotator.configure(text_format="star", loc="inside")
    annotator.set_pvalues_and_annotate(p_values)
    ax.set(xlabel=None)
    config = Config.load()
    plt.savefig(config.get("output")+column+".png")
    plt.close()

def main():
    config = Config.load()
    df = db.load().get_database_dataframe()
    for column in df.select_dtypes('number').columns:
        with gtp.suppress_stdout():
            plot_box_with_star(df,column,config.get("inspectdata_group"))