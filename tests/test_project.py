import pytest
import os
import funcy
import pip
import microcache
import requests_mock
from hatchery import project
from hatchery import snippets
from hatchery import helpers

try:
    from unittest import mock
except ImportError:
    import mock

PROJECT_NAME = 'myproject'
PACKAGE_NAME = 'mypackage'
INDEX_URL = 'https://mocked.pypi.python.org/pypi'


def setup_module(module):
    microcache.disable()


def teardown_module(module):
    microcache.enable()


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
        assert project.project_has_setup_py() is False
        open('setup.py', 'w').close()
        assert project.project_has_setup_py() is True


def test_setup_py_uses__version_py(tmpdir):
    with tmpdir.as_cwd():
        open('setup.py', 'w').close()
        assert project.setup_py_uses__version_py() is False
        snippet_content = snippets.get_snippet_content(
            snippet_name='setup.py',
            package_name=PACKAGE_NAME
        )
        with open('setup.py', 'a') as setup_py:
            setup_py.write(snippet_content)
        assert project.setup_py_uses__version_py() is True


def test_setup_py_uses___version__(tmpdir):
    with tmpdir.as_cwd():
        open('setup.py', 'w').close()
        assert project.setup_py_uses___version__() is False
        with open('setup.py', 'a') as setup_py:
            setup_py.write('setup(version=__version__)')
        assert project.setup_py_uses___version__() is True


def test_package_has_version_file(tmpdir):
    with tmpdir.as_cwd():
        assert project.package_has_version_file(PACKAGE_NAME) is False
        version_file = helpers.package_file_path('_version.py', PACKAGE_NAME)
        _make_package(PACKAGE_NAME, empty_module_files=[os.path.basename(version_file)])
        assert project.package_has_version_file(PACKAGE_NAME) is True


def test_version_file_has___version__(tmpdir):
    with tmpdir.as_cwd():
        version_file = helpers.package_file_path('_version.py', PACKAGE_NAME)
        _make_package(PACKAGE_NAME, empty_module_files=[os.path.basename(version_file)])
        assert project.version_file_has___version__(PACKAGE_NAME) is False
        snippet_content = snippets.get_snippet_content('_version.py')
        with open(version_file, 'a') as _version_py:
            _version_py.write(snippet_content)
        assert project.version_file_has___version__(PACKAGE_NAME) is True


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
        version_file = helpers.package_file_path('_version.py', PACKAGE_NAME)
        _make_package(PACKAGE_NAME, empty_module_files=[os.path.basename(version_file)])
        with pytest.raises(project.ProjectError):
            project.get_version(PACKAGE_NAME)
        with open(version_file, 'w') as _version_py:
            _version_py.write("__version__='someversion'")
        with microcache.temporarily_enabled():
            assert project.get_version(PACKAGE_NAME) == 'someversion'
            snippet_content = snippets.get_snippet_content('_version.py')
            with open(version_file, 'w') as _version_py:
                _version_py.write(snippet_content)
            assert project.get_version(PACKAGE_NAME) == 'someversion'
            assert project.get_version(PACKAGE_NAME, ignore_cache=True) == 'managed by hatchery'


def test_set_version(tmpdir):
    with tmpdir.as_cwd():
        version_file = helpers.package_file_path('_version.py', PACKAGE_NAME)
        _make_package(PACKAGE_NAME, empty_module_files=[os.path.basename(version_file)])
        snippet_content = snippets.get_snippet_content('_version.py')
        with open(version_file, 'w') as _version_py:
            _version_py.write(snippet_content)
        project.set_version(PACKAGE_NAME, '1.2.3')
        version_file_content = helpers.get_file_content(version_file)
        found = funcy.re_find(project.VERSION_SET_REGEX, version_file_content)
        assert found['version'] == '1.2.3'


def test__get_uploaded_versions():
    api_url = '/'.join((INDEX_URL, PROJECT_NAME, 'json'))
    with requests_mock.mock() as m:
        m.get(api_url, status_code=404)
        assert project._get_uploaded_versions(PROJECT_NAME, INDEX_URL) == []
        m.get(api_url, text='{"releases": {"0.1": [], "0.2": []}}')
        assert set(project._get_uploaded_versions(PROJECT_NAME, INDEX_URL)) == set(['0.1', '0.2'])


def test_version_already_uploaded():
    api_url = '/'.join((INDEX_URL, PROJECT_NAME, 'json'))
    with requests_mock.mock() as m:
        m.get(api_url, status_code=404)
        assert project.version_already_uploaded(PROJECT_NAME, '0.1', INDEX_URL) is False
        m.get(api_url, text='{"releases": {"0.1": [], "0.2": []}}')
        assert project.version_already_uploaded(PROJECT_NAME, '0.1', INDEX_URL) is True
        assert project.version_already_uploaded(PROJECT_NAME, '0.3', INDEX_URL) is False


def test_get_latest_uploaded_version():
    api_url = '/'.join((INDEX_URL, PROJECT_NAME, 'json'))
    with requests_mock.mock() as m:
        m.get(api_url, status_code=404)
        assert project.get_latest_uploaded_version(PROJECT_NAME, INDEX_URL) is None
        m.get(api_url, text='{"releases": {"0.1": [], "0.2": []}}')
        assert project.get_latest_uploaded_version(PROJECT_NAME, INDEX_URL) == '0.2'


def test_version_is_latest():
    api_url = '/'.join((INDEX_URL, PROJECT_NAME, 'json'))
    with requests_mock.mock() as m:
        m.get(api_url, status_code=404)
        assert project.version_is_latest(PROJECT_NAME, '0.1', INDEX_URL)
        m.get(api_url, text='{"releases": {"0.1": [], "0.2": []}}')
        assert project.version_is_latest(PROJECT_NAME, '0.1.5', INDEX_URL) is False
        assert project.version_is_latest(PROJECT_NAME, '0.2', INDEX_URL) is False
        assert project.version_is_latest(PROJECT_NAME, '0.3', INDEX_URL) is True


def test_project_has_readme_md(tmpdir):
    with tmpdir.as_cwd():
        assert project.project_has_readme_md() is False
        open('readme.md', 'w').close()
        assert project.project_has_readme_md() is True
        os.remove('readme.md')
        open('README.md', 'w').close()
        assert project.project_has_readme_md() is True



def test_convert_readme_to_rst(tmpdir):

    def _mock_pypandoc_convert_OSError(filename, format):
        raise OSError('this would happen if pandoc were not installed!')

    with tmpdir.as_cwd():
        with pytest.raises(project.ProjectError):
            project.convert_readme_to_rst()
        open('README', 'w').close()
        with pytest.raises(project.ProjectError):
            project.convert_readme_to_rst()
        os.remove('README')
        open('README.rst', 'w').close()
        with pytest.raises(project.ProjectError):
            project.convert_readme_to_rst()
        os.remove('README.rst')
        with open('README.md', 'w') as readme_md:
            readme_md.write('# heading')
        project.convert_readme_to_rst()
        assert helpers.regex_in_file(r'=======', 'README.rst') is True
        os.remove('README.rst')
        with mock.patch('pypandoc.convert', _mock_pypandoc_convert_OSError):
            with pytest.raises(project.ProjectError):
                project.convert_readme_to_rst()
