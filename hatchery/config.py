import yaml
import os
import copy
from . import cache

CONFIG_LOCATIONS = ['.hatchery.yml']
DEFAULT_CONFIG = {
    'test_command': None
}


class ConfigError(RuntimeError):
    pass


def from_yaml(_rebuild_cache_for_testing=False):
    """ Load configuration from yaml source(s), cached to only run once """
    if not cache.has('config') or _rebuild_cache_for_testing:
        ret = copy.deepcopy(DEFAULT_CONFIG)
        for k, v in DEFAULT_CONFIG.items():
            ret[k] = v
        for config_path in CONFIG_LOCATIONS:
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
        cache.upsert('config', ret)
    return cache.get('config')
