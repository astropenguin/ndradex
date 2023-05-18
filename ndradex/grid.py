__all__ = ["run"]


# standard library
from concurrent.futures import ProcessPoolExecutor
from enum import Enum, auto
from itertools import product, repeat
from pathlib import Path
from random import getrandbits
from tempfile import TemporaryDirectory


# dependencies
import numpy as np
import pandas as pd
import xarray as xr
from tqdm import tqdm
from .consts import (
    DV,
    GEOM,
    N_E,
    N_H,
    N_H2,
    N_HE,
    N_HP,
    N_MOL,
    N_OH2,
    N_PARALLEL,
    N_PH2,
    PROGRESS,
    RADEX_BIN,
    SQUEEZE,
    T_BG,
    T_KIN,
    TIMEOUT,
)
from .db import LAMDA
from .radex import run as run_radex


# constants
class Dims(Enum):
    QN_ul = "QN_ul"
    T_kin = "T_kin"
    N_mol = "N_mol"
    n_H2 = "H2"
    n_pH2 = "p-H2"
    n_oH2 = "o-H2"
    n_e = "e"
    n_H = "H"
    n_He = "He"
    n_Hp = "H+"
    T_bg = "T_bg"
    dv = "dv"
    geom = "geom"


class Vars(Enum):
    E_u = auto()
    freq = auto()
    wavel = auto()
    T_ex = auto()
    tau = auto()
    T_r = auto()
    pop_u = auto()
    pop_l = auto()
    I = auto()
    F = auto()


