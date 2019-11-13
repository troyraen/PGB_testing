import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

import asassn_data as ad
import unsupervised as uns


# load data
ffeats = 'features.dat'
cfeat = 'W3-W4' # restricts dffeats to rows where this column is not null
dfcsv, dffeats = ad.load_dfs(ffeats=ffeats, cfeat=cfeat, consol=True)


# restrict dfcsv rows
d = ad.get_hiprob(dfcsv) # class_probability > 0.99

feats = uc.csv_feats_dict
ft = feats['colors'] + feats['other'][0:2] + feats['mags'][0:3]

d = d.dropna(axis=0, subset=ft) # Use only rows with all features
d, __ = ad.set_type_info(d) # recalc numinType

numHi = 10000
numLow = 50
d = ad.get_hilow(dfeats, numHi=numHi, numLow=numLow)


# run isolation forest
forest, predics = uns.do_isolationForest(d[ft])
