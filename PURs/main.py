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


#-- Restrict dfcsv rows --#
d = ad.get_hiprob(dfcsv) # class_probability > 0.99

feats = ad.csv_feats_dict
ft = feats['colors'] + feats['other'][0:2] + feats['mags']

d = d.dropna(axis=0, subset=ft) # Use only rows with all features
d, __ = ad.set_type_info(d) # recalc numinType

numHi = 10000
numLow = 50
d = ad.get_hilow(d, numHi=numHi, numLow=numLow)


#-- Run isolation forest --#
kwargs = {
            # 'n_estimators': 1000,
            'behaviour': 'new',
            # 'max_samples': 1000,
            'random_state': 42,
            'contamination': 'auto',
            'max_features': 1
        }
forest, predics = uns.do_isoForest(d[ft], kwargs=kwargs)
# plot
d['IF_predics'] = predics
main = d.loc[d.numinType>numHi,:].groupby('IF_predics').size()
out = d.loc[d.numinType<numLow,:].groupby('IF_predics').size()
plt.figure()
plt.bar(main.index, main/main.sum(), alpha=0.5, label=f"Large classes (>{numHi})")
plt.bar(out.index, out/out.sum(), alpha=0.5, label=f"Small classes (<{numLow})")
plt.legend(loc='center')
plt.xticks((-1,1), ('Outlier','Inlier'))
plt.show(block=False)
