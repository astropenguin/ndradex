# standard library
from itertools import repeat
from pathlib import Path
from tempfile import NamedTemporaryFile


# dependencies
from ndradex.lamda import get_lamda
from ndradex.radex import RADEX_BIN, run, runmap, to_input


# test data
radex_input = (
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
radex_output = [
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
radex_params = {
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
    "n_Hp": 0.0,
    "T_bg": 2.73,
    "N": 1e15,
    "dv": 1.0,
}


# test functions
def test_run() -> None:
    with NamedTemporaryFile("w") as tempfile:
        get_lamda("co").to_datafile(tempfile.name)
        output = run(
            radex=RADEX_BIN / "radex-1",
            input=(tempfile.name, *radex_input),
        )

    # test non-existence of the input/output files
    assert not Path(radex_input[0]).exists()
    assert not Path(radex_input[1]).exists()

    # test equality of the output values
    assert output == radex_output


def test_runmap() -> None:
    with NamedTemporaryFile("w") as tempfile:
        get_lamda("co").to_datafile(tempfile.name)
        outputs = list(
            runmap(
                radexes=repeat(RADEX_BIN / "radex-1", 10),
                inputs=repeat((tempfile.name, *radex_input), 10),
            )
        )

    # test non-existence of the input/output files
    assert not Path(radex_input[0]).exists()
    assert not Path(radex_input[1]).exists()

    # test equality of the output values
    assert outputs[0] == radex_output


def test_to_input() -> None:
    input = to_input(datafile="dummy", **radex_params)
    assert input[1:] == radex_input
