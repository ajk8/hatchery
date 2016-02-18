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