# main function
def run(
    query,
    QN_ul,
    T_kin=T_KIN,
    N_mol=N_MOL,
    n_H2=N_H2,
    n_pH2=N_PH2,
    n_oH2=N_OH2,
    n_e=N_E,
    n_H=N_H,
    n_He=N_HE,
    n_Hp=N_HP,
    T_bg=T_BG,
    dv=DV,
    geom=GEOM,
    *,
    squeeze=SQUEEZE,
    progress=PROGRESS,
    timeout=TIMEOUT,
    n_procs=N_PARALLEL,
    work_dir=None,
):
    """Run grid RADEX calculation and get results as xarray.Dataset.

    This is the main function of ndRADEX. It provides 13 parameters
    which can be griddable (i.e., both scalar and array are accepted).
    The output is an xarray's Dataset of multi-dimensional DataArrays
    whose shapes are the product of gridded parameters (i.e., argument
    of parameter is array-like and its length is more than one).
    For example, if you run grid RADEX calculation for CO (1-0) with
    kinetic temperatures of [100, 200, 300, 400, 500] K, and H2
    densities of [1e3, 1e4, 1e5] cm^-3, then the shepe is (5, 3).
    For more information: https://github.com/astropenguin/ndradex/wiki

    Args:
        query (str): Name of LAMDA datafile (e.g., 'co' or 'co.dat').
            You can also specify the path or URL of the datafile.
        QN_ul (str, griddable): Name(s) of transition (e.g., '1-0').
        T_kin (int or float, griddable): Value(s) of kinetic temperature
            in units of K.
        N_mol (int or float, griddable): Value(s) of column density of
            molecule (or atom) in units of cm^-2.
        n_H2 (int or float, griddable): Value(s) of H2 density in units
            of cm^-3. Do not specify together with n_pH2 and n_OH2.
        n_pH2 (int or float, griddable): Value(s) of para-H2 density
            in units of cm^-3. Do not specify together with n_H2.
            This parameter is not activated by default.
        n_oH2 (int or float, griddable): Value(s) of ortho-H2 density
            in units of cm^-3. Do not specify together with n_H2.
            This parameter is not activated by default.
        n_e (int or float, griddable): Value(s) of electron density
            in units of cm^-3. This parameter is not activated by default.
        n_H (int or float, griddable): Value(s) of atomic hydrogen density
            in units of cm^-3. This parameter is not activated by default.
        n_He (int or float, griddable): Value(s) of atomic helium density
            in units of cm^-3. This parameter is not activated by default.
        n_Hp (int or float, griddable): Value(s) of ionized hydrogen density
            in units of cm^-3. This parameter is not activated by default.
        T_bg (int or float, griddable): Value(s) of background temperature
            in units of K.
        dv (int or float, griddable): Value(s) of FWHM width of a line
            in units of km s^-1.
        geom (str, griddable): Name(s) of geometry for photon escape
            probability. Either 'uni', 'lvg', or 'slab' is acccepted.
        squeeze (bool, optional): If True (default), then dimensions
            whose length is only one are dropped.
        progress (bool, optional): If True (default), then a bar is
            shown during the calculation to show the progress.
        timeout (int, optional): Timeout of a RADEX run in units of second.
            Default is None (unlimited run time is permitted).
        n_procs (int, optional): Number of processes for asynchronous
            RADEX calculations. Default is None (<number of CPU count>-1).
        work_dir (path-like, optional): Path of working directory under
            which a temporary directory for intermediate files is created.
            The temporary directory is sure to be automatically created and
            deleted even if the function is interrupted by some errors.
            Default is None (the OS-native temporary directory is used).

    Returns:
        dataset (xarray.Dataset): Dataset which contains DataArrays of:
            E_u: upper state energy in units of K,
            freq: transition frequency in units of GHz,
            wavel: transition wavelength in units of um,
            T_ex: excitation temperature in units of K,
            tau: opacity of line,
            T_r: peak intensity in units of K
            pop_u: upper state population
            pop_l: lower state population,
            I: flux of line in units of K km s^-1,
            F: flux of line in units of erg s^-1 cm^-2.

    Examples:
        To get the values of CO J=[1-0, 2-1] @ T_kin = [100, 200, 300,
        400, 500] K, n_H2 = [1e3, 1e4, 1e5] cm^-3, N_CO = 1e15 cm^-2,
        T_bg = 2.73 K, and dv = 1.0 km s^-1:

            >>> dataset = run('co', ['1-0', '2-1'],
                              T_kin=[100, 200, 300, 400, 500],
                              n_H2=[1e3, 1e4, 1e5],
                              N_mol=1e15, T_bg=2.73, dv=1.0)
            >>> print(dataset)
            <xarray.Dataset>
            Dimensions:      (QN_ul: 2, T_kin: 5, n_H2: 3)
            Coordinates:
            * QN_ul        (QN_ul) <U3 '1-0' '2-1'
            * T_kin        (T_kin) int64 100 200 300 400 500
                N_mol        float64 1e+15
            * n_H2         (n_H2) float64 1e+03 1e+04 1e+05
                T_bg         float64 2.73
                dv           float64 1.0
                geom         <U3 'uni'
                description  <U9 'LAMDA(CO)'
            Data variables:
                E_u          (QN_ul, T_kin, n_H2) float64 5.5 ...
                freq         (QN_ul, T_kin, n_H2) float64 115.3 ...
                wavel        (QN_ul, T_kin, n_H2) float64 2.601e+03 ...
                T_ex         (QN_ul, T_kin, n_H2) float64 132.5 ...
                tau          (QN_ul, T_kin, n_H2) float64 0.009966 ...
                T_r          (QN_ul, T_kin, n_H2) float64 1.278 ...
                pop_u        (QN_ul, T_kin, n_H2) float64 0.4934 ...
                pop_l        (QN_ul, T_kin, n_H2) float64 0.1715 ...
                I            (QN_ul, T_kin, n_H2) float64 1.36 ...
                F            (QN_ul, T_kin, n_H2) float64 2.684e-08 ...

    """
    empty = get_empty_array(
        QN_ul,
        T_kin,
        N_mol,
        n_H2,
        n_pH2,
        n_oH2,
        n_e,
        n_H,
        n_He,
        n_Hp,
        T_bg,
        dv,
        geom,
    )

    with TemporaryDirectory(dir=work_dir) as temp_dir:
        with LAMDA(query, temp_dir) as lamda:
            # make an empty dataset and flattened args
            dataset = get_empty_dataset(lamda, empty)
            iterables = [
                generate_inputs(lamda, empty),
                generate_radex_paths(lamda, empty),
                repeat(timeout),
            ]

            # run RADEX with multiprocess and update dataset
            execute(
                dataset,
                *iterables,
                dir=temp_dir,
                progress=progress,
                n_procs=n_procs,
            )

    return finalize(dataset, squeeze)


# sub functions
def generate_inputs(lamda, empty):
    """Generate RADEX input string iteratively."""
    template = get_input_template(lamda, empty)

    for kwargs in generate_kwargs(lamda, empty):
        yield template.format(**kwargs).split("\n")


