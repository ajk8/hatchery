import os
import pytest
import funcy
from hatchery import config


def test_from_yaml(tmpdir, monkeypatch):
    monkeypatch.setattr(funcy, 'memoize', lambda: 0)
    with tmpdir.as_cwd():
        config_dict = config.from_yaml(_rebuild_cache_for_testing=True)
        assert config_dict['test_command'] is None
        open('.hatchery.yml', 'w').close()
        config_dict = config.from_yaml(_rebuild_cache_for_testing=True)
        assert config_dict['test_command'] is None
        with open('.hatchery.yml', 'a') as f:
            f.write('test_command: "testme!"' + os.linesep)
        config_dict = config.from_yaml(_rebuild_cache_for_testing=True)
        assert config_dict['test_command'] == 'testme!'
        with open('.hatchery.yml', 'a') as f:
            f.write('garbage: "garbage!!"' + os.linesep)
        with pytest.raises(config.ConfigError):
            config.from_yaml(_rebuild_cache_for_testing=True)


