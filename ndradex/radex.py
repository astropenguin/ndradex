__all__ = ['run']

# from standard library
from logging import getLogger
from pathlib import Path
from subprocess import PIPE
from subprocess import run as sprun
from subprocess import CalledProcessError, TimeoutExpired
logger = getLogger(__name__)

# module constants
N_VARS = 10
RADEX_VERSION = '30nov2011'
ERROR_OUTPUT = ('NaN',) * N_VARS


# main function
def run(input, radex='radex-uni', dir='.', timeout=5,
        logfile='radex.log', encoding='utf-8'):
    """Run RADEX and get result as tuple of string.

    Args:
        input (str or sequence)
        radex (str or path, optional)
        dir (str or path, optional)
        timeout (int, optional)
        logfile (str or path, optional)
        encoding (str, optional)

    Returns:
        output (tuple of str)

    """
    try:
        input, outfile = ensure_input(input, encoding)
    except (AttributeError, IndexError, TypeError):
        logger.warning('RADEX did not run due to invalid input')
        return ERROR_OUTPUT

    try:
        cp = sprun([radex], input=input, cwd=dir, stdout=PIPE,
                   stderr=PIPE, timeout=timeout, check=True)
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
        remove_file(logfile)
        remove_file(outfile)


# utility functions
def ensure_input(input, encoding='utf-8'):
    if isinstance(input, (list, tuple)):
        outfile = input[1]
        input = '\n'.join(input).encode(encoding)
    else:
        outfile = input.split('\n')[1]
        input = input.encode(encoding)

    return input, outfile


def ensure_output(cp, outfile, encoding='utf-8'):
    if RADEX_VERSION not in cp.stdout.decode(encoding):
        raise RuntimeError('RADEX version is not valid')

    with open(outfile, encoding=encoding) as f:
        return f.readlines()[-1].split()[-N_VARS:]


def remove_file(path):
    """Remove file forcibly (i.e., rm -f <path>)."""
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass
