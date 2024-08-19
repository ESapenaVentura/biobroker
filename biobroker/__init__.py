__all__ = []
for v in dir():
    if not v.startswith('__') and v != 'mypackage':
        __all__.append(v)