def generate_radex_paths(lamda, empty):
    """Generate RADEX path iteratively."""
    path = str(RADEX_BIN / "radex-{geom}")

    for kwargs in generate_kwargs(lamda, empty):
        yield path.format(geom=kwargs[Dims.geom.name])


def get_empty_dataset(lamda, empty):
    """Make an empty xarray.Dataset for storing DataArrays."""
    dataset = xr.Dataset({var.name: empty.copy() for var in Vars})
    dataset.coords["description"] = repr(lamda)
    return dataset


def execute(dataset, *iterables, dir=".", progress=True, n_procs=None):
    """Run grid RADEX calculation and store results into a dataset."""
    total = np.prod(list(dataset.dims.values()))
    outfile = Path(dir, "grid.out").expanduser().resolve()

    # fmt: off
    with tqdm(total=total, disable=not progress) as bar, \
         ProcessPoolExecutor(n_procs) as executor, \
         outfile.open("w", buffering=1) as f:
    # fmt: on
        for output in executor.map(run_radex, *iterables):
            f.write(",".join(output) + "\n")
            bar.update(1)

    names = [var.name for var in Vars]
    df = pd.read_csv(outfile, header=None, names=names)

    for name in names:
        da = dataset[name]
        da.values = df[name].to_numpy().reshape(da.shape)


def finalize(dataset, squeeze=True):
    """Do finalization before returning a dataset."""
    if not squeeze:
        return dataset

    for dim in dataset.dims:
        coord = dataset.coords[dim]

        if np.issubdtype(coord.dtype, np.str_):
            continue

        if np.any(np.isnan(coord)):
            del dataset.coords[dim]

    return dataset.squeeze()


# utility functions
def get_empty_array(
    QN_ul,
    T_kin,
    N_mol,
    n_H2,
    n_pH2,
    n_oH2,
    n_e,
    n_H,
    n_He,
    n_Hp,
    T_bg,
    dv,
    geom,
):
    """Make an empty xarray.DataArray for storing grid RADEX results."""
    values = {
        Dims.QN_ul: ensure_values(QN_ul),
        Dims.T_kin: ensure_values(T_kin, "K"),
        Dims.N_mol: ensure_values(N_mol, "cm^-2"),
        Dims.n_H2: ensure_values(n_H2, "cm^-3"),
        Dims.n_pH2: ensure_values(n_pH2, "cm^-3"),
        Dims.n_oH2: ensure_values(n_oH2, "cm^-3"),
        Dims.n_e: ensure_values(n_e, "cm^-3"),
        Dims.n_H: ensure_values(n_H, "cm^-3"),
        Dims.n_He: ensure_values(n_He, "cm^-3"),
        Dims.n_Hp: ensure_values(n_Hp, "cm^-3"),
        Dims.T_bg: ensure_values(T_bg, "K"),
        Dims.dv: ensure_values(dv, "km/s"),
        Dims.geom: ensure_values(geom),
    }

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
        kwargs["id"] = get_random_hex(8)
        kwargs["freq_lim"] = freq_lim[kwargs["QN_ul"]]
        yield kwargs


def get_input_template(lamda, empty):
    """Make template string for RADEX input."""
    n_dims = [
        dim
        for dim in empty.dims
        if dim.startswith("n_") and not np.any(np.isnan(empty.coords[dim]))
    ]

    template = [
        f"{lamda}",
        f"{lamda}.{{id}}.out",
        "{freq_lim}",
        "{T_kin}",
        str(len(n_dims)),
    ]

    for dim in n_dims:
        template.extend([Dims[dim].value, f"{{{dim}}}"])

    template.extend(["{T_bg}", "{N_mol}", "{dv}", "0"])
    return "\n".join(template)


def ensure_values(values, unit=None):
    """Ensure the type of output and the unit of values."""
    # lazy import of astropy-related things
    from astropy import units as u

    if values is None:
        values = np.nan

    if isinstance(values, u.Quantity):
        unit = u.Unit(unit)
        values = values.to(unit)

    values = np.asarray(values)

    if values.size == 1 and not values.shape:
        return values[np.newaxis]
    else:
        return values


def get_random_hex(length: int = 8) -> str:
    """Return a random hexadecimal string of given length."""
    return f"{getrandbits(length * 4):x}"
