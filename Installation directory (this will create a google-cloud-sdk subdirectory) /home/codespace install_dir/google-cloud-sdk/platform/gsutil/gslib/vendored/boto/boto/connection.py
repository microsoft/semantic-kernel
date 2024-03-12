# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.
# Copyright (c) 2010 Google
# Copyright (c) 2008 rPath, Inc.
# Copyright (c) 2009 The Echo Nest Corporation
# Copyright (c) 2010, Eucalyptus Systems, Inc.
# Copyright (c) 2011, Nexenta Systems Inc.
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

#
# Parts of this code were copied or derived from sample code supplied by AWS.
# The following notice applies to that code.
#
#  This software code is made available "AS IS" without warranties of any
#  kind.  You may copy, display, modify and redistribute the software
#  code either by itself or as incorporated into your code; provided that
#  you do not remove any proprietary notices.  Your use of this software
#  code is at your own risk and you waive any claim against Amazon
#  Digital Services, Inc. or its affiliates with respect to your use of
#  this software code. (c) 2006 Amazon Digital Services, Inc. or its
#  affiliates.

"""
Handles basic connections to AWS
"""
from datetime import datetime
import errno
import os
import random
import re
import socket
import sys
import time
import xml.sax
import copy

from boto import auth
from boto import auth_handler
import boto
import boto.utils
import boto.handler
import boto.cacerts

from boto import config, UserAgent
from boto.compat import six, http_client, urlparse, quote, encodebytes
from boto.exception import AWSConnectionError
from boto.exception import BotoClientError
from boto.exception import BotoServerError
from boto.exception import PleaseRetryException
from boto.exception import S3ResponseError
from boto.provider import Provider
from boto.resultset import ResultSet

HAVE_HTTPS_CONNECTION = False
try:
    import ssl
    from boto import https_connection
    # Google App Engine runs on Python 2.5 so doesn't have ssl.SSLError.
    if hasattr(ssl, 'SSLError'):
        HAVE_HTTPS_CONNECTION = True
except ImportError:
    pass

try:
    import threading
except ImportError:
    import dummy_threading as threading

ON_APP_ENGINE = all(key in os.environ for key in (
    'USER_IS_ADMIN', 'CURRENT_VERSION_ID', 'GAE_APPLICATION'))

PORTS_BY_SECURITY = {True: 443,
                     False: 80}

DEFAULT_CA_CERTS_FILE = os.path.join(os.path.dirname(os.path.abspath(boto.cacerts.__file__)), "cacerts.txt")


class HostConnectionPool(object):

    """
    A pool of connections for one remote (host,port,is_secure).

    When connections are added to the pool, they are put into a
    pending queue.  The _mexe method returns connections to the pool
    before the response body has been read, so they connections aren't
    ready to send another request yet.  They stay in the pending queue
    until they are ready for another request, at which point they are
    returned to the pool of ready connections.

    The pool of ready connections is an ordered list of
    (connection,time) pairs, where the time is the time the connection
    was returned from _mexe.  After a certain period of time,
    connections are considered stale, and discarded rather than being
    reused.  This saves having to wait for the connection to time out
    if AWS has decided to close it on the other end because of
    inactivity.

    Thread Safety:

        This class is used only from ConnectionPool while it's mutex
        is held.
    """

    def __init__(self):
        self.queue = []

    def size(self):
        """
        Returns the number of connections in the pool for this host.
        Some of the connections may still be in use, and may not be
        ready to be returned by get().
        """
        return len(self.queue)

    def put(self, conn):
        """
        Adds a connection to the pool, along with the time it was
        added.
        """
        self.queue.append((conn, time.time()))

    def get(self):
        """
        Returns the next connection in this pool that is ready to be
        reused.  Returns None if there aren't any.
        """
        # Discard ready connections that are too old.
        self.clean()

        # Return the first connection that is ready, and remove it
        # from the queue.  Connections that aren't ready are returned
        # to the end of the queue with an updated time, on the
        # assumption that somebody is actively reading the response.
        for _ in range(len(self.queue)):
            (conn, _) = self.queue.pop(0)
            if self._conn_ready(conn):
                return conn
            else:
                self.put(conn)
        return None

    def _conn_ready(self, conn):
        """
        There is a nice state diagram at the top of http_client.py.  It
        indicates that once the response headers have been read (which
        _mexe does before adding the connection to the pool), a
        response is attached to the connection, and it stays there
        until it's done reading.  This isn't entirely true: even after
        the client is done reading, the response may be closed, but
        not removed from the connection yet.

        This is ugly, reading a private instance variable, but the
        state we care about isn't available in any public methods.
        """
        if ON_APP_ENGINE:
            # Google AppEngine implementation of HTTPConnection doesn't contain
            # _HTTPConnection__response attribute. Moreover, it's not possible
            # to determine if given connection is ready. Reusing connections
            # simply doesn't make sense with App Engine urlfetch service.
            return False
        else:
            response = getattr(conn, '_HTTPConnection__response', None)
            return (response is None) or response.isclosed()

    def clean(self):
        """
        Get rid of stale connections.
        """
        # Note that we do not close the connection here -- somebody
        # may still be reading from it.
        while len(self.queue) > 0 and self._pair_stale(self.queue[0]):
            self.queue.pop(0)

    def _pair_stale(self, pair):
        """
        Returns true of the (connection,time) pair is too old to be
        used.
        """
        (_conn, return_time) = pair
        now = time.time()
        return return_time + ConnectionPool.STALE_DURATION < now


