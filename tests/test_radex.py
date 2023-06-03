# standard library
from pathlib import Path


# dependencies
from ndradex.consts import RADEX_BIN
from ndradex.lamda import get_lamda
from ndradex.radex import run


# test data
radex_input = [
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


# test functions
def test_run() -> None:
    with get_lamda("co").to_tempfile() as file:
        output = run(
            radex=RADEX_BIN / "radex-1",
            input=[file.name] + radex_input,
        )

    # test non-existence of the input/output files
    assert not Path(radex_input[0]).exists()
    assert not Path(radex_input[1]).exists()

    # test equality of the output values
    assert output[0] == radex_output[0]
