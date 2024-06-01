__all__ = ["run"]


# standard library
from csv import writer as csv_writer
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from tempfile import TemporaryFile
from typing import Any, Collection, IO, Iterator, Literal, TypeVar, Union


# dependencies
import numpy as np
import pandas as pd
import xarray as xr
from astropy.units import Quantity
from tqdm import tqdm
from xarray_dataclasses import AsDataset, DataModel, Attr, Coordof, Data, Dataof
from .consts import (
    DV,
    N,
    N_E,
    N_H,
    N_H2,
    N_HE,
    N_HP,
    N_OH2,
    N_PH2,
    PARALLEL,
    PROGRESS,
    RADEX,
    SQUEEZE,
    T_BG,
    T_KIN,
    TIMEOUT,
    WORKDIR,
)
from .lamda import query
from .radex import Input, Parallel, Timeout, Workdir, runmap, to_input


# type hints
T = TypeVar("T")
Multiple = Union[Collection[T], T]
PathLike = Union[Path, str]
VarDims = tuple[
    Literal["transition"],
    Literal["T_kin"],
    Literal["n_H2"],
    Literal["n_pH2"],
    Literal["n_oH2"],
    Literal["n_e"],
    Literal["n_H"],
    Literal["n_He"],
    Literal["n_Hp"],
    Literal["T_bg"],
    Literal["N"],
    Literal["dv"],
    Literal["radex"],
]


# constants
CSV = "radex.csv"
OUTFILE = "radex.out"


def run(
    datafile: PathLike,
    transition: Multiple[str],
    *,
    T_kin: Multiple[float] = T_KIN,
    n_H2: Multiple[float] = N_H2,
    n_pH2: Multiple[float] = N_PH2,
    n_oH2: Multiple[float] = N_OH2,
    n_e: Multiple[float] = N_E,
    n_H: Multiple[float] = N_H,
    n_He: Multiple[float] = N_HE,
    n_Hp: Multiple[float] = N_HP,
    T_bg: Multiple[float] = T_BG,
    N: Multiple[float] = N,
    dv: Multiple[float] = DV,
    radex: Multiple[PathLike] = RADEX,
    # options
    parallel: Parallel = PARALLEL,
    progress: bool = PROGRESS,
    squeeze: bool = SQUEEZE,
    timeout: Timeout = TIMEOUT,
    workdir: Workdir = WORKDIR,
) -> xr.Dataset:
    """Run RADEX with multidimensional parameters.

    Args:
        datafile: Path of RADEX datafile.
        transition: Name(s) or ID(s) of transition.

    Keyword Args:
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
        n_Hp: Value(s) of proton density (cm^-3).
            Defaults to ``0.0`` (not used as a collider).
        T_bg: Value(s) of background temperature (K).
        N: Value(s) of column density (cm^-2).
        dv: Value(s) of line width (km s^-1).
        radex: Path(s) of RADEX binaries.
        parallel: Number of runs in parallel.
            Defaults to ``None`` (number of processors).
        progress: Whether to show a progress bar during runs.
        squeeze: Whether to drop dimensions whose length are 1.
        timeout: Timeout length per run in units of seconds.
            Defaults to ``None`` (unlimited run time).
        workdir: Path of the directory for intermediate files.
            Defaults to ``None`` (temporary directory).

    Returns:
        dataset: Result of multidimensional RADEX runs.

    """
    ds = EmptySet.new(
        datafile=datafile,
        transition=transition,
        T_kin=T_kin,
        n_H2=n_H2,
        n_pH2=n_pH2,
        n_oH2=n_oH2,
        n_e=n_e,
        n_H=n_H,
        n_He=n_He,
        n_Hp=n_Hp,
        T_bg=T_bg,
        N=N,
        dv=dv,
        radex=radex,
    )

    with (
        TemporaryFile("w+", buffering=1) as csv,
        tqdm(total=ds.I.size, disable=not progress) as bar,
    ):
        writer = csv_writer(csv)

        for output in runmap(
            radexes=gen_radexes(ds),
            inputs=gen_inputs(ds),
            tail=ds.transition.size,
            timeout=timeout,
            parallel=parallel,
            workdir=workdir,
        ):
            writer.writerows(output)
            bar.update(ds.transition.size)

        if squeeze:
            return update(ds, csv).squeeze()
        else:
            return update(ds, csv)


