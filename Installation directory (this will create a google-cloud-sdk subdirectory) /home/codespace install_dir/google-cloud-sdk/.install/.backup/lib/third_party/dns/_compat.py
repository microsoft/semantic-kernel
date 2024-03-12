import sys
import decimal
from decimal import Context

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2


if PY3:
    long = int
    xrange = range
else:
    long = long  # pylint: disable=long-builtin
    xrange = xrange  # pylint: disable=xrange-builtin

# unicode / binary types
if PY3:
    text_type = str
    binary_type = bytes
    string_types = (str,)
    unichr = chr
    def maybe_decode(x):
        return x.decode()
    def maybe_encode(x):
        return x.encode()
    def maybe_chr(x):
        return x
    def maybe_ord(x):
        return x
else:
    text_type = unicode  # pylint: disable=unicode-builtin, undefined-variable
    binary_type = str
    string_types = (
        basestring,  # pylint: disable=basestring-builtin, undefined-variable
    )
    unichr = unichr  # pylint: disable=unichr-builtin
    def maybe_decode(x):
        return x
    def maybe_encode(x):
        return x
    def maybe_chr(x):
        return chr(x)
    def maybe_ord(x):
        return ord(x)


def round_py2_compat(what):
    """
    Python 2 and Python 3 use different rounding strategies in round(). This
    function ensures that results are python2/3 compatible and backward
    compatible with previous py2 releases
    :param what: float
    :return: rounded long
    """
    d = Context(
        prec=len(str(long(what))),  # round to integer with max precision
        rounding=decimal.ROUND_HALF_UP
    ).create_decimal(str(what))  # str(): python 2.6 compat
    return long(d)
