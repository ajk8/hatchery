"""
hatchery (version {version})

Automate the process of testing, packaging, and uploading your project with
dynamic versioning and no source tree pollution!

Usage: hatchery [<task> ...] [options]

Just run from the root of your project and off you go.  Tasks can be
chained, and will always be run in the order below regardless of the order
in which they are specified.  Available tasks are:

    help        print this help output (ignores all other tasks)
    check       check to see if this project conforms to hatchery requirements
    clean       clean up the working directory
    test        run tests according to commands specified in .hatchery.yml
    package     create binary packages to be distributed
    register    register your package with the index if you haven't already
    upload      upload all created packages to a configured pypi index

General options:

    -h, --help      print this help output and quit
    --log-level=LEVEL
                    one of (debug, info, error, critical) [default: info]
    -s, --show-command-output
                    show output of all subcommands, even if they succeed.
                    output of failed commands will be shown irrespective of
                    this setting
    -r=VER, --release-version=VER
                    version to use when packaging and registering
                    Note: version will be inferred when uploading

Config files:

    hatchery endeavors to have as few implicit requirements on your project
    as possible (and those are managed using the "check" task).  In order
    for it to do its work, therefore, some configuration has to be provided.
    This is done using config files.  There are two files (user-level, and
    project-level) that can be used to specify these configuration files:

        {config_files}

    In the case where both files define the same parameters, the project-level
    file wins.  See README.md for more information about the available
    configuration parameters.
"""

import docopt
import logging
import funcy
import os
import workdir
from . import _version
from . import executor
from . import project
from . import config
from . import snippets

logger = logging.getLogger(__name__)
workdir.options.path = '.hatchery.work'


def _get_package_name_or_die():
    try:
        package_name = project.get_package_name()
    except project.PackageError as e:
        logger.error(str(e))
        raise SystemExit(1)
    return package_name


def _get_config_or_die(required_params=[], calling_task=None):
    try:
        config_dict = config.from_yaml()
        for key in required_params:
            if key not in config_dict.keys() or config_dict[key] is None:
                logger.error(
                    '{} was not set in hatchery config files, cannot continue with {}'.format(
                        key, calling_task
                    )
                )
                raise SystemExit(1)
    except config.ConfigError as e:
        logger.error(str(e))
        raise SystemExit(1)
    return config_dict


def _valid_version_or_die(release_version):
    if not project.version_is_valid(release_version):
        logger.error('version "{}" is not pip-compatible, try another!'.format(release_version))
        raise SystemExit(1)


def _check_and_set_version(release_version, package_name):
    set_flag = True
    if not release_version:
        set_flag = False
        release_version = project.get_version(package_name)
    _valid_version_or_die(release_version)
    if set_flag:
        project.set_version(package_name, release_version)
    return release_version


def task_upload(args):
    if not os.path.isdir(workdir.options.path):
        logger.error('{} does not exist, nothing to upload!'.format(workdir.options.path))
        raise SystemExit(1)
    with workdir.as_cwd():
        config_dict = _get_config_or_die(
            calling_task='upload',
            required_params=['pypi_repository']
        )
        pypi_repository = config_dict['pypi_repository']
        pypirc_dict = config.from_pypirc(pypi_repository)
        index_url = pypirc_dict['repository']
        project_name = project.get_project_name()
        package_name = _get_package_name_or_die()
        release_version = project.get_version(package_name, ignore_cache=True)
        _valid_version_or_die(release_version)
        if project.version_already_uploaded(project_name, release_version, index_url):
            logger.error('{}=={} already exists on index {}'.format(
                project_name, release_version, index_url
            ))
            raise SystemExit(1)
        result = executor.call(('twine', 'upload', '-r', pypi_repository, 'dist/*'))
        if result.exitval and 'not allowed to edit' in result.stderr:
            logger.error('could not upload packages, try `hatchery register`')
            raise SystemExit(1)


def task_register(args):
    release_version = args['--release-version']
    workdir.sync()
    with workdir.as_cwd():
        config_dict = _get_config_or_die(
            calling_task='register',
            required_params=['pypi_repository']
        )
        pypi_repository = config_dict['pypi_repository']
        package_name = _get_package_name_or_die()
        _check_and_set_version(release_version, package_name)
        result = executor.setup(('register', '-r', pypi_repository))
        if result.exitval or '(400)' in result.stdout:
            logger.error('failed to register project')
            raise SystemExit(result.exitval)


