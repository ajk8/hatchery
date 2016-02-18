import os
import shutil
import dirsync
import logbook
import funcy
from contextlib import contextmanager

WORKDIR = '.hatchery.work'
WORKDIR_EXCLUDES = [
    r'^\{}'.format(WORKDIR),
    r'^\.cache',
    r'^\.coverage',
    r'^.*\.egg-info',
    r'^.*__pycache__',
    r'^.*\.pyc'
]


@contextmanager
def as_cwd():
    """ Use WORKDIR as a temporary working directory """
    owd = os.getcwd()
    os.chdir(WORKDIR)
    yield
    os.chdir(owd)


@funcy.memoize
def sync(_sourcedir_for_testing=None):
    """ Create and populate WORKDIR, memoized so that it only runs once """
    sourcedir = _sourcedir_for_testing if _sourcedir_for_testing else '.'
    dirsync.sync(
        sourcedir=sourcedir,
        targetdir=WORKDIR,
        action='sync',
        create=True,
        exclude=WORKDIR_EXCLUDES,
        logger=logbook.Logger('dirsync', level=logbook.lookup_level('CRITICAL'))
    )


def remove():
    """ Remove WORKDIR """
    if os.path.isdir(WORKDIR):
        shutil.rmtree(WORKDIR)
