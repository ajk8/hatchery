import setuptools
import os
import requests
import logging
import microcache
import pypandoc
import funcy
from pkg_resources.extern import packaging
from . import helpers

logger = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.ERROR)


class ProjectError(RuntimeError):
    pass


def get_package_name():
    packages = setuptools.find_packages()
    if 'tests' in packages:
        packages.remove('tests')
    if len(packages) < 1:
        raise ProjectError('could not detect any packages to build!')
    elif len(packages) > 1:
        raise ProjectError('detected too many packages...something is amiss: ' + str(packages))
    return packages[0]


def project_has_setup_py():
    """ Check to make sure setup.py exists in the project """
    return os.path.isfile('setup.py')


def package_has_version_file(package_name):
    """ Check to make sure _version.py is contained in the package """
    version_file_path = helpers.package_file_path('_version.py', package_name)
    return os.path.isfile(version_file_path)


SETUP_PY_REGEX1 = r'with open\(.+_version\.py.+\)[^\:]+\:\s+exec\(.+read\(\)\)'
SETUP_PY_REGEX2 = r'=\s*find_module\(.+_version.+\)\s+_version\s*=\s*load_module\(.+_version.+\)'


def setup_py_uses__version_py():
    """ Check to make sure setup.py is exec'ing _version.py """
    for regex in (SETUP_PY_REGEX1, SETUP_PY_REGEX2):
        if helpers.regex_in_file(regex, 'setup.py'):
            return True
    return False


def setup_py_uses___version__():
    """ Check to make sure setup.py is using the __version__ variable in the setup block """
    setup_py_content = helpers.get_file_content('setup.py')
    ret = helpers.value_of_named_argument_in_function('version', 'setup', setup_py_content)
    return ret is not None and '__version__' in ret


VERSION_SET_REGEX = r'__version__\s*=\s*[\'"](?P<version>[^\'"]+)[\'"]'


def version_file_has___version__(package_name):
    """ Check to make sure _version.py defines __version__ as a string """
    return helpers.regex_in_package_file(VERSION_SET_REGEX, '_version.py', package_name)


def get_project_name():
    """ Grab the project name out of setup.py """
    setup_py_content = helpers.get_file_content('setup.py')
    ret = helpers.value_of_named_argument_in_function(
        'name', 'setup', setup_py_content, resolve_varname=True
    )
    if ret and ret[0] == ret[-1] in ('"', "'"):
        ret = ret[1:-1]
    return ret


def get_version(package_name, ignore_cache=False):
    """ Get the version which is currently configured by the package """
    if ignore_cache:
        with microcache.temporarily_disabled():
            found = helpers.regex_in_package_file(
                VERSION_SET_REGEX, '_version.py', package_name, return_match=True
            )
    else:
        found = helpers.regex_in_package_file(
            VERSION_SET_REGEX, '_version.py', package_name, return_match=True
        )
    if found is None:
        raise ProjectError('found {}, but __version__ is not defined')
    current_version = found['version']
    return current_version


def set_version(package_name, version_str):
    """ Set the version in _version.py to version_str """
    current_version = get_version(package_name)
    version_file_path = helpers.package_file_path('_version.py', package_name)
    version_file_content = helpers.get_file_content(version_file_path)
    version_file_content = version_file_content.replace(current_version, version_str)
    with open(version_file_path, 'w') as version_file:
        version_file.write(version_file_content)


def version_is_valid(version_str):
    """ Check to see if the version specified is a valid as far as pkg_resources is concerned

    >>> version_is_valid('blah')
    False
    >>> version_is_valid('1.2.3')
    True
    """
    try:
        packaging.version.Version(version_str)
    except packaging.version.InvalidVersion:
        return False
    return True


@microcache.this
def _get_uploaded_versions(project_name, index_url):
    """ Query the pypi index at index_url to find all of the "releases" """
    url = '/'.join((index_url, project_name, 'json'))
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['releases'].keys()
    logger.debug('could not find evidence of project at {} (return code {})'.format(
        url, response.status_code
    ))
    return []


def version_already_uploaded(project_name, version_str, index_url):
    """ Check to see if the version specified has already been uploaded to the configured index
    """
    all_versions = _get_uploaded_versions(project_name, index_url)
    return version_str in all_versions


def get_latest_uploaded_version(project_name, index_url):
    """ Grab the latest version of project_name according to index_url """
    all_versions = _get_uploaded_versions(project_name, index_url)
    ret = None
    for uploaded_version in all_versions:
        ret = ret or '0.0'
        left, right = packaging.version.Version(uploaded_version), packaging.version.Version(ret)
        if left > right:
            ret = uploaded_version
    return ret


def version_is_latest(project_name, version_str, index_url):
    """ Compare version_str with the latest (according to index_url) """
    if version_already_uploaded(project_name, version_str, index_url):
        return False
    latest_uploaded_version = get_latest_uploaded_version(project_name, index_url)
    if latest_uploaded_version is None:
        return True
    elif packaging.version.Version(version_str) > \
            packaging.version.Version(latest_uploaded_version):
        return True
    return False


def project_has_readme_md():
    """ See if project has a readme.md file """
    for filename in os.listdir('.'):
        if filename.lower() == 'readme.md':
            return True
    return False


def convert_readme_to_rst():
    """ Attempt to convert a README.md file into README.rst """
    project_files = os.listdir('.')
    for filename in project_files:
        if filename.lower() == 'readme':
            raise ProjectError(
                'found {} in project directory...'.format(filename) +
                'not sure what to do with it, refusing to convert'
            )
        elif filename.lower() == 'readme.rst':
            raise ProjectError(
                'found {} in project directory...'.format(filename) +
                'refusing to overwrite'
            )
    for filename in project_files:
        if filename.lower() == 'readme.md':
            rst_filename = 'README.rst'
            logger.info('converting {} to {}'.format(filename, rst_filename))
            try:
                rst_content = pypandoc.convert(filename, 'rst')
                with open('README.rst', 'w') as rst_file:
                    rst_file.write(rst_content)
                return
            except OSError as e:
                raise ProjectError(
                    'could not convert readme to rst due to pypandoc error:' + os.linesep + str(e)
                )
    raise ProjectError('could not find any README.md file to convert')


def multiple_packaged_versions(package_name):
    """ Look through built package directory and see if there are multiple versions there """
    dist_files = os.listdir('dist')
    versions = set()
    for filename in dist_files:
        version = funcy.re_find(r'{}-(.+).tar.gz'.format(package_name), filename)
        if version:
            versions.add(version)
    return len(versions) > 1
