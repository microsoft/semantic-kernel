import errno
import logging
import os
import platform
import socket
import ssl
import sys
import warnings

import pytest

try:
    try:
        import brotlicffi as brotli
    except ImportError:
        import brotli
except ImportError:
    brotli = None

from urllib3 import util
from urllib3.exceptions import HTTPWarning
from urllib3.packages import six
from urllib3.util import ssl_

try:
    import urllib3.contrib.pyopenssl as pyopenssl
except ImportError:
    pyopenssl = None

# We need a host that will not immediately close the connection with a TCP
# Reset.
if platform.system() == "Windows":
    # Reserved loopback subnet address
    TARPIT_HOST = "127.0.0.0"
else:
    # Reserved internet scoped address
    # https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml
    TARPIT_HOST = "240.0.0.0"

# (Arguments for socket, is it IPv6 address?)
VALID_SOURCE_ADDRESSES = [(("::1", 0), True), (("127.0.0.1", 0), False)]
# RFC 5737: 192.0.2.0/24 is for testing only.
# RFC 3849: 2001:db8::/32 is for documentation only.
INVALID_SOURCE_ADDRESSES = [("192.0.2.255", 0), ("2001:db8::1", 0)]

# We use timeouts in three different ways in our tests
#
# 1. To make sure that the operation timeouts, we can use a short timeout.
# 2. To make sure that the test does not hang even if the operation should succeed, we
#    want to use a long timeout, even more so on CI where tests can be really slow
# 3. To test our timeout logic by using two different values, eg. by using different
#    values at the pool level and at the request level.
SHORT_TIMEOUT = 0.001
LONG_TIMEOUT = 0.01
if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS") == "true":
    LONG_TIMEOUT = 0.5


def _can_resolve(host):
    """Returns True if the system can resolve host to an address."""
    try:
        socket.getaddrinfo(host, None, socket.AF_UNSPEC)
        return True
    except socket.gaierror:
        return False


def has_alpn(ctx_cls=None):
    """Detect if ALPN support is enabled."""
    ctx_cls = ctx_cls or util.SSLContext
    ctx = ctx_cls(protocol=ssl_.PROTOCOL_TLS)
    try:
        if hasattr(ctx, "set_alpn_protocols"):
            ctx.set_alpn_protocols(ssl_.ALPN_PROTOCOLS)
            return True
    except NotImplementedError:
        pass
    return False


# Some systems might not resolve "localhost." correctly.
# See https://github.com/urllib3/urllib3/issues/1809 and
# https://github.com/urllib3/urllib3/pull/1475#issuecomment-440788064.
RESOLVES_LOCALHOST_FQDN = _can_resolve("localhost.")


def clear_warnings(cls=HTTPWarning):
    new_filters = []
    for f in warnings.filters:
        if issubclass(f[2], cls):
            continue
        new_filters.append(f)
    warnings.filters[:] = new_filters


def setUp():
    clear_warnings()
    warnings.simplefilter("ignore", HTTPWarning)


def onlyPy279OrNewer(test):
    """Skips this test unless you are on Python 2.7.9 or later."""

    @six.wraps(test)
    def wrapper(*args, **kwargs):
        msg = "{name} requires Python 2.7.9+ to run".format(name=test.__name__)
        if sys.version_info < (2, 7, 9):
            pytest.skip(msg)
        return test(*args, **kwargs)

    return wrapper


def onlyPy2(test):
    """Skips this test unless you are on Python 2.x"""

    @six.wraps(test)
    def wrapper(*args, **kwargs):
        msg = "{name} requires Python 2.x to run".format(name=test.__name__)
        if not six.PY2:
            pytest.skip(msg)
        return test(*args, **kwargs)

    return wrapper


def onlyPy3(test):
    """Skips this test unless you are on Python3.x"""

    @six.wraps(test)
    def wrapper(*args, **kwargs):
        msg = "{name} requires Python3.x to run".format(name=test.__name__)
        if six.PY2:
            pytest.skip(msg)
        return test(*args, **kwargs)

    return wrapper


def notPyPy2(test):
    """Skips this test on PyPy2"""

    @six.wraps(test)
    def wrapper(*args, **kwargs):
        # https://github.com/testing-cabal/mock/issues/438
        msg = "{} fails with PyPy 2 dues to funcsigs bugs".format(test.__name__)
        if platform.python_implementation() == "PyPy" and sys.version_info[0] == 2:
            pytest.xfail(msg)
        return test(*args, **kwargs)

    return wrapper


