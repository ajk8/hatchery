import tokenize
import collections
import os
import funcy
import microcache
from io import StringIO

SimplifiedToken = collections.namedtuple('SimplifiedToken', ('typenum', 'value'))


@microcache.this
def value_of_named_argument_in_function(argument_name, function_name, search_str,
                                        resolve_varname=False):
    """ Parse an arbitrary block of python code to get the value of a named argument
        from inside a function call
    """
    try:
        search_str = unicode(search_str)
    except NameError:
        pass
    readline = StringIO(search_str).readline
    try:
        token_generator = tokenize.generate_tokens(readline)
        tokens = [SimplifiedToken(toknum, tokval) for toknum, tokval, _, _, _ in token_generator]
    except tokenize.TokenError as e:
        raise ValueError('search_str is not parse-able python code: ' + str(e))
    in_function = False
    is_var = False
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
            # value is set to another variable which we are going to attempt to resolve
            if resolve_varname and tokens[i+2].typenum == 1:
                is_var = True
                argument_name = tokens[i+2].value
                break

            # again, for a very specific usecase -- get the whole value and concatenate it
            # this will match something like _version.__version__
            j = 3
            while True:
                if tokens[i+j].value in (',', ')') or tokens[i+j].typenum == 58:
                    break
                j += 1

            return ''.join([t.value for t in tokens[i+2:i+j]]).strip()

    # this is very dumb logic, and only works if the function argument is set to a variable
    # which is set to a string value
    if is_var:
        for i in range(len(tokens)):
            if (
                tokens[i].typenum == tokenize.NAME and tokens[i].value == argument_name and
                tokens[i+1].typenum == tokenize.OP and tokens[i+1].value == '='
            ):
                return tokens[i+2].value.strip()

    return None


@microcache.this
def get_file_content(file_path):
    """ Load the content of a text file into a string """
    with open(file_path) as f:
        ret = f.read()
    return ret


@microcache.this
def package_file_path(filename, package_name):
    """ Convenience function to get the path to a package's version file

    >>> package_file_path('mymodule.py', 'mypackage')
    'mypackage/mymodule.py'
    """
    return os.path.join(package_name, filename)


@microcache.this
def regex_in_file(regex, filepath, return_match=False):
    """ Search for a regex in a file

    If return_match is True, return the found object instead of a boolean
    """
    file_content = get_file_content(filepath)
    re_method = funcy.re_find if return_match else funcy.re_test
    return re_method(regex, file_content)


@microcache.this
def regex_in_package_file(regex, filename, package_name, return_match=False):
    """ Search for a regex in a file contained within the package directory

    If return_match is True, return the found object instead of a boolean
    """
    filepath = package_file_path(filename, package_name)
    return regex_in_file(regex, filepath, return_match=return_match)