class ConnectionPool(object):

    """
    A connection pool that expires connections after a fixed period of
    time.  This saves time spent waiting for a connection that AWS has
    timed out on the other end.

    This class is thread-safe.
    """

    #
    # The amout of time between calls to clean.
    #

    CLEAN_INTERVAL = 5.0

    #
    # How long before a connection becomes "stale" and won't be reused
    # again.  The intention is that this time is less that the timeout
    # period that AWS uses, so we'll never try to reuse a connection
    # and find that AWS is timing it out.
    #
    # Experimentation in July 2011 shows that AWS starts timing things
    # out after three minutes.  The 60 seconds here is conservative so
    # we should never hit that 3-minute timout.
    #

    STALE_DURATION = 60.0

    def __init__(self):
        # Mapping from (host,port,is_secure) to HostConnectionPool.
        # If a pool becomes empty, it is removed.
        self.host_to_pool = {}
        # The last time the pool was cleaned.
        self.last_clean_time = 0.0
        self.mutex = threading.Lock()
        ConnectionPool.STALE_DURATION = \
            config.getfloat('Boto', 'connection_stale_duration',
                            ConnectionPool.STALE_DURATION)

    def __getstate__(self):
        pickled_dict = copy.copy(self.__dict__)
        pickled_dict['host_to_pool'] = {}
        del pickled_dict['mutex']
        return pickled_dict

    def __setstate__(self, dct):
        self.__init__()

    def size(self):
        """
        Returns the number of connections in the pool.
        """
        return sum(pool.size() for pool in self.host_to_pool.values())

    def get_http_connection(self, host, port, is_secure):
        """
        Gets a connection from the pool for the named host.  Returns
        None if there is no connection that can be reused. It's the caller's
        responsibility to call close() on the connection when it's no longer
        needed.
        """
        self.clean()
        with self.mutex:
            key = (host, port, is_secure)
            if key not in self.host_to_pool:
                return None
            return self.host_to_pool[key].get()

    def put_http_connection(self, host, port, is_secure, conn):
        """
        Adds a connection to the pool of connections that can be
        reused for the named host.
        """
        with self.mutex:
            key = (host, port, is_secure)
            if key not in self.host_to_pool:
                self.host_to_pool[key] = HostConnectionPool()
            self.host_to_pool[key].put(conn)

    def clean(self):
        """
        Clean up the stale connections in all of the pools, and then
        get rid of empty pools.  Pools clean themselves every time a
        connection is fetched; this cleaning takes care of pools that
        aren't being used any more, so nothing is being gotten from
        them.
        """
        with self.mutex:
            now = time.time()
            if self.last_clean_time + self.CLEAN_INTERVAL < now:
                to_remove = []
                for (host, pool) in self.host_to_pool.items():
                    pool.clean()
                    if pool.size() == 0:
                        to_remove.append(host)
                for host in to_remove:
                    del self.host_to_pool[host]
                self.last_clean_time = now


class HTTPRequest(object):

    def __init__(self, method, protocol, host, port, path, auth_path,
                 params, headers, body):
        """Represents an HTTP request.

        :type method: string
        :param method: The HTTP method name, 'GET', 'POST', 'PUT' etc.

        :type protocol: string
        :param protocol: The http protocol used, 'http' or 'https'.

        :type host: string
        :param host: Host to which the request is addressed. eg. abc.com

        :type port: int
        :param port: port on which the request is being sent. Zero means unset,
            in which case default port will be chosen.

        :type path: string
        :param path: URL path that is being accessed.

        :type auth_path: string
        :param path: The part of the URL path used when creating the
            authentication string.

        :type params: dict
        :param params: HTTP url query parameters, with key as name of
            the param, and value as value of param.

        :type headers: dict
        :param headers: HTTP headers, with key as name of the header and value
            as value of header.

        :type body: string
        :param body: Body of the HTTP request. If not present, will be None or
            empty string ('').
        """
        self.method = method
        self.protocol = protocol
        self.host = host
        self.port = port
        self.path = path
        if auth_path is None:
            auth_path = path
        self.auth_path = auth_path
        self.params = params
        # chunked Transfer-Encoding should act only on PUT request.
        if headers and 'Transfer-Encoding' in headers and \
                headers['Transfer-Encoding'] == 'chunked' and \
                self.method != 'PUT':
            self.headers = headers.copy()
            del self.headers['Transfer-Encoding']
        else:
            self.headers = headers
        self.body = body

    def __str__(self):
        return (('method:(%s) protocol:(%s) host(%s) port(%s) path(%s) '
                 'params(%s) headers(%s) body(%s)') % (self.method,
                 self.protocol, self.host, self.port, self.path, self.params,
                 self.headers, self.body))

    def authorize(self, connection, **kwargs):
        if not getattr(self, '_headers_quoted', False):
            for key in self.headers:
                val = self.headers[key]
                if isinstance(val, six.text_type):
                    safe = '!"#$%&\'()*+,/:;<=>?@[\\]^`{|}~ '
                    self.headers[key] = quote(val.encode('utf-8'), safe)
            setattr(self, '_headers_quoted', True)

        self.headers['User-Agent'] = UserAgent

        connection._auth_handler.add_auth(self, **kwargs)

        # I'm not sure if this is still needed, now that add_auth is
        # setting the content-length for POST requests.
        if 'Content-Length' not in self.headers:
            if 'Transfer-Encoding' not in self.headers or \
                    self.headers['Transfer-Encoding'] != 'chunked':
                self.headers['Content-Length'] = str(len(self.body))


