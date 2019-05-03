__all__ = ['run']

# from standard library
from enum import Enum, auto
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory

# from dependent packages
import ndradex
import numpy as np
import pandas as pd
import xarray as xr

# module constants
class Dims(Enum):
    QN_ul = auto()
    T_kin = auto()
    N_mol = auto()
    n_H2  = 'H2'
    n_pH2 = 'p-H2'
    n_oH2 = 'o-H2'
    n_e   = 'e'
    n_H   = 'H'
    n_He  = 'He'
    n_Hp  = 'H+'
    T_bg  = auto()
    dv    = auto()
    geom  = auto()

class Vars(Enum):
    E_u   = auto()
    freq  = auto()
    wavel = auto()
    T_ex  = auto()
    tau   = auto()
    T_r   = auto()
    pop_u = auto()
    pop_l = auto()
    I     = auto()
    F     = auto()


# main function
def run(query, QN_ul, T_kin=100, N_mol=1e15, n_H2=1e3,
        n_pH2=None, n_oH2=None, n_e=None, n_H=None, n_He=None,
        n_Hp=None, T_bg=2.73, dv=1.0, geom='uni', squeeze=True):
    """Run grid RADEX calculation and get results as xarray.Dataset."""
    empty = get_empty_array(QN_ul, T_kin, N_mol, n_H2, n_pH2, n_oH2,
                            n_e, n_H, n_He, n_Hp, T_bg, dv, geom)

    with TemporaryDirectory(dir='.') as tempdir:
        with ndradex.db.LAMDA(query, tempdir) as lamda:
            inputs = generate_inputs(lamda, empty)


# sub functions
def generate_inputs(lamda, empty):
    """Generate RADEX input string iteratively."""
    template = get_input_template(lamda, empty)

    for kwargs in generate_kwargs(lamda, empty):
        yield template.format(**kwargs)


def generate_radex_paths(lamda, empty):
    """Generate RADEX path iteratively."""
    for kwargs in generate_kwargs(lamda, empty):
        yield 'radex-' + kwargs['geom']


# utility functions
def get_empty_array(QN_ul, T_kin=100, N_mol=1e15, n_H2=1e3,
                    n_pH2=None, n_oH2=None, n_e=None, n_H=None,
                    n_He=None, n_Hp=None, T_bg=2.73, dv=1.0, geom='uni'):
    """Make an empty xarray.DataArray for storing grid RADEX results."""
    values = {Dims.QN_ul: ensure_values(QN_ul),
              Dims.T_kin: ensure_values(T_kin, 'K'),
              Dims.N_mol: ensure_values(N_mol, 'cm^-2'),
              Dims.n_H2:  ensure_values(n_H2, 'cm^-3'),
              Dims.n_pH2: ensure_values(n_pH2, 'cm^-3'),
              Dims.n_oH2: ensure_values(n_oH2, 'cm^-3'),
              Dims.n_e:   ensure_values(n_e, 'cm^-3'),
              Dims.n_H:   ensure_values(n_H, 'cm^-3'),
              Dims.n_He:  ensure_values(n_He, 'cm^-3'),
              Dims.n_Hp:  ensure_values(n_Hp, 'cm^-3'),
              Dims.T_bg:  ensure_values(T_bg, 'K'),
              Dims.dv:    ensure_values(dv, 'km/s'),
              Dims.geom:  ensure_values(geom)}

    coords = [(dim.name, values[dim]) for dim in Dims]
    shape = [c[1].size for c in coords]

    return xr.DataArray(np.empty(shape), coords)


def generate_kwargs(lamda, empty):
    """Generate keyword args for RADEX input iteratively."""
    freq_lim = lamda.freq_lim

    dims, coords = empty.dims, empty.coords
    flatargs = product(*(coords[dim].values for dim in dims))

    for args in flatargs:
        kwargs = dict(zip(dims, args))
        kwargs['id'] = ndradex.utils.random_hex()
        kwargs['freq_lim'] = freq_lim[kwargs['QN_ul']]
        yield kwargs


def get_input_template(lamda, empty):
    """Make template string for RADEX input."""
    n_dims = [dim for dim in empty.dims if dim.startswith('n_')
              and not np.any(np.isnan(empty.coords[dim]))]

    template = [f'{lamda}', f'{lamda}.{{id}}.out',
                '{freq_lim}', '{T_kin}', str(len(n_dims))]

    for dim in n_dims:
        template.extend([Dims[dim].value, f'{{{dim}}}'])

    template.extend(['{T_bg}', '{N_mol}', '{dv}', '0'])
    return '\n'.join(template)


def ensure_values(values, unit=None):
    # lazy import of astropy-related things
    from astropy import units as u

    if values is None:
        values = np.nan

    if isinstance(values, u.Quantity):
        unit = u.Unit(unit)
        values = values.to(unit)

    values = np.asarray(values)

    if values.size==1 and not values.shape:
        return values[np.newaxis]
    else:
        return values
