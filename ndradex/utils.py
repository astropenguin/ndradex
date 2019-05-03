__all__ = ['bar',
           'runner',
           'random_hex',
           'set_defaults']

# from standard library
import sys
from concurrent import futures
from functools import wraps
from inspect import signature
from logging import getLogger
from multiprocessing import cpu_count
from random import getrandbits
logger = getLogger(__name__)

# from dependent packages
from tqdm import tqdm, tqdm_notebook


# utility classes
class set_defaults:
    def __init__(self, **defaults):
        self.defaults = defaults

    def __call__(self, func):
        sig = signature(func)
        sig_new = self.modify_signature(sig)

        @wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig_new.bind(*args, **kwargs)
            bound.apply_defaults()
            return func(*bound.args, **bound.kwargs)

        return wrapper

    def modify_signature(self, sig):
        params = []

        for param in sig.parameters.values():
            if param.kind == param.VAR_POSITIONAL:
                params.append(param.replace())
                continue

            if param.kind == param.VAR_POSITIONAL:
                params.append(param.replace())
                continue

            if not param.name in self.defaults:
                params.append(param.replace())
                continue

            default = self.defaults[param.name]
            params.append(param.replace(default=default))

        return sig.replace(parameters=params)


# utility functions
def bar(*args, **kwargs):
    """Wrapper of tqdm for in both GUI and CUI."""
    if 'ipykernel' in sys.modules:
        return tqdm_notebook(*args, **kwargs)
    else:
        return tqdm(*args, **kwargs)


def random_hex(length=8):
    """Random hexadecimal string of given length."""
    return f'{getrandbits(length*4):x}'


def runner(n_proc=None):
    """Multiprocessing task runnner."""
    if n_proc is None:
        n_proc = cpu_count() - 1

    return futures.ProcessPoolExecutor(n_proc)
