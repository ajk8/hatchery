import tokenize
import collections
import os
import funcy
from io import StringIO

SimplifiedToken = collections.namedtuple('SimplifiedToken', ('typenum', 'value'))


def value_of_named_argument_in_function(argument_name, function_name, search_str):
    """ Parse an arbitrary block of python code to get the value of a named argument
        from inside a function call
    """
    try:
        search_str = unicode(search_str)
    except NameError:
        pass
    readline = StringIO(search_str).readline
    token_generator = tokenize.generate_tokens(readline)
    tokens = [SimplifiedToken(toknum, tokval) for toknum, tokval, _, _, _ in token_generator]
    in_function = False
    for i in range(len(tokens)):
        if (
            not in_function and
            tokens[i].typenum == tokenize.NAME and tokens[i].value == function_name and
            tokens[i+1].typenum == tokenize.OP and tokens[i+1].value == '('
        ):
            in_function = True
            continue
        elif (
            in_function and
            tokens[i].typenum == tokenize.NAME and tokens[i].value == argument_name and
            tokens[i+1].typenum == tokenize.OP and tokens[i+1].value == '='
        ):
            return tokens[i+2].value
    return None


def get_file_content(file_path):
    """ Load the content of a text file into a string """
    with open(file_path) as f:
        ret = f.read()
    return ret


def package_file_path(filename, package_name):
    """ Convenience function to get the path to a package's version file

    >>> package_file_path('mymodule.py', 'mypackage')
    'mypackage/mymodule.py'
    """
    return os.path.join(package_name, filename)


def regex_in_file(regex, filepath, return_match=False):
    """ Search for a regex in a file

    If return_match is True, return the found object instead of a boolean
    """
    file_content = get_file_content(filepath)
    re_method = funcy.re_find if return_match else funcy.re_test
    return re_method(regex, file_content)


def regex_in_package_file(regex, filename, package_name, return_match=False):
    """ Search for a regex in a file contained within the package directory

    If return_match is True, return the found object instead of a boolean
    """
    filepath = package_file_path(filename, package_name)
    return regex_in_file(regex, filepath, return_match=return_match)
