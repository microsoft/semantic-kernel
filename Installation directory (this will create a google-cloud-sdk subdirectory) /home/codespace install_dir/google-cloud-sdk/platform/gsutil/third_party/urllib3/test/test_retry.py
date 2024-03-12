import warnings

import mock
import pytest

from urllib3.exceptions import (
    ConnectTimeoutError,
    InvalidHeader,
    MaxRetryError,
    ReadTimeoutError,
    ResponseError,
    SSLError,
)
from urllib3.packages import six
from urllib3.packages.six.moves import xrange
from urllib3.response import HTTPResponse
from urllib3.util.retry import RequestHistory, Retry


@pytest.fixture(scope="function", autouse=True)
def no_retry_deprecations():
    with warnings.catch_warnings(record=True) as w:
        yield
    assert len([str(x.message) for x in w if "Retry" in str(x.message)]) == 0


class TestRetry(object):
    def test_string(self):
        """Retry string representation looks the way we expect"""
        retry = Retry()
        assert (
            str(retry)
            == "Retry(total=10, connect=None, read=None, redirect=None, status=None)"
        )
        for _ in range(3):
            retry = retry.increment(method="GET")
        assert (
            str(retry)
            == "Retry(total=7, connect=None, read=None, redirect=None, status=None)"
        )

    def test_retry_both_specified(self):
        """Total can win if it's lower than the connect value"""
        error = ConnectTimeoutError()
        retry = Retry(connect=3, total=2)
        retry = retry.increment(error=error)
        retry = retry.increment(error=error)
        with pytest.raises(MaxRetryError) as e:
            retry.increment(error=error)
        assert e.value.reason == error

    def test_retry_higher_total_loses(self):
        """A lower connect timeout than the total is honored"""
        error = ConnectTimeoutError()
        retry = Retry(connect=2, total=3)
        retry = retry.increment(error=error)
        retry = retry.increment(error=error)
        with pytest.raises(MaxRetryError):
            retry.increment(error=error)

    def test_retry_higher_total_loses_vs_read(self):
        """A lower read timeout than the total is honored"""
        error = ReadTimeoutError(None, "/", "read timed out")
        retry = Retry(read=2, total=3)
        retry = retry.increment(method="GET", error=error)
        retry = retry.increment(method="GET", error=error)
        with pytest.raises(MaxRetryError):
            retry.increment(method="GET", error=error)

    def test_retry_total_none(self):
        """if Total is none, connect error should take precedence"""
        error = ConnectTimeoutError()
        retry = Retry(connect=2, total=None)
        retry = retry.increment(error=error)
        retry = retry.increment(error=error)
        with pytest.raises(MaxRetryError) as e:
            retry.increment(error=error)
        assert e.value.reason == error

        error = ReadTimeoutError(None, "/", "read timed out")
        retry = Retry(connect=2, total=None)
        retry = retry.increment(method="GET", error=error)
        retry = retry.increment(method="GET", error=error)
        retry = retry.increment(method="GET", error=error)
        assert not retry.is_exhausted()

    def test_retry_default(self):
        """If no value is specified, should retry connects 3 times"""
        retry = Retry()
        assert retry.total == 10
        assert retry.connect is None
        assert retry.read is None
        assert retry.redirect is None
        assert retry.other is None

        error = ConnectTimeoutError()
        retry = Retry(connect=1)
        retry = retry.increment(error=error)
        with pytest.raises(MaxRetryError):
            retry.increment(error=error)

        retry = Retry(connect=1)
        retry = retry.increment(error=error)
        assert not retry.is_exhausted()

        assert Retry(0).raise_on_redirect
        assert not Retry(False).raise_on_redirect

    def test_retry_other(self):
        """If an unexpected error is raised, should retry other times"""
        other_error = SSLError()
        retry = Retry(connect=1)
        retry = retry.increment(error=other_error)
        retry = retry.increment(error=other_error)
        assert not retry.is_exhausted()

        retry = Retry(other=1)
        retry = retry.increment(error=other_error)
        with pytest.raises(MaxRetryError) as e:
            retry.increment(error=other_error)
        assert e.value.reason == other_error

    def test_retry_read_zero(self):
        """No second chances on read timeouts, by default"""
        error = ReadTimeoutError(None, "/", "read timed out")
        retry = Retry(read=0)
        with pytest.raises(MaxRetryError) as e:
            retry.increment(method="GET", error=error)
        assert e.value.reason == error

    def test_status_counter(self):
        resp = HTTPResponse(status=400)
        retry = Retry(status=2)
        retry = retry.increment(response=resp)
        retry = retry.increment(response=resp)
        with pytest.raises(MaxRetryError) as e:
            retry.increment(response=resp)
        assert str(e.value.reason) == ResponseError.SPECIFIC_ERROR.format(
            status_code=400
        )

    def test_backoff(self):
        """Backoff is computed correctly"""
        max_backoff = Retry.DEFAULT_BACKOFF_MAX

        retry = Retry(total=100, backoff_factor=0.2)
        assert retry.get_backoff_time() == 0  # First request

        retry = retry.increment(method="GET")
        assert retry.get_backoff_time() == 0  # First retry

        retry = retry.increment(method="GET")
        assert retry.backoff_factor == 0.2
        assert retry.total == 98
        assert retry.get_backoff_time() == 0.4  # Start backoff

        retry = retry.increment(method="GET")
        assert retry.get_backoff_time() == 0.8

        retry = retry.increment(method="GET")
        assert retry.get_backoff_time() == 1.6

        for _ in xrange(10):
            retry = retry.increment(method="GET")

        assert retry.get_backoff_time() == max_backoff

    def test_zero_backoff(self):
        retry = Retry()
        assert retry.get_backoff_time() == 0
        retry = retry.increment(method="GET")
        retry = retry.increment(method="GET")
        assert retry.get_backoff_time() == 0

    def test_backoff_reset_after_redirect(self):
        retry = Retry(total=100, redirect=5, backoff_factor=0.2)
        retry = retry.increment(method="GET")
        retry = retry.increment(method="GET")
        assert retry.get_backoff_time() == 0.4
        redirect_response = HTTPResponse(status=302, headers={"location": "test"})
        retry = retry.increment(method="GET", response=redirect_response)
        assert retry.get_backoff_time() == 0
        retry = retry.increment(method="GET")
        retry = retry.increment(method="GET")
        assert retry.get_backoff_time() == 0.4

    def test_sleep(self):
        # sleep a very small amount of time so our code coverage is happy
        retry = Retry(backoff_factor=0.0001)
        retry = retry.increment(method="GET")
        retry = retry.increment(method="GET")
        retry.sleep()

    def test_status_forcelist(self):
        retry = Retry(status_forcelist=xrange(500, 600))
        assert not retry.is_retry("GET", status_code=200)
        assert not retry.is_retry("GET", status_code=400)
        assert retry.is_retry("GET", status_code=500)

        retry = Retry(total=1, status_forcelist=[418])
        assert not retry.is_retry("GET", status_code=400)
        assert retry.is_retry("GET", status_code=418)

        # String status codes are not matched.
        retry = Retry(total=1, status_forcelist=["418"])
        assert not retry.is_retry("GET", status_code=418)

    def test_allowed_methods_with_status_forcelist(self):
        # Falsey allowed_methods means to retry on any method.
        retry = Retry(status_forcelist=[500], allowed_methods=None)
        assert retry.is_retry("GET", status_code=500)
        assert retry.is_retry("POST", status_code=500)

        # Criteria of allowed_methods and status_forcelist are ANDed.
        retry = Retry(status_forcelist=[500], allowed_methods=["POST"])
        assert not retry.is_retry("GET", status_code=500)
        assert retry.is_retry("POST", status_code=500)

    def test_exhausted(self):
        assert not Retry(0).is_exhausted()
        assert Retry(-1).is_exhausted()
        assert Retry(1).increment(method="GET").total == 0

    @pytest.mark.parametrize("total", [-1, 0])
    def test_disabled(self, total):
        with pytest.raises(MaxRetryError):
            Retry(total).increment(method="GET")

    def test_error_message(self):
        retry = Retry(total=0)
        with pytest.raises(MaxRetryError) as e:
            retry = retry.increment(
                method="GET", error=ReadTimeoutError(None, "/", "read timed out")
            )
        assert "Caused by redirect" not in str(e.value)
        assert str(e.value.reason) == "None: read timed out"

        retry = Retry(total=1)
        with pytest.raises(MaxRetryError) as e:
            retry = retry.increment("POST", "/")
            retry = retry.increment("POST", "/")
        assert "Caused by redirect" not in str(e.value)
        assert isinstance(e.value.reason, ResponseError)
        assert str(e.value.reason) == ResponseError.GENERIC_ERROR

        retry = Retry(total=1)
        response = HTTPResponse(status=500)
        with pytest.raises(MaxRetryError) as e:
            retry = retry.increment("POST", "/", response=response)
            retry = retry.increment("POST", "/", response=response)
        assert "Caused by redirect" not in str(e.value)
        msg = ResponseError.SPECIFIC_ERROR.format(status_code=500)
        assert str(e.value.reason) == msg

        retry = Retry(connect=1)
        with pytest.raises(MaxRetryError) as e:
            retry = retry.increment(error=ConnectTimeoutError("conntimeout"))
            retry = retry.increment(error=ConnectTimeoutError("conntimeout"))
        assert "Caused by redirect" not in str(e.value)
        assert str(e.value.reason) == "conntimeout"

    def test_history(self):
        retry = Retry(total=10, allowed_methods=frozenset(["GET", "POST"]))
        assert retry.history == tuple()
        connection_error = ConnectTimeoutError("conntimeout")
        retry = retry.increment("GET", "/test1", None, connection_error)
        history = (RequestHistory("GET", "/test1", connection_error, None, None),)
        assert retry.history == history

        read_error = ReadTimeoutError(None, "/test2", "read timed out")
        retry = retry.increment("POST", "/test2", None, read_error)
        history = (
            RequestHistory("GET", "/test1", connection_error, None, None),
            RequestHistory("POST", "/test2", read_error, None, None),
        )
        assert retry.history == history

        response = HTTPResponse(status=500)
        retry = retry.increment("GET", "/test3", response, None)
        history = (
            RequestHistory("GET", "/test1", connection_error, None, None),
            RequestHistory("POST", "/test2", read_error, None, None),
            RequestHistory("GET", "/test3", None, 500, None),
        )
        assert retry.history == history

    def test_retry_method_not_in_whitelist(self):
        error = ReadTimeoutError(None, "/", "read timed out")
        retry = Retry()
        with pytest.raises(ReadTimeoutError):
            retry.increment(method="POST", error=error)

    def test_retry_default_remove_headers_on_redirect(self):
        retry = Retry()

        assert list(retry.remove_headers_on_redirect) == ["authorization"]

    def test_retry_set_remove_headers_on_redirect(self):
        retry = Retry(remove_headers_on_redirect=["X-API-Secret"])

        assert list(retry.remove_headers_on_redirect) == ["x-api-secret"]

    @pytest.mark.parametrize("value", ["-1", "+1", "1.0", six.u("\xb2")])  # \xb2 = ^2
    def test_parse_retry_after_invalid(self, value):
        retry = Retry()
        with pytest.raises(InvalidHeader):
            retry.parse_retry_after(value)

    @pytest.mark.parametrize(
        "value, expected", [("0", 0), ("1000", 1000), ("\t42 ", 42)]
    )
    def test_parse_retry_after(self, value, expected):
        retry = Retry()
        assert retry.parse_retry_after(value) == expected

    @pytest.mark.parametrize("respect_retry_after_header", [True, False])
    def test_respect_retry_after_header_propagated(self, respect_retry_after_header):

        retry = Retry(respect_retry_after_header=respect_retry_after_header)
        new_retry = retry.new()
        assert new_retry.respect_retry_after_header == respect_retry_after_header

    @pytest.mark.freeze_time("2019-06-03 11:00:00", tz_offset=0)
    @pytest.mark.parametrize(
        "retry_after_header,respect_retry_after_header,sleep_duration",
        [
            ("3600", True, 3600),
            ("3600", False, None),
            # Will sleep due to header is 1 hour in future
            ("Mon, 3 Jun 2019 12:00:00 UTC", True, 3600),
            # Won't sleep due to not respecting header
            ("Mon, 3 Jun 2019 12:00:00 UTC", False, None),
            # Won't sleep due to current time reached
            ("Mon, 3 Jun 2019 11:00:00 UTC", True, None),
            # Won't sleep due to current time reached + not respecting header
            ("Mon, 3 Jun 2019 11:00:00 UTC", False, None),
            # Handle all the formats in RFC 7231 Section 7.1.1.1
            ("Mon, 03 Jun 2019 11:30:12 GMT", True, 1812),
            ("Monday, 03-Jun-19 11:30:12 GMT", True, 1812),
            # Assume that datetimes without a timezone are in UTC per RFC 7231
            ("Mon Jun  3 11:30:12 2019", True, 1812),
        ],
    )
    @pytest.mark.parametrize(
        "stub_timezone",
        [
            "UTC",
            "Asia/Jerusalem",
            None,
        ],
        indirect=True,
    )
    @pytest.mark.usefixtures("stub_timezone")
    def test_respect_retry_after_header_sleep(
        self, retry_after_header, respect_retry_after_header, sleep_duration
    ):
        retry = Retry(respect_retry_after_header=respect_retry_after_header)

        with mock.patch("time.sleep") as sleep_mock:
            # for the default behavior, it must be in RETRY_AFTER_STATUS_CODES
            response = HTTPResponse(
                status=503, headers={"Retry-After": retry_after_header}
            )

            retry.sleep(response)

            # The expected behavior is that we'll only sleep if respecting
            # this header (since we won't have any backoff sleep attempts)
            if respect_retry_after_header and sleep_duration is not None:
                sleep_mock.assert_called_with(sleep_duration)
            else:
                sleep_mock.assert_not_called()
