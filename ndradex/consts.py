__all__ = [
    "NDRADEX",
    "NDRADEX_CONFIG",
    "RADEX_BIN",
    "RADEX_VERSION",
    "LAMDA_ALIASES",
    "DV",
    "GEOM",
    "N_H2",
    "N_MOL",
    "T_BG",
    "T_KIN",
    "TIMEOUT",
    "N_E",
    "N_H",
    "N_HE",
    "N_HP",
    "N_OH2",
    "N_PH2",
]


# standard library
from os import getenv
from pathlib import Path
from typing import TypeVar


# dependencies
from tomlkit import load


# type hints
T = TypeVar("T")


# constants
NDRADEX = Path(__file__).parent
"""Path of the ndRADEX package"""


# helper functions
def ensure(toml: Path) -> Path:
    """Create an empty TOML file if it does not exist."""
    if not toml.exists():
        toml.parent.mkdir(parents=True, exist_ok=True)
        toml.touch()

    return toml


def getval(toml: Path, keys: str, default: T) -> T:
    """Return the value of the keys in a TOML file."""
    with open(toml, "r") as file:
        doc = load(file)

    for key in keys.split("."):
        if (doc := doc.get(key)) is None:
            return default

    return type(default)(doc.unwrap())


# config file and directory for it
if (env := getenv("NDRADEX_DIR")) is not None:
    NDRADEX_DIR = Path(env)
elif (env := getenv("XDG_CONFIG_HOME")) is not None:
    NDRADEX_DIR = Path(env) / "ndradex"
else:
    NDRADEX_DIR = Path.home() / ".config" / "ndradex"

NDRADEX_CONFIG = ensure(NDRADEX_DIR / "config.toml")


# query aliases for molecular/atomic databases
LAMDA_ALIASES: dict[str, str] = getval(NDRADEX_CONFIG, "lamda.aliases", {})
"""Query aliases for the LAMDA database."""


# default values for RADEX binaries
RADEX_BIN = getval(NDRADEX_CONFIG, "defaults.bin", NDRADEX / "bin")
"""Default path for the RADEX binaries."""

RADEX_VERSION = "30nov2011"
"""Supported version of the RADEX binaries."""


# default values for public functions
DV = getval(NDRADEX_CONFIG, "defaults.dv", 1.0)
"""Default value for the ``dv`` argument."""

GEOM = getval(NDRADEX_CONFIG, "defaults.geom", "uni")
"""Default value for the ``geom`` argument."""

N_H2 = getval(NDRADEX_CONFIG, "defaults.n_H2", 1e3)
"""Default value for the ``n_H2`` argument."""

N_MOL = getval(NDRADEX_CONFIG, "defaults.N_mol", 1e15)
"""Default value for the ``N_mol`` argument."""

N_PROCS = getval(NDRADEX_CONFIG, "defaults.n_procs", 2)
"""Default value for the ``n_procs`` argument."""

PROGRESS = getval(NDRADEX_CONFIG, "defaults.progress", True)
"""Default value for the ``progress`` argument."""

SQUEEZE = getval(NDRADEX_CONFIG, "defaults.squeeze", True)
"""Default value for the ``squeeze`` argument."""

TIMEOUT = getval(NDRADEX_CONFIG, "defaults.timeout", 30.0)
"""Default value for the ``timeout`` argument."""

T_BG = getval(NDRADEX_CONFIG, "defaults.T_bg", 2.73)
"""Default value for the ``T_bg`` argument."""

T_KIN = getval(NDRADEX_CONFIG, "defaults.T_kin", 100.0)
"""Default value for the ``T_kin`` argument."""


# default values for public functions (optional)
N_E = getval(NDRADEX_CONFIG, "defaults.n_e", 0.0) or None
"""Default value for the ``n_e`` argument."""

N_H = getval(NDRADEX_CONFIG, "defaults.n_H", 0.0) or None
"""Default value for the ``n_H`` argument."""

N_HE = getval(NDRADEX_CONFIG, "defaults.n_He", 0.0) or None
"""Default value for the ``n_He`` argument."""

N_HP = getval(NDRADEX_CONFIG, "defaults.n_Hp", 0.0) or None
"""Default value for the ``n_Hp`` argument."""

N_OH2 = getval(NDRADEX_CONFIG, "defaults.n_oH2", 0.0) or None
"""Default value for the ``n_oH2`` argument."""

N_PH2 = getval(NDRADEX_CONFIG, "defaults.n_pH2", 0.0) or None
"""Default value for the ``n_pH2`` argument."""
