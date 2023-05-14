__all__ = ["save_dataset", "load_dataset"]


# standard library
from pathlib import Path
from typing import Union


# dependencies
import xarray as xr


# type hints
PathLike = Union[Path, str]


def save_dataset(dataset: xr.Dataset, path: PathLike) -> None:
    """Save an xarray Dataset to a netCDF."""
    dataset.to_netcdf(path)


def load_dataset(path: PathLike) -> xr.Dataset:
    """Load a netCDF to an xarray Dataset."""
    return xr.open_dataset(path)
