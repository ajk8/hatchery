from hatchery import main
from hatchery import config
from hatchery import project
from hatchery import executor
import microcache
import pytest
import os
import testfixtures


def test__get_package_name_or_die(tmpdir):
    with tmpdir.as_cwd():
        with pytest.raises(SystemExit):
            main._get_package_name_or_die()
        os.mkdir('somepackage')
        open('somepackage/__init__.py', 'w').close()
        assert main._get_package_name_or_die() == 'somepackage'


def test__get_config_or_die(tmpdir, monkeypatch):
    with microcache.temporarily_disabled():
        with tmpdir.as_cwd():
            main._get_config_or_die()
            with pytest.raises(SystemExit):
                main._get_config_or_die(['notarealparam'])
            with open('.hatchery.yml', 'w') as fh:
                fh.write('notarealparam: "but valid yaml"\n')
                fh.flush()
            with pytest.raises(SystemExit):
                main._get_config_or_die()


def test__valid_version_or_die():
    main._valid_version_or_die('7.1')
    with pytest.raises(SystemExit):
        main._valid_version_or_die('#$$#%')


def test__latest_version_or_die(monkeypatch):
    monkeypatch.setattr(config, 'from_pypirc', lambda x: {'repository': 'foo'})
    monkeypatch.setattr(project, 'version_already_uploaded', lambda a, b, c, d: False)
    monkeypatch.setattr(project, 'version_is_latest', lambda a, b, c, d: True)
    main._latest_version_or_die('foo', 'bar', 'baz', True)
    monkeypatch.setattr(project, 'version_is_latest', lambda a, b, c, d: False)
    monkeypatch.setattr(project, 'get_latest_uploaded_version', lambda a, b, c: '1.0')
    with pytest.raises(SystemExit):
        main._latest_version_or_die('foo', 'bar', 'baz', True)
    monkeypatch.setattr(project, 'version_is_latest', lambda a, b, c, d: True)
    monkeypatch.setattr(project, 'version_already_uploaded', lambda a, b, c, d: True)
    with pytest.raises(SystemExit):
        main._latest_version_or_die('foo', 'bar', 'baz', True)


def test__check_and_set_version(monkeypatch):
    monkeypatch.setattr(main, '_latest_version_or_die', lambda a, b, c, d: True)
    monkeypatch.setattr(project, 'set_version', lambda x, y: None)
    assert main._check_and_set_version('0.1', 'a', 'b', 'c', True) == '0.1'
    monkeypatch.setattr(project, 'get_version', lambda x: '1.0')
    assert main._check_and_set_version(None, 'a', 'b', 'c', True) == '1.0'


def _somewhere_in_messages(log_capturer, search_str):
    for message in [r.msg for r in log_capturer.records]:
        if search_str in message:
            return True
    return False


def _nowhere_in_messages(messages, search_str):
    return not _somewhere_in_messages(messages, search_str)


def test__log_failure_and_die():
    with testfixtures.LogCapture() as lc:
        cr = executor.CallResult(1, 'happy_stdout', 'sad_stderr')
        with pytest.raises(SystemExit):
            main._log_failure_and_die('error', cr, False)
        assert _somewhere_in_messages(lc, 'error')
        assert _nowhere_in_messages(lc, 'happy_stdout')
        assert _nowhere_in_messages(lc, 'sad_stderr')
        with pytest.raises(SystemExit):
            main._log_failure_and_die('error', cr, True)
        assert _somewhere_in_messages(lc, 'error')
        assert _somewhere_in_messages(lc, 'happy_stdout')
        assert _somewhere_in_messages(lc, 'sad_stderr')
