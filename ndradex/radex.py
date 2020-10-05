__all__ = []


# standard library
from logging import getLogger, Logger
from pathlib import Path
from subprocess import CompletedProcess, PIPE
from subprocess import run as sprun
from subprocess import CalledProcessError, TimeoutExpired
from typing import Optional, Sequence, Tuple, Union


# dependencies
from . import RADEX_BINPATH, RADEX_VERSION


# constants
N_VARS: int = 10
ERROR_OUTPUT: Sequence[str] = ("NaN",) * N_VARS


# type aliases
InputLike = Union[Sequence[str], str]
PathLike = Union[Path, str]


# logger
logger: Logger = getLogger(__name__)


# main features
def run(
    input: InputLike,
    radex: Optional[PathLike] = None,
    timeout: Optional[int] = None,
    cleanup: bool = True,
    logfile: PathLike = "radex.log",
    encoding: str = "utf-8",
) -> Sequence[str]:
    """Run RADEX and get result as tuple of string.

    Note that this function only reads the last line of RADEX outfile.
    This means that only the values of the transition at the highest
    frequency spacified in the RADEX input will be returned.

    Args:
        input: RADEX input. See examples below.
        radex: RADEX path. If not spacified, then the builtin
            RADEX with uniform geometry will be used.
        timeout: Timeout of a RADEX run in units of second.
            Default is None (unlimited run time is permitted).
        cleanup: If True (default), then the RADEX outfile
            (e.g. radex.out) and logfile (e.g., radex.log) will be deleted.
        logfile: Path of logfile. This is only used for
            identifying the path of logfile in the cleanup method.
        encoding: File encofing. Default is utf-8.

    Returns:
        RADEX output values as a tuple of strings.

    Examples:
        To get the values of CO(1-0) @ T_kin = 100 K, n_H2 = 1e3 cm^-3,
        N_CO = 1e15 cm^-2, T_bg = 2.73 K, and dv = 1.0 km s^-1:

            >>> input = ['co.dat', 'radex.out', '110 120', '100',
                        '1', 'H2', '1e3', '2.73', '1e15', '1.0', 0]
            >>> output = run(input)

    """
    if radex is None:
        radex = RADEX_BINPATH / "radex-uni"

    try:
        input, outfile = ensure_input(input, encoding)
    except (AttributeError, IndexError, TypeError):
        logger.warning("RADEX did not run due to invalid input")
        return ERROR_OUTPUT

    try:
        cp = sprun(
            [radex],
            input=input,
            timeout=timeout,
            stdout=PIPE,
            stderr=PIPE,
            check=True,
        )
        return ensure_output(cp, outfile, encoding)
    except FileNotFoundError:
        logger.warning("RADEX path or moldata does not exist")
        return ERROR_OUTPUT
    except CalledProcessError:
        logger.warning("RADEX failed due to invalid input")
        return ERROR_OUTPUT
    except TimeoutExpired:
        logger.warning("RADEX interrupted due to timeout")
        return ERROR_OUTPUT
    except RuntimeError:
        logger.warning("RADEX version is not valid")
        return ERROR_OUTPUT
    finally:
        if cleanup:
            remove_file(logfile)
            remove_file(outfile)


# utility features
def ensure_input(input: InputLike, encoding: str = "utf-8") -> Tuple[str, str]:
    """Ensure the type of input and the path of outfile."""
    if isinstance(input, (list, tuple)):
        outfile = input[1]
        input = "\n".join(input).encode(encoding)
    else:
        outfile = input.split("\n")[1]
        input = input.encode(encoding)

    return input, outfile


def ensure_output(
    cp: CompletedProcess,
    outfile: str,
    encoding: str = "utf-8",
) -> Sequence[str]:
    """Ensure that the RADEX output is valid."""
    if RADEX_VERSION not in cp.stdout.decode(encoding):
        raise RuntimeError("RADEX version is not valid")

    with open(outfile, encoding=encoding) as f:
        return f.readlines()[-1].split()[-N_VARS:]


def remove_file(path: PathLike) -> None:
    """Remove file forcibly (i.e., rm -f <path>)."""
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass
