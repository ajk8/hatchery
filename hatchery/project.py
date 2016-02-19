import setuptools
import funcy
import os
import pip
from pkg_resources.extern import packaging
from . import snippets
from . import helpers

VERSION_FILE_NAME = '_version.py'


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
    version_file_path = helpers.package_file_path(VERSION_FILE_NAME, package_name)
    return os.path.isfile(version_file_path)


def setup_py_has_exec_block(package_name):
    """ Check to make sure setup.py is exec'ing _version.py """
    search_str = snippets.get_snippet_content(
        snippet_name='setup.py',
        package_name=package_name,
        version_file=VERSION_FILE_NAME
    ).strip()
    setup_py_content = helpers.get_file_content('setup.py')
    return search_str in setup_py_content


def setup_py_uses___version__():
    """ Check to make sure setup.py is using the __version__ variable in the setup block """
    setup_py_content = helpers.get_file_content('setup.py')
    return helpers.value_of_named_argument_in_function('version', 'setup', setup_py_content)


VERSION_SET_REGEX = r'__version__\s*=\s*[\'"](?P<version>[^\'"]+)[\'"]'


def version_file_has___version__(package_name):
    """ Check to make sure _version.py defines __version__ as a string """
    return helpers.regex_in_package_file(VERSION_SET_REGEX, VERSION_FILE_NAME, package_name)


def version_file_has___version_info__(package_name):
    """ Check to make sure _version.py defines a __version_info__ parameter """
    return helpers.regex_in_package_file(r'__version_info__\s*=', VERSION_FILE_NAME, package_name)


def package_uses___version__(package_name):
    """ Check to make sure the package imports __version__ """
    return helpers.regex_in_package_file(r'import.*__version__', '__init__.py', package_name)


def get_project_name():
    """ Grab the project name out of setup.py """
    setup_py_content = helpers.get_file_content('setup.py')
    ret = helpers.value_of_named_argument_in_function('name', 'setup', setup_py_content)
    if ret and ret[0] == ret[-1] in ('"', "'"):
        ret = ret[1:-1]
    return ret


def get_version(package_name):
    """ Get the version which is currently configured by the package """
    found = helpers.regex_in_package_file(VERSION_SET_REGEX, VERSION_FILE_NAME, package_name)
    version_file_path = helpers.package_file_path(VERSION_FILE_NAME, package_name)
    version_file_content = helpers.get_file_content(version_file_path)
    found = funcy.re_find(VERSION_SET_REGEX, version_file_content)
    if found is None:
        raise ProjectError('found {}, but __version__ is not defined')
    current_version = found['version']
    return current_version


def set_version(package_name, version_str):
    """ Set the version in _version.py to version_str """
    current_version = get_version(package_name)
    version_file_path = helpers.package_file_path(VERSION_FILE_NAME, package_name)
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


def version_already_uploaded(project_name, version_str, index_url):
    """ Check to see if the version specified has already been uploaded to the configured index
    """

    pf = pip.index.PackageFinder([], [index_url], session=pip.download.PipSession())
    try:
        req = pip.req.InstallRequirement(
            '{}=={}'.format(project_name, version_str), comes_from=None
        )
        pf.find_requirement(req, upgrade=False)
    except (pip.exceptions.DistributionNotFound, pip.exceptions.InstallationError):
        return False
    return True
