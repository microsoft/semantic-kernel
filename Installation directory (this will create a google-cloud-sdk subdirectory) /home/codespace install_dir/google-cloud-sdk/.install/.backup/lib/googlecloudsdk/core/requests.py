# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A module to get an unauthenticated requests.Session object."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import collections
import inspect
import io

from google.auth.transport import requests as google_auth_requests
from google.auth.transport.requests import _MutualTlsOffloadAdapter
from googlecloudsdk.core import context_aware
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import transport
from googlecloudsdk.core.util import http_proxy_types
from googlecloudsdk.core.util import platforms

import httplib2
import requests
import six

from six.moves import http_client as httplib
from six.moves import urllib
import socks
from urllib3.util.ssl_ import create_urllib3_context

try:
  import urllib.request as urllib_request  # pylint: disable=g-import-not-at-top
except ImportError:  # PY2
  import urllib as urllib_request  # pylint: disable=g-import-not-at-top


_INVALID_HTTPS_PROXY_ENV_VAR_WARNING = (
    'It appears that the current proxy configuration is using an HTTPS scheme '
    'for contacting the proxy server, which likely indicates an error in your '
    'HTTPS_PROXY environment variable setting. This can usually be resolved '
    'by setting HTTPS_PROXY=http://... instead of HTTPS_PROXY=https://... '
    'See https://cloud.google.com/sdk/docs/proxy-settings for more information.'
)
_invalid_https_proxy_env_var_warning_shown = False


def GetSession(timeout='unset',
               ca_certs=None,
               session=None,
               streaming_response_body=False,
               redact_request_body_reason=None,
               client_certificate=None,
               client_key=None,):
  """Get a requests.Session that is properly configured for use by gcloud.

  This method does not add credentials to the client. For a requests.Session
  that has been authenticated, use core.credentials.requests.GetSession().

  Args:
    timeout: double, The timeout in seconds. This is the
        socket level timeout. If timeout is None, timeout is infinite. If
        default argument 'unset' is given, a sensible default is selected using
        transport.GetDefaultTimeout().
    ca_certs: str, absolute filename of a ca_certs file that overrides the
        default. The gcloud config property for ca_certs, in turn, overrides
        this argument.
    session: requests.Session instance
    streaming_response_body: bool, True indicates that the response body will
        be a streaming body.
    redact_request_body_reason: str, the reason why the request body must be
        redacted if --log-http is used. If None, the body is not redacted.
    client_certificate: str, absolute filename of a client_certificate file that
        is set explicitly for client certificate authentication
    client_key: str, absolute filename of a client_key file that
        is set explicitly for client certificate authentication

  Returns:
    A requests.Session object configured with all the required settings
    for gcloud.
  """
  http_client = _CreateRawSession(timeout, ca_certs, session,
                                  client_certificate, client_key)
  http_client = RequestWrapper().WrapWithDefaults(
      http_client,
      streaming_response_body=streaming_response_body,
      redact_request_body_reason=redact_request_body_reason)
  return http_client


class ClientSideCertificate(
    collections.namedtuple('ClientSideCertificate',
                           ['certfile', 'keyfile', 'password'])):
  """Holds information about a client side certificate.

  Attributes:
    certfile: str, path to a cert file.
    keyfile: str, path to a key file.
    password: str, password to the private key.
  """

  def __new__(cls, certfile, keyfile, password=None):
    return super(ClientSideCertificate, cls).__new__(
        cls, certfile, keyfile, password)


def CreateSSLContext():
  """Returns a urrlib3 SSL context."""
  return create_urllib3_context()


