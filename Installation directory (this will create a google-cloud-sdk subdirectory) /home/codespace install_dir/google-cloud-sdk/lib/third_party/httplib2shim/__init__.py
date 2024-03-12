# Copyright (c) 2006 by Joe Gregorio, Google Inc.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from collections import abc
import errno
import socket
import ssl
import warnings

import httplib2
import six.moves.http_client
import urllib3


def _default_make_pool(http, proxy_info):
    """Creates a urllib3.PoolManager object that has SSL verification enabled."""

    if not http.ca_certs:
        http.ca_certs = httplib2.CA_CERTS

    ssl_disabled = http.disable_ssl_certificate_validation

    cert_reqs = 'CERT_REQUIRED' if http.ca_certs and not ssl_disabled else None

    if isinstance(proxy_info, abc.Callable):
        proxy_info = proxy_info()
    if proxy_info:
        if proxy_info.proxy_user and proxy_info.proxy_pass:
            proxy_url = 'http://{}:{}@{}:{}/'.format(
                proxy_info.proxy_user, proxy_info.proxy_pass,
                proxy_info.proxy_host, proxy_info.proxy_port,
            )
            proxy_headers = urllib3.util.request.make_headers(
                proxy_basic_auth='{}:{}'.format(
                    proxy_info.proxy_user, proxy_info.proxy_pass,
                )
            )
        else:
            proxy_url = 'http://{}:{}/'.format(
                proxy_info.proxy_host, proxy_info.proxy_port,
            )
            proxy_headers = {}

        return urllib3.ProxyManager(
            proxy_url=proxy_url,
            proxy_headers=proxy_headers,
            ca_certs=http.ca_certs,
            cert_reqs=cert_reqs,
        )
    return urllib3.PoolManager(
        ca_certs=http.ca_certs,
        cert_reqs=cert_reqs,
    )


def _patch_add_certificate(pool_manager):
    """Monkey-patches PoolManager to make it accept client certificates."""
    def add_certificate(key, cert, password):
        pool_manager._client_key = key
        pool_manager._client_cert = cert
        pool_manager._client_key_password = password

    def connection_from_host(host, port=None, scheme='http', pool_kwargs=None):
        pool = pool_manager._connection_from_host(host, port, scheme, pool_kwargs)
        # pool is urllib3.HTTPSConnectionPool, which uses VerifiedHTTPSConnection
        # to handle cert when ssl library is linked.
        pool.key_file = pool_manager._client_key
        pool.cert_file = pool_manager._client_cert
        pool.key_password = pool_manager._client_key_password
        return pool

    pool_manager.add_certificate = add_certificate
    pool_manager.add_certificate(None, None, None)
    pool_manager._connection_from_host = pool_manager.connection_from_host
    pool_manager.connection_from_host = connection_from_host


def patch(make_pool=_default_make_pool):
    """Monkey-patches httplib2.Http to be httplib2shim.Http.

    This effectively makes all clients of httplib2 use urlilb3. It's preferable
    to specify httplib2shim.Http explicitly where you can, but this can be
    useful in situations where you do not control the construction of the http
    object.

    Args:
        make_pool: A function that returns a urllib3.Pool-like object. This
            allows you to specify special arguments to your connection pool if
            needed. By default, this will create a urllib3.PoolManager with
            SSL verification enabled.
    """
    setattr(httplib2, '_HttpOriginal', httplib2.Http)
    httplib2.Http = Http
    Http._make_pool = make_pool


