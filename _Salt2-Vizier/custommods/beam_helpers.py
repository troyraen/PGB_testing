#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import numpy as np
import pandas as pd
from astropy.table import Table
from astropy.time import Time
import astropy.units as u

def extract_epochs(alert):
    """ Collects data from each observation epoch of a single alert.

    Args:
        alert (dict): dictionary of alert data from ZTF

    Returns:
        epoch_dict (dict): keys: 'mjd','flux','fluxerr','passband','photflag'
                           values: Lists of light curve data with one element
                                   per epoch.
    """

    # collect epochs
    epochs = alert['prv_candidates'] + [alert['candidate']]
    
    # prepare empty lists to zip epoch data
    mjd, flux, fluxerr, passband, photflag, magzpsci, magzpsciunc, zpsys = ([] for i in range(8))
    # passband mapping
    fid_dict = {1: 'g', 2: 'r', 3: 'i'}
    # set and track epochs with missing zeropoints
    zp_fallback, zp_in_keys = 26.0, [0 for i in range(len(epochs))]

    for epoch in epochs:
        # skip nondetections.
        if epoch['magpsf'] is None: continue
        # fix this. try setting magnitude to epoch['diffmaglim']

        # check zeropoint (early schema(s) did not contain this)
        if 'magzpsci' not in epoch.keys():  # fix this. do something better.
            _warn('Epoch does not have zeropoint data. '
                  'Setting to {}'.format(zp_fallback))
            zp_in_keys[n] = 1
            epoch['magzpsci'] = zp_fallback

        # Gather epoch data
        mjd.append(jd_to_mjd(epoch['jd']))
        f, ferr = mag_to_flux(epoch['magpsf'], epoch['magzpsci'],
                              epoch['sigmapsf'])
        flux.append(f)
        fluxerr.append(ferr)
        passband.append(fid_dict[epoch['fid']])
        photflag.append(4096)  # fix this, determines trigger time
        # (1st mjd where this == 6144)
        magzpsci.append(epoch['magzpsci'])
        magzpsciunc.append(epoch['magzpsciunc'])
        zpsys.append('ab')

    # check zeropoint consistency
    # either 0 or all epochs (with detections) should be missing zeropoints
    if sum(zp_in_keys) not in [0, len(mjd)]:
        raise ValueError((f'Inconsistent zeropoint values in alert {oid}. '
                          'Cannot continue with classification.'))

    # Set trigger date. fix this.
    photflag = np.asarray(photflag)
    photflag[flux == np.max(flux)] = 6144

    # Gather info
    epoch_dict = {
        'mjd': np.asarray(mjd),
        'flux': np.asarray(flux),
        'fluxerr': np.asarray(fluxerr),
        'passband': np.asarray(passband),
        'photflag': photflag,
        'magzpsci': magzpsci,
        'magzpsciunc': magzpsciunc,
        'zpsys': zpsys,
    }

    return epoch_dict

def mag_to_flux(mag, zeropoint, magerr):
    """ Converts an AB magnitude and its error to fluxes.
    """
    flux = 10 ** ((zeropoint - mag) / 2.5)
    fluxerr = flux * magerr * np.log(10 / 2.5)
    return flux, fluxerr

def jd_to_mjd(jd):
    """ Converts Julian Date to modified Julian Date.
    """
    return Time(jd, format='jd').mjd

def format_for_salt2(epoch_dict):
    """ Formats alert data for input to Salt2.
    
    Args:
        epoch_dict (dict): epoch_dict = extract_epochs(epochs)

    Returns:
        epoch_tbl: (Table): astropy Table of epoch data formatted for Salt2
    """

    col_map = {# salt2 name: ztf name,
                'time': 'mjd',
                'band': 'passband',
                'flux': 'flux',
                'fluxerr': 'fluxerr',
                'zp': 'magzpsci',
                'zpsys': 'zpsys',
                }

    data = {sname: epoch_dict[zname] for sname, zname in col_map.items()}
    data['band'] = [f'ztf{val}' for val in data['band']]  # salt2 registered bandpass name
    
    epoch_tbl = Table(data)

    return epoch_tbl
    
def is_transient(alert):
    """ Checks whether alert is likely to be an extragalactic transient.
    Most of this was taken from 
    https://github.com/ZwickyTransientFacility/ztf-avro-alert/blob/master/notebooks/Filtering_alerts.ipynb

    Args:
        alert (dict): dictionary of alert data from ZTF

    Returns:
        is_transient (bool): whether alert is likely to be an extragalactic transient.
    """

    dflc = make_dataframe(alert)
    candidate = dflc.loc[0]
    
    is_positive_sub = candidate['isdiffpos'] == 't'
    
    if (candidate['distpsnr1'] is None) or (candidate['distpsnr1'] > 1.5):
        no_pointsource_counterpart = True
    else:
        if candidate['sgscore1'] < 0.5:
            no_pointsource_counterpart = True
        else:
            no_pointsource_counterpart = False
            
    where_detected = (dflc['isdiffpos'] == 't') # nondetections will be None
    if np.sum(where_detected) >= 2:
        detection_times = dflc.loc[where_detected,'jd'].values
        dt = np.diff(detection_times)
        not_moving = np.max(dt) >= (30*u.minute).to(u.day).value
    else:
        not_moving = False
    
    # want minimum number of detections before fitting with Salt2
    if np.sum(where_detected) >= 10:
        ten_detections = True
    else:
        ten_detections = False
    
    no_ssobject = (candidate['ssdistnr'] is None) or (candidate['ssdistnr'] < 0) or (candidate['ssdistnr'] > 5)
    
    return is_positive_sub and no_pointsource_counterpart and not_moving and no_ssobject and ten_detections

def make_dataframe(alert):
    """ Packages an alert into a dataframe.
    Taken from https://github.com/ZwickyTransientFacility/ztf-avro-alert/blob/master/notebooks/Filtering_alerts.ipynb
    """
    dfc = pd.DataFrame(alert['candidate'], index=[0])
    df_prv = pd.DataFrame(alert['prv_candidates'])
    dflc = pd.concat([dfc,df_prv], ignore_index=True)
    # we'll attach some metadata--not this may not be preserved after all operations
    # https://stackoverflow.com/questions/14688306/adding-meta-information-metadata-to-pandas-dataframe
    dflc.objectId = alert['objectId']
    dflc.candid = alert['candid']
    return dflc