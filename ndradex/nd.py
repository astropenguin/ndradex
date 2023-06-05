__all__ = ["RADEX"]


# standard library
from dataclasses import dataclass
from typing import Any, Literal as L, Tuple


# dependencies
import numpy as np
from astropy.units import Quantity
from xarray_dataclasses import AsDataset, Attr, Coordof, Data, Dataof


# type hints
DataDims = Tuple[
    L["transition"],
    L["T_kin"],
    L["T_bg"],
    L["N"],
    L["n_H2"],
    L["n_pH2"],
    L["n_oH2"],
    L["n_e"],
    L["n_H"],
    L["n_He"],
    L["n_Hp"],
    L["dv"],
    L["radex"],
]


class Dim:
    """Ensure data for a dim to be 1D."""

    data: Any

    def __post_init__(self) -> None:
        self.data = np.atleast_1d(self.data)

        if not np.ndim(self.data) == 1:
            raise ValueError("Data for a dim must be 1D.")

        try:
            super().__post_init__()  # type: ignore
        except AttributeError:
            pass


class Units:
    """Convert data with units to given units."""

    data: Any
    units: Any

    def __post_init__(self) -> None:
        if isinstance(self.data, Quantity):
            self.data = self.data.to(self.units).value

        try:
            super().__post_init__()  # type: ignore
        except AttributeError:
            pass


@dataclass
class Transition(Dim):
    data: Data[L["transition"], Any]
    long_name: Attr[str] = "Transition"


@dataclass
class KineticTemperature(Dim, Units):
    data: Data[L["T_kin"], float]
    long_name: Attr[str] = "Kinetic temperature"
    units: Attr[str] = "K"


@dataclass
class H2Density(Dim, Units):
    data: Data[L["n_H2"], float]
    long_name: Attr[str] = "H2 density"
    units: Attr[str] = "cm^-3"


@dataclass
class ParaH2Density(Dim, Units):
    data: Data[L["n_pH2"], float]
    long_name: Attr[str] = "Para-H2 density"
    units: Attr[str] = "cm^-3"


@dataclass
class OrthoH2Density(Dim, Units):
    data: Data[L["n_oH2"], float]
    long_name: Attr[str] = "Ortho-H2 density"
    units: Attr[str] = "cm^-3"


@dataclass
class ElectronDensity(Dim, Units):
    data: Data[L["n_e"], float]
    long_name: Attr[str] = "Electron density"
    units: Attr[str] = "cm^-3"


@dataclass
class HydrogenDensity(Dim, Units):
    data: Data[L["n_H"], float]
    long_name: Attr[str] = "Hydrogen density"
    units: Attr[str] = "cm^-3"


@dataclass
class HeliumDensity(Dim, Units):
    data: Data[L["n_He"], float]
    long_name: Attr[str] = "Helium density"
    units: Attr[str] = "cm^-3"


@dataclass
class ProtonDensity(Dim, Units):
    data: Data[L["n_Hp"], float]
    long_name: Attr[str] = "Proton density"
    units: Attr[str] = "cm^-3"


@dataclass
class BackgroundTemperature(Dim, Units):
    data: Data[L["T_bg"], float]
    long_name: Attr[str] = "Background temperature"
    units: Attr[str] = "K"


@dataclass
class ColumnDensity(Dim, Units):
    data: Data[L["N"], float]
    long_name: Attr[str] = "Column density"
    units: Attr[str] = "cm^-2"


@dataclass
class LineWidth(Dim, Units):
    data: Data[L["dv"], float]
    long_name: Attr[str] = "Line width"
    units: Attr[str] = "km s^-1"


@dataclass
class RadexBinary(Dim):
    data: Data[L["radex"], str]
    long_name: Attr[str] = "RADEX binary"


@dataclass
class UpperStateEnergy(Units):
    data: Data[DataDims, float]
    long_name: Attr[str] = "Upper state energy"
    units: Attr[str] = "K"


@dataclass
class Frequency(Units):
    data: Data[DataDims, float]
    long_name: Attr[str] = "Frequency"
    units: Attr[str] = "GHz"


