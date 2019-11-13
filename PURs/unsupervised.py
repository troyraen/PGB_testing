""" Runs unsupervised clustering on ASAS-SN data with features extracted
    using UPSILoN
"""

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix
from sklearn.utils.multiclass import unique_labels



def norm_features(df, algor='minmax'):
    if algor == 'minmax':
        return (df-df.min())/(df.max()-df.min())
    # elif algor == 'standardize':
        # need to finish this...


def do_kmeans(df, dftest=None, nclusts=None, normfeats=True, color=None):
    """ Runs Kmeans clustering using training set df.
        Returns various dataframes of predictions on df and dftest using both all features
          and a subset of the top features as indicated by feature importance from the
          random forest classification run by Upsilon
          (paper: https://www.aanda.org/articles/aa/pdf/2016/03/aa27188-15.pdf)
          CURRENTLY returns only kmeans on top features

        color should be None or one of the colors from csv_colors (as a string)
    """
    d = df.copy()
    if dftest is not None:
        dt = dftest.copy()
    if nclusts is None:
        nclusts = len(d.intType.unique())
    # kwargs = {'init':'random'}
    kwargs = {}

    if normfeats:
        d = norm_features(d)
        if dftest is not None:
            dt = norm_features(dt)

    # find the clusters
    kmns = KMeans(n_clusters=nclusts, random_state=0, **kwargs).fit(d)

    # get predictions
    predics = kmns.predict(d)
    if dftest is not None:
        predics_test = kmns.predict(dt)

    # get distances from cluster means
    dists = kmns.transform(d)
    if dftest is not None:
        dists_test = kmns.transform(dt)

    if dftest is not None:
        return predics, predics_test, dists, dists_test
    else:
        return predics, dists


def do_isoForest(df, kwargs=None):
    """ Runs an isolation forest looking for outliers.
    """

    if kwargs is None:
        kwargs = {
                    # 'n_estimators': 1000,
                    'behaviour': 'new',
                    # 'max_samples': 1000,
                    'random_state': 42,
                    'contamination': 'auto',
                    'max_features': 3
                }

    forest = IsolationForest(**kwargs).fit(df)

    predics = forest.predict(df)

    return forest, predics



def plot_confusion_matrix(y_true, y_pred, classes,normalize=False,title=None):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """

    cmap = plt.cm.Blues

    if not title:
        if normalize:
            title = 'Normalized confusion matrix'
        else:
            title = 'Confusion matrix, without normalization'

    # Compute confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    # Only use the labels that appear in the data
    classes = classes[unique_labels(y_true, y_pred)]
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)

    fig, ax = plt.subplots()
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    ax.figure.colorbar(im, ax=ax)
    # We want to show all ticks...
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           # ... and label them with the respective list entries
           yticklabels=classes,
           title=title,
           ylabel='True label',
           xlabel='Predicted label',
           ylim=(-0.5,len(classes)-0.5))

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], fmt),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    return ax
