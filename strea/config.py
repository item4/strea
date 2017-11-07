import copy
import pathlib
import sys

from attrdict import AttrDict

import toml


__all__ = 'error', 'load',

DEFAULT = {
    'DEBUG': False,
    'PREFIX': '',
    'HANDLERS': (),
    'DATABASE_URL': '',
    'DATABASE_ECHO': False,
    'MODELS': (),
}


def error(message: str, *args):
    msg = message.format(*args)
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def load(path: pathlib.Path) -> AttrDict:
    """Load configuration from given path."""

    if not path.exists():
        error('File do not exists.')

    if not path.is_file():
        error('Given path is not file.')

    if not path.match('*.config.toml'):
        error('File suffix must be *.config.toml')

    config = AttrDict(copy.deepcopy(DEFAULT))
    config.update(toml.load(path.open()))

    return config
