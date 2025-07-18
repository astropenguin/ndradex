__all__ = [
    # ndradex-related
    "NDRADEX",
    "NDRADEX_CONFIG",
    "NDRADEX_DIR",
    # radex-related
    "RADEX_BIN",
    "RADEX_VERSION",
]


# standard library
from os import getenv
from pathlib import Path
from typing import Any, Optional, TypeVar, overload


# dependencies
from tomlkit import load


# type hints
T = TypeVar("T")


# helper functions
def ensure(toml: Path) -> Path:
    """Create an empty TOML file if it does not exist."""
    if not toml.exists():
        toml.parent.mkdir(parents=True, exist_ok=True)
        toml.touch()

    return toml


@overload
def getval(toml: Path, keys: str, default: type[T]) -> Optional[T]: ...


@overload
def getval(toml: Path, keys: str, default: T) -> T: ...


def getval(toml: Path, keys: str, default: Any) -> Any:
    """Return the value of the keys in a TOML file."""
    if isinstance(default, type):
        type_, default_ = default, None
    else:
        type_, default_ = type(default), default

    with open(toml) as file:
        doc = load(file)

    for key in keys.split("."):
        if (doc := doc.get(key)) is None:
            return default_

    return type_(doc.unwrap())


# ndradex-related
NDRADEX = Path(__file__).parent
"""Path of the ndRADEX package."""

NDRADEX_CONFIG: Path
"""Path of the ndRADEX config."""

NDRADEX_DIR: Path
"""Path of the ndRADEX directory."""

if (env := getenv("NDRADEX_DIR")) is not None:
    NDRADEX_DIR = Path(env)
elif (env := getenv("XDG_CONFIG_HOME")) is not None:
    NDRADEX_DIR = Path(env) / "ndradex"
else:
    NDRADEX_DIR = Path.home() / ".config" / "ndradex"

NDRADEX_CONFIG = ensure(NDRADEX_DIR / "config.toml")


# radex-related
RADEX_BIN = getval(NDRADEX_CONFIG, "radex.bin", NDRADEX / "bin")
"""Default path for the RADEX binaries."""

RADEX_VERSION = "30nov2011"
"""Supported version of the RADEX binaries."""
