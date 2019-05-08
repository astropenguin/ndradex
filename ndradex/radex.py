__all__ = []

# from standard library
from logging import getLogger
from pathlib import Path
from subprocess import PIPE
from subprocess import run as sprun
from subprocess import CalledProcessError, TimeoutExpired
logger = getLogger(__name__)

# from dependent packages
import ndradex

# module constants
N_VARS = 10
ERROR_OUTPUT = ('NaN',) * N_VARS


# main function
def run(input, radex=None, timeout=None, cleanup=True,
        logfile='radex.log', encoding='utf-8'):
    """Run RADEX and get result as tuple of string.

    Note that this function only reads the last line of RADEX outfile.
    This means that only the values of the transition at the highest
    frequency spacified in the RADEX input will be returned.

    Args:
        input (str or sequence): RADEX input. See examples below.
        radex (str or path, optional): RADEX path. If not spacified,
            then the builtin RADEX with uniform geometry will be used.
        timeout (int, optional): Timeout of a RADEX run in units of second.
            Default is None (unlimited run time is permitted).
        cleanup (bool, optional): If True (default), then the RADEX outfile
            (e.g. radex.out) and logfile (e.g., radex.log) will be deleted.
        logfile (str or path, optional): Path of logfile. This is only used
            for identifying the path of logfile in the cleanup method.
        encoding (str, optional): File encofing. Default is utf-8.

    Returns:
        output (tuple of str): RADEX output values.

    Examples:
        To get the values of CO(1-0) @ T_kin = 100 K, n_H2 = 1e3 cm^-3,
        N_CO = 1e15 cm^-2, T_bg = 2.73 K, and dv = 1.0 km s^-1:

            >>> input = ['co.dat', 'radex.out', '110 120', '100',
                        '1', 'H2', '1e3', '2.73', '1e15', '1.0', 0]
            >>> output = run(input)

    """
    if radex is None:
        radex = ndradex.RADEX_BINPATH / 'radex-uni'

    try:
        input, outfile = ensure_input(input, encoding)
    except (AttributeError, IndexError, TypeError):
        logger.warning('RADEX did not run due to invalid input')
        return ERROR_OUTPUT

    try:
        cp = sprun([radex], input=input, timeout=timeout,
                   stdout=PIPE, stderr=PIPE, check=True)
        return ensure_output(cp, outfile, encoding)
    except FileNotFoundError:
        logger.warning('RADEX path or moldata does not exist')
        return ERROR_OUTPUT
    except CalledProcessError:
        logger.warning('RADEX failed due to invalid input')
        return ERROR_OUTPUT
    except TimeoutExpired:
        logger.warning('RADEX interrupted due to timeout')
        return ERROR_OUTPUT
    except RuntimeError:
        logger.warning('RADEX version is not valid')
        return ERROR_OUTPUT
    finally:
        if cleanup:
            remove_file(logfile)
            remove_file(outfile)


# utility functions
def ensure_input(input, encoding='utf-8'):
    """Ensure the type of input and the path of outfile."""
    if isinstance(input, (list, tuple)):
        outfile = input[1]
        input = '\n'.join(input).encode(encoding)
    else:
        outfile = input.split('\n')[1]
        input = input.encode(encoding)

    return input, outfile


def ensure_output(cp, outfile, encoding='utf-8'):
    """Ensure that the RADEX output is valid."""
    if ndradex.RADEX_VERSION not in cp.stdout.decode(encoding):
        raise RuntimeError('RADEX version is not valid')

    with open(outfile, encoding=encoding) as f:
        return f.readlines()[-1].split()[-N_VARS:]


def remove_file(path):
    """Remove file forcibly (i.e., rm -f <path>)."""
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass
