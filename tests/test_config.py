import os
import pytest
import microcache
from hatchery import config


def test_from_yaml(tmpdir, monkeypatch):
    with microcache.temporarily_disabled():
        with tmpdir.as_cwd():
            # disable global config for testing purposes
            monkeypatch.setattr(config, 'CONFIG_LOCATIONS', ['.hatchery.yml1', '.hatchery.yml2'])
            config_dict = config.from_yaml()
            assert config_dict['test_command'] is None
            open('.hatchery.yml1', 'w').close()
            config_dict = config.from_yaml()
            assert config_dict['test_command'] is None
            with open('.hatchery.yml1', 'a') as f:
                f.write('test_command: "testme!"' + os.linesep)
            config_dict = config.from_yaml()
            assert config_dict['test_command'] == 'testme!'
            with open('.hatchery.yml2', 'w') as f:
                f.write('test_command: "i win!"')
            config_dict = config.from_yaml()
            assert config_dict['test_command'] == 'i win!'
            with open('.hatchery.yml1', 'a') as f:
                f.write('garbage: "garbage!!"' + os.linesep)
            with pytest.raises(config.ConfigError):
                config.from_yaml()


PYPIRC_DATA = '''
[pypi]
repository: https://pypi.python.org/pypi
username: someuser
password: somepass
'''


def test_from_pypirc(tmpdir):
    with tmpdir.as_cwd():
        with open('.pypirc', 'w') as pypirc_file:
            pypirc_file.write(PYPIRC_DATA)
        pypirc_config = config.from_pypirc('notthere', _pypirc_location_for_testing='.pypirc')
        assert pypirc_config == {}
        pypirc_config = config.from_pypirc('pypi', _pypirc_location_for_testing='.pypirc')
        assert pypirc_config['username'] == 'someuser'
