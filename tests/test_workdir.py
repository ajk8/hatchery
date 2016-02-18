import os
from hatchery import workdir


def test_as_cwd(tmpdir):
    with tmpdir.as_cwd():
        os.mkdir(workdir.WORKDIR)
        with workdir.as_cwd():
            assert os.getcwd() == os.path.join(str(tmpdir), workdir.WORKDIR)
        assert os.getcwd() == str(tmpdir)


def test_sync(tmpdir):
    with tmpdir.as_cwd():
        assert not os.path.exists(workdir.WORKDIR)
        workdir.sync(_sourcedir_for_testing=os.path.dirname(__file__))
        assert os.path.isfile(os.path.join(workdir.WORKDIR, 'test_workdir.py'))
        assert not os.path.exists(os.path.join(workdir.WORKDIR, '__pycache__'))


def test_remove(tmpdir):
    with tmpdir.as_cwd():
        if not os.path.isdir(workdir.WORKDIR):
            os.mkdir(workdir.WORKDIR)
        workdir.remove()
        assert not os.path.exists(workdir.WORKDIR)