def task_package(args):
    release_version = args['--release-version']
    workdir.sync()
    with workdir.as_cwd():
        config_dict = _get_config_or_die(
            calling_task='register',
            required_params=['create_wheel', 'readme_to_rst']
        )
        package_name = _get_package_name_or_die()
        _check_and_set_version(release_version, package_name)
        if config_dict['readme_to_rst']:
            if project.project_has_readme_md():
                try:
                    project.convert_readme_to_rst()
                except project.ProjectError as e:
                    if 'could not convert' in str(e):
                        logger.error(e)
                        raise SystemExit(1)
                    else:
                        logger.info(e)
        setup_args = ['sdist']
        if config_dict['create_wheel']:
            setup_args.append('bdist_wheel')
        result = executor.setup(setup_args)
        if result.exitval:
            logger.error('failed to package project')
            raise SystemExit(result.exitval)


def task_test(args):
    workdir.sync()
    with workdir.as_cwd():
        config_dict = _get_config_or_die(
            calling_task='test',
            required_params=['test_command']
        )
        test_commands = config_dict['test_command']
        if not funcy.is_list(test_commands):
            test_commands = [test_commands]
        for cmd_str in test_commands:
            result = executor.call(cmd_str)
            if result.exitval:
                raise SystemExit(result.exitval)


def task_clean(args):
    logger.info('cleaning up workspace')
    workdir.remove()


def task_check(args):
    logger.info('checking project for requirements')
    ret = 0
    logger.debug('verifying that project has a single package')
    package_name = project.get_package_name()
    logger.debug('checking state of {} file'.format(project.VERSION_FILE_NAME))
    if not project.package_has_version_file(package_name):
        logger.error('package does not have a {} file'.format(project.VERSION_FILE_NAME))
        ret = 1
    elif not project.version_file_has___version__(package_name):
        logger.error('package has a {} file but does not define a __version__ variable'.format(
            project.VERSION_FILE_NAME
        ))
        ret = 1
    logger.debug('checking state of setup.py')
    if not project.setup_py_has_exec_block(package_name):
        setup_py_block = snippets.get_snippet_content(
            'setup.py', package_name=package_name, version_file=project.VERSION_FILE_NAME
        )
        logger.error('setup.py must have the following block: ' + os.linesep + setup_py_block)
        ret = 1
    if not project.setup_py_uses___version__():
        logger.error(
            'setup.py must use the __version__ variable imported by the exec block' + os.linesep +
            'setup(' + os.linesep +
            '    ...' + os.linesep +
            '    version=__version__,' + os.linesep +
            '    ...' + os.linesep +
            ')')
        ret = 1
    if ret:
        raise SystemExit(ret)
    else:
        logger.info('everything looks good!')


ORDERED_TASKS = ['check', 'clean', 'test', 'package', 'register', 'upload']
CHECK_TASKS = [t for t in ORDERED_TASKS if t != 'clean']
RELVERSION_TASKS = ['package', 'register']


def hatchery():
    """ Main entry point for the hatchery program """
    args = docopt.docopt(__doc__)
    task_list = args['<task>']

    if not task_list or 'help' in task_list or args['--help']:
        print(__doc__.format(version=_version.__version__, config_files=config.CONFIG_LOCATIONS))
        return 0

    level_str = args['--log-level']
    try:
        level_const = getattr(logging, level_str.upper())
        logging.basicConfig(level=level_const)
    except LookupError:
        logging.basicConfig()
        logger.error('received invalid log level: ' + level_str)
        return 1

    for task in task_list:
        if task not in ORDERED_TASKS:
            logger.error('received invalid task: ' + task)
            return 1

    for task in CHECK_TASKS:
        if task in task_list:
            task_check(args)
            break

    for task in RELVERSION_TASKS:
        if task in task_list and not args['--release-version']:
            logger.error('--release-version is required for package and register tasks')
            return 1

    # all commands will raise a SystemExit if they fail
    # check will have already been run
    for task in ORDERED_TASKS:
        if task in task_list and task != 'check':
            globals()['task_' + task](args)
    return 0
