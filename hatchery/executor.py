import subprocess
import sys
import shlex
import logging
import funcy
import os

logger = logging.getLogger(__name__)


class CallResult(object):
    def __init__(self, exitval, stdout, stderr):
        self.exitval = exitval
        self.stdout = stdout
        self.stderr = stderr

    def format_error_msg(self):
        ret_lines = ['### exitval: {} ###'.format(self.exitval)]
        if self.stdout:
            ret_lines += ['### stdout ###', self.stdout, '### /stdout ###']
        if self.stderr:
            ret_lines += ['### stderr ###', self.stderr, '### /stderr ###']
        return os.linesep.join(ret_lines)


def call(cmd_args, suppress_output=False):
    """ Call an arbitary command and return the exit value, stdout, and stderr as a tuple

    Command can be passed in as either a string or iterable

    >>> result = call('hatchery', suppress_output=True)
    >>> result.exitval
    0
    >>> result = call(['hatchery', 'notreal'])
    >>> result.exitval
    1
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

    >>> result = setup('--name', suppress_output=True)
    >>> result.exitval
    0
    >>> result = setup('notreal')
    >>> result.exitval
    1
    """
    if not funcy.is_list(cmd_args) and not funcy.is_tuple(cmd_args):
        cmd_args = shlex.split(cmd_args)
    cmd_args = [sys.executable, 'setup.py'] + [x for x in cmd_args]
    return call(cmd_args, suppress_output=suppress_output)
