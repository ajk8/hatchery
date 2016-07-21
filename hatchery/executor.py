import subprocess
import sys
import shlex
import logging
import funcy
import os
import six

logger = logging.getLogger(__name__)


class CallResult(object):
    """ Basic representation of a command execution result """

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


class CallRequest(object):
    """ Class to wrap up command execution and non-blocking output capture """

    def __init__(self, cmd_args, suppress_output=False):
        self.cmd_args = cmd_args
        self.suppress_output = suppress_output
        self.stdout_str = ''
        self.stderr_str = ''
        self.process = None

    def _set_stream_process(self, stream_name):
        # this is magic...the behavior suggests that the code inside this with block
        # is assigned to events on self.process.stdout like a lambda function
        with getattr(self.process, stream_name):
            for line in iter(getattr(self.process, stream_name).readline, b''):
                if six.PY3:
                    line = line.decode()
                if not self.suppress_output:
                    getattr(sys, stream_name).write(line)
                    getattr(sys, stream_name).flush()
                setattr(self, stream_name + '_str', getattr(self, stream_name + '_str') + line)

    def run(self):
        self.process = subprocess.Popen(
            self.cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds='posix' in sys.builtin_module_names,
            bufsize=1
        )
        self._set_stream_process('stdout')
        self._set_stream_process('stderr')
        self.process.wait()

        return CallResult(self.process.returncode, self.stdout_str, self.stderr_str)


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
    call_request = CallRequest(cmd_args, suppress_output=suppress_output)
    call_result = call_request.run()
    if call_result.exitval:
        logger.error('`{}` returned error code {}'.format(' '.join(cmd_args), call_result.exitval))
    return call_result


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