@dataclass
class Wavelength(Units):
    data: Data[DataDims, float]
    long_name: Attr[str] = "Wavelength"
    units: Attr[str] = "um"


@dataclass
class ExcitationTemperature(Units):
    data: Data[DataDims, float]
    long_name: Attr[str] = "Excitation temperature"
    units: Attr[str] = "K"


@dataclass
class OpticalDepth(Units):
    data: Data[DataDims, float]
    long_name: Attr[str] = "Optical depth"
    units: Attr[str] = "dimensionless"


@dataclass
class PeakIntensity(Units):
    data: Data[DataDims, float]
    long_name: Attr[str] = "Peak intensity"
    units: Attr[str] = "K"


@dataclass
class UpperStatePopulation(Units):
    data: Data[DataDims, float]
    long_name: Attr[str] = "Upper state population"
    units: Attr[str] = "dimensionless"


@dataclass
class LowerStatePopulation(Units):
    data: Data[DataDims, float]
    long_name: Attr[str] = "Lower state population"
    units: Attr[str] = "dimensionless"


@dataclass
class IntegratedIntensity(Units):
    data: Data[DataDims, float]
    long_name: Attr[str] = "Integrated intensity"
    units: Attr[str] = "K km s^-1"


@dataclass
class Flux(Units):
    data: Data[DataDims, float]
    long_name: Attr[str] = "Flux"
    units: Attr[str] = "erg s^-1 cm^-2"


@dataclass
class RADEX(AsDataset):
    """Multidimensional RADEX dataset."""

    # dimensions
    transition: Coordof[Transition] = ""
    """Transition name(s) or ID(s)."""

    T_kin: Coordof[KineticTemperature] = 0.0
    """Kinetic temperature(s) in units of K."""

    n_H2: Coordof[H2Density] = 0.0
    """H2 density(ies) in units of cm^-3."""

    n_pH2: Coordof[ParaH2Density] = 0.0
    """Para-H2 density(ies) in units of cm^-3."""

    n_oH2: Coordof[OrthoH2Density] = 0.0
    """Ortho-H2 density(ies) in units of cm^-3."""

    n_e: Coordof[ElectronDensity] = 0.0
    """Electron density(ies) in units of cm^-3."""

    n_H: Coordof[HydrogenDensity] = 0.0
    """Hydrogen density(ies) in units of cm^-3."""

    n_He: Coordof[HeliumDensity] = 0.0
    """Helium density(ies) in units of cm^-3."""

    n_Hp: Coordof[ProtonDensity] = 0.0
    """Proton density(ies) in units of cm^-3."""

    T_bg: Coordof[BackgroundTemperature] = 0.0
    """Background temperature(s) in units of K."""

    N: Coordof[ColumnDensity] = 0.0
    """Column density(ies) in units of cm^-2."""

    dv: Coordof[LineWidth] = 0.0
    """Line width(s) in units of km s^-1."""

    radex: Coordof[RadexBinary] = ""
    """RADEX binary(ies)."""

    # data variables
    E_up: Dataof[UpperStateEnergy] = 0.0
    """Upper state energy(ies) in units of K."""

    freq: Dataof[Frequency] = 0.0
    """Frequency(ies) in units of GHz."""

    wavel: Dataof[Wavelength] = 0.0
    """Wavelength(s) in units of um."""

    T_ex: Dataof[ExcitationTemperature] = 0.0
    """Excitation temperature(s) in units of K."""

    tau: Dataof[OpticalDepth] = 0.0
    """Optical depth(s)."""

    T_R: Dataof[PeakIntensity] = 0.0
    """Peak temperature(s) in units of K."""

    pop_up: Dataof[UpperStatePopulation] = 0.0
    """Upper state population(s)."""

    pop_low: Dataof[LowerStatePopulation] = 0.0
    """Lower state population(s)."""

    I: Dataof[IntegratedIntensity] = 0.0
    """Integrated intensity(ies) in units of K km s^-1."""

    F: Dataof[Flux] = 0.0
    """Flux(es) in units of erg s^-1 cm^-2."""
