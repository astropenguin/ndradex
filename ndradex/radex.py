__all__ = ['run_radex']

# from standard library
from logging import getLogger
from pathlib import Path
from subprocess import run, PIPE
from subprocess import CalledProcessError, TimeoutExpired
logger = getLogger(__name__)

# module constants
N_VARS = 10
RADEX_VERSION = '30nov2011'
ERROR_OUTPUT = ['NaN'] * N_VARS


# main function
def run_radex(input, radex='radex-uni', log='radex.log',
              sep=', ', timeout=10, encoding='utf-8'):
    """Run RADEX and get numerical result as string.

    Args:
        input (str or sequence)
        radex (str or path, optional)
        log (str or path, optional)
        sep (str, optional)
        timeout (int, optional)
        encoding (str, optional)

    Returns:
        output (str)

    """
    radex, log = Path(radex), Path(log)
    input, output = ensure_input(input, encoding)

    try:
        cp = run([radex], input=input, timeout=timeout,
                 stdout=PIPE, stderr=PIPE, check=True)
        return sep.join(ensure_output(cp, output, encoding))
    except FileExistsError:
        logger.warning('RADEX path does not exist')
        return sep.join(ERROR_OUTPUT)
    except CalledProcessError:
        logger.warning('RADEX failed due to invalid input')
        return sep.join(ERROR_OUTPUT)
    except TimeoutExpired:
        logger.warning('RADEX interrupted due to timeout')
        return sep.join(ERROR_OUTPUT)
    except RuntimeError:
        logger.warning('RADEX version is not valid')
        return sep.join(ERROR_OUTPUT)
    finally:
        if log.exists():
            log.unlink()

        if output.exists():
            output.unlink()


# utility functions
def ensure_input(input, encoding='utf-8'):
    if isinstance(input, (list, tuple)):
        output = Path(input[1])
        input = '\n'.join(input).encode(encoding)
    else:
        output = Path(input.split('\n')[1])
        input = input.encode(encoding)

    return input, output


def ensure_output(cp, output, encoding='utf-8'):
    if RADEX_VERSION not in cp.stdout.decode(encoding):
        raise RuntimeError('Not a valid RADEX version')

    with open(output, encoding=encoding) as f:
        return f.readlines()[-1].split()[-N_VARS:]
