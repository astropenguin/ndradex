__all__ = ["LAMDA", "get_lamda"]


# standard library
from dataclasses import dataclass, field
from pathlib import Path
from re import compile
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Dict, IO, Optional, List, Tuple, Union, overload


# dependencies
from astropy.table import Row, Table
from astroquery.lamda import Lamda, parse_lamda_datafile, write_lamda_datafile
from requests_cache import CachedSession
from typing_extensions import Self
from .consts import LAMDA_ALIASES


# type hints
LevelLike = Union[int, str]
PathLike = Union[Path, str]
Tables = Tuple[Dict[str, Table], Table, Table]
Timeout = Optional[float]
TransitionLike = Union[int, str, Tuple[LevelLike, LevelLike]]


# constants
DATAFILE_SUFFIX = ".dat"
HTTP_SESSION = CachedSession("ndradex", use_cache_dir=True)
LEVEL_COLUMN = "Level"
LEVEL_NAME_COLUMN = "J"
TRANSITION_COLUMN = "Transition"
TRANSITION_SEP = "-"
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

    colliders: Dict[str, Table] = field(repr=False)
    """Tables of the collision partners."""

    @property
    def levels_(self) -> "TableSlicer":
        """Slicer of the levels table."""
        return TableSlicer(self.levels, get_level_id, self)

    @property
    def transitions_(self) -> "TableSlicer":
        """Slicer of the transitions table."""
        return TableSlicer(self.transitions, get_transition_id, self)

    @property
    def colliders_(self) -> Dict[str, "TableSlicer"]:
        """Slicer of the collision partner tables."""
        return {
            name: TableSlicer(table, get_transition_id, self)
            for name, table in self.colliders.items()
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
            levels=tables[2],
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

    def __post_init__(self) -> None:
        """Set default indexes to the tables."""
        self.levels.add_index(LEVEL_COLUMN, unique=True)
        self.transitions.add_index(TRANSITION_COLUMN, unique=True)

        for table in self.colliders.values():
            table.add_index(TRANSITION_COLUMN, unique=True)


@dataclass
class TableSlicer:
    """Slicer for Astropy tables."""

    table: Table
    """Table to be sliced."""

    getid: Callable[[Any, LAMDA], int] = field(repr=False)
    """Function for getting table IDs."""

    lamda: LAMDA = field(repr=False)
    """LAMDA object for getting table IDs."""

    @overload
    def __getitem__(self, query: slice) -> Table:
        ...

    @overload
    def __getitem__(self, query: List[Any]) -> Table:
        ...

    @overload
    def __getitem__(self, query: Any) -> Row:
        ...

    def __getitem__(self, query: Any) -> Any:
        """Slice the table by a query."""
        if isinstance(query, slice):
            if (start := query.start) is not None:
                start = self.getid(start, self.lamda)

            if (stop := query.stop) is not None:
                stop = self.getid(stop, self.lamda)

            index = slice(start, stop, query.step)
            return Table(self.table.loc[index])

        if isinstance(query, list):
            index = [self.getid(q, self.lamda) for q in query]
            return Table(self.table.loc[index])

        index = self.getid(query, self.lamda)
        return self.table.loc[index]


def get_lamda(query: str, *, cache: bool = True, timeout: Timeout = None) -> LAMDA:
    """Create a LAMDA object from a query.

    Args:
        query: Query string for a datafile. Either of the following:
            (1) name of the datafile (e.g. `"co"` or `"co.dat"`),
            (2) path of the datafile (e.g. `"/path/to/file.dat"`),
            or (3) URL of the datafile (e.g. `"https://example.com/co.dat"`).
        cache: Whether to cache the query result. Defaults to `True`.
        timeout: Timeout length in seconds. Defaults to `None` (no timeout).

    Returns:
        LAMDA object created from the query.

    """
    query = LAMDA_ALIASES.get(query, query)

    if URL_REGEX.match(query):
        return get_lamda_by_url(query, cache=cache, timeout=timeout)

    try:
        return get_lamda_by_path(query)
    except FileNotFoundError:
        return get_lamda_by_name(query, cache=cache, timeout=timeout)


def get_lamda_by_path(query: str) -> LAMDA:
    """Create a LAMDA object by a local datafile path."""
    return LAMDA.from_datafile(query)


def get_lamda_by_name(query: str, *, cache: bool, timeout: Timeout) -> LAMDA:
    """Create a LAMDA object by a datafile name."""
    tables = Lamda.query(Path(query).stem, cache=cache, timeout=timeout)
    return LAMDA.from_tables(tables)  # type: ignore


def get_lamda_by_url(query: str, *, cache: bool, timeout: Timeout) -> LAMDA:
    """Create a LAMDA object by a datafile URL."""
    if cache:
        response = HTTP_SESSION.get(query, timeout=timeout, expire_after=-1)
    else:
        response = HTTP_SESSION.get(query, timeout=timeout, expire_after=0)

    if not response.ok:
        raise FileNotFoundError(query)

    with NamedTemporaryFile("w", suffix=DATAFILE_SUFFIX) as file:
        file.write(response.text)
        return LAMDA.from_datafile(file.name)


def get_level_id(query: LevelLike, lamda: LAMDA) -> int:
    """Return a level ID from a query."""
    if not isinstance(query, (int, str)):
        raise TypeError(f"Query must be {LevelLike}.")

    if isinstance(query, int):
        return query

    level = query.strip()
    frame = lamda.levels.to_pandas(False).set_index(LEVEL_NAME_COLUMN)
    return int(frame[LEVEL_COLUMN].loc[level])


def get_transition_id(query: TransitionLike, lamda: LAMDA) -> int:
    """Return a transition ID from a query."""
    if not isinstance(query, (int, str, tuple)):
        raise TypeError(f"Query must be {TransitionLike}.")

    if isinstance(query, int):
        return query

    if isinstance(query, str):
        query = tuple(query.split(TRANSITION_SEP))

    upper = get_level_id(query[0], lamda)
    lower = get_level_id(query[1], lamda)
    frame = lamda.transitions.to_pandas(False).set_index(UPLOW_COLUMNS)
    return int(frame[TRANSITION_COLUMN].loc[(upper, lower)])