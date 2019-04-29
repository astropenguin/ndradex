# from standard library
from enum import Enum
from pathlib import Path
from subprocess import run, PIPE

# from dependent packages
import numpy as np
import xarray as xr

# module constants
class Dims(Enum):
    QN_ul = 'QN_ul'
    N_mol = 'N_mol'
    T_kin = 'T_kin'
    T_bg  = 'T_bg'
    n_H2  = 'n_H2'
    n_pH2 = 'n_p-H2'
    n_oH2 = 'n_o-H2'
    n_e   = 'n_e'
    n_H   = 'n_H'
    n_He  = 'n_He'
    n_Hp  = 'n_H+'
    dv    = 'dv'
    geo   = 'geo'

class Vars(Enum):
    E_u   = 'E_u'
    freq  = 'freq'
    wavel = 'wavel'
    T_ex  = 'T_ex'
    tau   = 'tau'
    T_r   = 'T_r'
    pop_u = 'pop_u'
    pop_l = 'pop_l'
    I     = 'I'
    F     = 'F'


# main function
def calc(moldata, transition, T_kin=100, N_mol=1e15,
         n_coll=1e3, T_bg=2.73, dV=1.0, geometry='uni'):
    pass


# utility functions
def _make_input(moldata, transition, T_kin, N_mol, n_coll, T_bg, dV):
    # moldata is either string or LAMDA instance
    pass


def _run_radex(input, geometry='uni'):
    # return cache if exists
    pass
