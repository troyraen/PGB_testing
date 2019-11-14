import pandas as pd
import numpy as np
from pathlib import Path
from matplotlib import pyplot as plt

import asassn_data as ad
import unsupervised as uns


#-- Load data --#
ffeats = Path('/home/tjr63/Documents/PGB/TOM_prop_unsupclust/features.dat')
fcsv = Path('/home/tjr63/Documents/PGB/TOM_prop_unsupclust/asassn-catalog.csv')
cfeat = 'W3-W4' # restricts dffeats to rows where this column is not null
dfcsv, dffeats = ad.load_dfs(fcsv=fcsv, ffeats=ffeats, cfeat=cfeat, consol=True)


#-- Use for filtering dfcsv rows --#
feats = ad.csv_feats_dict
nLarge, nSmall = 10000, 50


#-- Run isolation forest --#
ft = feats['colors'] + feats['other'][0:2] + feats['mags'] # features to use
d = ad.filter_dfcsv(dfcsv, feats=ft, nLarge=nLarge, nSmall=nSmall) # filter dfcsv

forest, predics = uns.do_isoForest(d[ft], kwargs=kwargs)
uns.plot_isoF_outliers(d, predics, nLarge=nLarge, nSmall=nSmall)


#-- Run kmeans --#
ft = feats['colors'] + feats['other'][:-1] + feats['mags']
d = ad.filter_dfcsv(dfcsv, feats=ft, nLarge=nLarge, nSmall=nSmall)
nclusts = len(d.loc[d.numinType>nLarge,'newType'].unique())

kmns, clusts, dists = do_kmeans(d[ft], nclusts=nclusts, normfeats=True)
uns.plot_kmeans_dist(d, clusts, dists, nLarge=nLarge, nSmall=nSmall)
