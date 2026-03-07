__all__ = ["run"]


# standard library
from contextlib import contextmanager
from csv import writer as csv_writer
from itertools import product
from os import PathLike
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Collection, IO, Iterator, TypeVar


# dependencies
import pandas as pd
import xarray as xr
from tqdm import tqdm
from .lamda import get_lamda
from .radex import RadexInput, runmap, to_input
from .specs import NDRadexOutput


# type hints
T = TypeVar("T")
Multiple = Collection[T] | T
StrPath = PathLike[str] | str


# constants
IN_FILE = "ndradex.in"
OUT_FILE = "ndradex.out"
NTH_FILE = "ndradex-{n}.out"


def run(
    datafile: StrPath,
    transition: Multiple[str],
    *,
    N: Multiple[float] = 1e15,
    T_kin: Multiple[float] = 1e2,
    n_H2: Multiple[float] = 1e3,
    n_pH2: Multiple[float] = 0.0,
    n_oH2: Multiple[float] = 0.0,
    n_e: Multiple[float] = 0.0,
    n_H: Multiple[float] = 0.0,
    n_He: Multiple[float] = 0.0,
    n_p: Multiple[float] = 0.0,
    T_bg: Multiple[float] = 2.73,
    I_bg: Multiple[StrPath] = "",
    dv: Multiple[float] = 1.0,
    radex: Multiple[StrPath] = "radex-uni",
    # options
    parallel: int | None = None,
    progress: bool = False,
    squeeze: bool = True,
    timeout: float | None = None,
    workdir: StrPath | None = None,
) -> xr.Dataset:
    """Run RADEX with multidimensional parameters.

    Args:
        datafile: Path of RADEX datafile.
        transition: Name(s) or ID(s) of transition.
        N: Value(s) of column density (cm^-2).
        T_kin: Value(s) of kinetic temperature (K).
        n_H2: Value(s) of H2 density (cm^-3).
        n_pH2: Value(s) of para-H2 density (cm^-3).
            Do not set nonzero value(s) together with ``n_H2``.
            Defaults to ``0.0`` (not used as a collider).
        n_oH2: Value(s) of ortho-H2 density (cm^-3).
            Do not set nonzero value(s) together with ``n_H2``.
            Defaults to ``0.0`` (not used as a collider).
        n_e: Value(s) of electron density (cm^-3).
            Defaults to ``0.0`` (not used as a collider).
        n_H: Value(s) of hydrogen density (cm^-3).
            Defaults to ``0.0`` (not used as a collider).
        n_He: Value(s) of helium density (cm^-3).
            Defaults to ``0.0`` (not used as a collider).
        n_p: Value(s) of proton density (cm^-3).
            Defaults to ``0.0`` (not used as a collider).
        T_bg: Value(s) of background temperature (K).
        I_bg: File(s) of user-defined background intensity.
        dv: Value(s) of line width (km s^-1).
        radex: Path(s) of RADEX binaries.
        parallel: Number of runs in parallel.
            Defaults to ``None`` (number of processors).
        progress: Whether to show a progress bar during runs.
        squeeze: Whether to drop dimensions whose length are 1.
        timeout: Timeout length per run in seconds.
            Defaults to ``None`` (unlimited run time).
        workdir: Path of the directory for intermediate files.
            Defaults to ``None`` (temporary directory).

    Returns:
        dataset: Result of multidimensional RADEX runs.

    """
    ds = NDRadexOutput.new(
        datafile=datafile,
        transition=transition,
        N=N,
        T_kin=T_kin,
        n_H2=n_H2,
        n_pH2=n_pH2,
        n_oH2=n_oH2,
        n_e=n_e,
        n_H=n_H,
        n_He=n_He,
        n_p=n_p,
        T_bg=T_bg,
        I_bg=I_bg,
        dv=dv,
        radex=radex,
    )

    with (
        set_workdir(workdir) as workdir,
        open(workdir / OUT_FILE, "w+", buffering=1) as csv,
        tqdm(total=ds.I.size, disable=not progress) as bar,
    ):
        writer = csv_writer(csv)

        for output in runmap(
            gen_radexes(ds),
            gen_inputs(ds, workdir),
            tail=ds.transition.size,
            timeout=timeout,
            parallel=parallel,
        ):
            writer.writerows(output)
            bar.update(ds.transition.size)

        if squeeze:
            return update_dataset(ds, csv).squeeze()
        else:
            return update_dataset(ds, csv)


def gen_inputs(dataset: xr.Dataset, workdir: Path, /) -> Iterator[RadexInput]:
    """Generate inputs to be passed to the RADEX binaries."""
    transitions = dataset.transition.values.tolist()
    lamda = get_lamda(dataset.datafile).prioritize(transitions)
    lamda.to_datafile(workdir / IN_FILE)
    freq = lamda.transitions[-len(transitions) :]["Frequency"]

    for n, index in enumerate(walk_dims(dataset)):
        yield to_input(
            datafile=workdir / IN_FILE,
            outfile=workdir / NTH_FILE.format(n=n),
            freq_min=min(freq) - 1e-9,  # type: ignore
            freq_max=max(freq) + 1e-9,  # type: ignore
            **index,
        )


def gen_radexes(dataset: xr.Dataset, /) -> Iterator[StrPath]:
    """Generate paths of the RADEX binaries."""
    for index in walk_dims(dataset):
        yield index["radex"]


@contextmanager
def set_workdir(workdir: StrPath | None = None, /) -> Iterator[Path]:
    """Set a directory for RADEX output files."""
    if workdir is None:
        with TemporaryDirectory() as workdir:
            yield Path(workdir).resolve()
    else:
        yield Path(workdir).expanduser().resolve()


def update_dataset(dataset: xr.Dataset, csv: IO[str], /) -> xr.Dataset:
    """Update data variables of a dataset by a CSV file."""
    csv.seek(0)
    df = pd.read_csv(csv, header=None, names=list(dataset.data_vars))

    dims = list(dataset.dims)
    dims.append(dims.pop(0))
    transposed = dataset.transpose(*dims)

    for name, var in transposed.data_vars.items():
        var[:] = df[name].to_numpy().reshape(var.shape)

    return dataset


def walk_dims(dataset: xr.Dataset, /) -> Iterator[dict[str, Any]]:
    """Generate combinations of the dataset's dimensions."""
    dims = dict(dataset.indexes)
    dims.pop("transition")

    for values in product(*dims.values()):
        yield dict(zip(dims.keys(), values))
