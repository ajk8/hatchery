import pytest
from hatchery import snippets


def test_get_snippet_content():
    with pytest.raises(ValueError):
        snippets.get_snippet_content('notasnippet')
    assert '__version__' in snippets.get_snippet_content('_version.py')
    with pytest.raises(KeyError):
        snippets.get_snippet_content('setup.py', badkey='badval')
    ret = snippets.get_snippet_content(
        snippet_name='setup.py',
        package_name='mypackage',
        version_file='_version.py'
    )
    assert '_version.py' in ret
    assert 'exec' in ret
