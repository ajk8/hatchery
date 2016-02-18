from hatchery import helpers


def test_value_of_named_argument_in_function():
    ret = helpers.value_of_named_argument_in_function(
        'version', 'setup', "setup(name='a', version='b')"
    )
    assert ret == "'b'"
    ret = helpers.value_of_named_argument_in_function(
        'version', 'setup', """setup(
            name='a',
            version=__name__
        )"""
    )
    assert ret == '__name__'
    ret = helpers.value_of_named_argument_in_function(
        'version', 'setup', "setup(name='a', verison='b')"
    )
    assert ret is None
