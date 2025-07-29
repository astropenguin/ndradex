__all__ = ["build", "to_input", "run", "runmap"]


# standard library
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from functools import partial
from itertools import chain, count
from logging import getLogger
from os import PathLike, devnull
from pathlib import Path
from shutil import which
from subprocess import (
    PIPE,
    CalledProcessError,
    CompletedProcess,
    TimeoutExpired,
    run as sprun,
)
from tempfile import TemporaryDirectory
from typing import Any, Iterable, Iterator


# type hints
RadexInput = tuple[str, ...]
RadexOutput = list[tuple[str, ...]]
StrPath = PathLike[str] | str


# constants
LOGGER = getLogger(__name__)
NDRADEX_BIN = Path(__file__).parent / "bin"
RADEX_OUTPUT_COLUMNS = 11
RADEX_VERSION = "30nov2011"


def build(
    *,
    force: bool = False,
    logfile: StrPath = devnull,
    miniter: int = 10,
    maxiter: int = 1_000_000,
) -> CompletedProcess[str]:
    """Build the builtin RADEX binaries.

    Args:
        force: Whether to forcibly rebuild the binaries.
        logfile: Path of the RADEX log file.
        miniter: Minimum number of iterations.
        maxiter: Maximum number of iterations.

    Returns:
        Completed process object as the result of the build.

    """
    targets = ["clean", "build"] if force else ["build"]

    return sprun(
        args=[
            "make",
            *targets,
            f"RADEX_LOGFILE={logfile}",
            f"RADEX_MINITER={miniter}",
            f"RADEX_MAXITER={maxiter}",
        ],
        cwd=NDRADEX_BIN,
        stderr=PIPE,
        stdout=PIPE,
        text=True,
    )


def to_input(
    *,
    datafile: StrPath,
    outfile: StrPath,
    freq_min: float,
    freq_max: float,
    T_kin: float,
    n_H2: float,
    n_pH2: float,
    n_oH2: float,
    n_e: float,
    n_H: float,
    n_He: float,
    n_Hp: float,
    T_bg: float,
    N: float,
    dv: float,
    **_: Any,
) -> RadexInput:
    """Convert parameters to an input for RADEX.

    Args:
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


def run(
    radex: StrPath,
    input: RadexInput,
    /,
    *,
    tail: int = 1,
    timeout: float | None = None,
    workdir: StrPath | None = None,
) -> RadexOutput:
    """Run RADEX and return an output object.

    If RADEX fails to run due to an invalid input, timeout, etc,
    this function does not raise an exception but returns
    an output object filled with ``'nan'``.

    Note that this function only reads the last N (= ``tail``) line(s)
    in a RADEX output file: This means that it only returns the results
    of the last N transitions written in a RADEX datafile.

    Args:
        radex: Path of the RADEX binary to be run.
        input: RADEX input to be passed to the RADEX binary.
        tail: Number of lines in a RADEX output file to be read.
        timeout: Timeout of the run in units of seconds.
            Defaults to ``None`` (unlimited run time).
        workdir: Path of the directory for a RADEX output file.
            Defaults to ``None`` (temporary directory).

    Returns:
        RADEX output as a list of string tuples.

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
    with set_workdir(workdir) as workdir:
        if (path := Path(radex)).exists():
            radex = str(path.expanduser().resolve())
        elif which(radex) is not None:
            radex = str(radex)
        else:
            radex = str(NDRADEX_BIN / radex)

        try:
            sprun(
                radex,
                input="\n".join(input),
                check=True,
                cwd=workdir,
                text=True,
                timeout=timeout,
                stderr=PIPE,
                stdout=PIPE,
            )
            return on_success(workdir / input[1], tail=tail)
        except CalledProcessError as error:
            return on_error(str(error.stderr), tail=tail)
        except (
            FileNotFoundError,
            IndexError,
            RuntimeError,
            TimeoutExpired,
            TypeError,
        ) as error:
            return on_error(str(error), tail=tail)


def runmap(
    radexes: Iterable[StrPath],
    inputs: Iterable[RadexInput],
    /,
    *,
    parallel: int | None = None,
    tail: int = 1,
    timeout: float | None = None,
    workdir: StrPath | None = None,
) -> Iterator[RadexOutput]:
    """Run RADEX in parallel and generate output objects.

    Args:
        radexes: Paths of the RADEX binaries to be run.
        inputs: RADEX inputs to be passed to the RADEX binaries.
        parallel: Number of runs in parallel.
            Defaults to ``None`` (number of processors).
        tail: Number of lines in a RADEX outfile to be read.
        timeout: Timeout length per run in units of seconds.
            Defaults to ``None`` (unlimited run time).
        workdir: Path of the directory for RADEX output files.
            Defaults to ``None`` (temporary directory).

    Yields:
        RADEX output as a list of string tuples.

    """

    with (
        set_workdir(workdir) as workdir,
        ProcessPoolExecutor(parallel) as executor,
    ):
        run_ = partial(run, tail=tail, timeout=timeout, workdir=workdir)
        yield from executor.map(run_, radexes, numbered(inputs))


def numbered(inputs: Iterable[RadexInput], /) -> Iterator[RadexInput]:
    """Add serial numbers to the names of RADEX output files."""
    for number, input in zip(count(), inputs):
        yield (input[0], f"{input[1]}.{number}", *input[2:])


def on_error(error: str, /, *, tail: int) -> RadexOutput:
    """Handle given RADEX error and return a RADEX output."""
    LOGGER.warning(f"RADEX failed to run: {error}")
    return [("nan",) * RADEX_OUTPUT_COLUMNS] * tail


def on_success(file: StrPath, /, *, tail: int) -> RadexOutput:
    """Handle given RADEX output file and return a RADEX output."""
    with open(file) as f:
        lines = f.readlines()

    if RADEX_VERSION not in lines[0]:
        raise RuntimeError("RADEX version is not valid")

    output: RadexOutput = []

    for line in lines[-tail:]:
        output.append(tuple(line.rsplit(None, RADEX_OUTPUT_COLUMNS - 1)))

    return output


@contextmanager
def set_workdir(workdir: StrPath | None = None, /) -> Iterator[Path]:
    """Set a directory for RADEX output files."""
    if workdir is None:
        with TemporaryDirectory() as workdir:
            yield Path(workdir)
    else:
        yield Path(workdir).expanduser()
