# standard library
from pathlib import Path


# dependencies
from ndradex.consts import RADEX_BIN
from ndradex.db import LAMDA
from ndradex.radex import run


# test data
radex_input = [
    "co.dat",
    "radex.out",
    "110 120",
    "100",
    "1",
    "H2",
    "1e3",
    "2.73",
    "1e15",
    "1.0",
    "0",
]
radex_output = [
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
]


# test functions
def test_run() -> None:
    with LAMDA(radex_input[0]):
        output = run(radex_input, RADEX_BIN / "radex-1")

    # test non-existence of the input/output files
    assert not Path(radex_input[0]).exists()
    assert not Path(radex_input[1]).exists()

    # test equality of the output values
    assert output[0] == radex_output[0]
    assert output[1] == radex_output[1]
    assert output[2] == radex_output[2]
    assert output[3] == radex_output[3]
    assert output[4] == radex_output[4]
    assert output[5] == radex_output[5]
    assert output[6] == radex_output[6]
    assert output[7] == radex_output[7]
    assert output[8] == radex_output[8]
    assert output[9] == radex_output[9]
