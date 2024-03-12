import datetime
import json
import logging
import os.path
import shutil
import ssl
import sys
import tempfile
import warnings
from test import (
    LONG_TIMEOUT,
    SHORT_TIMEOUT,
    TARPIT_HOST,
    notOpenSSL098,
    notSecureTransport,
    onlyPy279OrNewer,
    requires_network,
    requires_ssl_context_keyfile_password,
    resolvesLocalhostFQDN,
)

import mock
import pytest
import trustme

import urllib3.util as util
from dummyserver.server import (
    DEFAULT_CA,
    DEFAULT_CA_KEY,
    DEFAULT_CERTS,
    encrypt_key_pem,
)
from dummyserver.testcase import HTTPSDummyServerTestCase
from urllib3 import HTTPSConnectionPool
from urllib3.connection import RECENT_DATE, VerifiedHTTPSConnection
from urllib3.exceptions import (
    ConnectTimeoutError,
    InsecurePlatformWarning,
    InsecureRequestWarning,
    MaxRetryError,
    ProtocolError,
    SSLError,
    SystemTimeWarning,
)
from urllib3.packages import six
from urllib3.util.timeout import Timeout

from .. import has_alpn

# Retry failed tests
pytestmark = pytest.mark.flaky

ResourceWarning = getattr(
    six.moves.builtins, "ResourceWarning", type("ResourceWarning", (), {})
)


log = logging.getLogger("urllib3.connectionpool")
log.setLevel(logging.NOTSET)
log.addHandler(logging.StreamHandler(sys.stdout))


TLSv1_CERTS = DEFAULT_CERTS.copy()
TLSv1_CERTS["ssl_version"] = getattr(ssl, "PROTOCOL_TLSv1", None)

TLSv1_1_CERTS = DEFAULT_CERTS.copy()
TLSv1_1_CERTS["ssl_version"] = getattr(ssl, "PROTOCOL_TLSv1_1", None)

TLSv1_2_CERTS = DEFAULT_CERTS.copy()
TLSv1_2_CERTS["ssl_version"] = getattr(ssl, "PROTOCOL_TLSv1_2", None)

TLSv1_3_CERTS = DEFAULT_CERTS.copy()
TLSv1_3_CERTS["ssl_version"] = getattr(ssl, "PROTOCOL_TLS", None)


CLIENT_INTERMEDIATE_PEM = "client_intermediate.pem"
CLIENT_NO_INTERMEDIATE_PEM = "client_no_intermediate.pem"
CLIENT_INTERMEDIATE_KEY = "client_intermediate.key"
PASSWORD_CLIENT_KEYFILE = "client_password.key"
CLIENT_CERT = CLIENT_INTERMEDIATE_PEM


