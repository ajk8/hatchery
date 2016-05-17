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
    config      print the computed config contents to the console
    clean       clean up the working directory
    test        run tests according to commands specified in .hatchery.yml
    package     create binary packages to be distributed
    register    register your package with the index if you haven't already
    upload      upload all created packages to a configured pypi index
    tag         tag your git repository with the release version and push
                it back up to the origin

General options:

    -h, --help      print this help output and quit
    --log-level=LEVEL
                    one of (debug, info, error, critical) [default: info]
    -s, --stream-command-output
                    stream output of all subcommands as they are running.
                    if not set, output will be captured and printed to the
                    screen only on failed commands
    -r=VER, --release-version=VER
                    version to use when packaging and registering
                    Note: version will be inferred when uploading

Notes on tagging:

    Creating a tag requires a clean working copy, which means that there are
    two very important prerequisites:

        1. you should not use hatchery's tagging (and uploading) functionality
           until you have committed all of your changes (good practice anyway)
        2. you must have an entry for .hatchery.work in your .gitignore file
           so that hatchery itself does not dirty up your working tree

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
import git
import ruamel.yaml as yaml
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
    except project.ProjectError as e:
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


def _latest_version_or_die(release_version, project_name, pypi_repository):
    pypirc_dict = config.from_pypirc(pypi_repository)
    index_url = pypirc_dict['repository']
    if project.version_already_uploaded(project_name, release_version, index_url):
        logger.error('{}=={} already exists on index {}'.format(
            project_name, release_version, index_url
        ))
        raise SystemExit(1)
    elif not project.version_is_latest(project_name, release_version, index_url):
        latest_version = project.get_latest_uploaded_version(project_name, index_url)
        logger.error('{}=={} is older than the latest ({}) on index {}'.format(
            project_name, release_version, latest_version, index_url
        ))
        raise SystemExit(1)


def _check_and_set_version(release_version, package_name, project_name, pypi_repository):
    set_flag = True
    if not release_version:
        set_flag = False
        release_version = project.get_version(package_name)
    _valid_version_or_die(release_version)
    _latest_version_or_die(release_version, project_name, pypi_repository)
    if set_flag:
        project.set_version(package_name, release_version)
    return release_version


def _log_failure_and_die(error_msg, call_result, log_full_result):
    msg = error_msg
    if log_full_result:
        msg += os.linesep.join((':', call_result.format_error_msg()))
    logger.error(msg)
    raise SystemExit(1)


def task_tag(args):
    if not os.path.isdir(workdir.options.path):
        logger.error('{} does not exist, cannot fetch tag version!'.format(workdir.options.path))
        raise SystemExit(1)
    with workdir.as_cwd():
        config_dict = _get_config_or_die(
            calling_task='upload',
            required_params=['git_remote_name']
        )
        git_remote_name = config_dict['git_remote_name']
        package_name = _get_package_name_or_die()
        release_version = project.get_version(package_name, ignore_cache=True)

    # this part actually happens outside of the working directory!
    repo = git.Repo()
    if repo.is_dirty():
        logger.error('cannot create tag, repo is dirty')
        raise SystemExit(1)
    if git_remote_name not in [x.name for x in repo.remotes]:
        logger.error(
            'cannot push tag to remote "{}" as it is not defined in repo'.format(git_remote_name)
        )
        raise SystemExit(1)
    repo.create_tag(
        path=release_version,
        message='tag {} created by hatchery'.format(release_version)
    )
    repo.remotes[git_remote_name].push(tags=True)
    logger.info('version {} tagged and pushed!'.format(release_version))


def task_upload(args):
    suppress_output = not args['--stream-command-output']
    if not os.path.isdir(workdir.options.path):
        logger.error('{} does not exist, nothing to upload!'.format(workdir.options.path))
        raise SystemExit(1)
    with workdir.as_cwd():
        config_dict = _get_config_or_die(
            calling_task='upload',
            required_params=['pypi_repository']
        )
        pypi_repository = config_dict['pypi_repository']
        project_name = project.get_project_name()
        package_name = _get_package_name_or_die()
        if project.multiple_packaged_versions(package_name):
            logger.error(
                'multiple package versions found, refusing to upload -- run `hatchery clean`'
            )
            raise SystemExit(1)
        release_version = project.get_version(package_name, ignore_cache=True)
        _valid_version_or_die(release_version)
        _latest_version_or_die(release_version, project_name, pypi_repository)
        result = executor.call(
            ('twine', 'upload', '-r', pypi_repository, 'dist/*'), suppress_output=suppress_output
        )
        if result.exitval:
            if 'not allowed to edit' in result.stderr:
                logger.error('could not upload packages, try `hatchery register`')
            else:
                _log_failure_and_die(
                    'failed to upload packages', result, log_full_result=suppress_output
                )
            raise SystemExit(1)
    logger.info('successfully uploaded {}=={} to [{}]'.format(
        project_name, release_version, pypi_repository
    ))


