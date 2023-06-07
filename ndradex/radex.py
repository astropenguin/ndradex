__all__ = ["build", "run", "runmap", "to_input"]


# standard library
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from functools import partial
from itertools import chain, count
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


def build(
    *,
    force: bool = False,
    logfile: PathLike = RADEX_LOGFILE,
    miniter: int = RADEX_MINITER,
    maxiter: int = RADEX_MAXITER,
    fc: PathLike = FC,
) -> None:
    """Build the builtin RADEX binaries.

    This function builds them only when ``RADEX_BIN`` is
    set to the package's bin (``/path/to/ndradex/bin``):
    Otherwise, no build is run even if ``force=True``.

    Keyword Args:
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


def run(
    radex: PathLike,
    input: Input,
    # *,
    tail: int = 1,
    timeout: Timeout = None,
) -> Output:
    """Run RADEX and return an output object.

    If RADEX fails to run due to an invalid input, timeout, etc,
    this function does not raise an exception but returns
    an output object filled with ``"nan"``.

    Note that this function only reads the last N (= ``tail``) line(s)
    in a RADEX output file: This means that it only returns the results
    of the last N transitions written in a RADEX datafile.

    Args:
        radex: Path of the RADEX binary to be run.
        input: Input to be passed to the RADEX binary.

    Keyword Args:
        tail: Number of lines in a RADEX output file to be read.
        timeout: Timeout of the run in units of seconds.
            Defaults to ``None`` (unlimited run time).

    Returns:
        RADEX output object (list of tuple of strings).

    Examples:
        To get output of CO(1-0), CO(2-1), and CO(3-2)
        at T_kin = 100 K, T_bg = 2.73 K, N = 1e15 cm^-2,
        n_H2 = 1e3 cm^-3, and dv = 1.0 km s^-1::

            input = [
                "co.dat", "radex.out", "100 400", "100",
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


def runmap(
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

    Keyword Args:
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
        yield from executor.map(run_, radexes, numbered(inputs))


def to_input(
    *,
    datafile: PathLike,
    outfile: PathLike,
    freq_min: float = 0.0,
    freq_max: float = 0.0,
    T_kin: float = 0.0,
    n_H2: float = 0.0,
    n_pH2: float = 0.0,
    n_oH2: float = 0.0,
    n_e: float = 0.0,
    n_H: float = 0.0,
    n_He: float = 0.0,
    n_Hp: float = 0.0,
    T_bg: float = 0.0,
    N: float = 0.0,
    dv: float = 0.0,
) -> Tuple[str, ...]:
    """Convert parameters to an input for RADEX.

    Keyword Args:
        datafile: Path of RADEX datafile.
        outfile: Path of RADEX output file.
        freq_min: Minimum frequency (GHz).
        freq_max: Maximum frequency (GHz).
        T_kin: Kinetic temperature (K).
        n_H2: H2 density (cm^-3).
        n_pH2: Para-H2 density (cm^-3).
        n_oH2: Ortho-H2 density (cm^-3).
        n_e: Electron density (cm^-3).
        n_H: Hydrogen density (cm^-3).
        n_He: Helium density (cm^-3).
        n_Hp: Proton density (cm^-3).
        T_bg: Background temperature (K).
        N: Column density (cm^-2).
        dv: Line width (km s^-1).

    Returns:
        input: Input for ``run`` or ``runmap``.


    """
    n_all = [
        ("H2", n_H2),
        ("p-H2", n_pH2),
        ("o-H2", n_oH2),
        ("e", n_e),
        ("H", n_H),
        ("He", n_He),
        ("H+", n_Hp),
    ]
    n_use = list(filter(lambda n: n[1], n_all))

    input = (
        datafile,
        outfile,
        f"{freq_min} {freq_max}",
        T_kin,
        len(n_use),
        *chain(*n_use),
        T_bg,
        N,
        dv,
        0,
    )
    return tuple(map(str, input))


@contextmanager
def cleanup(*files: PathLike) -> Iterator[None]:
    """Remove files when a context is finished."""
    try:
        yield None
    finally:
        for file in files:
            Path(file).expanduser().unlink(missing_ok=True)


def numbered(inputs: Iterable[Input]) -> Iterator[Input]:
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
