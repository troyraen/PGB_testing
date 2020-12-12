#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import logging
from astropy import units as u
from astropy.table import Table
from astroquery.xmatch import XMatch
from apache_beam import DoFn


def alertDicts2AstropyTable(alertDicts):
    """ Example usage:
    Apply to a window of the stream: `beam.CombinePerKey(createAstropyTable)`.
    Use the result to query Vizier for the xmatch: `xmatchVizier(xmatchTable)`

    Args:
        alertDicts <[dict,]>: iterable containing alert dictionaries

    Returns:
        aXmatchTable <astropy.Table>: alert data needed for Vizier cross-match
    """

    logging.info(f'type(alertDicts) = {type(alertDicts)}')
    data_list = []
    for alertDict in alertDicts:
        logging.info(f'alertDict.keys() = {alertDict.keys()}')
        data_list.append({
                        'objectId': alertDict['objectId'],
                        'candid': alertDict['candid'],
                        'candidate_ra': alertDict['candidate']['ra'],
                        'candidate_dec': alertDict['candidate']['dec']
                        })

    return Table(rows=data_list)


class xmatchVizier(DoFn):
    """
    Args:
        fcat1 (string): Path to csv file,
                        as written by get_alerts_ra_dec(fout=fcat1).

        cat2  (string): Passed through to XMatch.query().

    Returns:
        An astropy table with columns
          angDist, alert_id, ra, dec, 2MASS, RAJ2000, DEJ2000,
          errHalfMaj, errHalfMin, errPosAng, Jmag, Hmag, Kmag,
          e_Jmag, e_Hmag, e_Kmag, Qfl, Rfl, X, MeasureJD

    """
    def __init__(self, vizierCat='vizier:II/246/out', max_xm_distance=5*u.arcsec):
        self.cat2 = vizierCat
        self.max_distance = max_xm_distance

    def process (self, aXmatchTable):

        xmatchTable = XMatch.query(
                        cat1=aXmatchTable,
                        cat2=self.cat2,
                        max_distance=self.max_distance,
                        colRA1='candidate_ra',
                        colDec1='candidate_dec')

        # fix column names for upload to BQ
        xmatchTable.rename_column('2MASS', '_2MASS')
        # reformat to [dict,]
        xmatchDicts = xmatchTable.to_pandas().to_dict(orient='records')

        return xmatchDicts
