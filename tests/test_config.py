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
[distutils]
index-servers:
    pypi

[pypi]
repository: https://pypi.python.org/pypi
username: someuser
password: somepass

[notindistutils]
repository: doesnotmatter
'''


def test_from_pypirc(tmpdir, monkeypatch):
    monkeypatch.setattr(config, 'PYPIRC_LOCATIONS', ['.pypirc'])
    with tmpdir.as_cwd():
        with open('.pypirc', 'w') as pypirc_file:
            pypirc_file.write(PYPIRC_DATA)
        for badindex in ['notindistutils', 'notanywhere']:
            with pytest.raises(config.ConfigError):
                pypirc_config = config.from_pypirc(badindex)
        pypirc_config = config.from_pypirc('pypi')
        assert pypirc_config['username'] == 'someuser'


def test_pypirc_temp():
    with microcache.temporarily_disabled():
        temp_file = config.pypirc_temp('somelocation')
        with open(temp_file) as fh:
            contents = fh.read()
        assert 'somelocation' in contents
        assert 'anonymous' in contents
        os.remove(temp_file)

