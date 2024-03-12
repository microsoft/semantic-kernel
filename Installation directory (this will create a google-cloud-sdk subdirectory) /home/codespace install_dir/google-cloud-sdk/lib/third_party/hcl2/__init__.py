"""For package documentation, see README"""

try:
    from .version import version as __version__
except ImportError:
    __version__ = "unknown"

from .api import load, loads
