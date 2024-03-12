from __future__ import absolute_import

import mock
import pytest

from urllib3 import HTTPConnectionPool
from urllib3.exceptions import EmptyPoolError
from urllib3.packages.six.moves import queue


class BadError(Exception):
    """
    This should not be raised.
    """

    pass


class TestMonkeypatchResistance(object):
    """
    Test that connection pool works even with a monkey patched Queue module,
    see obspy/obspy#1599, psf/requests#3742, urllib3/urllib3#1061.
    """

    def test_queue_monkeypatching(self):
        with mock.patch.object(queue, "Empty", BadError):
            with HTTPConnectionPool(host="localhost", block=True) as http:
                http._get_conn()
                with pytest.raises(EmptyPoolError):
                    http._get_conn(timeout=0)
