# standard library
from random import choices
from typing import Any
from warnings import catch_warnings, simplefilter


# dependencies
from astroquery.lamda import Lamda
from ndradex.lamda import LEVEL_COLUMN, TRANSITION_COLUMN, query
from pytest import mark


# test data
with catch_warnings():
    simplefilter("ignore")
    datafiles = list(Lamda.molecule_dict)
    datafiles.remove("si-h")
    datafiles.remove("so2@lowT")
    datafiles.remove("PO_hfs")

levels = [
    # (datafile, level, expected level ID)
    ("co", 1, 1),
    ("co", [1, 2], [1, 2]),
    ("co", slice(1, 2), [1, 2]),
    ("co", "0", 1),
    ("co", ["0", "1"], [1, 2]),
    ("co", slice("0", "1"), [1, 2]),
    ("oh", 1, 1),
    ("oh", [1, 2], [1, 2]),
    ("oh", slice(1, 2), [1, 2]),
    ("oh", "1.5_-_1", 1),
    ("oh", ["1.5_-_1", "1.5_+_1"], [1, 2]),
    ("oh", slice("1.5_-_1", "1.5_+_1"), [1, 2]),
]
transitions = [
    # (datafile, transition, expected transition ID)
    ("co", 1, 1),
    ("co", (2, 1), 1),
    ("co", [1, 2], [1, 2]),
    ("co", [(2, 1), (3, 2)], [1, 2]),
    ("co", slice(1, 2), [1, 2]),
    ("co", slice((2, 1), (3, 2)), [1, 2]),
    ("co", "1->0", 1),
    ("co", "1/0", 1),
    ("co", "1-0", 1),
    ("co", ("1", "0"), 1),
    ("co", ["1->0", "2->1"], [1, 2]),
    ("co", ["1/0", "2/1"], [1, 2]),
    ("co", ["1-0", "2-1"], [1, 2]),
    ("co", slice("1->0", "2->1"), [1, 2]),
    ("co", slice("1/0", "2/1"), [1, 2]),
    ("co", slice("1-0", "2-1"), [1, 2]),
    ("oh", 1, 1),
    ("oh", (3, 1), 1),
    ("oh", [1, 2], [1, 2]),
    ("oh", [(3, 1), (4, 2)], [1, 2]),
    ("oh", slice(1, 2), [1, 2]),
    ("oh", slice((3, 1), (4, 2)), [1, 2]),
    ("oh", "2.5_+_1->1.5_-_1", 1),
    ("oh", "2.5_+_1/1.5_-_1", 1),
    ("oh", ("2.5_+_1", "1.5_-_1"), 1),
    ("oh", ["2.5_+_1->1.5_-_1", "2.5_-_1->1.5_+_1"], [1, 2]),
    ("oh", ["2.5_+_1/1.5_-_1", "2.5_-_1/1.5_+_1"], [1, 2]),
    ("oh", slice("2.5_+_1->1.5_-_1", "2.5_-_1->1.5_+_1"), [1, 2]),
    ("oh", slice("2.5_+_1/1.5_-_1", "2.5_-_1/1.5_+_1"), [1, 2]),
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