class HTTPAdapter(requests.adapters.HTTPAdapter):
  """Transport adapter for requests.

  Transport adapters provide an interface to extend the default behavior of the
  requests library using the full power of the underlying urrlib3 library.

  See https://requests.readthedocs.io/en/master/user/advanced/
      #transport-adapters for more information about adapters.
  """

  def __init__(self, client_side_certificate, *args, **kwargs):
    self._cert_info = client_side_certificate
    super(HTTPAdapter, self).__init__(*args, **kwargs)

  def init_poolmanager(self, *args, **kwargs):
    self._add_ssl_context(kwargs)
    return super(HTTPAdapter, self).init_poolmanager(*args, **kwargs)

  def proxy_manager_for(self, *args, **kwargs):
    self._add_ssl_context(kwargs)
    return super(HTTPAdapter, self).proxy_manager_for(*args, **kwargs)

  def _add_ssl_context(self, kwargs):
    if not self._cert_info:
      return

    context = CreateSSLContext()

    cert_chain_kwargs = {}
    if self._cert_info.keyfile:
      cert_chain_kwargs['keyfile'] = self._cert_info.keyfile
    if self._cert_info.password:
      cert_chain_kwargs['password'] = self._cert_info.password

    context.load_cert_chain(self._cert_info.certfile, **cert_chain_kwargs)

    kwargs['ssl_context'] = context


def GetProxyInfo():
  """Returns the proxy string for use by requests from gcloud properties.

  See https://requests.readthedocs.io/en/master/user/advanced/#proxies.
  """
  proxy_type = properties.VALUES.proxy.proxy_type.Get()
  proxy_address = properties.VALUES.proxy.address.Get()
  proxy_port = properties.VALUES.proxy.port.GetInt()

  proxy_prop_set = len(
      [f for f in (proxy_type, proxy_address, proxy_port) if f])
  if proxy_prop_set > 0 and proxy_prop_set != 3:
    raise properties.InvalidValueError(
        'Please set all or none of the following properties: '
        'proxy/type, proxy/address and proxy/port')

  if not proxy_prop_set:
    return

  proxy_rdns = properties.VALUES.proxy.rdns.GetBool()
  proxy_user = properties.VALUES.proxy.username.Get()
  proxy_pass = properties.VALUES.proxy.password.Get()

  http_proxy_type = http_proxy_types.PROXY_TYPE_MAP[proxy_type]
  if http_proxy_type == socks.PROXY_TYPE_SOCKS4:
    proxy_scheme = 'socks4a' if proxy_rdns else 'socks4'
  elif http_proxy_type == socks.PROXY_TYPE_SOCKS5:
    proxy_scheme = 'socks5h' if proxy_rdns else 'socks5'
  elif http_proxy_type == socks.PROXY_TYPE_HTTP:
    proxy_scheme = 'http'
  else:
    raise ValueError('Unsupported proxy type: {}'.format(proxy_type))

  if proxy_user or proxy_pass:
    proxy_auth = ':'.join(
        urllib.parse.quote(x) or '' for x in (proxy_user, proxy_pass))
    proxy_auth += '@'
  else:
    proxy_auth = ''
  return '{}://{}{}:{}'.format(proxy_scheme, proxy_auth, proxy_address,
                               proxy_port)


def CreateMutualTlsOffloadAdapter(certificate_config_file_path):
  return _MutualTlsOffloadAdapter(certificate_config_file_path)