class TestHTTPS(HTTPSDummyServerTestCase):
    tls_protocol_name = None

    def tls_protocol_deprecated(self):
        return self.tls_protocol_name in {"TLSv1", "TLSv1.1"}

    @classmethod
    def setup_class(cls):
        super(TestHTTPS, cls).setup_class()

        cls.certs_dir = tempfile.mkdtemp()
        # Start from existing root CA as we don't want to change the server certificate yet
        with open(DEFAULT_CA, "rb") as crt, open(DEFAULT_CA_KEY, "rb") as key:
            root_ca = trustme.CA.from_pem(crt.read(), key.read())

        # Generate another CA to test verification failure
        bad_ca = trustme.CA()
        cls.bad_ca_path = os.path.join(cls.certs_dir, "ca_bad.pem")
        bad_ca.cert_pem.write_to_path(cls.bad_ca_path)

        # client cert chain
        intermediate_ca = root_ca.create_child_ca()
        cert = intermediate_ca.issue_cert(u"example.com")
        encrypted_key = encrypt_key_pem(cert.private_key_pem, b"letmein")

        cert.private_key_pem.write_to_path(
            os.path.join(cls.certs_dir, CLIENT_INTERMEDIATE_KEY)
        )
        encrypted_key.write_to_path(
            os.path.join(cls.certs_dir, PASSWORD_CLIENT_KEYFILE)
        )
        # Write the client cert and the intermediate CA
        client_cert = os.path.join(cls.certs_dir, CLIENT_INTERMEDIATE_PEM)
        cert.cert_chain_pems[0].write_to_path(client_cert)
        cert.cert_chain_pems[1].write_to_path(client_cert, append=True)
        # Write only the client cert
        cert.cert_chain_pems[0].write_to_path(
            os.path.join(cls.certs_dir, CLIENT_NO_INTERMEDIATE_PEM)
        )

    @classmethod
    def teardown_class(cls):
        super(TestHTTPS, cls).teardown_class()

        shutil.rmtree(cls.certs_dir)

    def test_simple(self):
        with HTTPSConnectionPool(
            self.host, self.port, ca_certs=DEFAULT_CA
        ) as https_pool:
            r = https_pool.request("GET", "/")
            assert r.status == 200, r.data

    @resolvesLocalhostFQDN
    def test_dotted_fqdn(self):
        with HTTPSConnectionPool(
            self.host + ".", self.port, ca_certs=DEFAULT_CA
        ) as pool:
            r = pool.request("GET", "/")
            assert r.status == 200, r.data

    def test_client_intermediate(self):
        """Check that certificate chains work well with client certs

        We generate an intermediate CA from the root CA, and issue a client certificate
        from that intermediate CA. Since the server only knows about the root CA, we
        need to send it the certificate *and* the intermediate CA, so that it can check
        the whole chain.
        """
        with HTTPSConnectionPool(
            self.host,
            self.port,
            key_file=os.path.join(self.certs_dir, CLIENT_INTERMEDIATE_KEY),
            cert_file=os.path.join(self.certs_dir, CLIENT_INTERMEDIATE_PEM),
            ca_certs=DEFAULT_CA,
        ) as https_pool:
            r = https_pool.request("GET", "/certificate")
            subject = json.loads(r.data.decode("utf-8"))
            assert subject["organizationalUnitName"].startswith("Testing cert")

    def test_client_no_intermediate(self):
        """Check that missing links in certificate chains indeed break

        The only difference with test_client_intermediate is that we don't send the
        intermediate CA to the server, only the client cert.
        """
        with HTTPSConnectionPool(
            self.host,
            self.port,
            cert_file=os.path.join(self.certs_dir, CLIENT_NO_INTERMEDIATE_PEM),
            key_file=os.path.join(self.certs_dir, CLIENT_INTERMEDIATE_KEY),
            ca_certs=DEFAULT_CA,
        ) as https_pool:
            with pytest.raises((SSLError, ProtocolError)):
                https_pool.request("GET", "/certificate", retries=False)

    @requires_ssl_context_keyfile_password
    def test_client_key_password(self):
        with HTTPSConnectionPool(
            self.host,
            self.port,
            ca_certs=DEFAULT_CA,
            key_file=os.path.join(self.certs_dir, PASSWORD_CLIENT_KEYFILE),
            cert_file=os.path.join(self.certs_dir, CLIENT_CERT),
            key_password="letmein",
        ) as https_pool:
            r = https_pool.request("GET", "/certificate")
            subject = json.loads(r.data.decode("utf-8"))
            assert subject["organizationalUnitName"].startswith("Testing cert")

    @requires_ssl_context_keyfile_password
    def test_client_encrypted_key_requires_password(self):
        with HTTPSConnectionPool(
            self.host,
            self.port,
            key_file=os.path.join(self.certs_dir, PASSWORD_CLIENT_KEYFILE),
            cert_file=os.path.join(self.certs_dir, CLIENT_CERT),
            key_password=None,
        ) as https_pool:
            with pytest.raises(MaxRetryError) as e:
                https_pool.request("GET", "/certificate")

            assert "password is required" in str(e.value)
            assert isinstance(e.value.reason, SSLError)

    def test_verified(self):
        with HTTPSConnectionPool(
            self.host, self.port, cert_reqs="CERT_REQUIRED", ca_certs=DEFAULT_CA
        ) as https_pool:
            conn = https_pool._new_conn()
            assert conn.__class__ == VerifiedHTTPSConnection

            with warnings.catch_warnings(record=True) as w:
                r = https_pool.request("GET", "/")
                assert r.status == 200

            # If we're using a deprecated TLS version we can remove 'DeprecationWarning'
            if self.tls_protocol_deprecated():
                w = [x for x in w if x.category != DeprecationWarning]

            # Modern versions of Python, or systems using PyOpenSSL, don't
            # emit warnings.
            if (
                sys.version_info >= (2, 7, 9)
                or util.IS_PYOPENSSL
                or util.IS_SECURETRANSPORT
            ):
                assert w == []
            else:
                assert len(w) > 1
                assert any(x.category == InsecureRequestWarning for x in w)

    def test_verified_with_context(self):
        ctx = util.ssl_.create_urllib3_context(cert_reqs=ssl.CERT_REQUIRED)
        ctx.load_verify_locations(cafile=DEFAULT_CA)
        with HTTPSConnectionPool(self.host, self.port, ssl_context=ctx) as https_pool:
            conn = https_pool._new_conn()
            assert conn.__class__ == VerifiedHTTPSConnection

            with mock.patch("warnings.warn") as warn:
                r = https_pool.request("GET", "/")
                assert r.status == 200

                # Modern versions of Python, or systems using PyOpenSSL, don't
                # emit warnings.
                if (
                    sys.version_info >= (2, 7, 9)
                    or util.IS_PYOPENSSL
                    or util.IS_SECURETRANSPORT
                ):
                    assert not warn.called, warn.call_args_list
                else:
                    assert warn.called
                    if util.HAS_SNI:
                        call = warn.call_args_list[0]
                    else:
                        call = warn.call_args_list[1]
                    error = call[0][1]
                    assert error == InsecurePlatformWarning

    def test_context_combines_with_ca_certs(self):
        ctx = util.ssl_.create_urllib3_context(cert_reqs=ssl.CERT_REQUIRED)
        with HTTPSConnectionPool(
            self.host, self.port, ca_certs=DEFAULT_CA, ssl_context=ctx
        ) as https_pool:
            conn = https_pool._new_conn()
            assert conn.__class__ == VerifiedHTTPSConnection

            with mock.patch("warnings.warn") as warn:
                r = https_pool.request("GET", "/")
                assert r.status == 200

                # Modern versions of Python, or systems using PyOpenSSL, don't
                # emit warnings.
                if (
                    sys.version_info >= (2, 7, 9)
                    or util.IS_PYOPENSSL
                    or util.IS_SECURETRANSPORT
                ):
                    assert not warn.called, warn.call_args_list
                else:
                    assert warn.called
                    if util.HAS_SNI:
                        call = warn.call_args_list[0]
                    else:
                        call = warn.call_args_list[1]
                    error = call[0][1]
                    assert error == InsecurePlatformWarning

    @onlyPy279OrNewer
    @notSecureTransport  # SecureTransport does not support cert directories
    @notOpenSSL098  # OpenSSL 0.9.8 does not support cert directories
    def test_ca_dir_verified(self, tmpdir):
        # OpenSSL looks up certificates by the hash for their name, see c_rehash
        # TODO infer the bytes using `cryptography.x509.Name.public_bytes`.
        # https://github.com/pyca/cryptography/pull/3236
        shutil.copyfile(DEFAULT_CA, str(tmpdir / "81deb5f7.0"))

        with HTTPSConnectionPool(
            self.host, self.port, cert_reqs="CERT_REQUIRED", ca_cert_dir=str(tmpdir)
        ) as https_pool:
            conn = https_pool._new_conn()
            assert conn.__class__ == VerifiedHTTPSConnection

            with warnings.catch_warnings(record=True) as w:
                r = https_pool.request("GET", "/")
                assert r.status == 200

            # If we're using a deprecated TLS version we can remove 'DeprecationWarning'
            if self.tls_protocol_deprecated():
                w = [x for x in w if x.category != DeprecationWarning]

            assert w == []

    def test_invalid_common_name(self):
        with HTTPSConnectionPool(
            "127.0.0.1", self.port, cert_reqs="CERT_REQUIRED", ca_certs=DEFAULT_CA
        ) as https_pool:
            with pytest.raises(MaxRetryError) as e:
                https_pool.request("GET", "/")
            assert isinstance(e.value.reason, SSLError)
            assert "doesn't match" in str(
                e.value.reason
            ) or "certificate verify failed" in str(e.value.reason)

    def test_verified_with_bad_ca_certs(self):
        with HTTPSConnectionPool(
            self.host, self.port, cert_reqs="CERT_REQUIRED", ca_certs=self.bad_ca_path
        ) as https_pool:
            with pytest.raises(MaxRetryError) as e:
                https_pool.request("GET", "/")
            assert isinstance(e.value.reason, SSLError)
            assert "certificate verify failed" in str(e.value.reason), (
                "Expected 'certificate verify failed', instead got: %r" % e.value.reason
            )

    def test_wrap_socket_failure_resource_leak(self):
        with HTTPSConnectionPool(
            self.host,
            self.port,
            cert_reqs="CERT_REQUIRED",
            ca_certs=self.bad_ca_path,
        ) as https_pool:
            conn = https_pool._get_conn()
            try:
                with pytest.raises(ssl.SSLError):
                    conn.connect()

                assert conn.sock
            finally:
                conn.close()

    def test_verified_without_ca_certs(self):
        # default is cert_reqs=None which is ssl.CERT_NONE
        with HTTPSConnectionPool(
            self.host, self.port, cert_reqs="CERT_REQUIRED"
        ) as https_pool:
            with pytest.raises(MaxRetryError) as e:
                https_pool.request("GET", "/")
            assert isinstance(e.value.reason, SSLError)
            # there is a different error message depending on whether or
            # not pyopenssl is injected
            assert (
                "No root certificates specified" in str(e.value.reason)
                # PyPy sometimes uses all-caps here
                or "certificate verify failed" in str(e.value.reason).lower()
                or "invalid certificate chain" in str(e.value.reason)
            ), (
                "Expected 'No root certificates specified',  "
                "'certificate verify failed', or "
                "'invalid certificate chain', "
                "instead got: %r" % e.value.reason
            )

    def test_no_ssl(self):
        with HTTPSConnectionPool(self.host, self.port) as pool:
            pool.ConnectionCls = None
            with pytest.raises(SSLError):
                pool._new_conn()
            with pytest.raises(MaxRetryError) as cm:
                pool.request("GET", "/", retries=0)
            assert isinstance(cm.value.reason, SSLError)

    def test_unverified_ssl(self):
        """Test that bare HTTPSConnection can connect, make requests"""
        with HTTPSConnectionPool(self.host, self.port, cert_reqs=ssl.CERT_NONE) as pool:
            with mock.patch("warnings.warn") as warn:
                r = pool.request("GET", "/")
                assert r.status == 200
                assert warn.called

                # Modern versions of Python, or systems using PyOpenSSL, only emit
                # the unverified warning. Older systems may also emit other
                # warnings, which we want to ignore here.
                calls = warn.call_args_list
                assert InsecureRequestWarning in [x[0][1] for x in calls]

    def test_ssl_unverified_with_ca_certs(self):
        with HTTPSConnectionPool(
            self.host, self.port, cert_reqs="CERT_NONE", ca_certs=self.bad_ca_path
        ) as pool:
            with mock.patch("warnings.warn") as warn:
                r = pool.request("GET", "/")
                assert r.status == 200
                assert warn.called

                # Modern versions of Python, or systems using PyOpenSSL, only emit
                # the unverified warning. Older systems may also emit other
                # warnings, which we want to ignore here.
                calls = warn.call_args_list

                # If we're using a deprecated TLS version we can remove 'DeprecationWarning'
                if self.tls_protocol_deprecated():
                    calls = [call for call in calls if call[0][1] != DeprecationWarning]

                if (
                    sys.version_info >= (2, 7, 9)
                    or util.IS_PYOPENSSL
                    or util.IS_SECURETRANSPORT
                ):
                    category = calls[0][0][1]
                elif util.HAS_SNI:
                    category = calls[1][0][1]
                else:
                    category = calls[2][0][1]
                assert category == InsecureRequestWarning

    def test_assert_hostname_false(self):
        with HTTPSConnectionPool(
            "localhost", self.port, cert_reqs="CERT_REQUIRED", ca_certs=DEFAULT_CA
        ) as https_pool:
            https_pool.assert_hostname = False
            https_pool.request("GET", "/")

    def test_assert_specific_hostname(self):
        with HTTPSConnectionPool(
            "localhost", self.port, cert_reqs="CERT_REQUIRED", ca_certs=DEFAULT_CA
        ) as https_pool:
            https_pool.assert_hostname = "localhost"
            https_pool.request("GET", "/")

    def test_server_hostname(self):
        with HTTPSConnectionPool(
            "127.0.0.1",
            self.port,
            cert_reqs="CERT_REQUIRED",
            ca_certs=DEFAULT_CA,
            server_hostname="localhost",
        ) as https_pool:
            conn = https_pool._new_conn()
            conn.request("GET", "/")

            # Assert the wrapping socket is using the passed-through SNI name.
            # pyopenssl doesn't let you pull the server_hostname back off the
            # socket, so only add this assertion if the attribute is there (i.e.
            # the python ssl module).
            if hasattr(conn.sock, "server_hostname"):
                assert conn.sock.server_hostname == "localhost"

    def test_assert_fingerprint_md5(self):
        with HTTPSConnectionPool(
            "localhost", self.port, cert_reqs="CERT_REQUIRED", ca_certs=DEFAULT_CA
        ) as https_pool:
            https_pool.assert_fingerprint = (
                "55:39:BF:70:05:12:43:FA:1F:D1:BF:4E:E8:1B:07:1D"
            )

            https_pool.request("GET", "/")

    def test_assert_fingerprint_sha1(self):
        with HTTPSConnectionPool(
            "localhost", self.port, cert_reqs="CERT_REQUIRED", ca_certs=DEFAULT_CA
        ) as https_pool:
            https_pool.assert_fingerprint = (
                "72:8B:55:4C:9A:FC:1E:88:A1:1C:AD:1B:B2:E7:CC:3E:DB:C8:F9:8A"
            )
            https_pool.request("GET", "/")

    def test_assert_fingerprint_sha256(self):
        with HTTPSConnectionPool(
            "localhost", self.port, cert_reqs="CERT_REQUIRED", ca_certs=DEFAULT_CA
        ) as https_pool:
            https_pool.assert_fingerprint = (
                "E3:59:8E:69:FF:C5:9F:C7:88:87:44:58:22:7F:90:8D:D9:BC:12:C4:90:79:D5:"
                "DC:A8:5D:4F:60:40:1E:A6:D2"
            )
            https_pool.request("GET", "/")

    def test_assert_invalid_fingerprint(self):
        def _test_request(pool):
            with pytest.raises(MaxRetryError) as cm:
                pool.request("GET", "/", retries=0)
            assert isinstance(cm.value.reason, SSLError)
            return cm.value.reason

        with HTTPSConnectionPool(
            self.host, self.port, cert_reqs="CERT_REQUIRED", ca_certs=DEFAULT_CA
        ) as https_pool:

            https_pool.assert_fingerprint = (
                "AA:AA:AA:AA:AA:AAAA:AA:AAAA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA"
            )
            e = _test_request(https_pool)
            assert "Fingerprints did not match." in str(e)

            # Uneven length
            https_pool.assert_fingerprint = "AA:A"
            e = _test_request(https_pool)
            assert "Fingerprint of invalid length:" in str(e)

            # Invalid length
            https_pool.assert_fingerprint = "AA"
            e = _test_request(https_pool)
            assert "Fingerprint of invalid length:" in str(e)

    def test_verify_none_and_bad_fingerprint(self):
        with HTTPSConnectionPool(
            "127.0.0.1", self.port, cert_reqs="CERT_NONE", ca_certs=self.bad_ca_path
        ) as https_pool:
            https_pool.assert_fingerprint = (
                "AA:AA:AA:AA:AA:AAAA:AA:AAAA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA"
            )
            with pytest.raises(MaxRetryError) as cm:
                https_pool.request("GET", "/", retries=0)
            assert isinstance(cm.value.reason, SSLError)

    def test_verify_none_and_good_fingerprint(self):
        with HTTPSConnectionPool(
            "127.0.0.1", self.port, cert_reqs="CERT_NONE", ca_certs=self.bad_ca_path
        ) as https_pool:
            https_pool.assert_fingerprint = (
                "72:8B:55:4C:9A:FC:1E:88:A1:1C:AD:1B:B2:E7:CC:3E:DB:C8:F9:8A"
            )
            https_pool.request("GET", "/")

    @notSecureTransport
    def test_good_fingerprint_and_hostname_mismatch(self):
        # This test doesn't run with SecureTransport because we don't turn off
        # hostname validation without turning off all validation, which this
        # test doesn't do (deliberately). We should revisit this if we make
        # new decisions.
        with HTTPSConnectionPool(
            "127.0.0.1", self.port, cert_reqs="CERT_REQUIRED", ca_certs=DEFAULT_CA
        ) as https_pool:
            https_pool.assert_fingerprint = (
                "72:8B:55:4C:9A:FC:1E:88:A1:1C:AD:1B:B2:E7:CC:3E:DB:C8:F9:8A"
            )
            https_pool.request("GET", "/")

    @requires_network
    def test_https_timeout(self):

        timeout = Timeout(total=None, connect=SHORT_TIMEOUT)
        with HTTPSConnectionPool(
            TARPIT_HOST,
            self.port,
            timeout=timeout,
            retries=False,
            cert_reqs="CERT_REQUIRED",
        ) as https_pool:
            with pytest.raises(ConnectTimeoutError):
                https_pool.request("GET", "/")

        timeout = Timeout(read=0.01)
        with HTTPSConnectionPool(
            self.host,
            self.port,
            timeout=timeout,
            retries=False,
            cert_reqs="CERT_REQUIRED",
        ) as https_pool:
            https_pool.ca_certs = DEFAULT_CA
            https_pool.assert_fingerprint = (
                "72:8B:55:4C:9A:FC:1E:88:A1:1C:AD:1B:B2:E7:CC:3E:DB:C8:F9:8A"
            )

        timeout = Timeout(total=None)
        with HTTPSConnectionPool(
            self.host, self.port, timeout=timeout, cert_reqs="CERT_NONE"
        ) as https_pool:
            https_pool.request("GET", "/")

    def test_tunnel(self):
        """test the _tunnel behavior"""
        timeout = Timeout(total=None)
        with HTTPSConnectionPool(
            self.host, self.port, timeout=timeout, cert_reqs="CERT_NONE"
        ) as https_pool:
            conn = https_pool._new_conn()
            try:
                conn.set_tunnel(self.host, self.port)
                conn._tunnel = mock.Mock()
                https_pool._make_request(conn, "GET", "/")
                conn._tunnel.assert_called_once_with()
            finally:
                conn.close()

    @requires_network
    def test_enhanced_timeout(self):
        with HTTPSConnectionPool(
            TARPIT_HOST,
            self.port,
            timeout=Timeout(connect=SHORT_TIMEOUT),
            retries=False,
            cert_reqs="CERT_REQUIRED",
        ) as https_pool:
            conn = https_pool._new_conn()
            try:
                with pytest.raises(ConnectTimeoutError):
                    https_pool.request("GET", "/")
                with pytest.raises(ConnectTimeoutError):
                    https_pool._make_request(conn, "GET", "/")
            finally:
                conn.close()

        with HTTPSConnectionPool(
            TARPIT_HOST,
            self.port,
            timeout=Timeout(connect=LONG_TIMEOUT),
            retries=False,
            cert_reqs="CERT_REQUIRED",
        ) as https_pool:
            with pytest.raises(ConnectTimeoutError):
                https_pool.request("GET", "/", timeout=Timeout(connect=SHORT_TIMEOUT))

        with HTTPSConnectionPool(
            TARPIT_HOST,
            self.port,
            timeout=Timeout(total=None),
            retries=False,
            cert_reqs="CERT_REQUIRED",
        ) as https_pool:
            conn = https_pool._new_conn()
            try:
                with pytest.raises(ConnectTimeoutError):
                    https_pool.request(
                        "GET", "/", timeout=Timeout(total=None, connect=SHORT_TIMEOUT)
                    )
            finally:
                conn.close()

    def test_enhanced_ssl_connection(self):
        fingerprint = "72:8B:55:4C:9A:FC:1E:88:A1:1C:AD:1B:B2:E7:CC:3E:DB:C8:F9:8A"

        with HTTPSConnectionPool(
            self.host,
            self.port,
            cert_reqs="CERT_REQUIRED",
            ca_certs=DEFAULT_CA,
            assert_fingerprint=fingerprint,
        ) as https_pool:
            r = https_pool.request("GET", "/")
            assert r.status == 200

    @onlyPy279OrNewer
    def test_ssl_correct_system_time(self):
        with HTTPSConnectionPool(
            self.host, self.port, ca_certs=DEFAULT_CA
        ) as https_pool:
            https_pool.cert_reqs = "CERT_REQUIRED"
            https_pool.ca_certs = DEFAULT_CA

            w = self._request_without_resource_warnings("GET", "/")
            assert [] == w

    @onlyPy279OrNewer
    def test_ssl_wrong_system_time(self):
        with HTTPSConnectionPool(
            self.host, self.port, ca_certs=DEFAULT_CA
        ) as https_pool:
            https_pool.cert_reqs = "CERT_REQUIRED"
            https_pool.ca_certs = DEFAULT_CA
            with mock.patch("urllib3.connection.datetime") as mock_date:
                mock_date.date.today.return_value = datetime.date(1970, 1, 1)

                w = self._request_without_resource_warnings("GET", "/")

                assert len(w) == 1
                warning = w[0]

                assert SystemTimeWarning == warning.category
                assert str(RECENT_DATE) in warning.message.args[0]

    def _request_without_resource_warnings(self, method, url):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with HTTPSConnectionPool(
                self.host, self.port, ca_certs=DEFAULT_CA
            ) as https_pool:
                https_pool.request(method, url)

        w = [x for x in w if not isinstance(x.message, ResourceWarning)]

        # If we're using a deprecated TLS version we can remove 'DeprecationWarning'
        if self.tls_protocol_deprecated():
            w = [x for x in w if x.category != DeprecationWarning]

        return w

    def test_set_ssl_version_to_tls_version(self):
        if self.tls_protocol_name is None:
            pytest.skip("Skipping base test class")

        with HTTPSConnectionPool(
            self.host, self.port, ca_certs=DEFAULT_CA
        ) as https_pool:
            https_pool.ssl_version = self.certs["ssl_version"]
            r = https_pool.request("GET", "/")
            assert r.status == 200, r.data

    def test_set_cert_default_cert_required(self):
        conn = VerifiedHTTPSConnection(self.host, self.port)
        conn.set_cert()
        assert conn.cert_reqs == ssl.CERT_REQUIRED

    def test_tls_protocol_name_of_socket(self):
        if self.tls_protocol_name is None:
            pytest.skip("Skipping base test class")

        with HTTPSConnectionPool(
            self.host, self.port, ca_certs=DEFAULT_CA
        ) as https_pool:
            conn = https_pool._get_conn()
            try:
                conn.connect()
                if not hasattr(conn.sock, "version"):
                    pytest.skip("SSLSocket.version() not available")
                assert conn.sock.version() == self.tls_protocol_name
            finally:
                conn.close()

    def test_default_tls_version_deprecations(self):
        if self.tls_protocol_name is None:
            pytest.skip("Skipping base test class")

        with HTTPSConnectionPool(
            self.host, self.port, ca_certs=DEFAULT_CA
        ) as https_pool:
            conn = https_pool._get_conn()
            try:
                with warnings.catch_warnings(record=True) as w:
                    conn.connect()
                    if not hasattr(conn.sock, "version"):
                        pytest.skip("SSLSocket.version() not available")
            finally:
                conn.close()

        if self.tls_protocol_deprecated():
            assert len(w) == 1
            assert str(w[0].message) == (
                "Negotiating TLSv1/TLSv1.1 by default is deprecated "
                "and will be disabled in urllib3 v2.0.0. Connecting to "
                "'%s' with '%s' can be enabled by explicitly opting-in "
                "with 'ssl_version'" % (self.host, self.tls_protocol_name)
            )
        else:
            assert w == []

    def test_no_tls_version_deprecation_with_ssl_version(self):
        if self.tls_protocol_name is None:
            pytest.skip("Skipping base test class")

        with HTTPSConnectionPool(
            self.host, self.port, ca_certs=DEFAULT_CA, ssl_version=util.PROTOCOL_TLS
        ) as https_pool:
            conn = https_pool._get_conn()
            try:
                with warnings.catch_warnings(record=True) as w:
                    conn.connect()
            finally:
                conn.close()

        assert w == []

    def test_no_tls_version_deprecation_with_ssl_context(self):
        if self.tls_protocol_name is None:
            pytest.skip("Skipping base test class")

        with HTTPSConnectionPool(
            self.host,
            self.port,
            ca_certs=DEFAULT_CA,
            ssl_context=util.ssl_.create_urllib3_context(),
        ) as https_pool:
            conn = https_pool._get_conn()
            try:
                with warnings.catch_warnings(record=True) as w:
                    conn.connect()
            finally:
                conn.close()

        assert w == []

    @pytest.mark.skipif(sys.version_info < (3, 8), reason="requires python 3.8+")
    def test_sslkeylogfile(self, tmpdir, monkeypatch):
        if not hasattr(util.SSLContext, "keylog_filename"):
            pytest.skip("requires OpenSSL 1.1.1+")
        keylog_file = tmpdir.join("keylogfile.txt")
        monkeypatch.setenv("SSLKEYLOGFILE", str(keylog_file))
        with HTTPSConnectionPool(
            self.host, self.port, ca_certs=DEFAULT_CA
        ) as https_pool:
            r = https_pool.request("GET", "/")
            assert r.status == 200, r.data
            assert keylog_file.check(file=1), "keylogfile '%s' should exist" % str(
                keylog_file
            )
            assert keylog_file.read().startswith(
                "# TLS secrets log file"
            ), "keylogfile '%s' should start with '# TLS secrets log file'" % str(
                keylog_file
            )

    @pytest.mark.parametrize("sslkeylogfile", [None, ""])
    def test_sslkeylogfile_empty(self, monkeypatch, sslkeylogfile):
        # Assert that an HTTPS connection doesn't error out when given
        # no SSLKEYLOGFILE or an empty value (ie 'SSLKEYLOGFILE=')
        if sslkeylogfile is not None:
            monkeypatch.setenv("SSLKEYLOGFILE", sslkeylogfile)
        else:
            monkeypatch.delenv("SSLKEYLOGFILE", raising=False)
        with HTTPSConnectionPool(self.host, self.port, ca_certs=DEFAULT_CA) as pool:
            r = pool.request("GET", "/")
            assert r.status == 200, r.data

    def test_alpn_default(self):
        """Default ALPN protocols are sent by default."""
        if not has_alpn() or not has_alpn(ssl.SSLContext):
            pytest.skip("ALPN-support not available")
        with HTTPSConnectionPool(self.host, self.port, ca_certs=DEFAULT_CA) as pool:
            r = pool.request("GET", "/alpn_protocol", retries=0)
            assert r.status == 200
            assert r.data.decode("utf-8") == util.ALPN_PROTOCOLS[0]


