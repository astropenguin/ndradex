__all__ = ['run_radex']

# from standard library
from logging import getLogger
from pathlib import Path
from subprocess import run, PIPE
from subprocess import CalledProcessError
logger = getLogger(__name__)

# module constants
RADEX_VERSION = '30nov2011'
ERROR_OUTPUT = ['NaN'] * 10


# main function
def run_radex(input, radex='radex-uni', sep=', ',
              log='radex.log', encoding='utf-8'):
    """Run RADEX and get numerical output as string.

    Args:
        input (str or sequence)
        radex (str or path, optional)
        sep (str, optional)
        log (str or path, optional)
        encoding (str, optional)

    Returns:
        output (str)

    """
    log = Path(log)
    radex = Path(radex)

    if isinstance(input, (list, tuple)):
        output = Path(input[1])
        input = '\n'.join(input).encode(encoding)
    else:
        output = Path(input.split('\n')[1])
        input = input.encode(encoding)

    try:
        cp = run([radex], input=input, stdout=PIPE, check=True)
        return sep.join(ensure_output(cp, output, encoding))
    except FileExistsError:
        logger.warning('RADEX path does not exist')
        return sep.join(ERROR_OUTPUT)
    except CalledProcessError:
        logger.warning('RADEX failed due to invalid input')
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
def ensure_output(cp, output, encoding='utf-8'):
    if RADEX_VERSION not in cp.stdout.decode('utf-8'):
        raise RuntimeError('Not a valid RADEX version')

    return lastline(output, encoding).split()[3:]


def lastline(file, encoding='utf-8'):
    """Get the last line of a file."""
    with open(file, encoding=encoding) as f:
        return f.readlines()[-1]
