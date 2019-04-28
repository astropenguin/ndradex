__all__ = ['LAMDA']

# from standard library
from logging import getLogger
from pathlib import Path
from tempfile import NamedTemporaryFile
logger = getLogger(__name__)

# from dependent packages
import ndradex as nd
from astropy.table import Column
from astroquery.lamda import Lamda
from astroquery.lamda import parse_lamda_datafile
from astroquery.lamda import write_lamda_datafile


class LAMDA:
    def __init__(self, moldata):
        if moldata in nd.config['alias']:
            moldata = nd.config['alias'][moldata]

        tables = self._get_tables(moldata)
        self._collrates = tables[0]
        self._transitions = tables[1]
        self._levels = tables[2]

    @property
    def qn_ul(self):
        """List of transition quantum numbers."""
        return list(self._transitions['QN_ul'])

    @property
    def freq(self):
        """Dictionary of radiation frequencies."""
        if hasattr(self, '_freq'):
            return self._freq

        freq = self._transitions['Frequency']
        self._freq = dict(zip(self.qn_ul, freq))
        return self._freq

    @property
    def a_coeff(self):
        """Dictionary of Einstein A coefficients."""
        if hasattr(self, '_a_coeff'):
            return self._a_coeff

        a_coeff = self._transitions['EinsteinA']
        self._a_coeff = dict(zip(self.qn_ul, a_coeff))
        return self._a_coeffs

    @property
    def e_up(self):
        """Dictionary of upper state energies."""
        if hasattr(self, '_e_up'):
            return self._e_up

        e_up = self._transitions['E_u(K)']
        self._e_up = dict(zip(self.qn_ul, e_up))
        return self._e_up

    def _get_tables(self, moldata):
        """(Down)load molecular data as astropy tables.

        This will also add a column of transition quantum
        numbers (i.e., 1-0) to the transition table (QN_ul).

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

        transitions.add_column(Column(data, 'QN_ul'))
        transitions.add_index('QN_ul')
        return collrates, transitions, levels

    def __enter__(self):
        """Create a temporary moldata file inside a context block."""
        self._tempfile = NamedTemporaryFile()
        tables = (self._collrates, self._transitions, self._levels)
        write_lamda_datafile(self._tempfile.name, tables)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Delete a temporary moldata file outside a context block."""
        self._tempfile.close()
        delattr(self, '_tempfile')

    def __repr__(self):
        if hasattr(self, '_tempfile'):
            return self._tempfile.name

        molecule = self._levels.meta['molecule']
        return f'LAMDA({molecule})'
