# from standard library
from enum import Enum
from pathlib import Path
from subprocess import run, PIPE

# from dependent packages
import numpy as np
import xarray as xr
import ndradex as nd

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
def _get_inputs(lamda, coords):
    keys, values = zip(*coords)
    template = _get_template(lamda, coords)

    for vals in product(*values):
        items = dict(zip(keys, vals))
        freq_lim = lamda.freq_lim[items['QN_ul']]
        yield template.format(freq_lim=freq_lim, **items)


def _get_outputs(lamda, coords):
    dataset = xr.Dataset()
    shape = [c[1].size for c in coords]

    for var in Vars:
        array = xr.DataArray(np.empty(shape), coords, name=var.value)
        dataset[var.value] = array

    dataset['desc'] = repr(lamda)
    return dataset


def _run_radex(input, geometry='uni'):
    # return cache if exists
    pass


def _get_coords(QN_ul, T_kin=100, T_bg=2.73, N_mol=1e15, n_H2=1e3,
                 dv=1.0, geo='uni', n_pH2=None, n_oH2=None,
                 n_e=None, n_H=None, n_He=None, n_Hp=None):
    """Make coords as list for xarray.DataArray objects."""
    items = {Dims.QN_ul: nd.ensure_values(QN_ul),
             Dims.T_kin: nd.ensure_values(T_kin, 'K'),
             Dims.T_bg:  nd.ensure_values(T_bg, 'K'),
             Dims.N_mol: nd.ensure_values(N_mol, 'cm^-2'),
             Dims.n_H2:  nd.ensure_values(n_H2, 'cm^-3'),
             Dims.n_pH2: nd.ensure_values(n_pH2, 'cm^-3'),
             Dims.n_oH2: nd.ensure_values(n_oH2, 'cm^-3'),
             Dims.n_e:   nd.ensure_values(n_e, 'cm^-3'),
             Dims.n_H:   nd.ensure_values(n_H, 'cm^-3'),
             Dims.n_He:  nd.ensure_values(n_He, 'cm^-3'),
             Dims.n_Hp:  nd.ensure_values(n_Hp, 'cm^-3'),
             Dims.dv:    nd.ensure_values(dv, 'km/s'),
             Dims.geo:   nd.ensure_values(geo)}

    return [(dim.value, items[dim]) for dim in Dims]


def _get_template(lamda, coords):
    prefix = 'n_'
    coords = [c for c in coords if np.all(c[1] != None)]
    n_coords = [c for c in coords if c[0].startswith(prefix)]

    template = '{}\n'.format(lamda)
    template += 'radex.out\n{freq_lim}\n{T_kin}\n'
    template += '{}\n'.format(len(n_coords))

    for dim, values in n_coords:
        template += '{}\n'.format(dim.lstrip(prefix))
        template += '{{{}}}\n'.format(dim)

    template += '{T_bg}\n{N_mol}\n{dv}\n0'
    return template
