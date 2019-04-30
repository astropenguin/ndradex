__all__ = ['run']

# from standard library
from concurrent.futures import ProcessPoolExecutor
from enum import Enum
from itertools import product
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
    geom  = 'geom'

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
def run(moldata, QN_ul, T_kin=100, N_mol=1e15, n_H2=1e3,
        n_pH2=None, n_oH2=None, n_e=None, n_H=None, n_He=None,
        n_Hp=None, T_bg=2.73, dv=1.0, geom='uni', squeeze=True):
    """Execute N-dim RADEX grid calculation."""
    coords = get_coords(QN_ul, T_kin, N_mol, n_H2, n_pH2, n_oH2,
                        n_e, n_H, n_He, n_Hp, T_bg, dv, geom)

    with TemporaryDirectory(dir='.') as tempdir:
        with nd.LAMDA(moldata, tempdir) as lamda:
            inputs = get_inputs(lamda, coords)
            geoms = get_geometries(coords)
            return calc(inputs, geoms)


def calc(inputs, geoms):
    with ProcessPoolExecutor(4) as executor:
        mapped = executor.map(nd.run_radex, inputs, radexes)


# sub functions
def get_inputs(lamda, coords):
    """Make RADEX input strings iteratively."""
    keys, values = zip(*coords)
    template = get_template(lamda, coords)

    for vals in product(*values):
        items = dict(zip(keys, vals))
        items['output_id'] = nd.utils.random_hex()
        items['freq_lim'] = lamda.freq_lim[items['QN_ul']]
        yield template.format(**items)


def get_radexes(coords):
    keys, values = zip(*coords)

    for vals in product(*values):
        geom = dict(zip(keys, vals))['geom']
        yield nd.config['radex'][geom]


def get_outputs(lamda, coords):
    """Make empty xarray.Dataset object."""
    dataset = xr.Dataset()
    shape = [c[1].size for c in coords]

    for var in Vars:
        array = xr.DataArray(np.empty(shape), coords, name=var.value)
        dataset[var.value] = array

    dataset['desc'] = repr(lamda)
    return dataset


# utility functions
def get_coords(QN_ul, T_kin=100, N_mol=1e15, n_H2=1e3,
                n_pH2=None, n_oH2=None, n_e=None, n_H=None,
                n_He=None, n_Hp=None, T_bg=2.73, dv=1.0, geom='uni'):
    """Make coords as list for xarray.DataArray objects."""
    items = {Dims.QN_ul: ensure_values(QN_ul),
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

    return [(dim.value, items[dim]) for dim in Dims]


def get_template(lamda, coords):
    """Make template string for RADEX input."""
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


def ensure_values(values, unit=None):
    # lazy import of astropy-related things
    from astropy import units as u

    if isinstance(values, u.Quantity):
        unit = u.Unit(unit)
        values = values.to(unit)

    values = np.asarray(values)

    if values.size==1 and not values.shape:
        return values[np.newaxis]
    else:
        return values
