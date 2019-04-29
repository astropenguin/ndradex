__all__ = ['LAMDA']

# from standard library
from logging import getLogger
from pathlib import Path
logger = getLogger(__name__)

# from dependent packages
import ndradex as nd
from astropy.table import Column
from astroquery.lamda import Lamda
from astroquery.lamda import parse_lamda_datafile
from astroquery.lamda import write_lamda_datafile


class LAMDA:
    def __init__(self, query, dir='.'):
        if query in nd.config['alias']:
            query = nd.config['alias'][query]

        tables = self._get_tables(query)
        path = self._get_temppath(query, dir)

        self._collrates = tables[0]
        self._transitions = tables[1]
        self._levels = tables[2]
        self._temppath = path

    @property
    def qn_ul(self):
        """List of transition quantum numbers."""
        return list(self._transitions['QN_ul'])

    @property
    def freq(self):
        """Transition frequencies in units of GHz."""
        if hasattr(self, '_freq'):
            return self._freq

        freq = self._transitions['Frequency']
        self._freq = dict(zip(self.qn_ul, freq))
        return self._freq

    @property
    def freq_lim(self):
        """Transition frequency ranges in units of GHz."""
        if hasattr(self, '_freq_lim'):
            return self._freq_lim

        freq = self._transitions['Frequency']
        freq_lim = [f'{(1-1e-9)*f} {(1+1e-9)*f}' for f in freq]
        self._freq_lim = dict(zip(self.qn_ul, freq_lim))
        return self._freq_lim

    @property
    def a_coeff(self):
        """Einstein A coefficients in units of s^-1."""
        if hasattr(self, '_a_coeff'):
            return self._a_coeff

        a_coeff = self._transitions['EinsteinA']
        self._a_coeff = dict(zip(self.qn_ul, a_coeff))
        return self._a_coeffs

    @property
    def e_up(self):
        """Upper state energies in units of K."""
        if hasattr(self, '_e_up'):
            return self._e_up

        e_up = self._transitions['E_u(K)']
        self._e_up = dict(zip(self.qn_ul, e_up))
        return self._e_up

    def _get_temppath(self, query, dir='.'):
        """Get path object for temporary moldata."""
        path = Path(query).expanduser()

        if path.exists():
            moldata = path.name
        else:
            moldata = query + '.dat'

        return Path(dir).expanduser() / moldata

    def _get_tables(self, query):
        """(Down)load molecular data as astropy tables.

        This will also add a column of transition quantum
        numbers (i.e., 1-0) to the transition table (QN_ul).

        """
        path = Path(query).expanduser()

        if path.exists():
            collrates, transitions, levels = parse_lamda_datafile(path)
        else:
            collrates, transitions, levels = Lamda.query(query)

        levels.add_index('Level')

        data = []
        for row in transitions:
            J_u = nd.parse_qn(levels.loc[row['Upper']]['J'])
            J_l = nd.parse_qn(levels.loc[row['Lower']]['J'])
            data.append(f'{J_u}-{J_l}')

        transitions.add_column(Column(data, 'QN_ul'))
        transitions.add_index('QN_ul')
        return collrates, transitions, levels

    def __enter__(self):
        """Create a temporary moldata inside a context block."""
        tables = (self._collrates, self._transitions, self._levels)
        write_lamda_datafile(self._temppath, tables)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Delete a temporary moldata outside a context block."""
        self._temppath.unlink()

    def __str__(self):
        return self._temppath.name

    def __repr__(self):
        molecule = self._levels.meta['molecule']
        return f'LAMDA({molecule})'
