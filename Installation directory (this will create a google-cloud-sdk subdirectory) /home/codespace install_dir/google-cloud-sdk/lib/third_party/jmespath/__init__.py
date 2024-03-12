import warnings
import sys
from jmespath import parser
from jmespath.visitor import Options

__version__ = '0.10.0'


if sys.version_info[:2] <= (2, 6) or ((3, 0) <= sys.version_info[:2] <= (3, 3)):
    python_ver = '.'.join(str(x) for x in sys.version_info[:3])

    warnings.warn(
        'You are using Python {0}, which will no longer be supported in '
        'version 0.11.0'.format(python_ver),
        DeprecationWarning)


def compile(expression):
    return parser.Parser().parse(expression)


def search(expression, data, options=None):
    return parser.Parser().parse(expression).search(data, options=options)
