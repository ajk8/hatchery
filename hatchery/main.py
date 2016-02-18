import click
import logbook
import funcy
from . import _version
from . import workdir
from . import executor
from . import project
from . import config

logger = logbook.Logger(__name__)


@click.group(chain=True, no_args_is_help=True)
@click.version_option(version=_version.__version__)
def hatchery(**kwargs):
    logbook.StderrHandler().push_application()


@hatchery.command()
@click.option('--release-version', '-r', type=str)
@click.option('--allow-invalid-version', is_flag=True)
@click.option('--no-wheel', is_flag=True)
def package(release_version, allow_invalid_version, no_wheel):
    workdir.sync()
    with workdir.as_cwd():
        try:
            package_name = project.get_package_name()
        except project.PackageError as e:
            logger.error(str(e))
            raise SystemExit(1)
        if release_version:
            if not project.version_is_valid(release_version) and not allow_invalid_version:
                logger.error(
                    'version {} is not pip-compatible, try another!'.format(release_version)
                )
                raise SystemExit(1)
            project.set_version(package_name, release_version)
        setup_args = ['sdist']
        if not no_wheel:
            setup_args.append('bdist_wheel')
        exitval = executor.setup(*setup_args)
        if exitval:
            raise SystemExit(exitval)


@hatchery.command()
def test():
    workdir.sync()
    with workdir.as_cwd():
        try:
            config_dict = config.from_yaml()
        except config.ConfigError as e:
            logger.error(e)
            raise SystemExit(1)
        if not config_dict['test_command']:
            logger.error('no test command found in config!')
            raise SystemExit(1)
        test_commands = config_dict['test_command']
        if not funcy.is_list(test_commands):
            test_commands = [test_commands]
        for cmd_str in test_commands:
            exitval = executor.call_str(cmd_str)
            if exitval:
                raise SystemExit(exitval)


@hatchery.command()
def clean():
    workdir.remove()
