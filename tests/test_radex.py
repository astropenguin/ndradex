# standard library
from itertools import repeat
from multiprocessing import set_start_method
from pathlib import Path
from tempfile import TemporaryDirectory

# dependencies
from ndradex.lamda import get_lamda
from ndradex.radex import RADEX_BIN, run, runmap, to_input

# use spawn for new process
set_start_method("spawn", force=True)

# test data
RADEX_INPUT = (
    "radex.out",
    "110.0 120.0",
    "100.0",
    "1",
    "H2",
    "1000.0",
    "2.73",
    "1000000000000000.0",
    "1.0",
    "0",
)
RADEX_OUTPUT = [
    (
        "1      -- 0",
        "5.5",
        "115.2712",
        "2600.7576",
        "132.463",
        "9.966E-03",
        "1.278E+00",
        "4.934E-01",
        "1.715E-01",
        "1.360E+00",
        "2.684E-08",
    )
]
RADEX_PARAMS = {
    "outfile": "radex.out",
    "freq_min": 110.0,
    "freq_max": 120.0,
    "T_kin": 100.0,
    "n_H2": 1e3,
    "n_pH2": 0.0,
    "n_oH2": 0.0,
    "n_e": 0.0,
    "n_H": 0.0,
    "n_He": 0.0,
    "n_p": 0.0,
    "T_bg": 2.73,
    "I_bg": "",
    "N": 1e15,
    "dv": 1.0,
}


def test_run() -> None:
    with TemporaryDirectory() as workdir:
        in_file = Path(workdir) / "co.dat"
        out_file = Path(workdir) / RADEX_INPUT[0]
        get_lamda("co").to_datafile(in_file)
        output = run(
            RADEX_BIN / "radex-1",
            (str(in_file), str(out_file), *RADEX_INPUT[1:]),
        )

    assert not in_file.exists()
    assert not out_file.exists()
    assert output == RADEX_OUTPUT


def test_runmap() -> None:
    with TemporaryDirectory() as workdir:
        in_file = Path(workdir) / "co.dat"
        out_file = Path(workdir) / RADEX_INPUT[0]
        get_lamda("co").to_datafile(in_file)
        outputs = runmap(
            repeat(RADEX_BIN / "radex-1", 10),
            repeat((str(in_file), str(out_file), *RADEX_INPUT[1:]), 10),
        )
        outputs = list(outputs)

    assert not in_file.exists()
    assert not out_file.exists()
    assert outputs[0] == RADEX_OUTPUT


def test_to_input() -> None:
    input = to_input(datafile="dummy", **RADEX_PARAMS)
    assert input[1:] == RADEX_INPUT
