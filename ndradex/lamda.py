# from standard library

# from dependent packages
import ndradex as nd
from astropy import units as u
from astropy.table import Column
from astroquery.lamda import Lamda


class LAMDA:
    def __init__(self, query):
        if query in nd.config['alias']:
            query = nd.config['alias'][query]

        tables = self._get_tables(query)
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

    def _get_tables(self, query):
        """(Down) load molecular data as astropy tables."""
        collrates, transitions, levels = Lamda.query(query)
        levels.add_index('Level')

        data = []
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


def list_moldata():
    names = list(Lamda.molecule_dict)

    for alias, name in nd.config['alias'].items():
        if name not in names:
            continue

        names.append(alias)

    return names
