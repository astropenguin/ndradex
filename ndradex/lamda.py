__all__ = ["LAMDA", "get_lamda"]


# standard library
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from os import PathLike
from pathlib import Path
from tempfile import NamedTemporaryFile


# dependencies
import numpy as np
from astropy.table import Table, join, vstack
from astroquery.lamda import Lamda, parse_lamda_datafile, write_lamda_datafile
from requests_cache import CachedSession
from typing_extensions import Self


# type hints
Tables = tuple[dict[str, Table], Table, Table]
Transitions = Sequence[int] | Sequence[str]


# constants
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
        return cls(*parse_lamda_datafile(datafile))  # type: ignore

    def to_datafile(self, datafile: PathLike[str] | str, /) -> None:
        """Save the LAMDA object to a LAMDA datafile."""
        saved_transitions = self.transitions.copy()
        saved_transitions.remove_column(NAMED_TRANSITION)
        tables = self.colliders, saved_transitions, self.levels
        write_lamda_datafile(datafile, tables)

    def prioritize(self, transitions: Transitions, /) -> Self:
        """Prioritize given transitions in the transitions table."""
        transitions = list(transitions)  # type: ignore

        if (kind := np.array(transitions).dtype.kind) == "i":
            name = TRANSITION
        elif kind == "U":
            name = NAMED_TRANSITION
        else:
            raise TypeError("Could not infer dtype of transitions.")

        with set_index(self.transitions, name):
            top = self.transitions.copy()
            bottom = top.loc[transitions]
            top.remove_rows(top.loc_indices[transitions])
            return replace(self, transitions=vstack([top, bottom]))

    def __post_init__(self) -> None:
        if not hasattr(self, "name"):
            name = self.levels.meta["molecule"]  # type: ignore
            object.__setattr__(self, "name", name)

        if NAMED_TRANSITION not in self.transitions.keys():
            joined = join(
                self.transitions,
                self.levels,
                keys_left="Upper",
                keys_right="Level",
            )
            joined = join(
                joined,
                self.levels,
                keys_left="Lower",
                keys_right="Level",
            )
            named_transition = joined["J_1"] + "-" + joined["J_2"]
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
            If the query is path-like (e.g. ``'co.dat'``) and it exists,
            the function creates from the datafile. If it does not exist
            but is found in ``astroquery.lamda.Lamda.moledule_dict``,
            the function creates from the dictionary.
            If the query is a URL (e.g. ``'https://example.com/co.dat'``),
            the function creates from the datafile at the URL.
        cache: Whether to cache the HTTP session.
        timeout: Timeout of the HTTP session in seconds.

    Returns:
        LAMDA object created from the parsed query.

    Examples::

        co = get_lamda("co")
        cs = get_lamda("/path/to/cs.dat")
        cn = get_lamda("https://example.com/cn.dat")

    """
    if (path := Path(query)).exists():
        return LAMDA.from_datafile(query)

    if path.stem in Lamda.molecule_dict:
        tables = Lamda.query(
            Path(query).stem,
            cache=cache,
            timeout=timeout,
        )
        return LAMDA(*tables)  # type: ignore

    response = HTTP_SESSION.get(
        url=str(path),
        timeout=timeout,
        expire_after=-1 if cache else 0,
    )
    response.raise_for_status()

    with NamedTemporaryFile("w") as tempfile:
        tempfile.write(response.text)
        return LAMDA.from_datafile(tempfile.name)


@contextmanager
def set_index(table: Table, name: str, /) -> Iterator[None]:
    """Temporarily set a index to given table.

    Args:
        table: Table to which the index will be set.
        name: Name of the index to be set.

    """
    if table.indices:
        raise ValueError("Indices already exist.")

    try:
        table.add_index(name)
        yield None
    finally:
        table.remove_indices(name)
