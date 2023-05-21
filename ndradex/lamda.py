__all__ = ["LAMDA", "get_lamda"]


# standard library
from dataclasses import dataclass, field
from pathlib import Path
from re import compile
from tempfile import NamedTemporaryFile
from typing import IO, Dict, Optional, Tuple, Union


# dependencies
from astropy.table import Table
from astroquery.lamda import Lamda, parse_lamda_datafile, write_lamda_datafile
from requests_cache import CachedSession
from typing_extensions import Self
from .consts import LAMDA_ALIASES


# type hints
PathLike = Union[Path, str]
Tables = Tuple[Dict[str, Table], Table, Table]
Timeout = Optional[float]


# constants
DAT = ".dat"
HTTP_SESSION = CachedSession("ndradex", use_cache_dir=True)
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

    def persist(self) -> IO[str]:
        """Save the LAMDA object to a temporary datafile."""
        file = NamedTemporaryFile("w", suffix=DAT)
        self.to_datafile(file.name)
        return file


def get_lamda(query: PathLike, *, cache: bool = True, timeout: Timeout = None) -> LAMDA:
    """Create a LAMDA object."""
    if isinstance(query, Path):
        query_ = str(query)
    else:
        query_ = LAMDA_ALIASES.get(query, query)

    if URL_REGEX.match(query_):
        return get_lamda_by_url(query_, cache=cache, timeout=timeout)

    try:
        return get_lamda_by_path(query_)
    except FileNotFoundError:
        return get_lamda_by_name(query_, cache=cache, timeout=timeout)


def get_lamda_by_name(query: str, *, cache: bool, timeout: Timeout) -> LAMDA:
    """Create a LAMDA object by a datafile name."""
    tables = Lamda.query(query.rstrip(DAT), cache=cache, timeout=timeout)
    return LAMDA.from_tables(tables)  # type: ignore


def get_lamda_by_path(query: PathLike) -> LAMDA:
    """Create a LAMDA object by a local datafile path."""
    return LAMDA.from_datafile(query)


def get_lamda_by_url(query: str, *, cache: bool, timeout: Timeout) -> LAMDA:
    """Create a LAMDA object by a datafile URL."""
    if cache:
        response = HTTP_SESSION.get(query, timeout=timeout, expire_after=-1)
    else:
        response = HTTP_SESSION.get(query, timeout=timeout, expire_after=0)

    if not response.ok:
        raise FileNotFoundError(query)

    with NamedTemporaryFile("w", suffix=DAT) as file:
        file.write(response.text)
        return LAMDA.from_datafile(file.name)
