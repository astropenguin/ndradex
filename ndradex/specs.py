# standard library
from dataclasses import dataclass, field
from os import PathLike
from typing import Any, Literal


# dependencies
import numpy as np
from astropy.units import Quantity
from xarray_dataclasses import AsDataset, Attr, Coordof, Data, Dataof


# type hints
StrPath = PathLike[str] | str
VarDims = tuple[
    Literal["transition"],
    Literal["N"],
    Literal["T_kin"],
    Literal["n_H2"],
    Literal["n_pH2"],
    Literal["n_oH2"],
    Literal["n_e"],
    Literal["n_H"],
    Literal["n_He"],
    Literal["n_p"],
    Literal["T_bg"],
    Literal["dv"],
    Literal["radex"],
]

# constants
DIMS = (
    "transition",
    "N",
    "T_kin",
    "n_H2",
    "n_pH2",
    "n_oH2",
    "n_e",
    "n_H",
    "n_He",
    "n_p",
    "T_bg",
    "dv",
    "radex",
)
VARS = (
    "line",
    "E_up",
    "freq",
    "wavel",
    "T_ex",
    "tau",
    "T_peak",
    "pop_up",
    "pop_low",
    "I",
    "F",
)


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
class ColumnDensity(Units):
    data: Data[Literal["N"], float]
    long_name: Attr[str] = "Column density"
    units: Attr[str] = "cm^-2"


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
    data: Data[Literal["n_p"], float]
    long_name: Attr[str] = "Proton density"
    units: Attr[str] = "cm^-3"


@dataclass
class BackgroundTemperature(Units):
    data: Data[Literal["T_bg"], float]
    long_name: Attr[str] = "Background temperature"
    units: Attr[str] = "K"


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
class LineName:
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
class NDRadexOutput(AsDataset):
    """Specifications for multidimensional RADEX outputs."""

    # attributes
    datafile: Attr[StrPath]

    # dimensions
    transition: Coordof[Transition]
    N: Coordof[ColumnDensity]
    T_kin: Coordof[KineticTemperature]
    n_H2: Coordof[H2Density]
    n_pH2: Coordof[ParaH2Density]
    n_oH2: Coordof[OrthoH2Density]
    n_e: Coordof[ElectronDensity]
    n_H: Coordof[HydrogenDensity]
    n_He: Coordof[HeliumDensity]
    n_p: Coordof[ProtonDensity]
    T_bg: Coordof[BackgroundTemperature]
    dv: Coordof[LineWidth]
    radex: Coordof[RadexBinary]

    # data variables
    line: Dataof[LineName] = field(init=False)
    E_up: Dataof[UpperStateEnergy] = field(init=False)
    freq: Dataof[Frequency] = field(init=False)
    wavel: Dataof[Wavelength] = field(init=False)
    T_ex: Dataof[ExcitationTemperature] = field(init=False)
    tau: Dataof[OpticalDepth] = field(init=False)
    T_peak: Dataof[PeakIntensity] = field(init=False)
    pop_up: Dataof[UpperStatePopulation] = field(init=False)
    pop_low: Dataof[LowerStatePopulation] = field(init=False)
    I: Dataof[IntegratedIntensity] = field(init=False)
    F: Dataof[Flux] = field(init=False)

    def __post_init__(self) -> None:
        """Set empty arrays to the data variables."""
        for dim in DIMS:
            setattr(self, dim, np.atleast_1d(getattr(self, dim)))

        shape = [len(getattr(self, dim)) for dim in DIMS]

        for var in VARS:
            setattr(self, var, np.empty(shape))