def gen_inputs(dataset: xr.Dataset) -> Iterator[Input]:
    """Generate inputs to be passed to the RADEX binaries."""
    lamda = query(str(dataset.datafile))
    transitions = dataset.transition.values.tolist()

    freq = lamda.transitions_loc[transitions]["Frequency"]
    freq_min = min(freq) - 1e-9  # type: ignore
    freq_max = max(freq) + 1e-9  # type: ignore

    with lamda.to_bottom(transitions).to_tempfile() as f:
        for index in walk_dims(dataset):
            yield to_input(
                datafile=f.name,
                outfile=OUTFILE,
                freq_min=freq_min,
                freq_max=freq_max,
                **index,
            )


def gen_radexes(dataset: xr.Dataset) -> Iterator[PathLike]:
    """Generate paths of the RADEX binaries."""
    for index in walk_dims(dataset):
        yield index["radex"]


def update(dataset: xr.Dataset, csv: IO[str]) -> xr.Dataset:
    """Update data variables of a dataset by a CSV file."""
    csv.seek(0)

    df = pd.read_csv(
        csv,
        header=None,
        names=list(dataset.data_vars),
    )

    # move transition to the last of dims
    dims = list(dataset.dims)
    dims.append(dims.pop(0))
    transposed = dataset.transpose(*dims)

    for name, var in transposed.data_vars.items():
        var[:] = df[name].to_numpy().reshape(var.shape)

    return dataset


def walk_dims(dataset: xr.Dataset) -> Iterator[dict[str, Any]]:
    """Generate combinations of indexes' values."""
    dims = dict(dataset.indexes)
    dims.pop("transition")

    for values in product(*dims.values()):
        yield dict(zip(dims.keys(), values))


class Units:
    """Convert data with units to given units."""

    data: Any
    units: Any

    def __post_init__(self) -> None:
        if isinstance(self.data, Quantity):
            self.data = self.data.to(self.units).value


@dataclass
class Transition:
    data: Data[Literal["transition"], Any]
    long_name: Attr[str] = "Transition"


@dataclass
class KineticTemperature(Units):
    data: Data[Literal["T_kin"], float]
    long_name: Attr[str] = "Kinetic temperature"
    units: Attr[str] = "K"


@dataclass
class H2Density(Units):
    data: Data[Literal["n_H2"], float]
    long_name: Attr[str] = "H2 density"
    units: Attr[str] = "cm^-3"


@dataclass
class ParaH2Density(Units):
    data: Data[Literal["n_pH2"], float]
    long_name: Attr[str] = "Para-H2 density"
    units: Attr[str] = "cm^-3"


@dataclass
class OrthoH2Density(Units):
    data: Data[Literal["n_oH2"], float]
    long_name: Attr[str] = "Ortho-H2 density"
    units: Attr[str] = "cm^-3"


@dataclass
class ElectronDensity(Units):
    data: Data[Literal["n_e"], float]
    long_name: Attr[str] = "Electron density"
    units: Attr[str] = "cm^-3"


@dataclass
class HydrogenDensity(Units):
    data: Data[Literal["n_H"], float]
    long_name: Attr[str] = "Hydrogen density"
    units: Attr[str] = "cm^-3"


@dataclass
class HeliumDensity(Units):
    data: Data[Literal["n_He"], float]
    long_name: Attr[str] = "Helium density"
    units: Attr[str] = "cm^-3"


@dataclass
class ProtonDensity(Units):
    data: Data[Literal["n_Hp"], float]
    long_name: Attr[str] = "Proton density"
    units: Attr[str] = "cm^-3"


@dataclass
class BackgroundTemperature(Units):
    data: Data[Literal["T_bg"], float]
    long_name: Attr[str] = "Background temperature"
    units: Attr[str] = "K"


