from collections import namedtuple

__all__ = ['__version__', 'version']

version_tuple = namedtuple('version', ['major', 'minor', 'micro'])

version = version_tuple(0, 0, 1)
__version__ = '.'.join(str(num) for num in version)
