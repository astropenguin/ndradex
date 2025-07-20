__all__ = ["LAMDA"]


# standard library
from dataclasses import dataclass, field, replace
from os import PathLike


# dependencies
from astropy.table import Table, join, vstack
from astroquery.lamda import parse_lamda_datafile, write_lamda_datafile
from typing_extensions import Self


# type hints
Tables = tuple[dict[str, Table], Table, Table]


# constants
NAMED_TRANSITION = "NamedTransition"


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

    def prioritize(self, transitions: list[int | str], /) -> Self:
        """Prioritize given transitions in the transitions table."""
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