def Session(
    timeout=None,
    ca_certs=None,
    disable_ssl_certificate_validation=False,
    session=None,
    client_certificate=None,
    client_key=None):
  """Returns a requests.Session subclass.

  Args:
    timeout: float, Request timeout, in seconds.
    ca_certs: str, absolute filename of a ca_certs file
    disable_ssl_certificate_validation: bool, If true, disable ssl certificate
        validation.
    session: requests.Session instance. Otherwise, a new requests.Session will
        be initialized.
    client_certificate: str, absolute filename of a client_certificate file
    client_key: str, absolute filename of a client_key file

  Returns: A requests.Session subclass.
  """
  session = session or requests.Session()
  proxy_info = GetProxyInfo()

  orig_request_method = session.request
  def WrappedRequest(*args, **kwargs):
    if 'timeout' not in kwargs:
      kwargs['timeout'] = timeout

    # Work around a proxy bug in Python's standard library on Windows.
    if _HasBpo42627() and 'proxies' not in kwargs:
      kwargs['proxies'] = _AdjustProxiesKwargForBpo42627(
          proxy_info, urllib_request.getproxies_environment(),
          orig_request_method, *args, **kwargs)

    return orig_request_method(*args, **kwargs)
  session.request = WrappedRequest

  if proxy_info:
    session.trust_env = False
    session.proxies = {
        'http': proxy_info,
        'https': proxy_info,
    }
  elif _HasInvalidHttpsProxyEnvVarScheme():
    # Requests (and by extension gcloud) currently only supports connecting to
    # proxy servers via HTTP. Until that changes, provide a more informative
    # message when attempting to connect via HTTPS (usually due to a
    # misconfigured HTTPS_PROXY env var), since this now results in a (rather
    # opaque) error as of newer versions of urllib3 (b/228647259#comment30).
    global _invalid_https_proxy_env_var_warning_shown
    if not _invalid_https_proxy_env_var_warning_shown:
      # Just do this once per command invocation to avoid spamming the warning
      # multiple times (we initialize multiple sessions per command).
      _invalid_https_proxy_env_var_warning_shown = True
      log.warning(_INVALID_HTTPS_PROXY_ENV_VAR_WARNING)

  client_side_certificate = None
  if client_certificate is not None and client_key is not None and ca_certs is not None:
    log.debug(
        'Using provided server certificate %s, client certificate %s, client certificate key %s',
        ca_certs, client_certificate, client_key)
    client_side_certificate = ClientSideCertificate(
        client_certificate, client_key)
    adapter = HTTPAdapter(client_side_certificate)
  else:
    ca_config = context_aware.Config()
    if ca_config:
      if ca_config.config_type == context_aware.ConfigType.ENTERPRISE_CERTIFICATE:
        adapter = CreateMutualTlsOffloadAdapter(
            ca_config.certificate_config_file_path)
      elif ca_config.config_type == context_aware.ConfigType.ON_DISK_CERTIFICATE:
        log.debug('Using client certificate %s',
                  ca_config.encrypted_client_cert_path)
        client_side_certificate = ClientSideCertificate(
            ca_config.encrypted_client_cert_path,
            ca_config.encrypted_client_cert_path,
            ca_config.encrypted_client_cert_password)
        adapter = HTTPAdapter(client_side_certificate)
      else:
        adapter = HTTPAdapter(None)
    else:
      adapter = HTTPAdapter(None)

  if disable_ssl_certificate_validation:
    session.verify = False
  elif ca_certs:
    session.verify = ca_certs

  session.mount('https://', adapter)
  return session


def _CreateRawSession(timeout='unset', ca_certs=None, session=None,
                      client_certificate=None, client_key=None):
  """Create a requests.Session matching the appropriate gcloud properties."""
  # Compared with setting the default timeout in the function signature (i.e.
  # timeout=300), this lets you test with short default timeouts by mocking
  # GetDefaultTimeout.
  if timeout != 'unset':
    effective_timeout = timeout
  else:
    effective_timeout = transport.GetDefaultTimeout()

  no_validate = properties.VALUES.auth.disable_ssl_validation.GetBool() or False
  ca_certs_property = properties.VALUES.core.custom_ca_certs_file.Get()
  # Believe an explicitly-set ca_certs property over anything we added.
  if ca_certs_property:
    ca_certs = ca_certs_property
  if no_validate:
    ca_certs = None
  return Session(timeout=effective_timeout,
                 ca_certs=ca_certs,
                 disable_ssl_certificate_validation=no_validate,
                 session=session,
                 client_certificate=client_certificate,
                 client_key=client_key)


def _GetURIFromRequestArgs(url, params):
  """Gets the complete URI by merging url and params from the request args."""
  url_parts = urllib.parse.urlsplit(url)
  query_params = urllib.parse.parse_qs(url_parts.query, keep_blank_values=True)
  for param, value in six.iteritems(params or {}):
    query_params[param] = value
  # Need to do this to convert a SplitResult into a list so it can be modified.
  url_parts = list(url_parts)
  # pylint:disable=redundant-keyword-arg, this is valid syntax for this lib
  url_parts[3] = urllib.parse.urlencode(query_params, doseq=True)

  # pylint:disable=too-many-function-args, This is just bogus.
  return urllib.parse.urlunsplit(url_parts)


