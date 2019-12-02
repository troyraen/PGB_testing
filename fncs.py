import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

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

def convert_mags(r, m=None,absM=None):
    """ send m to return M, and vice versa
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
    plt.plot(r, convert_mags(r,absM=absM))
    plt.semilogx()
    plt.plot()
    plt.show(block=False)

    return None
