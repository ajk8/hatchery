import subprocess
import sys
import shlex
import logbook

logger = logbook.Logger(__name__)


def call(*args):
    """ Call an arbitary command and return the exit value

    >>> call('hatchery')
    0
    >>> call('hatchery', 'notreal')
    2
    """
    logger.info('executing `{}`'.format(' '.join(args)))
    retval = subprocess.call(args)
    if retval:
        logger.error('`{}` returned error code {}'.format(' '.join(args), retval))
    return retval


def call_str(cmd_str):
    """ Call an arbitrary command with a string instead of *args

    >>> call_str('hatchery notreal')
    2
    """
    cmd_args = shlex.split(cmd_str)
    return call(*cmd_args)


def setup(*args):
    """ Call a setup.py command or list of commands

    >>> setup('--name')
    0
    >>> setup('notreal')
    1
    """
    cmd_args = [sys.executable, 'setup.py'] + [x for x in args]
    return call(*cmd_args)
