__all__ = [
    # submodules
    "lamda",
    "nd",
    "radex",
    # aliases
    "LAMDA",
    "get_lamda",
    "run",
]
__version__ = "0.3.1"

# dependencies
from . import lamda, nd, radex
from .lamda import LAMDA, get_lamda
from .nd import run

# builtin RADEX binaries
radex.build()
