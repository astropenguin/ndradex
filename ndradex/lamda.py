__all__ = ["LAMDA", "query"]


# standard library
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from pathlib import Path
from re import compile
from tempfile import NamedTemporaryFile
from typing import Any, Callable, ClassVar, IO, Generator, Optional, Union
from warnings import catch_warnings, simplefilter


# dependencies
import numpy as np
from astropy.table import Table
from astroquery.lamda import Lamda, parse_lamda_datafile, write_lamda_datafile
from requests_cache import CachedSession
from typing_extensions import Self
from .consts import DATAFILE, LEVEL, TRANSITION, alias


# type hints
LevelLike = Union[int, str]
PathLike = Union[Path, str]
Tables = tuple[dict[str, Table], Table, Table]
Timeout = Optional[float]
TransitionLike = Union[int, str, tuple[LevelLike, LevelLike]]


# constants
DATAFILE_SUFFIX = ".dat"
HTTP_SESSION = CachedSession("ndradex", use_cache_dir=True)
LEVEL_COLUMN = "Level"
LEVEL_NAME_COLUMN = "J"
LEVEL_NAME_REGEX = compile(r"^['\"\s]*(.+?)['\"\s]*$")
TRANSITION_COLUMN = "Transition"
TRANSITION_SEPS = "->", "/", "-"
UPLOW_COLUMNS = ["Upper", "Lower"]
URL_REGEX = compile(r"https?://")


@dataclass
class LAMDA:
    """LAMDA database of molecules and atoms."""

    name: str
    """Name of the molecule or atom."""

    levels: Table = field(repr=False)
    """Table of the energy levels."""

    transitions: Table = field(repr=False)
    """Table of the transitions."""

    colliders: dict[str, Table] = field(repr=False)
    """Tables of the collision partners."""

    @property
    def levels_loc(self) -> "TableLoc":
        """Custom TableLoc object for the levels."""
        return TableLoc(self.levels, self)

    @property
    def transitions_loc(self) -> "TableLoc":
        """Custom TableLoc object for the transitions."""
        return TableLoc(self.transitions, self)

    @property
    def colliders_loc(self) -> dict[str, "TableLoc"]:
        """Custom TableLoc objects for the collision partners."""
        return {
            collider: TableLoc(table, self)
            for collider, table in self.colliders.items()
        }

    @classmethod
    def from_datafile(cls, datafile: PathLike) -> Self:
        """Create a LAMDA object from a datafile."""
        datafile = Path(datafile).expanduser()
        tables = parse_lamda_datafile(datafile)
        return cls.from_tables(tables)  # type: ignore

    @classmethod
    def from_tables(cls, tables: Tables) -> Self:
        """Create a LAMDA object from tables."""
        return cls(
            name=tables[2].meta["molecule"],  # type: ignore
            levels=reformat_levels(tables[2]),
            transitions=tables[1],
            colliders=tables[0],
        )

    def to_datafile(self, datafile: PathLike) -> None:
        """Save the LAMDA object to a datafile."""
        tables = self.colliders, self.transitions, self.levels
        write_lamda_datafile(datafile, tables)

    def to_tempfile(self) -> IO[str]:
        """Save the LAMDA object to a temporary datafile."""
        file = NamedTemporaryFile("w", suffix=DATAFILE_SUFFIX)
        self.to_datafile(file.name)
        return file

    def to_bottom(self, transitions: list[TransitionLike]) -> Self:
        """Move transitions to the bottom of the transition table."""
        ids_all = self.transitions[TRANSITION_COLUMN]
        ids_sel = self.transitions_loc[transitions][TRANSITION_COLUMN]
        ids_mask = np.isin(ids_all, ids_sel)  # type: ignore
        ids_diff = np.delete(ids_all, ids_mask)  # type: ignore
        ids_new = np.append(ids_diff, ids_sel).tolist()  # type: ignore
        return replace(self, transitions=self.transitions_loc[ids_new])


def query(datafile: str, *, cache: bool = True, timeout: Timeout = None) -> LAMDA:
    """Create a LAMDA object from a RADEX datafile.

    Args:
        datafile: Query for a datafile. Either of the following:
            (1) name of the datafile (e.g. ``"co"`` or ``"co.dat"``),
            (2) path of the datafile (e.g. ``"/path/to/co.dat"``),
            (3) URL of the datafile (e.g. ``"https://example.com/co.dat"``).
        cache: Whether to cache the LAMDA object creation.
        timeout: Timeout length in units of seconds.
            Defaults to ``None`` (unlimited creation time).

    Returns:
        LAMDA object created from the RADEX datafile.

    """
    if URL_REGEX.match(datafile := alias(datafile, DATAFILE)):
        return get_lamda_by_url(datafile, cache=cache, timeout=timeout)

    try:
        return get_lamda_by_path(datafile)
    except FileNotFoundError:
        return get_lamda_by_name(datafile, cache=cache, timeout=timeout)


