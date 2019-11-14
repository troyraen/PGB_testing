""" Loads ASAS-SN data, including features extracted using UPSILoN.
"""

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

csv_cols = ['asassn_name', 'Other Names', 'id', 'raj2000', 'dej2000', 'l', 'b',
       'Mean Vmag', 'amplitude', 'period', 'Type', 'class_probability',
       'LKSL Statistic', 'rfr_score', 'epochhjd', 'gdr2_id', 'gmag', 'e_gmag',
       'bpmag', 'e_bpmag', 'rpmag', 'e_rpmag', 'BP-RP', 'parallax',
       'parallax_error', 'parallax_over_error', 'pmra', 'e_pmra', 'pmdec',
       'e_pmdec', 'v_t', 'dist', 'allwise_id', 'jmag', 'e_jmag', 'hmag',
       'e_hmag', 'kmag', 'e_kmag', 'w1mag', 'e_w1mag', 'w2mag', 'e_w2mag',
       'w3mag', 'e_w3mag', 'w4mag', 'e_w4mag', 'J-K', 'W1-W2', 'W3-W4',
       'APASS_DR9ID', 'APASS_Vmag', 'e_APASS_Vmag', 'APASS_Bmag',
       'e_APASS_Bmag', 'APASS_gpmag', 'e_APASS_gpmag', 'APASS_rpmag',
       'e_APASS_rpmag', 'APASS_ipmag', 'e_APASS_ipmag', 'B-V', 'E(B-V)',
       'Reference', 'Periodic', 'Classified', 'ASASSN_Discovery']

csv_feats_dict = {
            'type': ['Type', 'class_probability', 'Classified'],
            'other': ['amplitude', 'period', 'Mean Vmag', 'LKSL Statistic',
                        'rfr_score', 'Periodic'],
            'mags': ['gmag', 'bpmag', 'rpmag', 'jmag', 'hmag', 'kmag', 'w1mag',
                        'w2mag', 'w3mag', 'w4mag' ],
            'APASS_mags': ['APASS_Vmag', 'APASS_Bmag', 'APASS_gpmag', 'APASS_rpmag',
                            'APASS_ipmag'],
            'colors': ['BP-RP', 'J-K', 'W1-W2', 'W3-W4', 'B-V']
        }

def load_dfs(ffeats='upsilon_features.dat', fcsv='asassn-catalog.csv', \
                cfeat=None, consol=True):
    """ Returns dataframes of ASAS-SN csv file
        and features extracted using UPSILoN.

        cfeat = None or color from csv_feats_dict['colors']
                Restricts dffeats to rows where this column is not null

        consol=True
                consolidates types with those ending in ":" -> column 'newType'
                and convert types to ints -> column 'intType'
    """

    # load csv file
    dfcsv = pd.read_csv(fcsv)
    dfcsv = dfcsv.astype({'id':'str'})
    dfcsv = dfcsv.set_index('id', drop=False)

    # load features extracted from light curves using Upsilon
    dffeats = pd.read_csv(ffeats)
    dffeats = dffeats.set_index('id', drop=False)
    # add color info from csv file
    for c in csv_feats_dict['colors']:
        dffeats[c] = dfcsv.loc[dfcsv.id.isin(list(dffeats.id)),:][c]
    if cfeat is not None:
        dffeats = dffeats.dropna(subset=[cfeat])

    # consolidate types with those ending in ":" -> column 'newType'
    # and convert types to ints -> column 'intType'
    if consol == True:
        dfcsv = consol_types(dfcsv)
        dffeats = consol_types(dffeats)


    return dfcsv, dffeats


def consol_types(df):
    """ Adds column
          'newType': which merges Types ending in ":" with the base Type
    """
    d = df.copy()

    # consolidate types ending with ":"
    d['newType'] = d.Type.apply(lambda x: x if x[-1]!=":" else x[:-1])

    # recalculate numinType and reset intType
    d, _ = set_type_info(d)

    return d


def get_hiprob(df, cprob=0.99):

    d = df.loc[df.class_probability > cprob, :]

    # recalculate numinType and reset intType
    d, __ = set_type_info(d)

    return d


def get_large_small(df, nLarge=10000, nSmall=50):
    """ Returns df of classes with large and small number of examples.
    """

    d = df.loc[((df.numinType>nLarge) | (df.numinType<nSmall))]

    return d


def filter_dfcsv(dfcsv, feats=None, nLarge=10000, nSmall=50):

    if feats is None:
        feats = csv_feats_dict['colors'] +
                csv_feats_dict['other'][0:2] +
                csv_feats_dict['mags']

    # class_probability > 0.99
    d = get_hiprob(dfcsv)

    # keep only rows with all features
    d = d.dropna(axis=0, subset=feats)

    # recalc numinType
    d, __ = ad.set_type_info(d)

    # keep only large and small classes
    d = ad.get_large_small(d, nLarge=nLarge, nSmall=nSmall)

    return d


def set_type_info(df):
    """ Adds or updates columns:
          'numinType', number of stars of this type
          'intType', converts the Type str to an integer for
          supervised classification
    """
    d = df.copy()
    sz = d.groupby('newType').size()
    type2int = dict([(t,i) for i,t in \
                enumerate(sz.sort_values(ascending=False).index)])

    d['numinType'] = d.newType.map(dict(sz))
    d['intType'] = d.newType.map(type2int)

    return d, sz
