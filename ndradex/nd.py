__all__ = []


# standard library
from dataclasses import dataclass, field
from typing import Any, Literal as L, Tuple


# dependencies
import numpy as np
from astropy.units import Quantity
from xarray_dataclasses import AsDataset, DataModel
from xarray_dataclasses import Attr, Coordof, Data, Dataof


class Units:
    """Convert data with units to given units."""

    data: Any
    units: Any

    def __post_init__(self) -> None:
        if isinstance(self.data, Quantity):
            self.data = self.data.to(self.units).value


@dataclass
class Transition:
    data: Data[L["transition"], Any]
    long_name: Attr[str] = "Transition"


@dataclass
class KineticTemperature(Units):
    data: Data[L["T_kin"], float]
    long_name: Attr[str] = "Kinetic temperature"
    units: Attr[str] = "K"


@dataclass
class H2Density(Units):
    data: Data[L["n_H2"], float]
    long_name: Attr[str] = "H2 density"
    units: Attr[str] = "cm^-3"


@dataclass
class ParaH2Density(Units):
    data: Data[L["n_pH2"], float]
    long_name: Attr[str] = "Para-H2 density"
    units: Attr[str] = "cm^-3"


@dataclass
class OrthoH2Density(Units):
    data: Data[L["n_oH2"], float]
    long_name: Attr[str] = "Ortho-H2 density"
    units: Attr[str] = "cm^-3"


@dataclass
class ElectronDensity(Units):
    data: Data[L["n_e"], float]
    long_name: Attr[str] = "Electron density"
    units: Attr[str] = "cm^-3"


@dataclass
class HydrogenDensity(Units):
    data: Data[L["n_H"], float]
    long_name: Attr[str] = "Hydrogen density"
    units: Attr[str] = "cm^-3"


@dataclass
class HeliumDensity(Units):
    data: Data[L["n_He"], float]
    long_name: Attr[str] = "Helium density"
    units: Attr[str] = "cm^-3"


@dataclass
class ProtonDensity(Units):
    data: Data[L["n_Hp"], float]
    long_name: Attr[str] = "Proton density"
    units: Attr[str] = "cm^-3"


@dataclass
class BackgroundTemperature(Units):
    data: Data[L["T_bg"], float]
    long_name: Attr[str] = "Background temperature"
    units: Attr[str] = "K"


@dataclass
class ColumnDensity(Units):
    data: Data[L["N"], float]
    long_name: Attr[str] = "Column density"
    units: Attr[str] = "cm^-2"


@dataclass
class LineWidth(Units):
    data: Data[L["dv"], float]
    long_name: Attr[str] = "Line width"
    units: Attr[str] = "km s^-1"


@dataclass
class RadexBinary:
    data: Data[L["radex"], str]
    long_name: Attr[str] = "RADEX binary"


Dims = Tuple[
    L["transition"],
    L["T_kin"],
    L["n_H2"],
    L["n_pH2"],
    L["n_oH2"],
    L["n_e"],
    L["n_H"],
    L["n_He"],
    L["n_Hp"],
    L["T_bg"],
    L["N"],
    L["dv"],
    L["radex"],
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
    datafile: Attr[str]

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
