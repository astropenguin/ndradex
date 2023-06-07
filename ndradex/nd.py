__all__ = []


# standard library
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterator, Literal, Tuple, Union


# dependencies
import numpy as np
import xarray as xr
from astropy.units import Quantity
from xarray_dataclasses import AsDataset, DataModel
from xarray_dataclasses import Attr, Coordof, Data, Dataof
from .lamda import get_lamda
from .radex import Input, to_input


# type hints
PathLike = Union[Path, str]


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


Dims = Tuple[
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


@dataclass
class UpperStateEnergy(Units):
    data: Data[Dims, float]
    long_name: Attr[str] = "Upper state energy"
    units: Attr[str] = "K"


@dataclass
class Frequency(Units):
    data: Data[Dims, float]
    long_name: Attr[str] = "Frequency"
    units: Attr[str] = "GHz"


@dataclass
class Wavelength(Units):
    data: Data[Dims, float]
    long_name: Attr[str] = "Wavelength"
    units: Attr[str] = "um"


@dataclass
class ExcitationTemperature(Units):
    data: Data[Dims, float]
    long_name: Attr[str] = "Excitation temperature"
    units: Attr[str] = "K"


@dataclass
class OpticalDepth(Units):
    data: Data[Dims, float]
    long_name: Attr[str] = "Optical depth"
    units: Attr[str] = "dimensionless"


@dataclass
class PeakIntensity(Units):
    data: Data[Dims, float]
    long_name: Attr[str] = "Peak intensity"
    units: Attr[str] = "K"


@dataclass
class UpperStatePopulation(Units):
    data: Data[Dims, float]
    long_name: Attr[str] = "Upper state population"
    units: Attr[str] = "dimensionless"


@dataclass
class LowerStatePopulation(Units):
    data: Data[Dims, float]
    long_name: Attr[str] = "Lower state population"
    units: Attr[str] = "dimensionless"


@dataclass
class IntegratedIntensity(Units):
    data: Data[Dims, float]
    long_name: Attr[str] = "Integrated intensity"
    units: Attr[str] = "K km s^-1"


@dataclass
class Flux(Units):
    data: Data[Dims, float]
    long_name: Attr[str] = "Flux"
    units: Attr[str] = "erg s^-1 cm^-2"


@dataclass
class EmptySet(AsDataset):
    """Specification of an empty dataset."""

    # attributes
    datafile: Attr[PathLike]

    # dimensions
    transition: Coordof[Transition]
    T_kin: Coordof[KineticTemperature] = 0.0
    n_H2: Coordof[H2Density] = 0.0
    n_pH2: Coordof[ParaH2Density] = np.nan
    n_oH2: Coordof[OrthoH2Density] = np.nan
    n_e: Coordof[ElectronDensity] = np.nan
    n_H: Coordof[HydrogenDensity] = np.nan
    n_He: Coordof[HeliumDensity] = np.nan
    n_Hp: Coordof[ProtonDensity] = np.nan
    T_bg: Coordof[BackgroundTemperature] = 0.0
    N: Coordof[ColumnDensity] = 0.0
    dv: Coordof[LineWidth] = 0.0
    radex: Coordof[RadexBinary] = "radex"

    # data variables
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

        for dim in [str(entry.name) for entry in model.coords]:
            values = np.atleast_1d(getattr(self, dim))
            setattr(self, dim, values)
            shape.append(len(values))

        for var in [str(entry.name) for entry in model.data_vars]:
            setattr(self, var, np.empty(shape))


def gen_inputs(dataset: xr.Dataset, outfile: PathLike) -> Iterator[Input]:
    """Generate inputs to be passed to the RADEX binaries."""
    trans = dataset.transition.values.tolist()
    lamda = get_lamda(dataset.datafile)
    freq = lamda.transitions_loc[trans]["Frequency"]
    freq_min = min(freq) - 1e-9  # type: ignore
    freq_max = max(freq) + 1e-9  # type: ignore

    with lamda.to_bottom(trans).to_tempfile() as datafile:
        for index in walk_indexes(dataset):
            yield to_input(
                datafile=datafile.name,
                outfile=outfile,
                freq_min=freq_min,
                freq_max=freq_max,
                **index,
            )


def gen_radexes(dataset: xr.Dataset) -> Iterator[PathLike]:
    """Generate paths of the RADEX binaries."""
    for index in walk_indexes(dataset):
        yield index["radex"]


def walk_indexes(dataset: xr.Dataset) -> Iterator[Dict[str, Any]]:
    """Generate combinations of indexes' values."""
    indexes = dict(dataset.indexes)
    indexes.pop("transition")

    for values in product(*indexes.values()):
        yield dict(zip(indexes, values))

