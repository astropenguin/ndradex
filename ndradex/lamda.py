__all__ = ['LAMDA']

# from standard library
from typing import Union
from pathlib import Path

# from dependent packages
import ndradex as nd
from astropy import units as u
from astropy.table import Column
from astroquery.lamda import Lamda
from astroquery.lamda import parse_lamda_datafile
from astroquery.lamda import write_lamda_datafile

# module constants
PathLike = Union[Path, str]


class LAMDA:
    def __init__(self, moldata: PathLike):
        if moldata in nd.config['alias']:
            moldata = nd.config['alias'][moldata]

        tables = self._get_tables(moldata)
        self._collrates = tables[0]
        self._transitions = tables[1]
        self._levels = tables[2]

    @property
    def transitions(self):
        return list(self._transitions['Name'])

    @property
    def frequencies(self):
        if hasattr(self, '_frequencies'):
            return self._frequencies

        transitions = self._transitions['Name']
        frequencies = self._transitions['Frequency'] * u.GHz

        self._frequencies = dict(zip(transitions, frequencies))
        return self._frequencies

    @property
    def a_coeffs(self):
        if hasattr(self, '_a_coeffs'):
            return self._a_coeffs

        transitions = self._transitions['Name']
        a_coeffs = self._transitions['EinsteinA'] / u.s

        self._a_coeffs = dict(zip(transitions, a_coeffs))
        return self._a_coeffs

    @property
    def upper_energies(self):
        if hasattr(self, '_upper_energies'):
            return self._upper_energies

        transitions = self._transitions['Name']
        upper_energies = self._transitions['E_u(K)'] * u.K

        self._upper_energies = dict(zip(transitions, upper_energies))
        return self._upper_energies

    def _get_tables(self, moldata: PathLike):
        """(Down)load molecular data as astropy tables.

        This will also add a column of transition name
        (i.e., 1-0) to the transition table (as Name).

        """
        path = Path(moldata).expanduser()

        if path.exists():
            collrates, transitions, levels = parse_lamda_datafile(path)
        else:
            collrates, transitions, levels = Lamda.query(moldata)

        data = []
        levels.add_index('Level')

        for row in transitions:
            J_u = levels.loc[row['Upper']]['J']
            J_l = levels.loc[row['Lower']]['J']
            data.append(f'{J_u}-{J_l}')

        transitions.add_column(Column(data, 'Name'))
        transitions.add_index('Name')

        return collrates, transitions, levels

    def __repr__(self):
        molname = self._levels.meta['molecule']
        return f'LAMDA({molname})'
