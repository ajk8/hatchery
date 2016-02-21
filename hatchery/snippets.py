import os
from . import helpers

SNIPPETS_ROOT = os.path.join(os.path.dirname(__file__), 'snippets')


def get_snippet_content(snippet_name, **format_kwargs):
    """ Load the content from a snippet file which exists in SNIPPETS_ROOT """
    filename = snippet_name + '.snippet'
    snippet_file = os.path.join(SNIPPETS_ROOT, filename)
    if not os.path.isfile(snippet_file):
        raise ValueError('could not find snippet with name ' + filename)
    ret = helpers.get_file_content(snippet_file)
    if format_kwargs:
        ret = ret.format(**format_kwargs)
    return ret