def notWindows(test):
    """Skips this test on Windows"""

    @six.wraps(test)
    def wrapper(*args, **kwargs):
        msg = "{name} does not run on Windows".format(name=test.__name__)
        if platform.system() == "Windows":
            pytest.skip(msg)
        return test(*args, **kwargs)

    return wrapper


def onlyBrotlipy():
    return pytest.mark.skipif(brotli is None, reason="only run if brotlipy is present")


def notBrotlipy():
    return pytest.mark.skipif(
        brotli is not None, reason="only run if brotlipy is absent"
    )


def onlySecureTransport(test):
    """Runs this test when SecureTransport is in use."""

    @six.wraps(test)
    def wrapper(*args, **kwargs):
        msg = "{name} only runs with SecureTransport".format(name=test.__name__)
        if not ssl_.IS_SECURETRANSPORT:
            pytest.skip(msg)
        return test(*args, **kwargs)

    return wrapper


def notSecureTransport(test):
    """Skips this test when SecureTransport is in use."""

    @six.wraps(test)
    def wrapper(*args, **kwargs):
        msg = "{name} does not run with SecureTransport".format(name=test.__name__)
        if ssl_.IS_SECURETRANSPORT:
            pytest.skip(msg)
        return test(*args, **kwargs)

    return wrapper


def notOpenSSL098(test):
    """Skips this test for Python 3.5 macOS python.org distribution"""

    @six.wraps(test)
    def wrapper(*args, **kwargs):
        is_stdlib_ssl = not ssl_.IS_SECURETRANSPORT and not ssl_.IS_PYOPENSSL
        if is_stdlib_ssl and ssl.OPENSSL_VERSION == "OpenSSL 0.9.8zh 14 Jan 2016":
            pytest.xfail("{name} fails with OpenSSL 0.9.8zh".format(name=test.__name__))
        return test(*args, **kwargs)

    return wrapper


_requires_network_has_route = None


def requires_network(test):
    """Helps you skip tests that require the network"""

    def _is_unreachable_err(err):
        return getattr(err, "errno", None) in (
            errno.ENETUNREACH,
            errno.EHOSTUNREACH,  # For OSX
        )

    def _has_route():
        try:
            sock = socket.create_connection((TARPIT_HOST, 80), 0.0001)
            sock.close()
            return True
        except socket.timeout:
            return True
        except socket.error as e:
            if _is_unreachable_err(e):
                return False
            else:
                raise

    @six.wraps(test)
    def wrapper(*args, **kwargs):
        global _requires_network_has_route

        if _requires_network_has_route is None:
            _requires_network_has_route = _has_route()

        if _requires_network_has_route:
            return test(*args, **kwargs)
        else:
            msg = "Can't run {name} because the network is unreachable".format(
                name=test.__name__
            )
            pytest.skip(msg)

    return wrapper


def requires_ssl_context_keyfile_password(test):
    @six.wraps(test)
    def wrapper(*args, **kwargs):
        if (
            not ssl_.IS_PYOPENSSL and sys.version_info < (2, 7, 9)
        ) or ssl_.IS_SECURETRANSPORT:
            pytest.skip(
                "%s requires password parameter for "
                "SSLContext.load_cert_chain()" % test.__name__
            )
        return test(*args, **kwargs)

    return wrapper


def resolvesLocalhostFQDN(test):
    """Test requires successful resolving of 'localhost.'"""

    @six.wraps(test)
    def wrapper(*args, **kwargs):
        if not RESOLVES_LOCALHOST_FQDN:
            pytest.skip("Can't resolve localhost.")
        return test(*args, **kwargs)

    return wrapper


def withPyOpenSSL(test):
    @six.wraps(test)
    def wrapper(*args, **kwargs):
        if not pyopenssl:
            pytest.skip("pyopenssl not available, skipping test.")
            return test(*args, **kwargs)

        pyopenssl.inject_into_urllib3()
        result = test(*args, **kwargs)
        pyopenssl.extract_from_urllib3()
        return result

    return wrapper


class _ListHandler(logging.Handler):
    def __init__(self):
        super(_ListHandler, self).__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


class LogRecorder(object):
    def __init__(self, target=logging.root):
        super(LogRecorder, self).__init__()
        self._target = target
        self._handler = _ListHandler()

    @property
    def records(self):
        return self._handler.records

    def install(self):
        self._target.addHandler(self._handler)

    def uninstall(self):
        self._target.removeHandler(self._handler)

    def __enter__(self):
        self.install()
        return self.records

    def __exit__(self, exc_type, exc_value, traceback):
        self.uninstall()
        return False
