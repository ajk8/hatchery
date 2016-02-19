import yaml
import os
import copy
from . import cache

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

PYPIRC_LOCATIONS = ['~/.pypirc']
CONFIG_LOCATIONS = ['~/.hatchery/hatcher.yml', '.hatchery.yml']
DEFAULT_CONFIG = {
    'pypi_repository': None,
    'test_command': None
}


class ConfigError(RuntimeError):
    pass


@cache.me()
def from_yaml(_rebuild_cache_for_testing=False):
    """ Load configuration from yaml source(s), cached to only run once """
    ret = copy.deepcopy(DEFAULT_CONFIG)
    for k, v in DEFAULT_CONFIG.items():
        ret[k] = v
    for config_path in CONFIG_LOCATIONS:
        config_path = os.path.expanduser(config_path)
        if os.path.isfile(config_path):
            with open(config_path) as config_file:
                config_dict = yaml.load(config_file)
                if config_dict is None:
                    continue
                for k, v in config_dict.items():
                    if k not in DEFAULT_CONFIG.keys():
                        raise ConfigError(
                            'found garbage key "{}" in {}'.format(k, config_path)
                        )
                    ret[k] = v
    return ret


@cache.me()
def from_pypirc(pypi_repository, _pypirc_location_for_testing=None,
                _rebuild_cache_for_testing=False):
    """ Load configuration from .pypirc file, cached to only run once """
    ret = {}
    if _pypirc_location_for_testing is not None:
        pypirc_locations = [_pypirc_location_for_testing]
    else:
        pypirc_locations = PYPIRC_LOCATIONS
    for pypirc_path in pypirc_locations:
        pypirc_path = os.path.expanduser(pypirc_path)
        if os.path.isfile(pypirc_path):
            parser = configparser.SafeConfigParser()
            parser.read(pypirc_path)
            if pypi_repository in parser.sections():
                for option in parser.options(pypi_repository):
                    ret[option] = parser.get(pypi_repository, option)
    return ret