@pytest.mark.usefixtures("requires_tlsv1")
class TestHTTPS_TLSv1(TestHTTPS):
    tls_protocol_name = "TLSv1"
    certs = TLSv1_CERTS


@pytest.mark.usefixtures("requires_tlsv1_1")
class TestHTTPS_TLSv1_1(TestHTTPS):
    tls_protocol_name = "TLSv1.1"
    certs = TLSv1_1_CERTS


@pytest.mark.usefixtures("requires_tlsv1_2")
class TestHTTPS_TLSv1_2(TestHTTPS):
    tls_protocol_name = "TLSv1.2"
    certs = TLSv1_2_CERTS


@pytest.mark.usefixtures("requires_tlsv1_3")
class TestHTTPS_TLSv1_3(TestHTTPS):
    tls_protocol_name = "TLSv1.3"
    certs = TLSv1_3_CERTS


class TestHTTPS_NoSAN:
    def test_warning_for_certs_without_a_san(self, no_san_server):
        """Ensure that a warning is raised when the cert from the server has
        no Subject Alternative Name."""
        with mock.patch("warnings.warn") as warn:
            with HTTPSConnectionPool(
                no_san_server.host,
                no_san_server.port,
                cert_reqs="CERT_REQUIRED",
                ca_certs=no_san_server.ca_certs,
            ) as https_pool:
                r = https_pool.request("GET", "/")
                assert r.status == 200
                assert warn.called

    def test_common_name_without_san_with_different_common_name(
        self, no_san_server_with_different_commmon_name
    ):
        with HTTPSConnectionPool(
            no_san_server_with_different_commmon_name.host,
            no_san_server_with_different_commmon_name.port,
            cert_reqs="CERT_REQUIRED",
            ca_certs=no_san_server_with_different_commmon_name.ca_certs,
        ) as https_pool:
            with pytest.raises(MaxRetryError) as cm:
                https_pool.request("GET", "/")
            assert isinstance(cm.value.reason, SSLError)


