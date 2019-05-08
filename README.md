# ndRADEX

[![](https://img.shields.io/pypi/v/ndradex.svg?label=PyPI)](https://pypi.org/pypi/ndradex/)
[![](https://img.shields.io/pypi/pyversions/ndradex.svg?label=Python)](https://pypi.org/pypi/ndradex/)
[![Travis](https://img.shields.io/travis/astropenguin/ndradex/master.svg?label=Travis%20CI)](https://travis-ci.org/astropenguin/ndradex)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?label=License)](LICENSE)

:zap: Python package for RADEX grid calculation

## TL;DR

ndRADEX is a Python package which can run [RADEX], non-LTE molecular radiative transfer code, with parameters of multiple values (i.e., RADEX with grid parameters).
The output will be multi-dimensional arrays, which may be useful for parameter search of physical conditions in comparison with observed values.

## Features

- **Grid calculation:** ndRADEX has a simple `run()` function, where all parameters of RADEX can be griddable (i.e., they can be list-like with length of more than one).
- **Builtin RADEX:** ndRADEX provides builtin RADEX binaries in the package, which are automatically built during the package installation. You don't need any additional setups.
- **Multiprocessing:** ndRADEX supports multiprocessing RADEX run by default. At least twice speedup is expected compared to single processing.
- **Handy I/O:** The output of ndRADEX is a [xarray]'s Dataset, a standard multi-dimensional data structure as well as [pandas]. You can handle it in the same manner as NumPy and pandas (i.e., element-wise operation, save/load data, plotting, etc).

## Requirements

- Python 3.6 or 3.7
- gfortran (necessary to build RADEX)

## Installation

You can install ndRADEX with pip:

```shell
$ pip install ndradex
```

Please make sure that all requirements are met before the installation.

## Usages

Within Python, import the package like:

```python
>>> import ndradex
```

### Single RADEX run

The main funtion of ndRADEX is `ndradex.run()`.
For example, to get RADEX results of CO(1-0) with kinetic temperature of 100 K, CO column density of 1e15 cm^-2, and H2 density of 1e3 cm^-3:

```python
>>> ds = ndradex.run('co', '1-0', 100, 1e15, 1e3)
```

where `'co'` is a name of [LAMDA] datafile without extension (.dat), and `'1-0'` is a name of transition.
All available values are listed in [List of available LAMDA datafiles and transitions](https://github.com/astropenguin/ndradex/wiki/List-of-available-LAMDA-datafiles-and-transitions).
Note that you don't need to any download datafiles:
ndRADEX automatically does this.

In this case, other parameters like line width, background temperature are default values defined in the function.
The geometry of escape probability is uniform (`'uni'`) by default.
You can change these values with custom config (see customizations below).

The output is a [xarray]'s Dataset with no dimension:

```python
>>> print(ds)
<xarray.Dataset>
Dimensions:      ()
Coordinates:
    QN_ul        <U3 '1-0'
    T_kin        int64 100
    N_mol        float64 1e+15
    n_H2         float64 1e+03
    T_bg         float64 2.73
    dv           float64 1.0
    geom         <U3 'uni'
    description  <U9 'LAMDA(CO)'
Data variables:
    E_u          float64 5.5
    freq         float64 115.3
    wavel        float64 2.601e+03
    T_ex         float64 132.5
    tau          float64 0.009966
    T_r          float64 1.278
    pop_u        float64 0.4934
    pop_l        float64 0.1715
    I            float64 1.36
    F            float64 2.684e-08
```

You can access each result value like:

```python
>>> flux = ds['F'].values
```

### Grid RADEX run

As a natural extension, you can run grid RADEX calculation like:

```python
>>> ds = ndradex.run('co', ['1-0', '2-1'], T_kin=[100, 200, 300],
                     N_mol=1e15, n_H2=[1e3, 1e4, 1e5, 1e6, 1e7])
```

There are 13 parameters which can be griddable:
`QN_ul` (transition name), `T_kin` (kinetic temeperature), `N_mol` (column density), `n_H2` (H2 density), `n_pH2` (para-H2 density), `n_oH2` (ortho-H2 density), `n_e` (electron density), `n_H` (atomic hydrogen density), `n_He` (Helium density), `n_Hp` (ionized hydrogen density), `T_bg` (background temperature), `dv` (line width), and `geom` (photon escape geometry).

The output is a [xarray]'s Dataset with three dimensions of (`QN_ul`, `T_kin`, `n_H2`):

```python
>>> print(ds)
<xarray.Dataset>
Dimensions:      (QN_ul: 2, T_kin: 3, n_H2: 5)
Coordinates:
  * QN_ul        (QN_ul) <U3 '1-0' '2-1'
  * T_kin        (T_kin) int64 100 200 300
    N_mol        float64 1e+15
  * n_H2         (n_H2) float64 1e+03 1e+04 1e+05 1e+06 1e+07
    T_bg         float64 2.73
    dv           float64 1.0
    geom         <U3 'uni'
    description  <U9 'LAMDA(CO)'
Data variables:
    E_u          (QN_ul, T_kin, n_H2) float64 5.5 5.5 5.5 5.5 ... 16.6 16.6 16.6
    freq         (QN_ul, T_kin, n_H2) float64 115.3 115.3 115.3 ... 230.5 230.5
    wavel        (QN_ul, T_kin, n_H2) float64 2.601e+03 2.601e+03 ... 1.3e+03
    T_ex         (QN_ul, T_kin, n_H2) float64 132.5 -86.52 127.6 ... 316.6 301.6
    tau          (QN_ul, T_kin, n_H2) float64 0.009966 -0.005898 ... 0.0009394
    T_r          (QN_ul, T_kin, n_H2) float64 1.278 0.5333 ... 0.3121 0.2778
    pop_u        (QN_ul, T_kin, n_H2) float64 0.4934 0.201 ... 0.04972 0.04426
    pop_l        (QN_ul, T_kin, n_H2) float64 0.1715 0.06286 ... 0.03089 0.02755
    I            (QN_ul, T_kin, n_H2) float64 1.36 0.5677 ... 0.3322 0.2957
    F            (QN_ul, T_kin, n_H2) float64 2.684e-08 1.12e-08 ... 4.666e-08
```

For more information, run `help(rdradex.run)` to see the docstrings.

### Save/load results

You can save and load the dataset like:

```python
# save results to a netCDF file
>>> ndradex.save_dataset(ds, 'results.nc')

# load results from a netCDF file
>>> ds = ndradex.load_dataset('results.nc')
```

## Customizations

For the first time you import ndRADEX, the custom configuration file is created as `~/.config/ndradex/config.toml`.
By editing this, you can customize the following two settings of ndRADEX.
Note that you can change the path of configuration file by setting an environment variable, `NDRADEX_PATH`.

### Changing default values

As mentioned above, you can change the default values of the `run()` function like:

```toml
# config.toml

[grid]
T_bg = 10 # change default background temp to 10 K
geom = "lvg" # change default geometry to LVG
timeout = 30
n_procs = 2
```

You can also change the number of multiprocesses (`n_procs`) and timeout (`timeout`) here.
By default, only two processes are allocated.
It may be better to set a larger value if you want to accelerate the calculation.

### Setting datafile aliases

Sometimes datafile names are not intuitive (for example, name of CS datafile is `cs@lique`).
For convenience, you can define aliases of datafile names like:

```toml
# config.toml

[lamda]
CO = "co"
CS = "cs@lique"
H13CN = "https://home.strw.leidenuniv.nl/~moldata/datafiles/h13cn@xpol.dat"
```

As shown in the third example, you can also specify URL or local file path on the right hand.
After the customization, you can use these aliases in the `run()` function:

```python
>>> ds = ndradex.run('CS', '1-0', ...) # equiv to cs@lique
```

## References

- [RADEX]
- [LAMDA]
- [xarray]
- [pandas]

[xarray]: http://xarray.pydata.org/en/stable/
[RADEX]: https://home.strw.leidenuniv.nl/~moldata/radex.html
[LAMDA]: https://home.strw.leidenuniv.nl/~moldata/
[pandas]: https://pandas.pydata.org/
