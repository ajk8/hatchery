import pytest
import os
import funcy
import pip
from hatchery import project
from hatchery import snippets
from hatchery import helpers

try:
    from unittest import mock
except ImportError:
    import mock

PACKAGE_NAME = 'mypackage'


def _make_package(package_name, empty_module_files=[]):
    os.mkdir(package_name)
    open(os.path.join(package_name, '__init__.py'), 'w').close()
    for module_file in empty_module_files:
        open(os.path.join(package_name, module_file), 'w').close()


def test_get_package_name(tmpdir):
    with tmpdir.as_cwd():
        with pytest.raises(project.ProjectError):
            project.get_package_name()
        _make_package('package_name')
        assert project.get_package_name() == 'package_name'
        _make_package('tests')
        assert project.get_package_name() == 'package_name'
        _make_package('not_tests')
        with pytest.raises(project.ProjectError):
            project.get_package_name()


def test_project_has_setup_py(tmpdir):
    with tmpdir.as_cwd():
        assert not project.project_has_setup_py()
        open('setup.py', 'w').close()
        assert project.project_has_setup_py()


def test_setup_py_has_exec_block(tmpdir):
    with tmpdir.as_cwd():
        open('setup.py', 'w').close()
        assert not project.setup_py_has_exec_block(PACKAGE_NAME)
        snippet_content = snippets.get_snippet_content(
            snippet_name='setup.py',
            package_name=PACKAGE_NAME,
            version_file=project.VERSION_FILE_NAME
        )
        with open('setup.py', 'a') as setup_py:
            setup_py.write(snippet_content)
        assert project.setup_py_has_exec_block(PACKAGE_NAME)


def test_setup_py_uses___version__(tmpdir):
    with tmpdir.as_cwd():
        open('setup.py', 'w').close()
        assert not project.setup_py_uses___version__()
        with open('setup.py', 'a') as setup_py:
            setup_py.write('setup(version=__version__)')
        assert project.setup_py_uses___version__()


def test_package_has_version_file(tmpdir):
    with tmpdir.as_cwd():
        assert not project.package_has_version_file(PACKAGE_NAME)
        version_file = helpers.package_file_path(project.VERSION_FILE_NAME, PACKAGE_NAME)
        _make_package(PACKAGE_NAME, empty_module_files=[os.path.basename(version_file)])
        assert project.package_has_version_file(PACKAGE_NAME)


def test_version_file_has___version__(tmpdir):
    with tmpdir.as_cwd():
        version_file = helpers.package_file_path(project.VERSION_FILE_NAME, PACKAGE_NAME)
        _make_package(PACKAGE_NAME, empty_module_files=[os.path.basename(version_file)])
        assert not project.version_file_has___version__(PACKAGE_NAME)
        snippet_content = snippets.get_snippet_content(project.VERSION_FILE_NAME)
        with open(version_file, 'a') as _version_py:
            _version_py.write(snippet_content)
        assert project.version_file_has___version__(PACKAGE_NAME)


def test_version_file_has___version_info__(tmpdir):
    with tmpdir.as_cwd():
        version_file = helpers.package_file_path(project.VERSION_FILE_NAME, PACKAGE_NAME)
        _make_package(PACKAGE_NAME, empty_module_files=[os.path.basename(version_file)])
        assert not project.version_file_has___version_info__(PACKAGE_NAME)
        snippet_content = snippets.get_snippet_content(project.VERSION_FILE_NAME)
        with open(version_file, 'a') as _version_py:
            _version_py.write(snippet_content)
        assert project.version_file_has___version_info__(PACKAGE_NAME)


def test_package_uses___version__(tmpdir):
    with tmpdir.as_cwd():
        init_file = helpers.package_file_path('__init__.py', PACKAGE_NAME)
        _make_package(PACKAGE_NAME, empty_module_files=[os.path.basename(init_file)])
        assert not project.package_uses___version__(PACKAGE_NAME)
        with open(init_file, 'w') as init_py:
            init_py.write('from _version import __version__')
        assert project.package_uses___version__(PACKAGE_NAME)
        snippet_content = snippets.get_snippet_content('__init__.py')
        with open(init_file, 'w') as init_py:
            init_py.write(snippet_content)
        assert project.package_uses___version__(PACKAGE_NAME)


def test_get_project_name(tmpdir):
    with tmpdir.as_cwd():
        with pytest.raises(IOError):
            project.get_project_name()
        with open('setup.py', 'w') as setup_py:
            setup_py.write('setup(name="someproject")')
        assert project.get_project_name() == 'someproject'


def test_get_version(tmpdir):
    with tmpdir.as_cwd():
        with pytest.raises(IOError):
            project.get_version(PACKAGE_NAME)
        version_file = helpers.package_file_path(project.VERSION_FILE_NAME, PACKAGE_NAME)
        _make_package(PACKAGE_NAME, empty_module_files=[os.path.basename(version_file)])
        with pytest.raises(project.ProjectError):
            project.get_version(PACKAGE_NAME)
        snippet_content = snippets.get_snippet_content(project.VERSION_FILE_NAME)
        with open(version_file, 'w') as _version_py:
            _version_py.write(snippet_content)
        assert project.get_version(PACKAGE_NAME) == 'managed by hatchery'


def test_set_version(tmpdir):
    with tmpdir.as_cwd():
        version_file = helpers.package_file_path(project.VERSION_FILE_NAME, PACKAGE_NAME)
        _make_package(PACKAGE_NAME, empty_module_files=[os.path.basename(version_file)])
        snippet_content = snippets.get_snippet_content(project.VERSION_FILE_NAME)
        with open(version_file, 'w') as _version_py:
            _version_py.write(snippet_content)
        project.set_version(PACKAGE_NAME, '1.2.3')
        version_file_content = helpers.get_file_content(version_file)
        found = funcy.re_find(project.VERSION_SET_REGEX, version_file_content)
        assert found['version'] == '1.2.3'


def test_version_already_uploaded_true():

    def _mock_findreq_found(self, req, upgrade):
        return True

    def _mock_findreq_notfound(self, req, upgrade):
        raise pip.exceptions.DistributionNotFound("you've been mocked!")

    with mock.patch('pip.index.PackageFinder.find_requirement', _mock_findreq_found):
        ret = project.version_already_uploaded('someprj', '1.2.3', 'https://pypi.python.org/pypi')
        assert ret is True
    with mock.patch('pip.index.PackageFinder.find_requirement', _mock_findreq_notfound):
        ret = project.version_already_uploaded('someprj', '1.2.3', 'https://pypi.python.org/pypi')
        assert ret is False