class TestHTTPS_IPV4SAN:
    def test_can_validate_ip_san(self, ipv4_san_server):
        """Ensure that urllib3 can validate SANs with IP addresses in them."""
        with HTTPSConnectionPool(
            ipv4_san_server.host,
            ipv4_san_server.port,
            cert_reqs="CERT_REQUIRED",
            ca_certs=ipv4_san_server.ca_certs,
        ) as https_pool:
            r = https_pool.request("GET", "/")
            assert r.status == 200


class TestHTTPS_IPv6Addr:
    @pytest.mark.parametrize("host", ["::1", "[::1]"])
    def test_strip_square_brackets_before_validating(self, ipv6_addr_server, host):
        """Test that the fix for #760 works."""
        with HTTPSConnectionPool(
            host,
            ipv6_addr_server.port,
            cert_reqs="CERT_REQUIRED",
            ca_certs=ipv6_addr_server.ca_certs,
        ) as https_pool:
            r = https_pool.request("GET", "/")
            assert r.status == 200


class TestHTTPS_IPV6SAN:
    @pytest.mark.parametrize("host", ["::1", "[::1]"])
    def test_can_validate_ipv6_san(self, ipv6_san_server, host):
        """Ensure that urllib3 can validate SANs with IPv6 addresses in them."""
        with HTTPSConnectionPool(
            host,
            ipv6_san_server.port,
            cert_reqs="CERT_REQUIRED",
            ca_certs=ipv6_san_server.ca_certs,
        ) as https_pool:
            r = https_pool.request("GET", "/")
            assert r.status == 200
