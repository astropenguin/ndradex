# from standard library

# from dependent packages
import ndradex as nd
from astroquery.lamda import Lamda


class LAMDA:
    def __init__(self, query):
        if query in nd.config['alias']:
            query = nd.config['alias'][query]

        collrates, transitions, levels = Lamda.query(query)

        self._collrates = collrates
        self._transitions = transitions
        self._levels = levels

        for table in self._collrates.values():
            table.add_index('Transition')

        self._transitions.add_index('Transition')
        self._levels.add_index('Level')

    def get_frequency(self, transition):
        pass

    def get_n_crit(transition, temperature, **kwargs):
        pass

    def list_transitions(self):
        transitions = []

        for row in self._transitions:
            index_u = row['Upper']
            index_l = row['Lower']
            J_u = self._levels.loc[index_u]['J']
            J_l = self._levels.loc[index_l]['J']
            transitions.append(f'{J_u}-{J_l}')

        return transitions


def list_moldata():
    names = list(Lamda.molecule_dict)

    for alias, name in nd.config['alias'].items():
        if name not in names:
            continue

        names.append(alias)

    return names
