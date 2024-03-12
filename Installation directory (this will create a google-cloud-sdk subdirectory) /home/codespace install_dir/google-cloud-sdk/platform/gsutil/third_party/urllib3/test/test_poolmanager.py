import socket
from test import resolvesLocalhostFQDN

import pytest

from urllib3 import connection_from_url
from urllib3.exceptions import ClosedPoolError, LocationValueError
from urllib3.poolmanager import PoolKey, PoolManager, key_fn_by_scheme
from urllib3.util import retry, timeout


class TestPoolManager(object):
    @resolvesLocalhostFQDN
    def test_same_url(self):
        # Convince ourselves that normally we don't get the same object
        conn1 = connection_from_url("http://localhost:8081/foo")
        conn2 = connection_from_url("http://localhost:8081/bar")

        assert conn1 != conn2

        # Now try again using the PoolManager
        p = PoolManager(1)

        conn1 = p.connection_from_url("http://localhost:8081/foo")
        conn2 = p.connection_from_url("http://localhost:8081/bar")

        assert conn1 == conn2

        # Ensure that FQDNs are handled separately from relative domains
        p = PoolManager(2)

        conn1 = p.connection_from_url("http://localhost.:8081/foo")
        conn2 = p.connection_from_url("http://localhost:8081/bar")

        assert conn1 != conn2

    def test_many_urls(self):
        urls = [
            "http://localhost:8081/foo",
            "http://www.google.com/mail",
            "http://localhost:8081/bar",
            "https://www.google.com/",
            "https://www.google.com/mail",
            "http://yahoo.com",
            "http://bing.com",
            "http://yahoo.com/",
        ]

        connections = set()

        p = PoolManager(10)

        for url in urls:
            conn = p.connection_from_url(url)
            connections.add(conn)

        assert len(connections) == 5

    def test_manager_clear(self):
        p = PoolManager(5)

        conn_pool = p.connection_from_url("http://google.com")
        assert len(p.pools) == 1

        conn = conn_pool._get_conn()

        p.clear()
        assert len(p.pools) == 0

        with pytest.raises(ClosedPoolError):
            conn_pool._get_conn()

        conn_pool._put_conn(conn)

        with pytest.raises(ClosedPoolError):
            conn_pool._get_conn()

        assert len(p.pools) == 0

    @pytest.mark.parametrize("url", ["http://@", None])
    def test_nohost(self, url):
        p = PoolManager(5)
        with pytest.raises(LocationValueError):
            p.connection_from_url(url=url)

    def test_contextmanager(self):
        with PoolManager(1) as p:
            conn_pool = p.connection_from_url("http://google.com")
            assert len(p.pools) == 1
            conn = conn_pool._get_conn()

        assert len(p.pools) == 0

        with pytest.raises(ClosedPoolError):
            conn_pool._get_conn()

        conn_pool._put_conn(conn)

        with pytest.raises(ClosedPoolError):
            conn_pool._get_conn()

        assert len(p.pools) == 0

    def test_http_pool_key_fields(self):
        """Assert the HTTPPoolKey fields are honored when selecting a pool."""
        connection_pool_kw = {
            "timeout": timeout.Timeout(3.14),
            "retries": retry.Retry(total=6, connect=2),
            "block": True,
            "strict": True,
            "source_address": "127.0.0.1",
        }
        p = PoolManager()
        conn_pools = [
            p.connection_from_url("http://example.com/"),
            p.connection_from_url("http://example.com:8000/"),
            p.connection_from_url("http://other.example.com/"),
        ]

        for key, value in connection_pool_kw.items():
            p.connection_pool_kw[key] = value
            conn_pools.append(p.connection_from_url("http://example.com/"))

        assert all(
            x is not y
            for i, x in enumerate(conn_pools)
            for j, y in enumerate(conn_pools)
            if i != j
        )
        assert all(isinstance(key, PoolKey) for key in p.pools.keys())

    def test_https_pool_key_fields(self):
        """Assert the HTTPSPoolKey fields are honored when selecting a pool."""
        connection_pool_kw = {
            "timeout": timeout.Timeout(3.14),
            "retries": retry.Retry(total=6, connect=2),
            "block": True,
            "strict": True,
            "source_address": "127.0.0.1",
            "key_file": "/root/totally_legit.key",
            "cert_file": "/root/totally_legit.crt",
            "cert_reqs": "CERT_REQUIRED",
            "ca_certs": "/root/path_to_pem",
            "ssl_version": "SSLv23_METHOD",
        }
        p = PoolManager()
        conn_pools = [
            p.connection_from_url("https://example.com/"),
            p.connection_from_url("https://example.com:4333/"),
            p.connection_from_url("https://other.example.com/"),
        ]
        # Asking for a connection pool with the same key should give us an
        # existing pool.
        dup_pools = []

        for key, value in connection_pool_kw.items():
            p.connection_pool_kw[key] = value
            conn_pools.append(p.connection_from_url("https://example.com/"))
            dup_pools.append(p.connection_from_url("https://example.com/"))

        assert all(
            x is not y
            for i, x in enumerate(conn_pools)
            for j, y in enumerate(conn_pools)
            if i != j
        )
        assert all(pool in conn_pools for pool in dup_pools)
        assert all(isinstance(key, PoolKey) for key in p.pools.keys())

    def test_default_pool_key_funcs_copy(self):
        """Assert each PoolManager gets a copy of ``pool_keys_by_scheme``."""
        p = PoolManager()
        assert p.key_fn_by_scheme == p.key_fn_by_scheme
        assert p.key_fn_by_scheme is not key_fn_by_scheme

    def test_pools_keyed_with_from_host(self):
        """Assert pools are still keyed correctly with connection_from_host."""
        ssl_kw = {
            "key_file": "/root/totally_legit.key",
            "cert_file": "/root/totally_legit.crt",
            "cert_reqs": "CERT_REQUIRED",
            "ca_certs": "/root/path_to_pem",
            "ssl_version": "SSLv23_METHOD",
        }
        p = PoolManager(5, **ssl_kw)
        conns = [p.connection_from_host("example.com", 443, scheme="https")]

        for k in ssl_kw:
            p.connection_pool_kw[k] = "newval"
            conns.append(p.connection_from_host("example.com", 443, scheme="https"))

        assert all(
            x is not y
            for i, x in enumerate(conns)
            for j, y in enumerate(conns)
            if i != j
        )

    def test_https_connection_from_url_case_insensitive(self):
        """Assert scheme case is ignored when pooling HTTPS connections."""
        p = PoolManager()
        pool = p.connection_from_url("https://example.com/")
        other_pool = p.connection_from_url("HTTPS://EXAMPLE.COM/")

        assert 1 == len(p.pools)
        assert pool is other_pool
        assert all(isinstance(key, PoolKey) for key in p.pools.keys())

    def test_https_connection_from_host_case_insensitive(self):
        """Assert scheme case is ignored when getting the https key class."""
        p = PoolManager()
        pool = p.connection_from_host("example.com", scheme="https")
        other_pool = p.connection_from_host("EXAMPLE.COM", scheme="HTTPS")

        assert 1 == len(p.pools)
        assert pool is other_pool
        assert all(isinstance(key, PoolKey) for key in p.pools.keys())

    def test_https_connection_from_context_case_insensitive(self):
        """Assert scheme case is ignored when getting the https key class."""
        p = PoolManager()
        context = {"scheme": "https", "host": "example.com", "port": "443"}
        other_context = {"scheme": "HTTPS", "host": "EXAMPLE.COM", "port": "443"}
        pool = p.connection_from_context(context)
        other_pool = p.connection_from_context(other_context)

        assert 1 == len(p.pools)
        assert pool is other_pool
        assert all(isinstance(key, PoolKey) for key in p.pools.keys())

    def test_http_connection_from_url_case_insensitive(self):
        """Assert scheme case is ignored when pooling HTTP connections."""
        p = PoolManager()
        pool = p.connection_from_url("http://example.com/")
        other_pool = p.connection_from_url("HTTP://EXAMPLE.COM/")

        assert 1 == len(p.pools)
        assert pool is other_pool
        assert all(isinstance(key, PoolKey) for key in p.pools.keys())

    def test_http_connection_from_host_case_insensitive(self):
        """Assert scheme case is ignored when getting the https key class."""
        p = PoolManager()
        pool = p.connection_from_host("example.com", scheme="http")
        other_pool = p.connection_from_host("EXAMPLE.COM", scheme="HTTP")

        assert 1 == len(p.pools)
        assert pool is other_pool
        assert all(isinstance(key, PoolKey) for key in p.pools.keys())

    def test_assert_hostname_and_fingerprint_flag(self):
        """Assert that pool manager can accept hostname and fingerprint flags."""
        fingerprint = "92:81:FE:85:F7:0C:26:60:EC:D6:B3:BF:93:CF:F9:71:CC:07:7D:0A"
        p = PoolManager(assert_hostname=True, assert_fingerprint=fingerprint)
        pool = p.connection_from_url("https://example.com/")
        assert 1 == len(p.pools)
        assert pool.assert_hostname
        assert fingerprint == pool.assert_fingerprint

    def test_http_connection_from_context_case_insensitive(self):
        """Assert scheme case is ignored when getting the https key class."""
        p = PoolManager()
        context = {"scheme": "http", "host": "example.com", "port": "8080"}
        other_context = {"scheme": "HTTP", "host": "EXAMPLE.COM", "port": "8080"}
        pool = p.connection_from_context(context)
        other_pool = p.connection_from_context(other_context)

        assert 1 == len(p.pools)
        assert pool is other_pool
        assert all(isinstance(key, PoolKey) for key in p.pools.keys())

    def test_custom_pool_key(self):
        """Assert it is possible to define a custom key function."""
        p = PoolManager(10)

        p.key_fn_by_scheme["http"] = lambda x: tuple(x["key"])
        pool1 = p.connection_from_url(
            "http://example.com", pool_kwargs={"key": "value"}
        )
        pool2 = p.connection_from_url(
            "http://example.com", pool_kwargs={"key": "other"}
        )
        pool3 = p.connection_from_url(
            "http://example.com", pool_kwargs={"key": "value", "x": "y"}
        )

        assert 2 == len(p.pools)
        assert pool1 is pool3
        assert pool1 is not pool2

    def test_override_pool_kwargs_url(self):
        """Assert overriding pool kwargs works with connection_from_url."""
        p = PoolManager(strict=True)
        pool_kwargs = {"strict": False, "retries": 100, "block": True}

        default_pool = p.connection_from_url("http://example.com/")
        override_pool = p.connection_from_url(
            "http://example.com/", pool_kwargs=pool_kwargs
        )

        assert default_pool.strict
        assert retry.Retry.DEFAULT == default_pool.retries
        assert not default_pool.block

        assert not override_pool.strict
        assert 100 == override_pool.retries
        assert override_pool.block

    def test_override_pool_kwargs_host(self):
        """Assert overriding pool kwargs works with connection_from_host"""
        p = PoolManager(strict=True)
        pool_kwargs = {"strict": False, "retries": 100, "block": True}

        default_pool = p.connection_from_host("example.com", scheme="http")
        override_pool = p.connection_from_host(
            "example.com", scheme="http", pool_kwargs=pool_kwargs
        )

        assert default_pool.strict
        assert retry.Retry.DEFAULT == default_pool.retries
        assert not default_pool.block

        assert not override_pool.strict
        assert 100 == override_pool.retries
        assert override_pool.block

    def test_pool_kwargs_socket_options(self):
        """Assert passing socket options works with connection_from_host"""
        p = PoolManager(socket_options=[])
        override_opts = [
            (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1),
            (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
        ]
        pool_kwargs = {"socket_options": override_opts}

        default_pool = p.connection_from_host("example.com", scheme="http")
        override_pool = p.connection_from_host(
            "example.com", scheme="http", pool_kwargs=pool_kwargs
        )

        assert default_pool.conn_kw["socket_options"] == []
        assert override_pool.conn_kw["socket_options"] == override_opts

    def test_merge_pool_kwargs(self):
        """Assert _merge_pool_kwargs works in the happy case"""
        p = PoolManager(strict=True)
        merged = p._merge_pool_kwargs({"new_key": "value"})
        assert {"strict": True, "new_key": "value"} == merged

    def test_merge_pool_kwargs_none(self):
        """Assert false-y values to _merge_pool_kwargs result in defaults"""
        p = PoolManager(strict=True)
        merged = p._merge_pool_kwargs({})
        assert p.connection_pool_kw == merged
        merged = p._merge_pool_kwargs(None)
        assert p.connection_pool_kw == merged

    def test_merge_pool_kwargs_remove_key(self):
        """Assert keys can be removed with _merge_pool_kwargs"""
        p = PoolManager(strict=True)
        merged = p._merge_pool_kwargs({"strict": None})
        assert "strict" not in merged

    def test_merge_pool_kwargs_invalid_key(self):
        """Assert removing invalid keys with _merge_pool_kwargs doesn't break"""
        p = PoolManager(strict=True)
        merged = p._merge_pool_kwargs({"invalid_key": None})
        assert p.connection_pool_kw == merged

    def test_pool_manager_no_url_absolute_form(self):
        """Valides we won't send a request with absolute form without a proxy"""
        p = PoolManager(strict=True)
        assert p._proxy_requires_url_absolute_form("http://example.com") is False
        assert p._proxy_requires_url_absolute_form("https://example.com") is False
