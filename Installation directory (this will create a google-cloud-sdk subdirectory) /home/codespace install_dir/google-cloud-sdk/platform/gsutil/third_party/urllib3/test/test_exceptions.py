import pickle

import pytest

from urllib3.connectionpool import HTTPConnectionPool
from urllib3.exceptions import (
    ClosedPoolError,
    ConnectTimeoutError,
    EmptyPoolError,
    HeaderParsingError,
    HostChangedError,
    HTTPError,
    LocationParseError,
    MaxRetryError,
    ReadTimeoutError,
)


class TestPickle(object):
    @pytest.mark.parametrize(
        "exception",
        [
            HTTPError(None),
            MaxRetryError(None, None, None),
            LocationParseError(None),
            ConnectTimeoutError(None),
            HTTPError("foo"),
            HTTPError("foo", IOError("foo")),
            MaxRetryError(HTTPConnectionPool("localhost"), "/", None),
            LocationParseError("fake location"),
            ClosedPoolError(HTTPConnectionPool("localhost"), None),
            EmptyPoolError(HTTPConnectionPool("localhost"), None),
            HostChangedError(HTTPConnectionPool("localhost"), "/", None),
            ReadTimeoutError(HTTPConnectionPool("localhost"), "/", None),
        ],
    )
    def test_exceptions(self, exception):
        result = pickle.loads(pickle.dumps(exception))
        assert isinstance(result, type(exception))


class TestFormat(object):
    def test_header_parsing_errors(self):
        hpe = HeaderParsingError("defects", "unparsed_data")

        assert "defects" in str(hpe)
        assert "unparsed_data" in str(hpe)