class Http(httplib2.Http):
    """A httplib2.Http subclass that uses urllib3 to perform requests.

    This allows full thread safety, connection pooling, and proper SSL
    verification support.
    """
    _make_pool = _default_make_pool

    def __init__(self, cache=None, timeout=None,
                 proxy_info=httplib2.proxy_info_from_environment,
                 ca_certs=None, disable_ssl_certificate_validation=False,
                 pool=None):
        disable_ssl = disable_ssl_certificate_validation

        super(Http, self).__init__(
            cache=cache,
            timeout=timeout,
            proxy_info=proxy_info,
            ca_certs=ca_certs,
            disable_ssl_certificate_validation=disable_ssl)

        if not pool:
            pool = self._make_pool(proxy_info=proxy_info)

        _patch_add_certificate(pool)
        self.pool = pool

    @classmethod
    def _create_full_uri(cls, conn, request_uri):
        # Reconstruct the full uri from the connection object.
        if isinstance(conn, six.moves.http_client.HTTPSConnection):
            scheme = 'https'
        else:
            scheme = 'http'

        host = conn.host

        # Reformat IPv6 hosts.
        if _is_ipv6(host):
            host = '[{}]'.format(host)

        port = ''
        if conn.port is not None:
            port = ':{}'.format(conn.port)

        return '{}://{}{}{}'.format(scheme, host, port, request_uri)

    def _conn_request(self, conn, request_uri, method, body, headers):
        full_uri = self._create_full_uri(conn, request_uri)

        decode = True if method != 'HEAD' else False

        try:
            urllib3_response = self.pool.request(
                method,
                full_uri,
                body=body,
                headers=headers,
                redirect=False,
                retries=urllib3.Retry(total=False, redirect=0),
                timeout=urllib3.Timeout(total=self.timeout),
                decode_content=decode)

            response = _map_response(urllib3_response, decode=decode)
            content = urllib3_response.data

        except Exception as e:
            raise _map_exception(e)

        return response, content

    def add_certificate(self, key, cert, domain, password=None):
        self.pool.add_certificate(key, cert, password)

    def __getstate__(self):
        dict = super(Http, self).__getstate__()
        del dict['pool']
        return dict

    def __setstate__(self, dict):
        super(Http, self).__setstate__(dict)
        self.pool = self._make_pool(proxy_info=self.proxy_info())


def _is_ipv6(addr):
    """Checks if a given address is an IPv6 address."""
    try:
        # From https://docs.python.org/2/library/socket.html#socket.getaddrinfo
        # AI_NUMERICHOST will disable domain name resolution and will raise
        # an error if host is a domain name.
        socket.getaddrinfo(addr, None, 0, 0, 0, socket.AI_NUMERICHOST)
    except socket.gaierror:
        # addr is a domain name.
        return False
    try:
        socket.inet_aton(addr)
        # addr is an ipv4 address.
        return False
    except socket.error:
        return True

def _map_response(response, decode=False):
    """Maps a urllib3 response to a httplib/httplib2 Response."""
    # This causes weird deepcopy errors, so it's commented out for now.
    # item._urllib3_response = response
    headers = response.getheaders()
    headers.pop('status', None)  # httplib2 ignores this header too
    item = httplib2.Response(headers)
    item.status = response.status
    item['status'] = str(item.status)
    item.reason = response.reason
    item.version = response.version

    # httplib2 expects the content-encoding header to be stripped and the
    # content length to be the length of the uncompressed content.
    # This does not occur for 'HEAD' requests.
    if decode and item.get('content-encoding') in ['gzip', 'deflate']:
        item['content-length'] = str(len(response.data))
        item['-content-encoding'] = item.pop('content-encoding')

    return item


def _map_exception(e):
    """Maps an exception from urlib3 to httplib2."""
    if isinstance(e, urllib3.exceptions.MaxRetryError):
        if not e.reason:
            return e
        e = e.reason
    message = e.args[0] if e.args else ''
    if isinstance(e, urllib3.exceptions.ResponseError):
        if 'too many redirects' in message:
            return httplib2.RedirectLimit(message)
    if isinstance(e, urllib3.exceptions.NewConnectionError):
        if ('Name or service not known' in message or
                'nodename nor servname provided, or not known' in message):
            return httplib2.ServerNotFoundError(
                'Unable to find hostname.')
        if 'Connection refused' in message:
            return socket.error((errno.ECONNREFUSED, 'Connection refused'))
    if isinstance(e, urllib3.exceptions.DecodeError):
        return httplib2.FailedToDecompressContent(
            'Content purported as compressed but not uncompressable.',
            httplib2.Response({'status': 500}), '')
    if isinstance(e, urllib3.exceptions.TimeoutError):
        return socket.timeout('timed out')
    if isinstance(e, urllib3.exceptions.ConnectTimeoutError):
        return socket.timeout('connect timed out')
    if isinstance(e, urllib3.exceptions.SSLError):
        return ssl.SSLError(*e.args)

    return e
