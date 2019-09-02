__version__ = '0.2.0'
__author__  = 'astropenguin'


# ignore FutureWarning
import warnings
warnings.simplefilter('ignore', FutureWarning)


# load user config
def _load_config():
    # from standard library
    import os
    from collections import defaultdict
    from pathlib import Path

    # from dependent packages
    import toml

    # name of config
    config = 'config.toml'

    if 'NDRADEX_PATH' in os.environ:
        path = os.environ.get('NDRADEX_PATH')
        user = Path(path).expanduser().resolve()
    else:
        user = Path.home() / '.config' / 'ndradex'

    if not user.exists():
        user.mkdir(parents=True)

    (user/config).touch()

    with (user/config).open() as f:
        return defaultdict(dict, toml.load(f))

config = _load_config()


# package constants
def _get_constants():
    # from standard library
    import os
    from pathlib import Path

    if 'NDRADEX_BINPATH' in os.environ:
        path = os.environ.get('NDRADEX_BINPATH')
        radex_binpath = Path(path).expanduser().resolve()
    else:
        radex_binpath = Path(__path__[0], 'bin')

    radex_version = '30nov2011'
    return radex_binpath, radex_version

RADEX_BINPATH, RADEX_VERSION = _get_constants()


# import modules
from .utils import *
from .radex import *
from .db import *
from .grid import *
