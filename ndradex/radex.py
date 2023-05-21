__all__ = ["run"]


# standard library
from logging import getLogger
from pathlib import Path
from subprocess import PIPE, run as sprun
from subprocess import CalledProcessError, TimeoutExpired
from typing import List, Optional, Sequence, Union


# dependencies
from .consts import NDRADEX, RADEX_VERSION


# type hints
PathLike = Union[Path, str]


# constants
N_OUTPUT_VALUES = 10


# module logger
logger = getLogger(__name__)


def run(
    input: Sequence[str],
    radex: PathLike,
    cleanup: bool = True,
    timeout: Optional[float] = None,
) -> List[str]:
    """Run RADEX and return the output as a list of strings.

    Note that the function only reads the last line of a RADEX output.
    This means that the function will only return the values
    of the highest-frequency transition specified in the RADEX input.

    Args:
        input: Input strings for RADEX. See the examples below.
        radex: Absolute path of the RADEX binary to be run.
        cleanup: If True, the RADEX output file will be deleted.
        timeout: Timeout of the run in units of seconds.
            Default is None (unlimited run time is allowed).

    Returns:
        RADEX output as a list of strings.

    Examples:
        To get output of CO(1-0) @ T_kin = 100 K, n_H2 = 1e3 cm^-3,
        N_CO = 1e15 cm^-2, T_bg = 2.73 K, and dv = 1.0 km s^-1::

            input = [
                "co.dat", "radex.out", "110 120", "100",
                "1", "H2", "1e3", "2.73", "1e15", "1.0", "0",
            ]
            output = run(input, "/path/to/radex")

    """
    try:
        sprun(
            str(radex),
            input="\n".join(input),
            timeout=timeout,
            stdout=PIPE,
            stderr=PIPE,
            check=True,
            text=True,
        )
        return finalize(input[1], cleanup)
    except (IndexError, TypeError):
        logger.warning("RADEX did not run due to invalid input")
        return ["NaN"] * N_OUTPUT_VALUES
    except FileNotFoundError:
        logger.warning("RADEX path or moldata does not exist")
        return ["NaN"] * N_OUTPUT_VALUES
    except CalledProcessError:
        logger.warning("RADEX failed due to invalid input")
        return ["NaN"] * N_OUTPUT_VALUES
    except TimeoutExpired:
        logger.warning("RADEX interrupted due to timeout")
        return ["NaN"] * N_OUTPUT_VALUES
    except RuntimeError:
        logger.warning("RADEX version is not valid")
        return ["NaN"] * N_OUTPUT_VALUES


def build(force: bool = False) -> None:
    """Build the builtin RADEX binaries."""
    if force:
        sprun(
            args=["make", "clean"],
            cwd=NDRADEX / "bin",
            stdout=PIPE,
            stderr=PIPE,
            check=True,
        )

    sprun(
        args=[
            "make",
            "build",
            "RADEX_LOGFILE=/dev/null",
            "RADEX_MAXITER=999999",
        ],
        cwd=NDRADEX / "bin",
        stdout=PIPE,
        stderr=PIPE,
        check=True,
    )


def finalize(output: PathLike, cleanup: bool) -> List[str]:
    """Read a RADEX output file and return the final output."""
    try:
        with open(output) as f:
            lines = f.readlines()

        if RADEX_VERSION not in lines[0]:
            raise RuntimeError("RADEX version is not valid")

        return lines[-1].split()[-N_OUTPUT_VALUES:]
    finally:
        if cleanup:
            Path(output).unlink(missing_ok=True)