def get_lamda_by_path(datafile: str) -> LAMDA:
    """Create a LAMDA object from a local RADEX datafile."""
    return LAMDA.from_datafile(datafile)


def get_lamda_by_name(datafile: str, *, cache: bool, timeout: Timeout) -> LAMDA:
    """Create a LAMDA object from an astroquery RADEX datafile."""
    with catch_warnings():
        simplefilter("ignore")
        tables = Lamda.query(Path(datafile).stem, cache=cache, timeout=timeout)
        return LAMDA.from_tables(tables)  # type: ignore


def get_lamda_by_url(datafile: str, *, cache: bool, timeout: Timeout) -> LAMDA:
    """Create a LAMDA object from a remote RADEX datafile."""
    response = HTTP_SESSION.get(
        url=datafile,
        timeout=timeout,
        expire_after=-1 if cache else 0,
    )

    if not response.ok:
        raise FileNotFoundError(datafile)

    with NamedTemporaryFile("w", suffix=DATAFILE_SUFFIX) as file:
        file.write(response.text)
        return LAMDA.from_datafile(file.name)


def get_level_id(level: LevelLike, lamda: LAMDA) -> int:
    """Return a level ID from a level-like object."""
    if not isinstance(level, (int, str)):
        raise TypeError(f"Level must be {LevelLike}.")

    if isinstance(level, int):
        return level

    if isinstance(level, str):
        level = alias(level, LEVEL).strip()

    frame = lamda.levels.to_pandas(False).set_index(LEVEL_NAME_COLUMN)
    return int(frame[LEVEL_COLUMN].loc[level])


def get_transition_id(transition: TransitionLike, lamda: LAMDA) -> int:
    """Return a transition ID from a transition-like object."""
    if not isinstance(transition, (int, str, tuple)):
        raise TypeError(f"Transition must be {TransitionLike}.")

    if isinstance(transition, int):
        return transition

    if isinstance(transition, str):
        transition = split_transition(alias(transition, TRANSITION))

    uplow = tuple(get_level_id(level, lamda) for level in transition)
    frame = lamda.transitions.to_pandas(False).set_index(UPLOW_COLUMNS)
    return int(frame[TRANSITION_COLUMN].loc[uplow])


def reformat_levels(levels: Table) -> Table:
    """Remove unnecessary strings from level names."""

    @np.vectorize
    def trim(level_name: str) -> str:
        return LEVEL_NAME_REGEX.sub(r"\1", level_name)

    level_names = levels[LEVEL_NAME_COLUMN]
    level_names[:] = trim(level_names)  # type: ignore
    return levels


@contextmanager
def set_indices(lamda: LAMDA) -> Generator[None, Any, None]:
    """Temporarily Set indices to tables in a LAMDA object."""
    try:
        lamda.levels.add_index(LEVEL_COLUMN)
        lamda.transitions.add_index(TRANSITION_COLUMN)
        yield None
    finally:
        lamda.levels.remove_indices(LEVEL_COLUMN)
        lamda.transitions.remove_indices(TRANSITION_COLUMN)


def split_transition(transition: str) -> tuple[str, str]:
    """Split a transition string in upper and lower levels."""
    for sep in TRANSITION_SEPS:
        if len(subs := transition.split(sep, 1)) == 2:
            return subs[0].strip(), subs[1].strip()

    raise ValueError(f"{transition} cannot be split in two.")


@dataclass
class TableLoc:
    """Custom TableLoc for LAMDA tables."""

    table: Table
    """Table to be sliced."""

    lamda: LAMDA = field(repr=False)
    """LAMDA object for getting table IDs."""

    get_ids: ClassVar[dict[str, Callable[[Any, LAMDA], int]]]
    """Functions for getting an ID from a query."""

    get_ids = {
        LEVEL_COLUMN: get_level_id,
        TRANSITION_COLUMN: get_transition_id,
    }

    def index(self, query: Any) -> Union[slice, list[int], int]:
        """Convert a query to an index for a TableLoc object."""
        get_id = self.get_ids[self.table.colnames[0]]

        if isinstance(query, slice):
            if (start := query.start) is not None:
                start = get_id(start, self.lamda)

            if (stop := query.stop) is not None:
                stop = get_id(stop, self.lamda)

            return slice(start, stop, query.step)
        elif isinstance(query, list):
            return [get_id(q, self.lamda) for q in query]
        else:
            return get_id(query, self.lamda)

    def __getitem__(self, query: Any) -> Table:
        """Slice the table by a query."""
        with set_indices(self.lamda):
            return Table(self.table.loc[self.index(query)])
