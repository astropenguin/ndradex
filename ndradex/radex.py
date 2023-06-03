__all__ = ["run"]


# standard library
from contextlib import contextmanager
from logging import getLogger
from pathlib import Path
from subprocess import run as sprun
from subprocess import PIPE, CalledProcessError, TimeoutExpired
from typing import Iterator, List, Optional, Sequence, Tuple, Union


# dependencies
from .consts import NDRADEX, RADEX_BIN, RADEX_VERSION


# type hints
Output = List[Tuple[str, ...]]
PathLike = Union[Path, str]
Timeout = Optional[float]


# constants
N_COLUMNS = 11


# module logger
logger = getLogger(__name__)


def run(
    radex: PathLike,
    input: Sequence[str],
    tail: int = 1,
    timeout: Timeout = None,
) -> Output:
    """Run RADEX and return an output object.

    Note that this function only reads the last N=``tail`` line(s)
    in a RADEX outfile: This means that it only returns the results
    of the last N transitions written in a RADEX datafile.

    Args:
        radex: Path of the RADEX binary to be run.
        input: Input strings for the RADEX binary.
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


def build(force: bool = False) -> None:
    """Build the builtin RADEX binaries."""
    if not RADEX_BIN == NDRADEX / "bin":
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
            "RADEX_LOGFILE=/dev/null",
            "RADEX_MAXITER=999999",
        ],
        cwd=NDRADEX / "bin",
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


def parse_error(error: Exception, tail: int) -> Output:
    """Parse a Python error and return an output object."""
    return [("nan",) * N_COLUMNS] * tail


def parse_file(file: PathLike, tail: int) -> Output:
    """Parse a RADEX output file and return an output object."""
    with open(file) as f:
        lines = f.readlines()

    if RADEX_VERSION not in lines[0]:
        raise RuntimeError("RADEX version is not valid")

    output: Output = []

    for line in lines[-tail:]:
        output.append(tuple(line.rsplit(None, N_COLUMNS - 1)))

    return output
