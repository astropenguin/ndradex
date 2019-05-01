__all__ = ['LAMDA']

# from standard library
from logging import getLogger
from pathlib import Path
logger = getLogger(__name__)

# from dependent packages
import ndradex as nd


class LAMDA:
    def __init__(self, query, dir=None):
        if query in nd.config['alias']:
            query = nd.config['alias'][query]

        tables = get_tables(query)
        temppath = get_temppath(query, dir)

        self._collrates = tables[0]
        self._transitions = tables[1]
        self._levels = tables[2]
        self._temppath = temppath

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

    def __enter__(self):
        """Create a temporary moldata inside a context block."""
        # lazy import of astropy-related things
        from astroquery.lamda import write_lamda_datafile

        tables = (self._collrates, self._transitions, self._levels)
        write_lamda_datafile(self._temppath, tables)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Delete a temporary moldata outside a context block."""
        self._temppath.unlink()

    def __str__(self):
        return str(self._temppath)

    def __repr__(self):
        molecule = self._levels.meta['molecule']
        return f'LAMDA({molecule})'


# utility functions
def get_tables(query):
    """(Down)load molecular data as astropy tables.

    This will also add a column of transition quantum
    numbers (i.e., 1-0) to the transition table (QN_ul).

    """
    # lazy import of astropy-related things
    from astropy.table import Column
    from astroquery.lamda import Lamda
    from astroquery.lamda import parse_lamda_datafile

    path = Path(query).expanduser()

    if path.exists():
        collrates, transitions, levels = parse_lamda_datafile(path)
    else:
        collrates, transitions, levels = Lamda.query(path.stem)

    levels.add_index('Level')

    data = []
    for row in transitions:
        J_u = ensure_qn(levels.loc[row['Upper']]['J'])
        J_l = ensure_qn(levels.loc[row['Lower']]['J'])
        data.append(f'{J_u}-{J_l}')

    transitions.add_column(Column(data, 'QN_ul'))
    transitions.add_index('QN_ul')
    return collrates, transitions, levels


def get_temppath(query, dir=None):
    """Get path object for temporary moldata."""
    moldata = Path(query).stem + '.dat'

    if dir is None:
        return Path('.', moldata).expanduser()
    else:
        return Path(dir, moldata).expanduser()


def ensure_qn(qn):
    """Trim unnecessary characters from QN string."""
    try:
        return str(int(qn))
    except ValueError:
        return qn.strip('" ')