@dataclass
class ColumnDensity(Units):
    data: Data[Literal["N"], float]
    long_name: Attr[str] = "Column density"
    units: Attr[str] = "cm^-2"


@dataclass
class LineWidth(Units):
    data: Data[Literal["dv"], float]
    long_name: Attr[str] = "Line width"
    units: Attr[str] = "km s^-1"


@dataclass
class RadexBinary:
    data: Data[Literal["radex"], str]
    long_name: Attr[str] = "RADEX binary"


@dataclass
class Line:
    data: Data[VarDims, str]
    long_name: Attr[str] = "Line name"


@dataclass
class UpperStateEnergy(Units):
    data: Data[VarDims, float]
    long_name: Attr[str] = "Upper state energy"
    units: Attr[str] = "K"


@dataclass
class Frequency(Units):
    data: Data[VarDims, float]
    long_name: Attr[str] = "Frequency"
    units: Attr[str] = "GHz"


@dataclass
class Wavelength(Units):
    data: Data[VarDims, float]
    long_name: Attr[str] = "Wavelength"
    units: Attr[str] = "um"


@dataclass
class ExcitationTemperature(Units):
    data: Data[VarDims, float]
    long_name: Attr[str] = "Excitation temperature"
    units: Attr[str] = "K"


@dataclass
class OpticalDepth(Units):
    data: Data[VarDims, float]
    long_name: Attr[str] = "Optical depth"
    units: Attr[str] = "dimensionless"


@dataclass
class PeakIntensity(Units):
    data: Data[VarDims, float]
    long_name: Attr[str] = "Peak intensity"
    units: Attr[str] = "K"


@dataclass
class UpperStatePopulation(Units):
    data: Data[VarDims, float]
    long_name: Attr[str] = "Upper state population"
    units: Attr[str] = "dimensionless"


@dataclass
class LowerStatePopulation(Units):
    data: Data[VarDims, float]
    long_name: Attr[str] = "Lower state population"
    units: Attr[str] = "dimensionless"


@dataclass
class IntegratedIntensity(Units):
    data: Data[VarDims, float]
    long_name: Attr[str] = "Integrated intensity"
    units: Attr[str] = "K km s^-1"


@dataclass
class Flux(Units):
    data: Data[VarDims, float]
    long_name: Attr[str] = "Flux"
    units: Attr[str] = "erg s^-1 cm^-2"


@dataclass
class EmptySet(AsDataset):
    """Specification of an empty dataset."""

    # attributes
    datafile: Attr[PathLike]

    # dimensions
    transition: Coordof[Transition]
    T_kin: Coordof[KineticTemperature]
    n_H2: Coordof[H2Density]
    n_pH2: Coordof[ParaH2Density]
    n_oH2: Coordof[OrthoH2Density]
    n_e: Coordof[ElectronDensity]
    n_H: Coordof[HydrogenDensity]
    n_He: Coordof[HeliumDensity]
    n_Hp: Coordof[ProtonDensity]
    T_bg: Coordof[BackgroundTemperature]
    N: Coordof[ColumnDensity]
    dv: Coordof[LineWidth]
    radex: Coordof[RadexBinary]

    # data variables
    line: Dataof[Line] = field(init=False)
    E_up: Dataof[UpperStateEnergy] = field(init=False)
    freq: Dataof[Frequency] = field(init=False)
    wavel: Dataof[Wavelength] = field(init=False)
    T_ex: Dataof[ExcitationTemperature] = field(init=False)
    tau: Dataof[OpticalDepth] = field(init=False)
    T_R: Dataof[PeakIntensity] = field(init=False)
    pop_up: Dataof[UpperStatePopulation] = field(init=False)
    pop_low: Dataof[LowerStatePopulation] = field(init=False)
    I: Dataof[IntegratedIntensity] = field(init=False)
    F: Dataof[Flux] = field(init=False)

    def __post_init__(self) -> None:
        """Set empty arrays to data variables."""
        model = DataModel.from_dataclass(self)
        shape = []

        for entry in model.coords:
            shape.append(len(np.atleast_1d(entry.value)))

        for entry in model.data_vars:
            setattr(self, str(entry.name), np.empty(shape))