class Request(transport.Request):
  """Encapsulates parameters for making a general HTTP request.

  This implementation does additional manipulation to ensure that the request
  parameters are specified in the same way as they were specified by the
  caller. That is, if the user calls:
      request('URI', 'GET', None, {'header': '1'})

  After modifying the request, we will call request using positional
  parameters, instead of transforming the request into:
      request('URI', method='GET', body=None, headers={'header': '1'})
  """

  @classmethod
  def FromRequestArgs(cls, *args, **kwargs):
    return cls(*args, **kwargs)

  def __init__(self, method, url, params=None, data=None, headers=None,
               **kwargs):
    self._kwargs = kwargs
    uri = _GetURIFromRequestArgs(url, params)
    super(Request, self).__init__(uri, method, headers or {}, data)

  def ToRequestArgs(self):
    args = [self.method, self.uri]
    kwargs = dict(self._kwargs)
    kwargs['headers'] = self.headers
    if self.body:
      kwargs['data'] = self.body
    return args, kwargs


class Response(transport.Response):
  """Encapsulates responses from making a general HTTP request."""

  @classmethod
  def FromResponse(cls, response):
    return cls(response.status_code, response.headers, response.content)


class RequestWrapper(transport.RequestWrapper):
  """Class for wrapping request.Session requests."""

  request_class = Request
  response_class = Response

  def DecodeResponse(self, response, response_encoding):
    """Returns the response without decoding."""
    del response_encoding  # unused
    # The response decoding is handled by the _ApitoolsRequests.request method.
    return response


def GoogleAuthRequest():
  """Returns a gcloud's requests session to refresh google-auth credentials."""
  return google_auth_requests.Request(session=GetSession())


class _GoogleAuthApitoolsCredentials():

  def __init__(self, credentials):
    self.credentials = credentials

  def refresh(self, http_client):  # pylint: disable=invalid-name
    del http_client  # unused
    auth_request = GoogleAuthRequest()
    self.credentials.refresh(auth_request)


def GetApitoolsRequests(session, response_handler=None, response_encoding=None):
  """Returns an authenticated httplib2.Http-like object for use by apitools."""
  http_client = _ApitoolsRequests(session, response_handler, response_encoding)
  # apitools needs this attribute to do credential refreshes during batch API
  # requests.
  if hasattr(session, '_googlecloudsdk_credentials'):
    creds = _GoogleAuthApitoolsCredentials(session._googlecloudsdk_credentials)  # pylint: disable=protected-access

    orig_request_method = http_client.request

    # The closure that will replace 'httplib2.Http.request'.
    def HttpRequest(*args, **kwargs):
      return orig_request_method(*args, **kwargs)

    http_client.request = HttpRequest
    setattr(http_client.request, 'credentials', creds)

  return http_client


class ResponseHandler(six.with_metaclass(abc.ABCMeta)):
  """Handler to process the Http Response.

  Attributes:
    use_stream: bool, if True, the response body gets returned as a stream
        of data instead of returning the entire body at once.
  """

  def __init__(self, use_stream):
    """Initializes ResponseHandler.

    Args:
      use_stream: bool, if True, the response body gets returned as a stream of
        data instead of returning the entire body at once.
    """
    self.use_stream = use_stream

  @abc.abstractmethod
  def handle(self, response_stream):
    """Handles the http response."""


class _ApitoolsRequests():
  """A httplib2.Http-like object for use by apitools."""

  def __init__(self, session, response_handler=None, response_encoding=None):
    self.session = session
    # Mocks the dictionary of connection instances that apitools iterates over
    # to modify the underlying connection.
    self.connections = {}
    if response_handler:
      if not isinstance(response_handler, ResponseHandler):
        raise ValueError('response_handler should be of type ResponseHandler.')
    self._response_handler = response_handler
    self._response_encoding = response_encoding

  def ResponseHook(self, response, *args, **kwargs):
    """Response hook to be used if response_handler has been set."""
    del args, kwargs  # Unused.
    if response.status_code not in (httplib.OK, httplib.PARTIAL_CONTENT):
      log.debug('Skipping response_handler as response is invalid.')
      return

    if (self._response_handler.use_stream and
        properties.VALUES.core.log_http.GetBool() and
        properties.VALUES.core.log_http_streaming_body.GetBool()):
      # The response_handler uses streaming body, but since a request was
      # made to log the response body, we should retain a copy of the response
      # data. A call to response.content would read the entire data in-memory.
      stream = io.BytesIO(response.content)
    else:
      stream = response.raw
    self._response_handler.handle(stream)

  def request(
      self,
      uri,
      method='GET',
      body=None,
      headers=None,
      redirections=0,
      connection_type=None,
  ):  # pylint: disable=invalid-name
    """Makes an HTTP request using httplib2 semantics."""
    del connection_type  # Unused

    if redirections > 0:
      self.session.max_redirects = redirections

    hooks = {}
    if self._response_handler is not None:
      hooks['response'] = self.ResponseHook
      use_stream = self._response_handler.use_stream
    else:
      use_stream = False

    response = self.session.request(
        method, uri, data=body, headers=headers, stream=use_stream, hooks=hooks)
    headers = dict(response.headers)
    headers['status'] = response.status_code

    if use_stream:
      # If use_stream is True, we assume that the data will be read from the
      # response_handler
      content = b''
    elif self._response_encoding is not None:
      # We update response.encoding before calling response.text because
      # response.text property will try to make an educated guess about the
      # encoding based on the response header, which might be different from
      # the self._response_encoding set by the caller.
      response.encoding = self._response_encoding
      content = response.text
    else:
      content = response.content

    return httplib2.Response(headers), content


