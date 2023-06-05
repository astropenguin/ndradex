__all__ = ["build", "maprun", "run"]


# standard library
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from functools import partial
from itertools import count
from logging import getLogger
from os import devnull, getenv
from pathlib import Path
from subprocess import PIPE, CalledProcessError, TimeoutExpired, run as sprun
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple, Union


# dependencies
from .consts import NDRADEX, RADEX_BIN, RADEX_VERSION


# type hints
Input = Sequence[str]
Output = List[Tuple[str, ...]]
Parallel = Optional[int]
PathLike = Union[Path, str]
Timeout = Optional[float]


# constants
FC = getenv("FC", "gfortran")
NAN = str(float("nan"))
NDRADEX_BIN = NDRADEX / "bin"
RADEX_COLUMNS = 11
RADEX_LOGFILE = devnull
RADEX_MAXITER = 1_000_000
RADEX_MINITER = 10


# module logger
logger = getLogger(__name__)


def run(
    radex: PathLike,
    input: Input,
    # *,
    tail: int = 1,
    timeout: Timeout = None,
) -> Output:
    """Run RADEX and return an output object.

    Note that this function only reads the last N=``tail`` line(s)
    in a RADEX outfile: This means that it only returns the results
    of the last N transitions written in a RADEX datafile.

    Args:
        radex: Path of the RADEX binary to be run.
        input: Input to be passed to the RADEX binary.
        tail: Number of lines in a RADEX outfile to be read.
        timeout: Timeout of the run in units of seconds.
            Defaults to ``None`` (unlimited run time).

    Returns:
        RADEX output object (list of list of strings).

    Examples:
        To get output of CO(1-0), CO(2-1), and CO(3-2)
        at T_kin = 100 K, n_H2 = 1e3 cm^-3, N_CO = 1e15 cm^-2,
        T_bg = 2.73 K, and dv = 1.0 km s^-1::

            input = [
                "co.dat", "radex.out", "100 1000", "100",
                "1", "H2", "1e3", "2.73", "1e15", "1.0", "0",
            ]
            output = run("/path/to/radex", input, tail=3)

    """
    with cleanup(input[1]):
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
            return parse_file(input[1], tail=tail)
        except CalledProcessError as error:
            logger.warning(f"RADEX failed to run: {error.stderr}")
            return parse_error(error, tail=tail)
        except (
            FileNotFoundError,
            IndexError,
            RuntimeError,
            TimeoutExpired,
            TypeError,
        ) as error:
            logger.warning(f"RADEX failed to run: {error}")
            return parse_error(error, tail=tail)


def maprun(
    radexes: Iterable[PathLike],
    inputs: Iterable[Input],
    # *,
    tail: int = 1,
    timeout: Timeout = None,
    parallel: Parallel = None,
) -> Iterator[Output]:
    """Run RADEX in parallel and generate output objects.

    Args:
        radexes: Paths of the RADEX binaries to be run.
        inputs: Inputs to be passed to the RADEX binaries.
        tail: Number of lines in a RADEX outfile to be read.
        timeout: Timeout of the run in units of seconds.
            Defaults to ``None`` (unlimited run time).
        parallel: Number of runs in parallel.
            Defaults to ``None`` (number of processors).

    Yields:
        RADEX output object (list of list of strings).

    """
    run_ = partial(run, tail=tail, timeout=timeout)

    with ProcessPoolExecutor(parallel) as executor:
        yield from executor.map(run_, radexes, numbering(inputs))


def build(
    *,
    force: bool = False,
    logfile: str = RADEX_LOGFILE,
    miniter: int = RADEX_MINITER,
    maxiter: int = RADEX_MAXITER,
    fc: PathLike = FC,
) -> None:
    """Build the builtin RADEX binaries.

    This function builds them only when ``RADEX_BIN`` is
    set to the package's bin (``/path/to/ndradex/bin``):
    Otherwise, no build is run even if ``force=True``.

    Args:
        force: Whether to forcibly rebuild the binaries.
        logfile: Path of the RADEX log file.
        miniter: Minimum number of iterations.
        maxiter: Maximum number of iterations.
        fc: Path of the Fortran compiler.

    Returns:
        This function returns nothing.

    """
    if not RADEX_BIN == NDRADEX_BIN:
        return None

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
            f"FC={fc}",
            f"RADEX_LOGFILE={logfile}",
            f"RADEX_MINITER={miniter}",
            f"RADEX_MAXITER={maxiter}",
        ],
        cwd=NDRADEX_BIN,
        stdout=PIPE,
        stderr=PIPE,
        check=True,
    )


@contextmanager
def cleanup(*files: PathLike) -> Iterator[None]:
    """Remove files when a context is finished."""
    try:
        yield None
    finally:
        for file in files:
            Path(file).expanduser().unlink(missing_ok=True)


def numbering(inputs: Iterable[Input]) -> Iterator[Input]:
    """Add serial numbers to the names of RADEX output files."""
    for number, input in zip(count(), inputs):
        yield (input[0], f"{input[1]}.{number}", *input[2:])


def parse_error(error: Exception, tail: int) -> Output:
    """Parse a Python error and return an output object."""
    return [(NAN,) * RADEX_COLUMNS] * tail


def parse_file(file: PathLike, tail: int) -> Output:
    """Parse a RADEX output file and return an output object."""
    with open(file) as f:
        lines = f.readlines()

    if RADEX_VERSION not in lines[0]:
        raise RuntimeError("RADEX version is not valid")

    output: Output = []

    for line in lines[-tail:]:
        output.append(tuple(line.rsplit(None, RADEX_COLUMNS - 1)))

    return output
