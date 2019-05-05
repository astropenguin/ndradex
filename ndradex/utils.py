__all__ = ['save_dataset',
           'load_dataset']

# from standard library
from concurrent import futures
from functools import wraps
from inspect import signature
from logging import getLogger
from multiprocessing import cpu_count
from random import getrandbits
logger = getLogger(__name__)

# from dependent packages
import xarray as xr


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
def save_dataset(dataset, path):
    """Save dataset to a netCDF."""
    dataset.to_netcdf(path)


def load_dataset(path):
    """Load a netCDF to a dataset."""
    return xr.open_dataset(path)


def random_hex(length=8):
    """Random hexadecimal string of given length."""
    return f'{getrandbits(length*4):x}'


def runner(n_procs=None):
    """Multiprocessing task runnner."""
    if n_procs is None:
        n_procs = cpu_count() - 1

    return futures.ProcessPoolExecutor(n_procs)
