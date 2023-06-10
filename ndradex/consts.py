__all__ = [
    "NDRADEX",
    "NDRADEX_CONFIG",
    "RADEX_BIN",
    "RADEX_VERSION",
    "LAMDA_ALIASES",
    # defaults
    "DV",
    "N",
    "RADEX",
    "N_E",
    "N_H",
    "N_H2",
    "N_HE",
    "N_HP",
    "N_OH2",
    "N_PH2",
    "PARALLEL",
    "PROGRESS",
    "RADEX",
    "SQUEEZE",
    "T_BG",
    "T_KIN",
    "TIMEOUT",
    "WORKDIR",
]


# standard library
from os import getenv
from pathlib import Path
from typing import Any, Optional, TypeVar, overload


# dependencies
from tomlkit import load


# type hints
T = TypeVar("T")


# constants
NDRADEX = Path(__file__).parent
"""Path of the ndRADEX package"""

TOML_SEP = "."
"""Separator between TOML keys."""


# helper functions
def ensure(toml: Path) -> Path:
    """Create an empty TOML file if it does not exist."""
    if not toml.exists():
        toml.parent.mkdir(parents=True, exist_ok=True)
        toml.touch()

    return toml


@overload
def getval(toml: Path, keys: str, default: type[T]) -> Optional[T]:
    ...


@overload
def getval(toml: Path, keys: str, default: T) -> T:
    ...


def getval(toml: Path, keys: str, default: Any) -> Any:
    """Return the value of the keys in a TOML file."""
    if isinstance(default, type):
        type_, default_ = default, None
    else:
        type_, default_ = type(default), default

    with open(toml) as file:
        doc = load(file)

    for key in keys.split(TOML_SEP):
        if (doc := doc.get(key)) is None:
            return default_

    return type_(doc.unwrap())


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

N = getval(NDRADEX_CONFIG, "defaults.N", 1e15)
"""Default value for the ``N_mol`` argument."""

N_E = getval(NDRADEX_CONFIG, "defaults.n_e", 0.0)
"""Default value for the ``n_e`` argument."""

N_H = getval(NDRADEX_CONFIG, "defaults.n_H", 0.0)
"""Default value for the ``n_H`` argument."""

N_H2 = getval(NDRADEX_CONFIG, "defaults.n_H2", 1e3)
"""Default value for the ``n_H2`` argument."""

N_HE = getval(NDRADEX_CONFIG, "defaults.n_He", 0.0)
"""Default value for the ``n_He`` argument."""

N_HP = getval(NDRADEX_CONFIG, "defaults.n_Hp", 0.0)
"""Default value for the ``n_Hp`` argument."""

N_OH2 = getval(NDRADEX_CONFIG, "defaults.n_oH2", 0.0)
"""Default value for the ``n_oH2`` argument."""

N_PH2 = getval(NDRADEX_CONFIG, "defaults.n_pH2", 0.0)
"""Default value for the ``n_pH2`` argument."""

PARALLEL = getval(NDRADEX_CONFIG, "defaults.parallel", int)
"""Default value for the ``parallel`` argument."""

PROGRESS = getval(NDRADEX_CONFIG, "defaults.progress", False)
"""Default value for the ``progress`` argument."""

RADEX = getval(NDRADEX_CONFIG, "defaults.radex", "radex-1")
"""Default value for the ``radex`` argument."""

SQUEEZE = getval(NDRADEX_CONFIG, "defaults.squeeze", True)
"""Default value for the ``squeeze`` argument."""

T_BG = getval(NDRADEX_CONFIG, "defaults.T_bg", 2.73)
"""Default value for the ``T_bg`` argument."""

T_KIN = getval(NDRADEX_CONFIG, "defaults.T_kin", 100.0)
"""Default value for the ``T_kin`` argument."""

TIMEOUT = getval(NDRADEX_CONFIG, "defaults.timeout", float)
"""Default value for the ``timeout`` argument."""

WORKDIR = getval(NDRADEX_CONFIG, "defaults.workdir", Path)
"""Default value for the ``workdir`` argument."""
