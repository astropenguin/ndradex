# dependencies
from astroquery import lamda
from ndradex.lamda import (
    LEVEL_COLUMN,
    TRANSITION_COLUMN,
    LevelLike,
    TransitionLike,
    get_lamda,
)
from pytest import mark


# test data
datafile_names = list(lamda.Lamda.molecule_dict)
datafile_names.remove("so2@lowT")
levels = [
    # (datafile name, query, expected level ID)
    ("co", 1, 1),
    ("co", 2, 2),
    ("co", "0", 1),
    ("co", "1", 2),
    ("cn", 1, 1),
    ("cn", 2, 2),
    ("cn", "0_0.5", 1),
    ("cn", "1_0.5", 2),
]
transitions = [
    # (datafile name, query, expected transition ID)
    ("co", 1, 1),
    ("co", 2, 2),
    ("co", "1-0", 1),
    ("co", "2-1", 2),
    ("co", (2, 1), 1),
    ("co", (3, 2), 2),
    ("co", ("1", "0"), 1),
    ("co", ("2", "1"), 2),
    ("cn", 1, 1),
    ("cn", 2, 2),
    ("cn", "1_0.5-0_0.5", 1),
    ("cn", "1_1.5-0_0.5", 2),
    ("cn", (2, 1), 1),
    ("cn", (3, 1), 2),
    ("cn", ("1_0.5", "0_0.5"), 1),
    ("cn", ("1_1.5", "0_0.5"), 2),
]


# test functions
@mark.parametrize("name", datafile_names)
def test_get_lamda_by_name(name: str) -> None:
    assert get_lamda(name)


@mark.parametrize("name", datafile_names)
def test_get_lamda_by_path(name: str) -> None:
    with get_lamda(name).to_tempfile() as file:
        assert get_lamda(file.name)


@mark.parametrize("name, query, level", levels)
def test_level(name: str, query: LevelLike, level: int) -> None:
    assert get_lamda(name).level(query)[LEVEL_COLUMN] == level


@mark.parametrize("name, query, transition", transitions)
def test_transition(name: str, query: TransitionLike, transition: int) -> None:
    assert get_lamda(name).transition(query)[TRANSITION_COLUMN] == transition