def _HasInvalidHttpsProxyEnvVarScheme():
  """Returns whether the HTTPS proxy env var is using an HTTPS scheme."""
  # We call urllib.getproxies_environment instead of checking os.environ
  # ourselves to ensure we match the semantics of what the requests library ends
  # up doing.
  env_proxies = urllib_request.getproxies_environment()
  return env_proxies.get('https', '').startswith('https://')


def _HasBpo42627():
  """Returns whether Python is affected by https://bugs.python.org/issue42627.

  Due to a bug in Python's standard library, urllib.request misparses the
  Windows registry proxy settings and assumes that HTTPS URLs should use an
  HTTPS proxy, when in fact they should use an HTTP proxy.

  This bug affects PY<3.9, as well as lower patch versions of 3.9, 3.10, and
  3.11.

  Returns:
    True if proxies read from the Windows registry are being parsed incorrectly.
  """
  return (
      platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS
      and hasattr(urllib_request, 'getproxies_registry')
      and urllib_request.getproxies_registry().get('https', '').startswith(
          'https://')
  )


def _AdjustProxiesKwargForBpo42627(
    gcloud_proxy_info, environment_proxies,
    orig_request_method, *args, **kwargs):
  """Returns proxies to workaround https://bugs.python.org/issue42627 if needed.

  Args:
    gcloud_proxy_info: str, Proxy info from gcloud properties.
    environment_proxies: dict, Proxy config from http/https_proxy env vars.
    orig_request_method: function, The original requests.Session.request method.
    *args: Positional arguments to the original request method.
    **kwargs: Keyword arguments to the original request method.
  Returns:
    Optional[dict], Adjusted proxies to pass to the request method, or None if
      no adjustment is necessary.
  """
  # Proxy precedence:
  #   gcloud properties > http/https/no_proxy env vars > registry settings
  # So if proxy settings come from either of the first two, then there's no need
  # to adjust anything.
  if gcloud_proxy_info or environment_proxies:
    return None

  # We want to correct proxies incorrectly parsed from the registry by sending a
  # tweaked 'proxies' kwarg to the requests.Session.request method. However,
  # proxies passed in this manner apply unconditionally, and we still wish to
  # respect the "ProxyOverride" settings from the registry. So we extract the
  # URL passed to the method, and only pass a corrected HTTPS proxy if requests
  # would end up using the proxy for that URL when taking "ProxyOverride"
  # settings into account.
  url = inspect.getcallargs(orig_request_method, *args, **kwargs)['url']  # pylint: disable=deprecated-method, for PY2 compatibility
  proxies = requests.utils.get_environ_proxies(url)  # Respects ProxyOverride.
  https_proxy = proxies.get('https')
  if not https_proxy:
    return None

  if not https_proxy.startswith('https://'):
    # This should theoretically never happen, since
    # requests.utils.get_environ_proxies should have returned proxies from the
    # registry if we got here, and those will have been bugged. But just in case
    # some implementation detail changes, don't try to adjust anything.
    return None

  return {
      'https': https_proxy.replace('https://', 'http://', 1)
  }