def task_register(args):
    release_version = args['--release-version']
    suppress_output = not args['--stream-command-output']
    workdir.sync()
    with workdir.as_cwd():
        config_dict = _get_config_or_die(
            calling_task='register',
            required_params=['pypi_repository']
        )
        pypi_repository = config_dict['pypi_repository']
        project_name = project.get_project_name()
        package_name = _get_package_name_or_die()
        if not release_version:
            release_version = project.get_version(package_name)
            if not project.version_is_valid(release_version):
                logger.info('using version 0.0 for registration purposes')
                release_version = '0.0'
        _check_and_set_version(release_version, package_name, project_name, pypi_repository)
        result = executor.setup(
            ('register', '-r', pypi_repository), suppress_output=suppress_output
        )
        if result.exitval or '(400)' in result.stdout:
            _log_failure_and_die(
                'failed to register project', result, log_full_result=suppress_output
            )
    logger.info('successfully registered {} with [{}]'.format(project_name, pypi_repository))


def task_package(args):
    release_version = args['--release-version']
    suppress_output = not args['--stream-command-output']
    workdir.sync()
    with workdir.as_cwd():
        config_dict = _get_config_or_die(
            calling_task='register',
            required_params=['create_wheel', 'readme_to_rst', 'pypi_repository']
        )
        pypi_repository = config_dict['pypi_repository']
        project_name = project.get_project_name()
        package_name = _get_package_name_or_die()
        _check_and_set_version(release_version, package_name, project_name, pypi_repository)
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
        result = executor.setup(setup_args, suppress_output=suppress_output)
        if result.exitval:
            _log_failure_and_die(
                'failed to package project', result, log_full_result=suppress_output
            )
    logger.info('successfully packaged {}=={}'.format(project_name, release_version))


def task_test(args):
    suppress_output = not args['--stream-command-output']
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
            result = executor.call(cmd_str, suppress_output=suppress_output)
            if result.exitval:
                _log_failure_and_die('tests failed', result, log_full_result=suppress_output)
    logger.info('testing completed successfully')


def task_clean(args):
    workdir.remove()


def task_config(args):
    config_dict = _get_config_or_die(
        calling_task='config',
        required_params=[]
    )
    print(os.linesep.join((
        '### yaml ###',
        '',
        yaml.dump(config_dict, Dumper=yaml.RoundTripDumper, indent=4),
        '### /yaml ###'
    )))


def task_check(args):
    logger.debug('verifying that project has a single package')
    try:
        package_name = project.get_package_name()
    except project.ProjectError as e:
        logger.error(str(e))
        raise SystemExit(1)
    ret = 0
    logger.debug('checking state of _version.py file')
    if (not project.package_has_version_file(package_name) or
            not project.version_file_has___version__(package_name)):
        _version_py_block = snippets.get_snippet_content('_version.py', package_name=package_name)
        logger.error(os.linesep.join((
            'package does not have a valid _version.py file',
            '',
            _version_py_block
        )))
        ret = 1
    logger.debug('checking state of setup.py')
    if not project.setup_py_uses__version_py() or not project.setup_py_uses___version__():
        setup_py_block = snippets.get_snippet_content('setup.py', package_name=package_name)
        logger.error(os.linesep.join((
            'could not detect valid method in setup.py:',
            '',
            setup_py_block
        )))
        ret = 1
    if ret:
        raise SystemExit(ret)
    logger.info('all checks passed!')


ORDERED_TASKS = ['check', 'config', 'clean', 'test', 'package', 'register', 'upload', 'tag']
CHECK_TASKS = [t for t in ORDERED_TASKS if t not in ('config', 'clean')]


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
        if level_const == logging.DEBUG:
            workdir.options.debug = True
    except LookupError:
        logging.basicConfig()
        logger.error('received invalid log level: ' + level_str)
        return 1

    for task in task_list:
        if task not in ORDERED_TASKS:
            logger.info('starting task: check')
            logger.error('received invalid task: ' + task)
            return 1

    for task in CHECK_TASKS:
        if task in task_list:
            task_check(args)
            break

    if 'package' in task_list and not args['--release-version']:
        logger.error('--release-version is required for the package task')
        return 1

    config_dict = _get_config_or_die(
        calling_task='hatchery',
        required_params=['auto_push_tag']
    )
    if config_dict['auto_push_tag'] and 'upload' in task_list:
        logger.info('adding task: tag (auto_push_tag==True)')
        task_list.append('tag')

    # all commands will raise a SystemExit if they fail
    # check will have already been run
    for task in ORDERED_TASKS:
        if task in task_list and task != 'check':
            logger.info('starting task: ' + task)
            globals()['task_' + task](args)

    logger.info("all's well that ends well...hatchery out")
    return 0
