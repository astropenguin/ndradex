# from standard library
from pathlib import Path
from subprocess import run, PIPE

# from dependent packages
import numpy as np
import xarray as xr


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
