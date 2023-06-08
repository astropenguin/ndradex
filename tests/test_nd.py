# standard library
from random import choice


# dependencies
from ndradex.nd import run
from xarray.testing import assert_equal


# test data
nd_params = {
    "radex": ["radex-1", "radex-2"],
    "transition": ["1-0", "2-1", "3-2"],
    "T_kin": [100.0, 200.0, 300.0, 400.0],
    "n_H2": [1e1, 1e2, 1e3, 1e4, 1e5],
    "N": [1e11, 1e12, 1e13, 1e14, 1e15, 1e16],
    "T_bg": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0],
    "dv": [1.0],
}


def test_run() -> None:
    ds_nd = run("co.dat", **nd_params, squeeze=False, timeout=1.0)

    for _ in range(100):
        params = {k: choice(v) for k, v in nd_params.items()}
        ds_one = run("co.dat", **params, squeeze=False, timeout=1.0)
        assert_equal(ds_nd.sel(ds_one.coords), ds_one)
