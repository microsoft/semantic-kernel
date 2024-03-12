import pytest

from urllib3.exceptions import MaxRetryError, NewConnectionError, ProxyError
from urllib3.poolmanager import ProxyManager
from urllib3.util.retry import Retry
from urllib3.util.url import parse_url

from .port_helpers import find_unused_port


class TestProxyManager(object):
    @pytest.mark.parametrize("proxy_scheme", ["http", "https"])
    def test_proxy_headers(self, proxy_scheme):
        url = "http://pypi.org/project/urllib3/"
        proxy_url = "{}://something:1234".format(proxy_scheme)
        with ProxyManager(proxy_url) as p:
            # Verify default headers
            default_headers = {"Accept": "*/*", "Host": "pypi.org"}
            headers = p._set_proxy_headers(url)

            assert headers == default_headers

            # Verify default headers don't overwrite provided headers
            provided_headers = {
                "Accept": "application/json",
                "custom": "header",
                "Host": "test.python.org",
            }
            headers = p._set_proxy_headers(url, provided_headers)

            assert headers == provided_headers

            # Verify proxy with nonstandard port
            provided_headers = {"Accept": "application/json"}
            expected_headers = provided_headers.copy()
            expected_headers.update({"Host": "pypi.org:8080"})
            url_with_port = "http://pypi.org:8080/project/urllib3/"
            headers = p._set_proxy_headers(url_with_port, provided_headers)

            assert headers == expected_headers

    def test_default_port(self):
        with ProxyManager("http://something") as p:
            assert p.proxy.port == 80
        with ProxyManager("https://something") as p:
            assert p.proxy.port == 443

    def test_invalid_scheme(self):
        with pytest.raises(AssertionError):
            ProxyManager("invalid://host/p")
        with pytest.raises(ValueError):
            ProxyManager("invalid://host/p")

    def test_proxy_tunnel(self):
        http_url = parse_url("http://example.com")
        https_url = parse_url("https://example.com")
        with ProxyManager("http://proxy:8080") as p:
            assert p._proxy_requires_url_absolute_form(http_url)
            assert p._proxy_requires_url_absolute_form(https_url) is False

        with ProxyManager("https://proxy:8080") as p:
            assert p._proxy_requires_url_absolute_form(http_url)
            assert p._proxy_requires_url_absolute_form(https_url) is False

        with ProxyManager("https://proxy:8080", use_forwarding_for_https=True) as p:
            assert p._proxy_requires_url_absolute_form(http_url)
            assert p._proxy_requires_url_absolute_form(https_url)

    def test_proxy_connect_retry(self):
        retry = Retry(total=None, connect=False)
        port = find_unused_port()
        with ProxyManager("http://localhost:{}".format(port)) as p:
            with pytest.raises(ProxyError) as ei:
                p.urlopen("HEAD", url="http://localhost/", retries=retry)
            assert isinstance(ei.value.original_error, NewConnectionError)

        retry = Retry(total=None, connect=2)
        with ProxyManager("http://localhost:{}".format(port)) as p:
            with pytest.raises(MaxRetryError) as ei:
                p.urlopen("HEAD", url="http://localhost/", retries=retry)
            assert isinstance(ei.value.reason.original_error, NewConnectionError)
