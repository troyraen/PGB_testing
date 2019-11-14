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


def do_kmeans(df, nclusts=None, normfeats=True):
    """ Runs Kmeans clustering on df.

    """

    d = norm_features(df) if normfeats else df.copy()

    # find the clusters
    kwargs = {
                # 'init':'random'
            }
    kmns = KMeans(n_clusters=nclusts, random_state=13, **kwargs).fit(d)

    # get results
    clusts = kmns.predict(d) # cluster assignments
    dists = kmns.transform(d) # distances from cluster means

    return kmns, clusts, dists

def plot_kmeans_dist(df, clusts, dists, nLarge=10000, nSmall=50):
    d = df.copy()
    d['minDist'] = np.amin(dists, axis=1)

    large = d.loc[d.numinType>nLarge,'minDist']
    small = d.loc[d.numinType<nSmall,'minDist']

    plt.figure()
    kwargs = {'alpha':0.5, 'density':True, 'bins':20}
    plt.hist(large, label=f"Large classes (>{nLarge})", **kwargs)
    plt.hist(small, label=f"Small classes (<{nSmall})", **kwargs)
    plt.legend(loc=1)
    plt.xlabel('Minimum distance to cluster center')
    plt.title('K-means')
    plt.show(block=False)

    return None



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
                    'max_features': 1
                }

    forest = IsolationForest(**kwargs).fit(df)

    predics = forest.predict(df)

    return forest, predics


def plot_isoF_outliers(df, predics, nLarge=10000, nSmall=50):

    d = df.copy()
    d['IF_predics'] = predics

    large = d.loc[d.numinType>nLarge,:].groupby('IF_predics').size()
    small = d.loc[d.numinType<nSmall,:].groupby('IF_predics').size()

    plt.figure()
    plt.bar(large.index, large/large.sum(), alpha=0.5, label=f"Large classes (>{nLarge})")
    plt.bar(small.index, small/small.sum(), alpha=0.5, label=f"Small classes (<{nSmall})")
    plt.legend(loc='center')
    plt.xticks((-1,1), ('Outlier','Inlier'))
    plt.ylabel('Fraction in Category')
    plt.title('Isolation Forest')
    plt.show(block=False)

    return None


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
