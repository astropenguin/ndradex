__version__ = "0.2.2"
__author__ = "Akio Taniguchi"


# ignore FutureWarning
import warnings

warnings.simplefilter("ignore", FutureWarning)


# install builtin RADEX
def _install_radex() -> None:
    # from standard library
    from subprocess import PIPE, run

    if (
        (RADEX_BINPATH / "radex-uni").exists()
        and (RADEX_BINPATH / "radex-lvg").exists()
        and (RADEX_BINPATH / "radex-slab").exists()
    ):
        return

    run(
        args=[
            "make",
            "build",
            "LOGFILE=/dev/null",
            "MAXITER=999999",
        ],
        stdout=PIPE,
        stderr=PIPE,
        cwd=RADEX_BINPATH,
        check=True,
    )


_install_radex()


# submodules
from . import consts
from .utils import *  # noqa
from .radex import *  # noqa
from .db import *  # noqa
from .grid import *  # noqa
