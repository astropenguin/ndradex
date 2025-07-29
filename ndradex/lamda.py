__all__ = ["LAMDA", "get_lamda"]


# standard library
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from os import PathLike
from pathlib import Path
from re import compile
from tempfile import NamedTemporaryFile
from warnings import catch_warnings, simplefilter


# dependencies
import numpy as np
from astropy.table import Table, vstack
from astroquery.lamda import Lamda, parse_lamda_datafile, write_lamda_datafile
from numpy.typing import ArrayLike
from requests_cache import CachedSession
from typing_extensions import Self


# constants
HTTP_REGEX = compile(r"https?://")
HTTP_SESSION = CachedSession("ndradex", backend="memory")
NAMED_TRANSITION = "NamedTransition"
TRANSITION = "Transition"


@dataclass(frozen=True)
class LAMDA:
    """LAMDA database of molecules and atoms.

    Args:
        colliders: Tables of the collision partners.
        transitions: Table of the transitions.
        levels: Table of the energy levels.

    """

    name: str = field(init=False)
    """Name of the molecule or atom."""

    colliders: dict[str, Table] = field(repr=False)
    """Tables of the collision partners."""

    transitions: Table = field(repr=False)
    """Table of the transitions."""

    levels: Table = field(repr=False)
    """Table of the energy levels."""

    @classmethod
    def from_datafile(cls, datafile: PathLike[str] | str, /) -> Self:
        """Create a LAMDA object from a LAMDA datafile."""
        return cls(*parse_lamda_datafile(str(datafile)))  # type: ignore

    def to_datafile(self, datafile: PathLike[str] | str, /) -> None:
        """Save the LAMDA object to a LAMDA datafile."""
        saved_transitions = self.transitions.copy()
        saved_transitions.remove_column(NAMED_TRANSITION)
        tables = self.colliders, saved_transitions, self.levels
        write_lamda_datafile(datafile, tables)

    def prioritize(self, transitions: ArrayLike, /) -> Self:
        """Prioritize given transitions in the transitions table."""
        transitions = np.atleast_1d(transitions)

        if (kind := transitions.dtype.kind) == "i":
            index = TRANSITION
        elif kind == "U":
            index = NAMED_TRANSITION
        else:
            raise TypeError("Could not infer dtype of transitions.")

        with set_index(self.transitions, index):
            top = self.transitions.copy()
            bottom = top.copy().loc[transitions]
            top.remove_rows(top.loc_indices[transitions])
            return replace(self, transitions=vstack([top, bottom]))

    def __post_init__(self) -> None:
        name = self.levels.meta["molecule"]  # type: ignore
        object.__setattr__(self, "name", name)

        if NAMED_TRANSITION in self.transitions.keys():
            return None

        with set_index(self.levels, "Level"):
            J_upper = Table(self.levels.loc[self.transitions["Upper"]])["J"]
            J_lower = Table(self.levels.loc[self.transitions["Lower"]])["J"]

        named_transition = J_upper + "-" + J_lower  # type: ignore
        named_transition.name = NAMED_TRANSITION
        self.transitions.add_column(named_transition)


def get_lamda(
    query: str,
    /,
    *,
    cache: bool = True,
    timeout: float | None = None,
) -> LAMDA:
    """Parse given query to create a LAMDA object.

    Args:
        query: Query string for the LAMDA object.
            If the query is a URL (e.g. ``'https://example.com/co.dat'``),
            the function creates from the datafile at the URL.
            If the query is path-like (e.g. ``'co.dat'``) and it exists,
            the function creates from the datafile. If it does not exist
            but is found in ``astroquery.lamda.Lamda.moledule_dict``
            (e.g. ``'co'``), the function creates from the dictionary.
        cache: Whether to cache the HTTP session.
        timeout: Timeout of the HTTP session in seconds.

    Returns:
        LAMDA object created from the parsed query.

    Examples::

        co = get_lamda("co")
        cs = get_lamda("/path/to/cs.dat")
        cn = get_lamda("https://example.com/cn.dat")

    """
    with catch_warnings():
        simplefilter("ignore")

        if HTTP_REGEX.match(query):
            response = HTTP_SESSION.get(
                url=query,
                timeout=timeout,
                expire_after=-1 if cache else 0,
            )
            response.raise_for_status()

            with NamedTemporaryFile("w") as tempfile:
                tempfile.write(response.text)
                return LAMDA.from_datafile(tempfile.name)

        if (path := Path(query)).exists():
            return LAMDA.from_datafile(path)

        tables = Lamda.query(query, cache=cache, timeout=timeout)
        return LAMDA(*tables)  # type: ignore


@contextmanager
def set_index(table: Table, index: str, /) -> Iterator[None]:
    """Temporarily set a index to given table.

    Args:
        table: Table to which the index will be set.
        index: Name of the index to be set.

    """
    if table.indices:
        raise ValueError("Indices already exist.")

    try:
        table.add_index(index)
        yield None
    finally:
        table.remove_indices(index)
