__all__ = ["LAMDA"]


# standard library
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import IO, Dict, Tuple, Union


# dependencies
from astropy.table import Table
from astroquery.lamda import parse_lamda_datafile, write_lamda_datafile
from typing_extensions import Self


# type hints
PathLike = Union[Path, str]
Tables = Tuple[Dict[str, Table], Table, Table]


# constants
DAT = ".dat"


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
        datafile = Path(datafile).expanduser().with_suffix(DAT)
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

