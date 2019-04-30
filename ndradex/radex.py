# from standard library
from enum import Enum
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory

# from dependent packages
import numpy as np
import xarray as xr
import ndradex as nd

# module constants
class Dims(Enum):
    QN_ul = 'QN_ul'
    T_kin = 'T_kin'
    N_mol = 'N_mol'
    n_H2  = 'n_H2'
    n_pH2 = 'n_p-H2'
    n_oH2 = 'n_o-H2'
    n_e   = 'n_e'
    n_H   = 'n_H'
    n_He  = 'n_He'
    n_Hp  = 'n_H+'
    T_bg  = 'T_bg'
    dv    = 'dv'

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
def calc(moldata, QN_ul, T_kin=100, T_bg=2.73, N_mol=1e15,
         n_H2=1e3, dv=1.0, n_pH2=None, n_oH2=None, n_e=None,
         n_H=None, n_He=None, n_Hp=None, geometry='uni'):
    """Execute N-dim RADEX calculation."""
    coords = _get_coords(QN_ul, T_kin, N_mol, n_H2, n_pH2,
                         n_oH2, n_e, n_H, n_He, n_Hp, T_bg, dv)

    with TemporaryDirectory(dir='.') as tempdir:
        with nd.LAMDA(moldata, tempdir) as lamda:
            inputs = _get_inputs(lamda, coords)
            outputs = _get_outputs(lamda, coords)


# utility functions
def _get_inputs(lamda, coords):
    keys, values = zip(*coords)
    template = _get_template(lamda, coords)

    for vals in product(*values):
        items = dict(zip(keys, vals))
        qn_ul = items['QN_ul']
        items['output_id'] = nd.random_hex()
        items['freq_lim'] = lamda.freq_lim[qn_ul]
        yield template.format(**items)


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


def _get_coords(QN_ul, T_kin=100, N_mol=1e15, n_H2=1e3,
                n_pH2=None, n_oH2=None, n_e=None, n_H=None,
                n_He=None, n_Hp=None, T_bg=2.73, dv=1.0):
    """Make coords as list for xarray.DataArray objects."""
    items = {Dims.QN_ul: nd.ensure_values(QN_ul),
             Dims.T_kin: nd.ensure_values(T_kin, 'K'),
             Dims.N_mol: nd.ensure_values(N_mol, 'cm^-2'),
             Dims.n_H2:  nd.ensure_values(n_H2, 'cm^-3'),
             Dims.n_pH2: nd.ensure_values(n_pH2, 'cm^-3'),
             Dims.n_oH2: nd.ensure_values(n_oH2, 'cm^-3'),
             Dims.n_e:   nd.ensure_values(n_e, 'cm^-3'),
             Dims.n_H:   nd.ensure_values(n_H, 'cm^-3'),
             Dims.n_He:  nd.ensure_values(n_He, 'cm^-3'),
             Dims.n_Hp:  nd.ensure_values(n_Hp, 'cm^-3'),
             Dims.T_bg:  nd.ensure_values(T_bg, 'K'),
             Dims.dv:    nd.ensure_values(dv, 'km/s')}

    return [(dim.value, items[dim]) for dim in Dims]


def _get_template(lamda, coords):
    prefix = 'n_'
    coords = [c for c in coords if np.all(c[1] != None)]
    n_coords = [c for c in coords if c[0].startswith(prefix)]

    template = '{}\n'.format(lamda)
    template += '{}.{{output_id}}\n'.format(lamda)
    template += '{freq_lim}\n{T_kin}\n'
    template += '{}\n'.format(len(n_coords))

    for dim, values in n_coords:
        template += '{}\n'.format(dim.lstrip(prefix))
        template += '{{{}}}\n'.format(dim)

    template += '{T_bg}\n{N_mol}\n{dv}\n0'
    return template