class HTTPResponse(http_client.HTTPResponse):

    def __init__(self, *args, **kwargs):
        http_client.HTTPResponse.__init__(self, *args, **kwargs)
        self._cached_response = ''

    def read(self, amt=None):
        """Read the response.

        This method does not have the same behavior as
        http_client.HTTPResponse.read.  Instead, if this method is called with
        no ``amt`` arg, then the response body will be cached.  Subsequent
        calls to ``read()`` with no args **will return the cached response**.

        """
        if amt is None:
            # The reason for doing this is that many places in boto call
            # response.read() and except to get the response body that they
            # can then process.  To make sure this always works as they expect
            # we're caching the response so that multiple calls to read()
            # will return the full body.  Note that this behavior only
            # happens if the amt arg is not specified.
            if not self._cached_response:
                self._cached_response = http_client.HTTPResponse.read(self)
            return self._cached_response
        else:
            return http_client.HTTPResponse.read(self, amt)


class AWSAuthConnection(object):
    def __init__(self, host, aws_access_key_id=None,
                 aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, path='/',
                 provider='aws', security_token=None,
                 suppress_consec_slashes=True,
                 validate_certs=True, profile_name=None):
        """
        :type host: str
        :param host: The host to make the connection to

        :keyword str aws_access_key_id: Your AWS Access Key ID (provided by
            Amazon). If none is specified, the value in your
            ``AWS_ACCESS_KEY_ID`` environmental variable is used.
        :keyword str aws_secret_access_key: Your AWS Secret Access Key
            (provided by Amazon). If none is specified, the value in your
            ``AWS_SECRET_ACCESS_KEY`` environmental variable is used.
        :keyword str security_token: The security token associated with
            temporary credentials issued by STS.  Optional unless using
            temporary credentials.  If none is specified, the environment
            variable ``AWS_SECURITY_TOKEN`` is used if defined.

        :type is_secure: boolean
        :param is_secure: Whether the connection is over SSL

        :type https_connection_factory: list or tuple
        :param https_connection_factory: A pair of an HTTP connection
            factory and the exceptions to catch.  The factory should have
            a similar interface to L{http_client.HTTPSConnection}.

        :param str proxy: Address/hostname for a proxy server

        :type proxy_port: int
        :param proxy_port: The port to use when connecting over a proxy

        :type proxy_user: str
        :param proxy_user: The username to connect with on the proxy

        :type proxy_pass: str
        :param proxy_pass: The password to use when connection over a proxy.

        :type port: int
        :param port: The port to use to connect

        :type suppress_consec_slashes: bool
        :param suppress_consec_slashes: If provided, controls whether
            consecutive slashes will be suppressed in key paths.

        :type validate_certs: bool
        :param validate_certs: Controls whether SSL certificates
            will be validated or not.  Defaults to True.

        :type profile_name: str
        :param profile_name: Override usual Credentials section in config
            file to use a named set of keys instead.
        """
        self.suppress_consec_slashes = suppress_consec_slashes
        self.num_retries = 6
        # Override passed-in is_secure setting if value was defined in config.
        if config.has_option('Boto', 'is_secure'):
            is_secure = config.getboolean('Boto', 'is_secure')
        self.is_secure = is_secure
        # Whether or not to validate server certificates.
        # The default is now to validate certificates.  This can be
        # overridden in the boto config file are by passing an
        # explicit validate_certs parameter to the class constructor.
        self.https_validate_certificates = config.getbool(
            'Boto', 'https_validate_certificates',
            validate_certs)
        if self.https_validate_certificates and not HAVE_HTTPS_CONNECTION:
            raise BotoClientError(
                "SSL server certificate validation is enabled in boto "
                "configuration, but Python dependencies required to "
                "support this feature are not available. Certificate "
                "validation is only supported when running under Python "
                "2.6 or later.")
        certs_file = config.get_value(
            'Boto', 'ca_certificates_file', DEFAULT_CA_CERTS_FILE)
        if certs_file == 'system':
            certs_file = None
        self.ca_certificates_file = certs_file
        if port:
            self.port = port
        else:
            self.port = PORTS_BY_SECURITY[is_secure]

        self.handle_proxy(proxy, proxy_port, proxy_user, proxy_pass)
        # define exceptions from http_client that we want to catch and retry
        self.http_exceptions = (http_client.HTTPException, socket.error,
                                socket.gaierror, http_client.BadStatusLine)
        # define subclasses of the above that are not retryable.
        self.http_unretryable_exceptions = []
        if HAVE_HTTPS_CONNECTION:
            self.http_unretryable_exceptions.append(
                https_connection.InvalidCertificateException)

        # define values in socket exceptions we don't want to catch
        self.socket_exception_values = (errno.EINTR,)
        if https_connection_factory is not None:
            self.https_connection_factory = https_connection_factory[0]
            self.http_exceptions += https_connection_factory[1]
        else:
            self.https_connection_factory = None
        if (is_secure):
            self.protocol = 'https'
        else:
            self.protocol = 'http'
        self.host = host
        self.path = path
        # if the value passed in for debug
        if not isinstance(debug, six.integer_types):
            debug = 0
        self.debug = config.getint('Boto', 'debug', debug)
        self.host_header = None

        # Timeout used to tell http_client how long to wait for socket timeouts.
        # Default is to leave timeout unchanged, which will in turn result in
        # the socket's default global timeout being used. To specify a
        # timeout, set http_socket_timeout in Boto config. Regardless,
        # timeouts will only be applied if Python is 2.6 or greater.
        self.http_connection_kwargs = {}
        if (sys.version_info[0], sys.version_info[1]) >= (2, 6):
            # If timeout isn't defined in boto config file, use 70 second
            # default as recommended by
            # http://docs.aws.amazon.com/amazonswf/latest/apireference/API_PollForActivityTask.html
            self.http_connection_kwargs['timeout'] = config.getint(
                'Boto', 'http_socket_timeout', 70)

        is_anonymous_connection = getattr(self, 'anon', False)

        if isinstance(provider, Provider):
            # Allow overriding Provider
            self.provider = provider
        else:
            self._provider_type = provider
            self.provider = Provider(self._provider_type,
                                     aws_access_key_id,
                                     aws_secret_access_key,
                                     security_token,
                                     profile_name,
                                     anon=is_anonymous_connection)

        # Allow config file to override default host, port, and host header.
        if self.provider.host:
            self.host = self.provider.host
        if self.provider.port:
            self.port = self.provider.port
        if self.provider.host_header:
            self.host_header = self.provider.host_header

        self._pool = ConnectionPool()
        self._connection = (self.host, self.port, self.is_secure)
        self._last_rs = None
        self._auth_handler = auth.get_auth_handler(
            host, config, self.provider, self._required_auth_capability())
        if getattr(self, 'AuthServiceName', None) is not None:
            self.auth_service_name = self.AuthServiceName
        self.request_hook = None

    def __repr__(self):
        return '%s:%s' % (self.__class__.__name__, self.host)

    def _required_auth_capability(self):
        return []

    def _get_auth_service_name(self):
        return getattr(self._auth_handler, 'service_name')

    # For Sigv4, the auth_service_name/auth_region_name properties allow
    # the service_name/region_name to be explicitly set instead of being
    # derived from the endpoint url.
    def _set_auth_service_name(self, value):
        self._auth_handler.service_name = value
    auth_service_name = property(_get_auth_service_name, _set_auth_service_name)

    def _get_auth_region_name(self):
        return getattr(self._auth_handler, 'region_name')

    def _set_auth_region_name(self, value):
        self._auth_handler.region_name = value
    auth_region_name = property(_get_auth_region_name, _set_auth_region_name)

    def connection(self):
        return self.get_http_connection(*self._connection)
    connection = property(connection)

    def aws_access_key_id(self):
        return self.provider.access_key
    aws_access_key_id = property(aws_access_key_id)
    gs_access_key_id = aws_access_key_id
    access_key = aws_access_key_id

    def aws_secret_access_key(self):
        return self.provider.secret_key
    aws_secret_access_key = property(aws_secret_access_key)
    gs_secret_access_key = aws_secret_access_key
    secret_key = aws_secret_access_key

    def profile_name(self):
        return self.provider.profile_name
    profile_name = property(profile_name)

    def get_path(self, path='/'):
        # The default behavior is to suppress consecutive slashes for reasons
        # discussed at
        # https://groups.google.com/forum/#!topic/boto-dev/-ft0XPUy0y8
        # You can override that behavior with the suppress_consec_slashes param.
        if not self.suppress_consec_slashes:
            return self.path + re.sub('^(/*)/', "\\1", path)
        pos = path.find('?')
        if pos >= 0:
            params = path[pos:]
            path = path[:pos]
        else:
            params = None
        if path[-1] == '/':
            need_trailing = True
        else:
            need_trailing = False
        path_elements = self.path.split('/')
        path_elements.extend(path.split('/'))
        path_elements = [p for p in path_elements if p]
        path = '/' + '/'.join(path_elements)
        if path[-1] != '/' and need_trailing:
            path += '/'
        if params:
            path = path + params
        return path

    def server_name(self, port=None):
        if not port:
            port = self.port
        if port == 80:
            signature_host = self.host
        else:
            ver_int = sys.version_info[0] * 10 + sys.version_info[1]
            if port == 443 and ver_int >= 26:  # Py >= 2.6
                signature_host = self.host
            else:
                # In versions < 2.6, Python's http_client would append ":443"
                # to the hostname sent in the Host header and so we needed to
                # make sure we did the same when calculating the V2 signature.
                signature_host = '%s:%d' % (self.host, port)
        return signature_host

    def handle_proxy(self, proxy, proxy_port, proxy_user, proxy_pass):
        self.proxy = proxy
        self.proxy_port = proxy_port
        self.proxy_user = proxy_user
        self.proxy_pass = proxy_pass
        if 'http_proxy' in os.environ and not self.proxy:
            pattern = re.compile(
                '(?:http://)?'
                '(?:(?P<user>[\w\-\.]+):(?P<pass>.*)@)?'
                '(?P<host>[\w\-\.]+)'
                '(?::(?P<port>\d+))?'
            )
            match = pattern.match(os.environ['http_proxy'])
            if match:
                self.proxy = match.group('host')
                self.proxy_port = match.group('port')
                self.proxy_user = match.group('user')
                self.proxy_pass = match.group('pass')
        else:
            if not self.proxy:
                self.proxy = config.get_value('Boto', 'proxy', None)
            if not self.proxy_port:
                self.proxy_port = config.get_value('Boto', 'proxy_port', None)
            if not self.proxy_user:
                self.proxy_user = config.get_value('Boto', 'proxy_user', None)
            if not self.proxy_pass:
                self.proxy_pass = config.get_value('Boto', 'proxy_pass', None)

        if not self.proxy_port and self.proxy:
            print("http_proxy environment variable does not specify "
                  "a port, using default")
            self.proxy_port = self.port

        self.no_proxy = os.environ.get('no_proxy', '') or os.environ.get('NO_PROXY', '')
        self.use_proxy = (self.proxy is not None)

    def get_http_connection(self, host, port, is_secure):
        conn = self._pool.get_http_connection(host, port, is_secure)
        if conn is not None:
            return conn
        else:
            return self.new_http_connection(host, port, is_secure)

    def skip_proxy(self, host):
        if not self.no_proxy:
            return False

        if self.no_proxy == "*":
            return True

        hostonly = host
        hostonly = host.split(':')[0]

        for name in self.no_proxy.split(','):
            if name and (hostonly.endswith(name) or host.endswith(name)):
                return True

        return False

    def new_http_connection(self, host, port, is_secure):
        if host is None:
            host = self.server_name()

        # Make sure the host is really just the host, not including
        # the port number
        host = boto.utils.parse_host(host)

        http_connection_kwargs = self.http_connection_kwargs.copy()

        # Connection factories below expect a port keyword argument
        http_connection_kwargs['port'] = port

        # Override host with proxy settings if needed
        if self.use_proxy and not is_secure and \
                not self.skip_proxy(host):
            host = self.proxy
            http_connection_kwargs['port'] = int(self.proxy_port)

        if is_secure:
            boto.log.debug(
                'establishing HTTPS connection: host=%s, kwargs=%s',
                host, http_connection_kwargs)
            if self.use_proxy and not self.skip_proxy(host):
                connection = self.proxy_ssl(host, is_secure and 443 or 80)
            elif self.https_connection_factory:
                connection = self.https_connection_factory(host)
            elif self.https_validate_certificates and HAVE_HTTPS_CONNECTION:
                connection = https_connection.CertValidatingHTTPSConnection(
                    host, ca_certs=self.ca_certificates_file,
                    **http_connection_kwargs)
            else:
                connection = http_client.HTTPSConnection(
                    host, **http_connection_kwargs)
        else:
            boto.log.debug('establishing HTTP connection: kwargs=%s' %
                           http_connection_kwargs)
            if self.https_connection_factory:
                # even though the factory says https, this is too handy
                # to not be able to allow overriding for http also.
                connection = self.https_connection_factory(
                    host, **http_connection_kwargs)
            else:
                connection = http_client.HTTPConnection(
                    host, **http_connection_kwargs)
        if self.debug > 1:
            connection.set_debuglevel(self.debug)
        # self.connection must be maintained for backwards-compatibility
        # however, it must be dynamically pulled from the connection pool
        # set a private variable which will enable that
        if host.split(':')[0] == self.host and is_secure == self.is_secure:
            self._connection = (host, port, is_secure)
        # Set the response class of the http connection to use our custom
        # class.
        connection.response_class = HTTPResponse
        return connection

    def put_http_connection(self, host, port, is_secure, connection):
        self._pool.put_http_connection(host, port, is_secure, connection)

    def proxy_ssl(self, host=None, port=None):
        if host and port:
            host = '%s:%d' % (host, port)
        else:
            host = '%s:%d' % (self.host, self.port)
        # Seems properly to use timeout for connect too
        timeout = self.http_connection_kwargs.get("timeout")
        if timeout is not None:
            sock = socket.create_connection((self.proxy,
                                             int(self.proxy_port)), timeout)
        else:
            sock = socket.create_connection((self.proxy, int(self.proxy_port)))
        boto.log.debug("Proxy connection: CONNECT %s HTTP/1.0\r\n", host)
        sock.sendall(six.ensure_binary("CONNECT %s HTTP/1.0\r\n" % host))
        sock.sendall(six.ensure_binary("User-Agent: %s\r\n" % UserAgent))
        if self.proxy_user and self.proxy_pass:
            for k, v in self.get_proxy_auth_header().items():
                sock.sendall(six.ensure_binary("%s: %s\r\n" % (k, v)))
            # See discussion about this config option at
            # https://groups.google.com/forum/?fromgroups#!topic/boto-dev/teenFvOq2Cc
            if config.getbool('Boto', 'send_crlf_after_proxy_auth_headers', False):
                sock.sendall(six.ensure_binary("\r\n"))
        else:
            sock.sendall(six.ensure_binary("\r\n"))
        resp = http_client.HTTPResponse(sock, debuglevel=self.debug)
        resp.begin()

        if resp.status != 200:
            # Fake a socket error, use a code that make it obvious it hasn't
            # been generated by the socket library
            raise socket.error(
                -71,
                six.ensure_binary(
                    "Error talking to HTTP proxy %s:%s: %s (%s)" %
                    (self.proxy,
                     self.proxy_port,
                     resp.status,
                     resp.reason)))

        # We can safely close the response, it duped the original socket
        resp.close()

        h = http_client.HTTPConnection(host)

        if self.https_validate_certificates and HAVE_HTTPS_CONNECTION:
            msg = "wrapping ssl socket for proxied connection; "
            if self.ca_certificates_file:
                msg += "CA certificate file=%s" % self.ca_certificates_file
            else:
                msg += "using system provided SSL certs"
            boto.log.debug(msg)
            key_file = self.http_connection_kwargs.get('key_file', None)
            cert_file = self.http_connection_kwargs.get('cert_file', None)

            context = ssl.create_default_context()
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = True
            if cert_file:
              context.load_cert_chain(cert_file, key_file)
            context.load_verify_locations(self.ca_certificates_file)
            sslSock = context.wrap_socket(sock, server_hostname=self.host)
            cert = sslSock.getpeercert()
            hostname = self.host.split(':', 0)[0]
            if not https_connection.ValidateCertificateHostname(cert, hostname):
                raise https_connection.InvalidCertificateException(
                    hostname, cert, 'hostname mismatch')
        else:
            # Fallback for old Python without ssl.wrap_socket
            if hasattr(http_client, 'ssl'):
                sslSock = http_client.ssl.SSLSocket(sock)
            else:
                sslSock = socket.ssl(sock, None, None)
                sslSock = http_client.FakeSocket(sock, sslSock)

        # This is a bit unclean
        h.sock = sslSock
        return h

    def prefix_proxy_to_path(self, path, host=None):
        path = self.protocol + '://' + (host or self.server_name()) + path
        return path

    def get_proxy_auth_header(self):
        auth = encodebytes(self.proxy_user + ':' + self.proxy_pass)
        return {'Proxy-Authorization': 'Basic %s' % auth}

    # For passing proxy information to other connection libraries, e.g. cloudsearch2
    def get_proxy_url_with_auth(self):
        if not self.use_proxy:
            return None

        if self.proxy_user or self.proxy_pass:
            if self.proxy_pass:
                login_info = '%s:%s@' % (self.proxy_user, self.proxy_pass)
            else:
                login_info = '%s@' % self.proxy_user
        else:
            login_info = ''

        return 'http://%s%s:%s' % (login_info, self.proxy, str(self.proxy_port or self.port))

    def set_host_header(self, request):
        try:
            request.headers['Host'] = \
                self._auth_handler.host_header(self.host, request)
        except AttributeError:
            request.headers['Host'] = self.host.split(':', 1)[0]

    def set_request_hook(self, hook):
        self.request_hook = hook

    def _mexe(self, request, sender=None, override_num_retries=None,
              retry_handler=None):
        """
        mexe - Multi-execute inside a loop, retrying multiple times to handle
               transient Internet errors by simply trying again.
               Also handles redirects.

        This code was inspired by the S3Utils classes posted to the boto-users
        Google group by Larry Bates.  Thanks!

        """
        boto.log.debug('Method: %s' % request.method)
        boto.log.debug('Path: %s' % request.path)
        boto.log.debug('Data: %s' % request.body)
        boto.log.debug('Headers: %s' % request.headers)
        boto.log.debug('Host: %s' % request.host)
        boto.log.debug('Port: %s' % request.port)
        boto.log.debug('Params: %s' % request.params)
        response = None
        body = None
        ex = None
        if override_num_retries is None:
            num_retries = config.getint('Boto', 'num_retries', self.num_retries)
        else:
            num_retries = override_num_retries
        i = 0
        connection = self.get_http_connection(request.host, request.port,
                                              self.is_secure)

        # Convert body to bytes if needed
        if not isinstance(request.body, bytes) and hasattr(request.body,
                                                           'encode'):
            request.body = request.body.encode('utf-8')

        while i <= num_retries:
            # Use binary exponential backoff to desynchronize client requests.
            next_sleep = min(random.random() * (2 ** i),
                             float(boto.config.get('Boto', 'max_retry_delay', 60)))
            try:
                # we now re-sign each request before it is retried
                boto.log.debug('Token: %s' % self.provider.security_token)
                request.authorize(connection=self)
                # Only force header for non-s3 connections, because s3 uses
                # an older signing method + bucket resource URLs that include
                # the port info. All others should be now be up to date and
                # not include the port.
                if 's3' not in self._required_auth_capability():
                    if not getattr(self, 'anon', False):
                        if not request.headers.get('Host'):
                            self.set_host_header(request)
                boto.log.debug('Final headers: %s' % request.headers)
                request.start_time = datetime.now()
                if callable(sender):
                    response = sender(connection, request.method, request.path,
                                      request.body, request.headers)
                else:
                    connection.request(request.method, request.path,
                                       request.body, request.headers)
                    response = connection.getresponse()
                boto.log.debug('Response headers: %s' % response.getheaders())
                location = response.getheader('location')
                # -- gross hack --
                # http_client gets confused with chunked responses to HEAD requests
                # so I have to fake it out
                if request.method == 'HEAD' and getattr(response,
                                                        'chunked', False):
                    response.chunked = 0
                if callable(retry_handler):
                    status = retry_handler(response, i, next_sleep)
                    if status:
                        msg, i, next_sleep = status
                        if msg:
                            boto.log.debug(msg)
                        time.sleep(next_sleep)
                        continue
                if response.status in [500, 502, 503, 504]:
                    msg = 'Received %d response.  ' % response.status
                    msg += 'Retrying in %3.1f seconds' % next_sleep
                    boto.log.debug(msg)
                    body = response.read()
                    if isinstance(body, bytes):
                        body = body.decode('utf-8')
                elif response.status < 300 or response.status >= 400 or \
                        not location:
                    # don't return connection to the pool if response contains
                    # Connection:close header, because the connection has been
                    # closed and default reconnect behavior may do something
                    # different than new_http_connection. Also, it's probably
                    # less efficient to try to reuse a closed connection.
                    conn_header_value = response.getheader('connection')
                    if conn_header_value == 'close':
                        connection.close()
                    else:
                        self.put_http_connection(request.host, request.port,
                                                 self.is_secure, connection)
                    if self.request_hook is not None:
                        self.request_hook.handle_request_data(request, response)
                    return response
                else:
                    scheme, request.host, request.path, \
                        params, query, fragment = urlparse(location)
                    if query:
                        request.path += '?' + query
                    # urlparse can return both host and port in netloc, so if
                    # that's the case we need to split them up properly
                    if ':' in request.host:
                        request.host, request.port = request.host.split(':', 1)
                    msg = 'Redirecting: %s' % scheme + '://'
                    msg += request.host + request.path
                    boto.log.debug(msg)
                    connection = self.get_http_connection(request.host,
                                                          request.port,
                                                          scheme == 'https')
                    response = None
                    continue
            except PleaseRetryException as e:
                boto.log.debug('encountered a retry exception: %s' % e)
                connection = self.new_http_connection(request.host, request.port,
                                                      self.is_secure)
                response = e.response
                ex = e
            except self.http_exceptions as e:
                for unretryable in self.http_unretryable_exceptions:
                    if isinstance(e, unretryable):
                        boto.log.debug(
                            'encountered unretryable %s exception, re-raising' %
                            e.__class__.__name__)
                        raise
                boto.log.debug('encountered %s exception, reconnecting' %
                               e.__class__.__name__)
                connection = self.new_http_connection(request.host, request.port,
                                                      self.is_secure)
                ex = e
            time.sleep(next_sleep)
            i += 1
        # If we made it here, it's because we have exhausted our retries
        # and stil haven't succeeded.  So, if we have a response object,
        # use it to raise an exception.
        # Otherwise, raise the exception that must have already happened.
        if self.request_hook is not None:
            self.request_hook.handle_request_data(request, response, error=True)
        if response:
            raise BotoServerError(response.status, response.reason, body)
        elif ex:
            raise ex
        else:
            msg = 'Please report this exception as a Boto Issue!'
            raise BotoClientError(msg)

    def build_base_http_request(self, method, path, auth_path,
                                params=None, headers=None, data='', host=None):
        path = self.get_path(path)
        if auth_path is not None:
            auth_path = self.get_path(auth_path)
        if params is None:
            params = {}
        else:
            params = params.copy()
        if headers is None:
            headers = {}
        else:
            headers = headers.copy()
        if self.host_header and not boto.utils.find_matching_headers('host', headers):
            headers['host'] = self.host_header
        host = host or self.host
        if self.use_proxy and not self.skip_proxy(host):
            if not auth_path:
                auth_path = path
            path = self.prefix_proxy_to_path(path, host)
            if self.proxy_user and self.proxy_pass and not self.is_secure:
                # If is_secure, we don't have to set the proxy authentication
                # header here, we did that in the CONNECT to the proxy.
                headers.update(self.get_proxy_auth_header())
        return HTTPRequest(method, self.protocol, host, self.port,
                           path, auth_path, params, headers, data)

    def _find_s3_host(self, endpoint):
        # An s3 endpoint is of the form bucket-name.s3(.{region}).amazonaws.com,
        # where the host is everything after "bucket-name." Note that ".s3."
        # can also appear in bucket-name, so we need to find the last
        # occurrence of ".s3." to find the host.
        ix = endpoint.rfind('.s3.')
        if ix == -1:
            return None
        return ix + 1

    def _get_s3_host(self, endpoint):
        ix = self._find_s3_host(endpoint)
        if ix:
            return endpoint[ix:]

    def _change_s3_host(self, endpoint, new_host):
        ix = self._find_s3_host(endpoint)
        if ix:
            return endpoint[:ix] + new_host

    def _fix_s3_endpoint_region(self, endpoint, correct_region):
        """Return a new bucket endpoint that uses correct_region.
        Return None if host substitution is not possible.
        """
        if not (endpoint and correct_region):
            return None
        new_host = 's3.%s.amazonaws.com' % correct_region
        new_endpoint = self._change_s3_host(endpoint, new_host)
        if new_endpoint:
            return new_endpoint
        boto.log.debug('Could not change s3 host for %s' % endpoint)

    def _get_correct_s3_endpoint_from_response(self, request,
                                               err, get_header):
        """Attempt to return a new s3 endpoint using the correct region to
        access a bucket. Return None if a retry is not possible."""

        # 1. Look at error response headers, if available.
        if callable(get_header):
            region = get_header('x-amz-bucket-region')
            if region:
                boto.log.debug('Got correct region from response headers.')
                return self._fix_s3_endpoint_region(request.host, region)

        # 2. Look in the response body.
        if err.region:
            boto.log.debug('Got correct region from parsed xml in err.region.')
            return self._fix_s3_endpoint_region(request.host, err.region)
        elif err.error_code == 'IllegalLocationConstraintException':
            region_regex = (
                'The (.*?) location constraint is incompatible for the region '
                'specific endpoint this request was sent to\.'
            )
            match = re.search(region_regex, err.body)
            if match and match.group(1) != 'unspecified':
                region = match.group(1)
                boto.log.debug('Got correct region from response body.')
                return self._fix_s3_endpoint_region(request.host, region)
        elif err.endpoint:
            boto.log.debug('Got correct endpoint from response body.')
            return err.endpoint

        # 3. Last resort: send another request.
        boto.log.debug('Sending a bucket HEAD request to get correct region.')
        req = self.build_base_http_request(
            'HEAD', '/', '/', {}, None, '', request.host)
        bucket_head_response = self._mexe(req, None, None)
        region = bucket_head_response.getheader('x-amz-bucket-region')
        if region:
            boto.log.debug('Got correct region from a bucket head request.')
            return self._fix_s3_endpoint_region(request.host, region)

    def _change_s3_host_from_error(self, request, err, get_header=None):
        new_endpoint = self._get_correct_s3_endpoint_from_response(
            request,
            err,
            get_header
        )
        if not new_endpoint:
            return None

        msg = 'This request was sent to %s, ' % request.host
        msg += 'when it should have been sent to %s. ' % new_endpoint
        request.host = new_endpoint

        new_host = self._get_s3_host(new_endpoint)
        if new_host and new_host != self.host:
            msg += 'This error may have arisen because your S3 host, '
            msg += 'currently %s, is configured incorrectly. ' % self.host
            msg += 'Please change your configuration to use %s ' % new_host
            msg += 'to avoid multiple unnecessary redirects '
            msg += 'and signing attempts.'
            self.host = new_host

        boto.log.debug(msg)
        return request

    def _get_request_for_s3_retry(self, http_request, response, err):
        if response:
            body = response.read()
            if body:
                body = body.decode('utf-8')
            # wrap response in an S3 error so its xml body is parsed.
            err = S3ResponseError(response.status, response.reason, body)
            return self._change_s3_host_from_error(
                http_request,
                err,
                get_header=response.getheader
            )
        elif err:
            return self._change_s3_host_from_error(
                http_request,
                err
            )

    def make_request(self, method, path, headers=None, data='', host=None,
                     auth_path=None, sender=None, override_num_retries=None,
                     params=None, retry_handler=None):
        """Make a request to the server.
        Include logic for retrying on s3 region errors.
        """
        if params is None:
            params = {}
        http_request = self.build_base_http_request(
            method, path, auth_path, params, headers, data, host)
        response, err = None, None
        try:
            response = self._mexe(http_request, sender, override_num_retries,
                                  retry_handler=retry_handler)
        except S3ResponseError as e:
            # Sender functions passed into _mexe often call
            # connection.getresponse directly, and raise their own exceptions
            # if a request fails. See _send_file_internal in s3/key.py. The
            # exception can contain information useful for a retry, however,
            # so it needs to be in scope for the retry logic below.
            err = e

        status = (response or err).status
        if http_request.host.endswith('amazonaws.com') and status in [301, 400]:
            retry_request = self._get_request_for_s3_retry(
                http_request,
                response,
                err
            )
            if retry_request:
                return self._mexe(retry_request, sender, override_num_retries,
                                  retry_handler=retry_handler)

        if response:
            # Note: a response returned here will not be readable using
            # response.read(amt) if it came from an s3 request and its status
            # code is 301 or 400. This is because response.read() is called
            # above under these conditions, and response.read(amt) does not
            # return bytes after read has been called once. Make sure to check
            # for a non-error status code before calling response.read(amt)!
            return response
        elif err:
            raise err

    def close(self):
        """(Optional) Close any open HTTP connections.  This is non-destructive,
        and making a new request will open a connection again."""

        boto.log.debug('closing all HTTP connections')
        self._connection = None  # compat field


