__all__ = [
    "save_dataset",
    "load_dataset",
]


# standard library
from concurrent.futures import ProcessPoolExecutor
from functools import wraps
from inspect import signature, Signature
from logging import getLogger, Logger
from multiprocessing import cpu_count
from pathlib import Path
from random import getrandbits
from typing import Callable, Optional, Union


# dependencies
import xarray as xr


# type aliases
PathLike = Union[Path, str]


# logger
logger: Logger = getLogger(__name__)


# main features
class set_defaults:
    def __init__(self, **defaults) -> None:
        self.defaults = defaults

    def __call__(self, func: Callable) -> Callable:
        sig = signature(func)
        sig_new = self.modify_signature(sig)

        @wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig_new.bind(*args, **kwargs)
            bound.apply_defaults()
            return func(*bound.args, **bound.kwargs)

        return wrapper

    def modify_signature(self, sig: Signature) -> Signature:
        params = []

        for param in sig.parameters.values():
            if param.kind == param.VAR_POSITIONAL:
                params.append(param.replace())
                continue

            if param.kind == param.VAR_POSITIONAL:
                params.append(param.replace())
                continue

            if param.name not in self.defaults:
                params.append(param.replace())
                continue

            default = self.defaults[param.name]
            params.append(param.replace(default=default))

        return sig.replace(parameters=params)


def save_dataset(dataset: xr.Dataset, path: PathLike) -> None:
    """Save dataset to a netCDF."""
    dataset.to_netcdf(path)


def load_dataset(path: PathLike) -> xr.Dataset:
    """Load a netCDF to a dataset."""
    return xr.open_dataset(path)


def random_hex(length: int = 8) -> str:
    """Random hexadecimal string of given length."""
    return f"{getrandbits(length*4):x}"


def runner(n_procs: Optional[int] = None) -> ProcessPoolExecutor:
    """Multiprocessing task runnner."""
    if n_procs is None:
        n_procs = cpu_count() - 1

    return ProcessPoolExecutor(n_procs)
