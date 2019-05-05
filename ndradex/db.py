__all__ = ['LAMDA']

# from standard library
import re
import warnings
from logging import getLogger
from pathlib import Path
from urllib.parse import urlparse
logger = getLogger(__name__)

# from dependent packages
import ndradex
import numpy as np


class LAMDA:
    def __init__(self, query, dir='.'):
        if query in ndradex.config['lamda']:
            query = ndradex.config['lamda'][query]

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')

            tables = get_tables(query)
            path = get_data_path(query, dir)

        self._collrates = tables[0]
        self._transitions = tables[1]
        self._levels = tables[2]
        self._data_path = path

        self.desc = self._levels.meta['molecule']

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

    @property
    def n_crit(self):
        """Critical densities in units of cm^-3."""
        # lazy import of astropy-related things
        from astroquery.lamda.utils import ncrit

        if hasattr(self, '_n_crit'):
            return self._n_crit

        tables = (self._collrates, self._transitions, self._levels)

        funcs = []
        for qn_ul in self.qn_ul:
            index_u = self._transitions.loc[qn_ul]['Upper']
            index_l = self._transitions.loc[qn_ul]['Lower']

            @np.vectorize
            def func(temperature):
                return ncrit(tables, index_u, index_l, temperature).value

            funcs.append(func)

        self._n_crit = dict(zip(self.qn_ul, funcs))
        return self._n_crit

    def __enter__(self):
        """Create a temporary LAMDA data inside a context block."""
        # lazy import of astropy-related things
        from astroquery.lamda import write_lamda_datafile

        tables = (self._collrates, self._transitions, self._levels)
        write_lamda_datafile(self._data_path, tables)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Delete a temporary LAMDA data outside a context block."""
        self._data_path.unlink()

    def __str__(self):
        return str(self._data_path)

    def __repr__(self):
        return f'LAMDA({self.desc})'


# utility functions
def get_tables(query):
    """(Down)load LAMDA data as astropy tables.

    This will also add a column of transition quantum
    numbers (i.e., 1-0) to the transition table (QN_ul).

    """
    # lazy import of astropy-related things
    from astropy.table import Column

    collrates, transitions, levels = get_raw_tables(query)
    levels.add_index('Level')

    data = []
    for row in transitions:
        qn_u = ensure_qn(levels.loc[row['Upper']]['J'])
        qn_l = ensure_qn(levels.loc[row['Lower']]['J'])
        data.append(f'{qn_u}-{qn_l}')

    transitions.add_column(Column(data, 'QN_ul'))
    transitions.add_index('QN_ul')
    return collrates, transitions, levels


def get_raw_tables(query):
    """(Down)load LAMDA data as astropy tables."""
    # lazy import of astropy-related things
    from astroquery.lamda import Lamda
    from astroquery.lamda import parse_lamda_datafile

    if query.startswith('http'):
        name = Path(urlparse(query).path).stem
        Lamda.molecule_dict[name] = query
        return Lamda.query(name)

    path = Path(query).expanduser().resolve()

    if path.exists():
        return parse_lamda_datafile(path)

    try:
        return Lamda.query(query)
    except:
        raise ValueError(query)


def get_data_path(query, dir='.'):
    """Get path object for temporary LAMDA data."""
    data = Path(query).stem + '.dat'
    return Path(dir, data).expanduser().resolve()


def ensure_qn(qn):
    """Trim unnecessary characters from QN string."""
    # trim (double)quotation mark
    qn = re.sub(r'\'|"', '', qn)

    # trim space of both ends
    qn = re.sub(r'^\s+|\s+$', '', qn)

    # convert space or underscore to comma
    qn = re.sub(r'\s+|_', ',', qn)

    # trim unnecessary zero of int (e.g., 01 -> 1)
    pat = re.compile(r'^0([0-9])$')
    qn = ','.join(pat.sub(r'\1', _) for _ in qn.split(','))

    # trim unnecessary zero of float (e.g., 3.50 -> 3.5)
    pat = re.compile(r'([0-9]+.[0-9]+)')
    qn = ','.join(pat.sub(r'\1', _) for _ in qn.split(','))

    # add parenthesis if at least one comma exists
    return re.sub(r'(.*,.*)', r'(\1)', qn)


def list_available(path, max_transitions=None):
    """List names of datafiles and transitions in Markdown."""
    # lazy import of astropy-related things
    from astroquery.lamda import Lamda

    def sorter(name):
        name = re.sub(r'[a-z]-(.*)', r'\1', name)
        return ''.join(re.findall(r'[a-z]', name))

    names, descs, trans = [], [], []
    for name in sorted(Lamda.molecule_dict, key=sorter):
        try:
            lamda = LAMDA(name)
        except:
            continue

        names.append(f'`{name}`')
        descs.append(lamda.desc)
        trans.append([f'`{q}`' for q in lamda.qn_ul])

    with open(path, 'w') as f:
        f.write('| Query name | Description | Transitions (QN_ul) |\n')
        f.write('| --- | --- | --- |\n')

        for name, desc, tran in zip(names, descs, trans):
            if max_transitions is None or len(tran) <= max_transitions:
                tran = ', '.join(tran)
            else:
                tran = ', '.join(tran[:max_transitions]) + ', ...'

            f.write(f'| {name} | {desc} | {tran} |\n')
