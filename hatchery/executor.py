import subprocess
import sys
import shlex
import logging
import collections
import funcy

logger = logging.getLogger(__name__)


CallResult = collections.namedtuple('CallResult', ('exitval', 'stdout', 'stderr'))


def call(cmd_args, suppress_output=False):
    """ Call an arbitary command and return the exit value, stdout, and stderr as a tuple

    Command can be passed in as either a string or iterable

    >>> call('hatchery', suppress_output=True)  # doctest: +ELLIPSIS
    CallResult(exitval=0, ...)
    >>> call(['hatchery', 'notreal'])  # doctest: +ELLIPSIS
    CallResult(exitval=1, ...)
    """
    if not funcy.is_list(cmd_args) and not funcy.is_tuple(cmd_args):
        cmd_args = shlex.split(cmd_args)
    logger.info('executing `{}`'.format(' '.join(cmd_args)))
    out = err = ''
    p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while p.returncode is None:
        _out, _err = p.communicate()
        _out, _err = _out.decode(), _err.decode()
        if not suppress_output:
            sys.stdout.write(_out)
            sys.stderr.write(_err)
        out += _out
        err += _err
    if p.returncode:
        logger.error('`{}` returned error code {}'.format(' '.join(cmd_args), p.returncode))
    return CallResult(p.returncode, out, err)


def setup(cmd_args, suppress_output=False):
    """ Call a setup.py command or list of commands

    >>> setup('--name', suppress_output=True)  # doctest: +ELLIPSIS
    CallResult(exitval=0, ...)
    >>> setup('notreal')  # doctest: +ELLIPSIS
    CallResult(exitval=1, ...)
    """
    if not funcy.is_list(cmd_args) and not funcy.is_tuple(cmd_args):
        cmd_args = shlex.split(cmd_args)
    cmd_args = [sys.executable, 'setup.py'] + [x for x in cmd_args]
    return call(cmd_args, suppress_output=suppress_output)
