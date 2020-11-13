#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import numpy as np
from astropy.time import Time

def extract_epochs(epochs):
    """ Collects data from each observation epoch of a single alert.

    Args:
        epochs (list[dict]): one dict per observation epoch

    Returns:
        epoch_dict (dict): keys: 'mjd','flux','fluxerr','passband','photflag'
                           values: Lists of light curve data with one element
                                   per epoch.
    """

    # prepare empty lists to zip epoch data
    mjd, flux, fluxerr, passband, photflag = ([] for i in range(5))
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
        'photflag': photflag
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
