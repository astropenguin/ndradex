# standard library
from random import choices
from typing import Any


# dependencies
from astroquery import lamda
from ndradex.lamda import LEVEL_COLUMN, TRANSITION_COLUMN, get_lamda
from pytest import mark


# test data
datafile_names = list(lamda.Lamda.molecule_dict)
datafile_names.remove("so2@lowT")
levels = [
    # (datafile name, query, expected level ID)
    ("co", 1, 1),
    ("co", [1, 2], [1, 2]),
    ("co", slice(1, 2), [1, 2]),
    ("co", "0", 1),
    ("co", ["0", "1"], [1, 2]),
    ("co", slice("0", "1"), [1, 2]),
    ("cn", 1, 1),
    ("cn", [1, 2], [1, 2]),
    ("cn", slice(1, 2), [1, 2]),
    ("cn", "0_0.5", 1),
    ("cn", ["0_0.5", "1_0.5"], [1, 2]),
    ("cn", slice("0_0.5", "1_0.5"), [1, 2]),
]
transitions = [
    # (datafile name, query, expected transition ID)
    ("co", 1, 1),
    ("co", (2, 1), 1),
    ("co", [1, 2], [1, 2]),
    ("co", [(2, 1), (3, 2)], [1, 2]),
    ("co", slice(1, 2), [1, 2]),
    ("co", slice((2, 1), (3, 2)), [1, 2]),
    ("co", "1-0", 1),
    ("co", ("1", "0"), 1),
    ("co", ["1-0", "2-1"], [1, 2]),
    ("co", slice("1-0", "2-1"), [1, 2]),
    ("cn", 1, 1),
    ("cn", (2, 1), 1),
    ("cn", [1, 2], [1, 2]),
    ("cn", [(2, 1), (3, 1)], [1, 2]),
    ("cn", slice(1, 2), [1, 2]),
    ("cn", slice((2, 1), (3, 1)), [1, 2]),
    ("cn", "1_0.5-0_0.5", 1),
    ("cn", ("1_0.5", "0_0.5"), 1),
    ("cn", ["1_0.5-0_0.5", "1_1.5-0_0.5"], [1, 2]),
    ("cn", slice("1_0.5-0_0.5", "1_1.5-0_0.5"), [1, 2]),
]


# test functions
@mark.parametrize("name", choices(datafile_names, k=10))
def test_get_lamda_by_name(name: str) -> None:
    assert get_lamda(name)


@mark.parametrize("name", choices(datafile_names, k=10))
def test_get_lamda_by_path(name: str) -> None:
    with get_lamda(name).to_tempfile() as file:
        assert get_lamda(file.name)


@mark.parametrize("name, query, expected", levels)
def test_levels(name: str, query: Any, expected: Any) -> None:
    lamda = get_lamda(name)
    assert (lamda.levels_loc[query][LEVEL_COLUMN] == expected).all()


@mark.parametrize("name, query, expected", transitions)
def test_transitions(name: str, query: Any, expected: Any) -> None:
    lamda = get_lamda(name)
    assert (lamda.transitions_loc[query][TRANSITION_COLUMN] == expected).all()
