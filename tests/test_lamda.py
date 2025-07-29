# standard library
from random import choices
from tempfile import NamedTemporaryFile
from warnings import catch_warnings, simplefilter


# dependencies
import numpy as np
from astroquery.lamda import Lamda
from ndradex.lamda import get_lamda, set_index
from pytest import mark


# test data
with catch_warnings():
    simplefilter("ignore")

    molecule_dict = Lamda.molecule_dict.copy()
    molecule_dict.pop("si-h")
    molecule_dict.pop("so2@lowT")
    molecule_dict.pop("PO_hfs")

    datafiles = list(molecule_dict.keys())
    dataurls = list(molecule_dict.values())


# test functions
@mark.parametrize("datafile", choices(datafiles, k=10))
def test_LAMDA_init(datafile: str) -> None:
    lamda = get_lamda(datafile)

    with set_index(lamda.levels, "Level"):
        J_upper = lamda.levels.loc[lamda.transitions["Upper"]]["J"]
        J_lower = lamda.levels.loc[lamda.transitions["Lower"]]["J"]

        left = J_upper + "-" + J_lower
        right = lamda.transitions["NamedTransition"]
        assert (left == right).all()


@mark.parametrize("datafile", choices(datafiles, k=10))
def test_LAMDA_prioritize(datafile: str) -> None:
    lamda = get_lamda(datafile)
    left = np.array(lamda.transitions["Transition"])
    left = np.random.permutation(left[:10])

    prioritized = lamda.prioritize(list(left))
    right = prioritized.transitions["Transition"][-len(left) :]
    assert (left == right).all()  # type: ignore


@mark.parametrize("datafile", choices(datafiles, k=10))
def test_get_lamda_by_path(datafile: str) -> None:
    with NamedTemporaryFile("w") as tempfile:
        get_lamda(datafile).to_datafile(tempfile.name)
        assert get_lamda(tempfile.name)


@mark.parametrize("datafile", choices(datafiles, k=10))
def test_get_lamda_by_dict(datafile: str) -> None:
    assert get_lamda(datafile)


@mark.parametrize("dataurl", choices(dataurls, k=1))
def test_get_lamda_by_url(dataurl: str) -> None:
    assert get_lamda(dataurl)
