_CACHE = {}


def upsert(k, v):
    """ Perform an upsert on the cache

    >>> from . import cache
    >>> cache.has('upsert')
    False
    >>> cache.upsert('upsert', 'this')
    >>> cache.get('upsert')
    'this'
    >>> cache.upsert('upsert', 'that')
    >>> cache.get('upsert')
    'that'
    """
    _CACHE[k] = v


def get(k):
    """ Get a value out of the cache

    >>> from . import cache
    >>> cache.get('get')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    KeyError: 'key not cached: get'
    >>> cache.upsert('get', 'got')
    >>> cache.get('get')
    'got'
    """
    if not has(k):
        raise KeyError('key not cached: ' + k)
    return _CACHE[k]


def has(k):
    """ See if a key is in the cache

    >>> from . import cache
    >>> cache.has('has')
    False
    >>> cache.upsert('has', 'now')
    >>> cache.has('has')
    True
    """
    return k in _CACHE.keys()


def me(k=None):
    """ Use the cache as a decorator, essentially memoize with an override

    >>> from . import cache
    >>> @cache.me()
    ... def dummy():
    ...     return 'value'
    ...
    >>> dummy()
    'value'
    >>> cache.get('dummy(){}')
    'value'
    >>> @cache.me('smarty')
    ... def dummy():
    ...     return 'value'
    ...
    >>> dummy()
    'value'
    >>> cache.get('smarty(){}')
    'value'
    """

    def me_decorator(func):

        _k = k if k else func.__name__

        def func_wrapper(*args, **kwargs):
            __k = _k + str(args) + str(kwargs)
            if not has(__k) or (
                '_rebuild_cache_for_testing' in kwargs.keys() and
                kwargs['_rebuild_cache_for_testing']
            ):
                v = func(*args, **kwargs)
                upsert(__k, v)
            return get(__k)

        return func_wrapper

    return me_decorator
