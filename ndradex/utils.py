__all__ = ['ensure_values',
           'set_defaults']

# from standard library
import re
from functools import wraps
from inspect import signature
from logging import getLogger
from pathlib import Path
logger = getLogger(__name__)

# from dependent packages
import numpy as np
from astropy import units as u


def ensure_values(values, unit=None):
    if isinstance(values, u.Quantity):
        unit = u.Unit(unit)
        values = values.to(unit)

    values = np.asarray(values)

    if values.size==1 and not values.shape:
        return values[np.newaxis]
    else:
        return values


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
