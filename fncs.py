from warnings import warn as _warn
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

H0 = 70 # km/s/Mpc
c = 3e5 # km/s

# LSST limiting magnitudes
# saturation will occur at ~(these values - 7)
LSST_mag_limits = {
                    'u': 23.5,
                    'g': 24.8,
                    'r': 24.4,
                    'i': 23.9,
                    'z': 23.3,
                    'y': 22.1
                    }

def calc_rL_from_mu(mu):
    """ returns luminosity distance [pc], given distance modulus mu
    """
    return 10*10**(mu/5)

def calc_z_from_r(r):
    """ r (array): distance in [Mpc]
        Returns z estimate using z = H0*r/c
            estimate is reasonable for 1 >> z >> 0.003
    """
    z = H0*r/c
    if min(z) < 0.003 or max(z) > 1:
        _warn("z is outside the range for which this approximation is good.")
    return z

def plot_distmod_v_rLandz(mu=None):
    """ mu (array): distance modulus for x axis
    """

    if mu is None: mu = np.linspace(0,45)
    rL = calc_rL_from_mu(mu) # pc
    rL_Mpc = rL/1e6
    # z = calc_z_from_r(rL_Mpc)

    plt.figure()
    ax1 = plt.gca()
    # ax2 = ax1.twinx()
    ax1.scatter(mu, rL, s=10)
    # ax2.scatter(mu, z, s=1)

    plt.semilogy()
    plt.xlabel('m - M')
    ax1.set_ylabel(f'r$_L$ [pc]')
    # ax2.set_ylabel(f'z')
    plt.grid(which='both')
    plt.show(block=False)

    return None

def bright(m1_m_m2, b1=1):
    b2 = b1* 2.5**(m1_m_m2)
    return b2

def plot_bright(m1_m_m2=None, save=None):
    if m1_m_m2 is None:
        m1_m_m2 = np.linspace(.1,20)

    plt.figure()
    plt.plot(m1_m_m2,bright(m1_m_m2))
    plt.semilogy()
    plt.grid(which='both')

    plt.xlabel('m1-m2')
    plt.ylabel(r'$\frac{b2}{b1} = 2.5^{m1 - m2}$')

    if save is not None: plt.savefig(save)
    plt.show(block=False)

def convert_mags(rL, m=None,absM=None):
    """ send m to return M, and vice versa
        rL: luminosity distance
    """

    if m is None:
        m = absM + 5*np.log10(r/10)
        return m

    else:
        absM = m - 5*np.log10(r/10)
        return absM



def plot_mMr(absM=None, r=None):
    if r is None:
        r = np.logspace(np.log10(1.1),np.log10(1e6)) # pc

    # if absM is None:
    #     absM = np.linspace(10,-20,31)

    plt.figure()
    # for M in absM:
    plt.plot(r, convert_mags(r,absM=absM), label=f'M = {absM}')
    plt.semilogx()
    plt.plot()
    plt.xlabel('r [pc]')
    plt.ylabel('m [mag]')
    plt.legend()
    plt.show(block=False)

    return None
