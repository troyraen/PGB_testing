import pandas as pd
import numpy as np
from pathlib import Path
from matplotlib import pyplot as plt

import asassn_data as ad


#-- Load data --#
ffeats = Path('/home/tjr63/Documents/PGB/TOM_prop_unsupclust/features.dat')
fcsv = Path('/home/tjr63/Documents/PGB/TOM_prop_unsupclust/asassn-catalog.csv')
# cfeat = 'W3-W4' # restricts dffeats to rows where this column is not null
dfcsv, dffeats = ad.load_dfs(fcsv=fcsv, ffeats=ffeats, cfeat=None, consol=True)

# test features
feats = ad.csv_feats_dict
ft = feats['colors'] + feats['other'][0:2] + feats['mags'] # features to use

# filter for large,small classes, high class_probability
nLarge, nSmall, cprob = 10000, 50, 0.99
d = ad.filter_dfcsv(dfcsv, feats=ft, nLarge=nLarge, nSmall=nSmall, cprob=cprob) # filter dfcsv
lclasses = d.loc[d.numinType>nLarge,'newType'].unique()
sclasses = d.loc[d.numinType<nSmall,'newType'].unique()

# dataframe for results
idxs = pd.MultiIndex.from_product([list(sclasses),list(lclasses)],
                                    names=['small_class', 'large_class'])
simdf = pd.DataFrame(data=None, index=idxs, columns=['dist','dist_std'])

# calc distance between classes
#   using Euclidean distance between feature means
davg = d[ft+['newType']].groupby('newType').mean()
dstd = d[ft+['newType']].groupby('newType').std()
for sc in sclasses:
    for lc in lclasses:
        dist, dist_std = 0, 0
        for f in ft:
            dist = dist + (davg.loc[sc,f] - davg.loc[lc,f])**2
            dist_std = dist_std + (davg.loc[sc,f]/dstd.loc[sc,f] -
                                   davg.loc[lc,f]/dstd.loc[lc,f])**2

        simdf.loc[(sc,lc),'dist'] = np.sqrt(dist)
        simdf.loc[(sc,lc),'dist_std'] = np.sqrt(dist_std)