class AWSQueryConnection(AWSAuthConnection):

    APIVersion = ''
    ResponseError = BotoServerError

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, host=None, debug=0,
                 https_connection_factory=None, path='/', security_token=None,
                 validate_certs=True, profile_name=None, provider='aws'):
        super(AWSQueryConnection, self).__init__(
            host, aws_access_key_id,
            aws_secret_access_key,
            is_secure, port, proxy,
            proxy_port, proxy_user, proxy_pass,
            debug, https_connection_factory, path,
            security_token=security_token,
            validate_certs=validate_certs,
            profile_name=profile_name,
            provider=provider)

    def _required_auth_capability(self):
        return []


    def get_utf8_value(self, value):
        return boto.utils.get_utf8_value(value)


    def make_request(self, action, params=None, path='/', verb='GET'):
        http_request = self.build_base_http_request(verb, path, None,
                                                    params, {}, '',
                                                    self.host)
        if action:
            http_request.params['Action'] = action
        if self.APIVersion:
            http_request.params['Version'] = self.APIVersion
        return self._mexe(http_request)

    def build_list_params(self, params, items, label):
        if isinstance(items, six.string_types):
            items = [items]
        for i in range(1, len(items) + 1):
            params['%s.%d' % (label, i)] = items[i - 1]

    def build_complex_list_params(self, params, items, label, names):
        """Serialize a list of structures.

        For example::

            items = [('foo', 'bar', 'baz'), ('foo2', 'bar2', 'baz2')]
            label = 'ParamName.member'
            names = ('One', 'Two', 'Three')
            self.build_complex_list_params(params, items, label, names)

        would result in the params dict being updated with these params::

            ParamName.member.1.One = foo
            ParamName.member.1.Two = bar
            ParamName.member.1.Three = baz

            ParamName.member.2.One = foo2
            ParamName.member.2.Two = bar2
            ParamName.member.2.Three = baz2

        :type params: dict
        :param params: The params dict.  The complex list params
            will be added to this dict.

        :type items: list of tuples
        :param items: The list to serialize.

        :type label: string
        :param label: The prefix to apply to the parameter.

        :type names: tuple of strings
        :param names: The names associated with each tuple element.

        """
        for i, item in enumerate(items, 1):
            current_prefix = '%s.%s' % (label, i)
            for key, value in zip(names, item):
                full_key = '%s.%s' % (current_prefix, key)
                params[full_key] = value

    # generics

    def get_list(self, action, params, markers, path='/',
                 parent=None, verb='GET'):
        if not parent:
            parent = self
        response = self.make_request(action, params, path, verb)
        body = response.read()
        boto.log.debug(body)
        if not body:
            boto.log.error('Null body %s' % body)
            raise self.ResponseError(response.status, response.reason, body)
        elif response.status == 200:
            rs = ResultSet(markers)
            h = boto.handler.XmlHandler(rs, parent)
            if isinstance(body, six.text_type):
                body = body.encode('utf-8')
            xml.sax.parseString(body, h)
            return rs
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)

    def get_object(self, action, params, cls, path='/',
                   parent=None, verb='GET'):
        if not parent:
            parent = self
        response = self.make_request(action, params, path, verb)
        body = response.read()
        boto.log.debug(body)
        if not body:
            boto.log.error('Null body %s' % body)
            raise self.ResponseError(response.status, response.reason, body)
        elif response.status == 200:
            obj = cls(parent)
            h = boto.handler.XmlHandler(obj, parent)
            if isinstance(body, six.text_type):
                body = body.encode('utf-8')
            xml.sax.parseString(body, h)
            return obj
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)

    def get_status(self, action, params, path='/', parent=None, verb='GET'):
        if not parent:
            parent = self
        response = self.make_request(action, params, path, verb)
        body = response.read()
        boto.log.debug(body)
        if not body:
            boto.log.error('Null body %s' % body)
            raise self.ResponseError(response.status, response.reason, body)
        elif response.status == 200:
            rs = ResultSet()
            h = boto.handler.XmlHandler(rs, parent)
            xml.sax.parseString(body, h)
            return rs.status
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)
