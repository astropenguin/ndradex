# standard library
from random import choices
from typing import Any


# dependencies
from astroquery.lamda import Lamda
from ndradex.lamda import LEVEL_COLUMN, TRANSITION_COLUMN, query
from pytest import mark


# test data
datafiles = list(Lamda.molecule_dict)
datafiles.remove("so2@lowT")
levels = [
    # (datafile, level, expected level ID)
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
    # (datafile, transition, expected transition ID)
    ("co", 1, 1),
    ("co", (2, 1), 1),
    ("co", [1, 2], [1, 2]),
    ("co", [(2, 1), (3, 2)], [1, 2]),
    ("co", slice(1, 2), [1, 2]),
    ("co", slice((2, 1), (3, 2)), [1, 2]),
    ("co", "1 -> 0", 1),
    ("co", "1 / 0", 1),
    ("co", "1-0", 1),
    ("co", ("1", "0"), 1),
    ("co", ["1 -> 0", "2 -> 1"], [1, 2]),
    ("co", ["1 / 0", "2 / 1"], [1, 2]),
    ("co", ["1-0", "2-1"], [1, 2]),
    ("co", slice("1 -> 0", "2 -> 1"), [1, 2]),
    ("co", slice("1 / 0", "2 / 1"), [1, 2]),
    ("co", slice("1-0", "2-1"), [1, 2]),
    ("cn", 1, 1),
    ("cn", (2, 1), 1),
    ("cn", [1, 2], [1, 2]),
    ("cn", [(2, 1), (3, 1)], [1, 2]),
    ("cn", slice(1, 2), [1, 2]),
    ("cn", slice((2, 1), (3, 1)), [1, 2]),
    ("cn", "1_0.5 -> 0_0.5", 1),
    ("cn", "1_0.5 / 0_0.5", 1),
    ("cn", "1_0.5-0_0.5", 1),
    ("cn", ("1_0.5", "0_0.5"), 1),
    ("cn", ["1_0.5 -> 0_0.5", "1_1.5 -> 0_0.5"], [1, 2]),
    ("cn", ["1_0.5 / 0_0.5", "1_1.5 / 0_0.5"], [1, 2]),
    ("cn", ["1_0.5-0_0.5", "1_1.5-0_0.5"], [1, 2]),
    ("cn", slice("1_0.5 -> 0_0.5", "1_1.5 -> 0_0.5"), [1, 2]),
    ("cn", slice("1_0.5 / 0_0.5", "1_1.5 / 0_0.5"), [1, 2]),
    ("cn", slice("1_0.5-0_0.5", "1_1.5-0_0.5"), [1, 2]),
    ("p-h3o+", 1, 1),
    ("p-h3o+", (3, 2), 1),
    ("p-h3o+", [1, 2], [1, 2]),
    ("p-h3o+", [(3, 2), (3, 1)], [1, 2]),
    ("p-h3o+", slice(1, 2), [1, 2]),
    ("p-h3o+", slice((3, 2), (3, 1)), [1, 2]),
    ("p-h3o+", "1_1_- -> 2_1_+", 1),
    ("p-h3o+", "1_1_- / 2_1_+", 1),
    ("p-h3o+", ("1_1_-", "2_1_+"), 1),
    ("p-h3o+", ["1_1_- -> 2_1_+", "1_1_- -> 1_1_+"], [1, 2]),
    ("p-h3o+", ["1_1_- / 2_1_+", "1_1_- / 1_1_+"], [1, 2]),
    ("p-h3o+", slice("1_1_- -> 2_1_+", "1_1_- -> 1_1_+"), [1, 2]),
    ("p-h3o+", slice("1_1_- / 2_1_+", "1_1_- / 1_1_+"), [1, 2]),
]


# test functions
@mark.parametrize("datafile", choices(datafiles, k=10))
def test_query_by_name(datafile: str) -> None:
    assert query(datafile)


@mark.parametrize("datafile", choices(datafiles, k=10))
def test_query_by_path(datafile: str) -> None:
    with query(datafile).to_tempfile() as file:
        assert query(file.name)


@mark.parametrize("datafile, level, expected_id", levels)
def test_levels(datafile: str, level: Any, expected_id: Any) -> None:
    id = query(datafile).levels_loc[level][LEVEL_COLUMN]
    assert (id == expected_id).all()


@mark.parametrize("datafile, transition, expected_id", transitions)
def test_transitions(datafile: str, transition: Any, expected_id: Any) -> None:
    id = query(datafile).transitions_loc[transition][TRANSITION_COLUMN]
    assert (id == expected_id).all()
