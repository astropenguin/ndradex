__version__ = '0.1'
__author__  = 'astropenguin'


# load config
def _load_config():
    # standard library
    import os
    from collections import defaultdict
    from logging import getLogger
    from shutil import copy
    from pathlib import Path
    logger = getLogger(__name__)

    # dependent packages
    import toml

    if 'NDRADEX_PATH' in os.environ:
        path = os.environ.get('NDRADEX_PATH')
        user = Path(path).expanduser()
    else:
        user = Path.home() / '.config' / 'ndradex'

    config = 'config.toml'
    data = Path(__path__[0]) / 'data'

    if not user.exists():
        logger.info(f'creating {user}')
        user.mkdir(parents=True)

    if not (user/config).exists():
        logger.info(f'creating {user/config}')
        copy(data/config, user/config)

    with (user/config).open() as f:
        return defaultdict(dict, toml.load(f))

config = _load_config()


# import modules
from .lamda import *
