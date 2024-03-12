# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Run a web flow for oauth2."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import contextlib
import select
import socket
import sys
import webbrowser
import wsgiref
from google_auth_oauthlib import flow as google_auth_flow

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions as c_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import requests
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import pkg_resources

from oauthlib.oauth2.rfc6749 import errors as rfc6749_errors

from requests import exceptions as requests_exceptions
import six
from six.moves import input  # pylint: disable=redefined-builtin
from six.moves.urllib import parse

_PORT_SEARCH_ERROR_MSG = (
    'Failed to start a local webserver listening on any port '
    'between {start_port} and {end_port}. Please check your '
    'firewall settings or locally running programs that may be '
    'blocking or using those ports.')

_PORT_SEARCH_START = 8085
_PORT_SEARCH_END = _PORT_SEARCH_START + 100


class Error(c_exceptions.Error):
  """Exceptions for the flow module."""


class AuthRequestRejectedError(Error):
  """Exception for when the authentication request was rejected."""


class AuthRequestFailedError(Error):
  """Exception for when the authentication request failed."""


class LocalServerCreationError(Error):
  """Exception for when a local server cannot be created."""


class LocalServerTimeoutError(Error):
  """Exception for when the local server timeout before receiving request."""


class WebBrowserInaccessible(Error):
  """Exception for when a web browser is required but not accessible."""


def RaiseProxyError(source_exc):
  six.raise_from(AuthRequestFailedError(
      'Could not reach the login server. A potential cause of this could be '
      'because you are behind a proxy. Please set the environment variables '
      'HTTPS_PROXY and HTTP_PROXY to the address of the proxy in the format '
      '"protocol://address:port" (without quotes) and try again.\n'
      'Example: HTTPS_PROXY=http://192.168.0.1:8080'), source_exc)


def PromptForAuthCode(message, authorize_url, client_config=None):
  ImportReadline(client_config)
  log.err.Print(message.format(url=authorize_url))
  return input('Enter authorization code: ').strip()


@contextlib.contextmanager
def HandleOauth2FlowErrors():
  try:
    yield
  except requests_exceptions.ProxyError as e:
    RaiseProxyError(e)
  except rfc6749_errors.AccessDeniedError as e:
    six.raise_from(AuthRequestRejectedError(e), e)
  except ValueError as e:
    raise six.raise_from(AuthRequestFailedError(e), e)


class WSGIServer(wsgiref.simple_server.WSGIServer):
  """WSGI server to handle more than one connections.

  A normal WSGI server will handle connections one-by-one. When running a local
  server to handle auth redirects, browser opens two connections. One connection
  is used to send the authorization code. The other one is opened but not used.
  Some browsers (i.e. Chrome) send data in the first connection. Other browsers
  (i.e. Safari) send data in the second connection. To make the server working
  for all these browsers, the server should be able to handle two connections
  and smartly read data from the correct connection.
  """

  # pylint: disable=invalid-name, follow the style of the base class.
  def _conn_closed(self, conn):
    """Check if conn is closed at the client side."""
    return not conn.recv(1024, socket.MSG_PEEK)

  def _handle_closed_conn(self, closed_socket, sockets_to_read,
                          client_connections):
    sockets_to_read.remove(closed_socket)
    client_connections[:] = [
        conn for conn in client_connections if conn[0] is not closed_socket
    ]
    self.shutdown_request(closed_socket)

  def _handle_new_client(self, listening_socket, socket_to_read,
                         client_connections):
    request, client_address = listening_socket.accept()
    client_connections.append((request, client_address))
    socket_to_read.append(request)

  def _handle_non_data_conn(self, data_conn, client_connections):
    for request, _ in client_connections:
      if request is not data_conn:
        self.shutdown_request(request)

  def _find_data_conn_with_client_address(self, data_conn, client_connections):
    for request, client_address in client_connections:
      if request is data_conn:
        return request, client_address

  def _find_data_conn(self):
    """Finds the connection which will be used to send data."""
    sockets_to_read = [self.socket]
    client_connections = []
    while True:
      sockets_ready_to_read, _, _ = select.select(sockets_to_read, [], [])
      for s in sockets_ready_to_read:
        # Listening socket is ready to accept client.
        if s is self.socket:
          self._handle_new_client(s, sockets_to_read, client_connections)
        else:
          if self._conn_closed(s):
            self._handle_closed_conn(s, sockets_to_read, client_connections)
          # Found the connection which will be used to send data.
          else:
            self._handle_non_data_conn(s, client_connections)
            return self._find_data_conn_with_client_address(
                s, client_connections)

  # pylint: enable=invalid-name

  def handle_request(self):
    """Handle one request."""
    request, client_address = self._find_data_conn()
    # The following section largely copies the
    # socketserver.BaseSever._handle_request_noblock.
    if self.verify_request(request, client_address):
      try:
        self.process_request(request, client_address)
      except Exception:  # pylint: disable=broad-except
        self.handle_error(request, client_address)
        self.shutdown_request(request)
      except:
        self.shutdown_request(request)
        raise
    else:
      self.shutdown_request(request)


_LOCALHOST = 'localhost'


class InstalledAppFlow(
    six.with_metaclass(abc.ABCMeta, google_auth_flow.InstalledAppFlow)):
  """Base class of authorization flow for installed app.

  Attributes:
    oauth2session: requests_oauthlib.OAuth2Session, The OAuth 2.0 session from
      requests_oauthlib.
    client_type: str, The client type, either "web" or "installed".
    client_config: The client configuration in the Google client secrets format.
    autogenerate_code_verifier: bool, If true, auto-generate a code verifier.
    require_local_server: bool, True if this flow needs a local server to handle
      redirect.
  """

  def __init__(self,
               oauth2session,
               client_type,
               client_config,
               redirect_uri=None,
               code_verifier=None,
               autogenerate_code_verifier=False,
               require_local_server=False):
    session = requests.GetSession(session=oauth2session)
    super(InstalledAppFlow, self).__init__(
        session,
        client_type,
        client_config,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
        autogenerate_code_verifier=autogenerate_code_verifier)
    self.original_client_config = client_config
    if require_local_server:
      self.host = _LOCALHOST
      self.app = _RedirectWSGIApp()
      self.server = CreateLocalServer(self.app, self.host, _PORT_SEARCH_START,
                                      _PORT_SEARCH_END)
      self.redirect_uri = 'http://{}:{}/'.format(self.host,
                                                 self.server.server_port)
    elif redirect_uri:
      self.redirect_uri = redirect_uri
    else:
      self.redirect_uri = self._OOB_REDIRECT_URI
    # include_client_id should be set to True for 1P, and False for 3P.
    self.include_client_id = self.client_config.get('3pi') is None

  def Run(self, **kwargs):
    with HandleOauth2FlowErrors():
      return self._Run(**kwargs)

  @abc.abstractmethod
  def _Run(self, **kwargs):
    pass

  @property
  def _for_adc(self):
    """If the flow is for application default credentials."""
    return (
        self.client_config.get('is_adc')
        or self.client_config.get('client_id') != config.CLOUDSDK_CLIENT_ID
    )

  @property
  def _target_command(self):
    if self._for_adc:
      return 'gcloud auth application-default login'
    else:
      return 'gcloud auth login'

  @classmethod
  def FromInstalledAppFlow(cls, source_flow):
    """Creates an instance of the current flow from an existing flow."""
    return cls.from_client_config(
        source_flow.original_client_config,
        source_flow.oauth2session.scope,
        autogenerate_code_verifier=source_flow.autogenerate_code_verifier)


class FullWebFlow(InstalledAppFlow):
  """The complete OAuth 2.0 authorization flow.

  This class supports user account login using "gcloud auth login" with browser.
  Specifically, it does the following:
    1. Try to find an available port for the local server which handles the
       redirect.
    2. Create a WSGI app on the local server which can direct browser to
       Google's confirmation pages for authentication.
  """

  def __init__(self,
               oauth2session,
               client_type,
               client_config,
               redirect_uri=None,
               code_verifier=None,
               autogenerate_code_verifier=False):
    super(FullWebFlow, self).__init__(
        oauth2session,
        client_type,
        client_config,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
        autogenerate_code_verifier=autogenerate_code_verifier,
        require_local_server=True)

  def _Run(self, **kwargs):
    """Run the flow using the server strategy.

    The server strategy instructs the user to open the authorization URL in
    their browser and will attempt to automatically open the URL for them.
    It will start a local web server to listen for the authorization
    response. Once authorization is complete the authorization server will
    redirect the user's browser to the local web server. The web server
    will get the authorization code from the response and shutdown. The
    code is then exchanged for a token.

    Args:
        **kwargs: Additional keyword arguments passed through to
          "authorization_url".

    Returns:
        google.oauth2.credentials.Credentials: The OAuth 2.0 credentials
          for the user.

    Raises:
      LocalServerTimeoutError: If the local server handling redirection timeout
        before receiving the request.
    """
    auth_url, _ = self.authorization_url(**kwargs)

    webbrowser.open(auth_url, new=1, autoraise=True)

    authorization_prompt_message = (
        'Your browser has been opened to visit:\n\n    {url}\n')
    log.err.Print(authorization_prompt_message.format(url=auth_url))
    self.server.handle_request()
    self.server.server_close()

    if not self.app.last_request_uri:
      raise LocalServerTimeoutError(
          'Local server timed out before receiving the redirection request.')
    # Note: using https here because oauthlib requires that
    # OAuth 2.0 should only occur over https.
    authorization_response = self.app.last_request_uri.replace(
        'http:', 'https:')

    # TODO(b/204953716): Remove verify=None
    self.fetch_token(
        authorization_response=authorization_response,
        include_client_id=self.include_client_id,
        verify=None,
    )
    return self.credentials


# TODO(b/206804357): Remove OOB flow from gcloud.
class OobFlow(InstalledAppFlow):
  """Out-of-band flow.

  This class supports user account login using "gcloud auth login" without
  browser.
  """

  def __init__(self,
               oauth2session,
               client_type,
               client_config,
               redirect_uri=None,
               code_verifier=None,
               autogenerate_code_verifier=False):
    super(OobFlow, self).__init__(
        oauth2session,
        client_type,
        client_config,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
        autogenerate_code_verifier=autogenerate_code_verifier,
        require_local_server=False)

  def _Run(self, **kwargs):
    """Run the flow using the console strategy.

    The console strategy instructs the user to open the authorization URL
    in their browser. Once the authorization is complete the authorization
    server will give the user a code. The user then must copy & paste this
    code into the application. The code is then exchanged for a token.

    Args:
        **kwargs: Additional keyword arguments passed through to
          "authorization_url".

    Returns:
        google.oauth2.credentials.Credentials: The OAuth 2.0 credentials
          for the user.
    """
    kwargs.setdefault('prompt', 'consent')
    auth_url, _ = self.authorization_url(**kwargs)

    authorization_prompt_message = (
        'Go to the following link in your browser:\n\n    {url}\n')
    code = PromptForAuthCode(authorization_prompt_message, auth_url)
    # TODO(b/204953716): Remove verify=None
    self.fetch_token(code=code, include_client_id=True, verify=None)

    return self.credentials


class UrlManager(object):
  """A helper for url manipulation."""

  def __init__(self, url):
    self._parse_url = parse.urlparse(url)
    self._scheme, self._netloc, self._path, self._query = (
        self._parse_url.scheme, self._parse_url.netloc, self._parse_url.path,
        self._parse_url.query)
    self._parsed_query = parse.parse_qsl(self._query)

  def UpdateQueryParams(self, query_params):
    """Updates query params in the url using query_params.

    Args:
       query_params: A list of two-element tuples. The first element in the
         tuple is the query key and the second element is the query value.
    """
    for key, value in query_params:
      self._RemoveQueryParam(key)
      self._parsed_query.append((key, value))

  def RemoveQueryParams(self, query_keys):
    """Removes query params from the url.

    Args:
      query_keys: A list of query keys to remove.
    """
    for p in query_keys:
      self._RemoveQueryParam(p)

  def _RemoveQueryParam(self, query_key):
    self._parsed_query[:] = [p for p in self._parsed_query if p[0] != query_key]

  def ContainQueryParams(self, query_keys):
    """If the url contains the query keys in query_key.

    Args:
      query_keys: A list of query keys to check in the url.

    Returns:
      True if all query keys in query_keys are contained in url. Otherwise,
        return False.
    """
    parsed_query_keys = {k for (k, v) in self._parsed_query}
    return all([p in parsed_query_keys for p in query_keys])

  def GetQueryParam(self, query_key):
    """Gets the value of the query_key.

    Args:
       query_key: str, A query key to get the value for.

    Returns:
      The value of the query_key. None if query_key does not exist in the url.
    """
    for k, v in self._parsed_query:
      if query_key == k:
        return v

  def GetUrl(self):
    """Gets the current url in the string format."""
    encoded_query = parse.urlencode(self._parsed_query)
    return parse.urlunparse(
        (self._scheme, self._netloc, self._path, '', encoded_query, ''))

  def GetPort(self):
    try:
      _, port = self._netloc.rsplit(':', 1)
      return int(port)
    except ValueError:
      return None


_REQUIRED_QUERY_PARAMS_IN_AUTH_RESPONSE = ('state', 'code')

_AUTH_RESPONSE_ERR_MSG = (
    'The provided authorization response is invalid. Expect a url '
    'with query parameters of [{}].'.format(
        ', '.join(_REQUIRED_QUERY_PARAMS_IN_AUTH_RESPONSE)))


def _ValidateAuthResponse(auth_response):
  if UrlManager(auth_response).ContainQueryParams(
      _REQUIRED_QUERY_PARAMS_IN_AUTH_RESPONSE):
    return
  raise AuthRequestFailedError(_AUTH_RESPONSE_ERR_MSG)


def PromptForAuthResponse(helper_msg, prompt_msg, client_config=None):
  ImportReadline(client_config)
  log.err.Print(helper_msg)
  log.err.Print('\n')
  return input(prompt_msg).strip()


def ImportReadline(client_config):
  if (
      client_config is not None
      and '3pi' in client_config
      and (sys.platform.startswith('dar') or sys.platform.startswith('linux'))
  ):
    # Importing readline alters the built-in input() method
    # to use the GNU readline interface.
    # The basic OSX input() has an input limit of 1024 characters,
    # which is sometimes not enough for us.
    import readline  # pylint: disable=unused-import, g-import-not-at-top


class NoBrowserFlow(InstalledAppFlow):
  """Flow to authorize gcloud on a machine without access to web browsers.

  Out-of-band flow (OobFlow) is deprecated. This flow together with the helper
  flow NoBrowserHelperFlow is the replacement. gcloud in
  environments without access to browsers (i.e. access via ssh) can use this
  flow to authorize gcloud. This flow will print authorization parameters
  which will be taken by the helper flow to build the final authorization
  request. The helper flow (run by a gcloud instance
  with access to browsers) will launch the browser and ask for user's
  authorization. After the authorization, the helper flow will print the
  authorization response to pass back to this flow to continue the process
  (exchanging for the refresh/access tokens).
  """

  _REQUIRED_GCLOUD_VERSION_FOR_BYOID = '420.0.0'
  _REQUIRED_GCLOUD_VERSION = '372.0.0'
  _HELPER_MSG = ('You are authorizing {target} without access to a web '
                 'browser. Please run the following command on a machine with '
                 'a web browser and copy its output back here. Make sure the '
                 'installed gcloud version is {version} or newer.\n\n'
                 '{command} --remote-bootstrap="{partial_url}"')
  _PROMPT_MSG = 'Enter the output of the above command: '

  def __init__(self,
               oauth2session,
               client_type,
               client_config,
               redirect_uri=None,
               code_verifier=None,
               autogenerate_code_verifier=False):
    super(NoBrowserFlow, self).__init__(
        oauth2session,
        client_type,
        client_config,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
        autogenerate_code_verifier=autogenerate_code_verifier,
        require_local_server=False)

  def _PromptForAuthResponse(self, partial_url):
    if not self._for_adc:
      target = 'gcloud CLI'
      command = 'gcloud auth login'
    else:
      target = 'client libraries'
      command = 'gcloud auth application-default login'
    helper_msg = self._HELPER_MSG.format(
        target=target,
        version=self._REQUIRED_GCLOUD_VERSION_FOR_BYOID
        if self.client_config.get('3pi')
        else self._REQUIRED_GCLOUD_VERSION,
        command=command,
        partial_url=partial_url,
    )

    return PromptForAuthResponse(
        helper_msg, self._PROMPT_MSG, self.client_config
    )

  def _Run(self, **kwargs):
    auth_url, _ = self.authorization_url(**kwargs)
    url_manager = UrlManager(auth_url)
    # redirect_uri needs to be provided by the helper flow because the helper
    # will dynamically select a port on its localhost to handle redirect.
    url_manager.RemoveQueryParams(['redirect_uri'])
    # token_usage=remote is to indicate that the authorization is to bootstrap a
    # a different gcloud instance.
    url_manager.UpdateQueryParams([('token_usage', 'remote')])
    auth_response = self._PromptForAuthResponse(url_manager.GetUrl())
    _ValidateAuthResponse(auth_response)
    redirect_port = UrlManager(auth_response).GetPort()
    # Even though we started the local service using "localhost" as host name,
    # system may use a different name. So, the host name in the auth
    # response may not be "localhost". However, we should ignore it and keep
    # using "localhost" as the redirect_uri in token exchange because it is
    # what was used during authorization.
    self.redirect_uri = 'http://{}:{}/'.format(_LOCALHOST, redirect_port)

    # include_client_id should be set to True for 1P, and False for 3P.
    include_client_id = self.client_config.get('3pi') is None
    # TODO(b/204953716): Remove verify=None
    self.fetch_token(
        authorization_response=auth_response,
        include_client_id=include_client_id,
        verify=None,
    )
    return self.credentials


class NoBrowserHelperFlow(InstalledAppFlow):
  """Helper flow for the NoBrowserFlow to help another gcloud to authorize.

  This flow takes the authorization parameters (i.e. requested scopes) generated
  by the NoBrowserFlow and launches the browser for users to authorize.
  After users authorize, print the authorization response which will be taken
  by NoBrowserFlow to continue the login process
  (exchanging for refresh/access token).
  """

  _COPY_AUTH_RESPONSE_INSTRUCTION = (
      'Copy the following line back to the gcloud CLI waiting to continue '
      'the login flow.')
  _COPY_AUTH_RESPONSE_WARNING = (
      '{bold}WARNING: The following line enables access to your Google Cloud '
      'resources. Only copy it to the trusted machine that you ran the '
      '`{command} --no-browser` command on earlier.{normal}')
  _PROMPT_TO_CONTINUE_MSG = (
      'DO NOT PROCEED UNLESS YOU ARE BOOTSTRAPPING GCLOUD '
      'ON A TRUSTED MACHINE WITHOUT A WEB BROWSER AND THE ABOVE COMMAND WAS '
      'THE OUTPUT OF `{command} --no-browser` FROM THE TRUSTED MACHINE.')

  def __init__(self,
               oauth2session,
               client_type,
               client_config,
               redirect_uri=None,
               code_verifier=None,
               autogenerate_code_verifier=False):
    super(NoBrowserHelperFlow, self).__init__(
        oauth2session,
        client_type,
        client_config,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
        autogenerate_code_verifier=autogenerate_code_verifier,
        require_local_server=True)
    self.partial_auth_url = None

  @property
  def _for_adc(self):
    client_id = UrlManager(self.partial_auth_url).GetQueryParam('client_id')
    return client_id != config.CLOUDSDK_CLIENT_ID

  def _PrintCopyInstruction(self, auth_response):
    con = console_attr.GetConsoleAttr()

    log.status.write(self._COPY_AUTH_RESPONSE_INSTRUCTION + ' ')
    log.status.Print(
        self._COPY_AUTH_RESPONSE_WARNING.format(
            bold=con.GetFontCode(bold=True),
            command=self._target_command,
            normal=con.GetFontCode()))
    log.status.write('\n')
    log.status.Print(auth_response)

  def _ShouldContinue(self):
    """Ask users to confirm before actually running the flow."""
    return console_io.PromptContinue(
        self._PROMPT_TO_CONTINUE_MSG.format(command=self._target_command),
        prompt_string='Proceed',
        default=False)

  def _Run(self, **kwargs):
    self.partial_auth_url = kwargs.pop('partial_auth_url')
    auth_url_manager = UrlManager(self.partial_auth_url)
    auth_url_manager.UpdateQueryParams([('redirect_uri', self.redirect_uri)] +
                                       list(kwargs.items()))
    auth_url = auth_url_manager.GetUrl()
    if not self._ShouldContinue():
      return
    webbrowser.open(auth_url, new=1, autoraise=True)

    authorization_prompt_message = (
        'Your browser has been opened to visit:\n\n    {url}\n')
    log.err.Print(authorization_prompt_message.format(url=auth_url))
    self.server.handle_request()
    self.server.server_close()

    if not self.app.last_request_uri:
      raise LocalServerTimeoutError(
          'Local server timed out before receiving the redirection request.')
    # Note: using https here because oauthlib requires that
    # OAuth 2.0 should only occur over https.
    authorization_response = self.app.last_request_uri.replace(
        'http:', 'https:')
    self._PrintCopyInstruction(authorization_response)


class RemoteLoginWithAuthProxyFlow(InstalledAppFlow):
  """Flow to authorize gcloud on a machine without access to web browsers.

  Out-of-band flow (OobFlow) is deprecated. gcloud in
  environments without access to browsers (eg. access via ssh) can use this
  flow to authorize gcloud. This flow will print a url which the user has to
  copy to a browser in any machine and perform authorization. After the
  authorization, the user is redirected to gcloud's auth proxy which displays
  the auth code. User copies the auth code back to gcloud to continue the
  process (exchanging auth code for the refresh/access tokens).
  """

  def __init__(self,
               oauth2session,
               client_type,
               client_config,
               redirect_uri=None,
               code_verifier=None,
               autogenerate_code_verifier=False):
    super(RemoteLoginWithAuthProxyFlow, self).__init__(
        oauth2session,
        client_type,
        client_config,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
        autogenerate_code_verifier=autogenerate_code_verifier,
        require_local_server=False)

  def _Run(self, **kwargs):
    """Run the flow using the console strategy.

    The console strategy instructs the user to open the authorization URL
    in their browser. Once the authorization is complete the authorization
    server will give the user a code. The user then must copy & paste this
    code into the application. The code is then exchanged for a token.

    Args:
        **kwargs: Additional keyword arguments passed through to
          "authorization_url".

    Returns:
        google.oauth2.credentials.Credentials: The OAuth 2.0 credentials
          for the user.
    """

    kwargs.setdefault('prompt', 'consent')
    # when the parameter token_usage=remote is present, the DUSI of the token is
    # not attached to the local device whose browser is used to provide consent.
    kwargs.setdefault('token_usage', 'remote')
    auth_url, _ = self.authorization_url(**kwargs)

    authorization_prompt_message = (
        'Go to the following link in your browser:\n\n    {url}\n'
    )

    code = PromptForAuthCode(
        authorization_prompt_message, auth_url, self.client_config
    )

    # TODO(b/204953716): Remove verify=None
    self.fetch_token(
        code=code, include_client_id=self.include_client_id, verify=None
    )

    return self.credentials


def CreateLocalServer(wsgi_app, host, search_start_port, search_end_port):
  """Creates a local wsgi server.

  Finds an available port in the range of [search_start_port, search_end_point)
  for the local server.

  Args:
    wsgi_app: A wsgi app running on the local server.
    host: hostname of the server.
    search_start_port: int, the port where the search starts.
    search_end_port: int, the port where the search ends.

  Raises:
    LocalServerCreationError: If it cannot find an available port for
      the local server.

  Returns:
    WSGISever, a wsgi server.
  """
  port = search_start_port
  local_server = None
  while not local_server and port < search_end_port:
    try:
      local_server = wsgiref.simple_server.make_server(
          host,
          port,
          wsgi_app,
          server_class=WSGIServer,
          handler_class=google_auth_flow._WSGIRequestHandler)  # pylint:disable=protected-access
    except (socket.error, OSError):
      port += 1
  if local_server:
    return local_server
  raise LocalServerCreationError(
      _PORT_SEARCH_ERROR_MSG.format(
          start_port=search_start_port, end_port=search_end_port - 1))


class _RedirectWSGIApp(object):
  """WSGI app to handle the authorization redirect.

  Stores the request URI and responds with a confirmation page.
  """

  def __init__(self):
    self.last_request_uri = None

  def __call__(self, environ, start_response):
    """WSGI Callable.

    Args:
        environ (Mapping[str, Any]): The WSGI environment.
        start_response (Callable[str, list]): The WSGI start_response callable.

    Returns:
        Iterable[bytes]: The response body.
    """
    start_response(
        six.ensure_str('200 OK'),
        [(six.ensure_str('Content-type'), six.ensure_str('text/html'))])
    self.last_request_uri = wsgiref.util.request_uri(environ)
    query = self.last_request_uri.split('?', 1)[-1]
    query = dict(parse.parse_qsl(query))
    if 'code' in query:
      page = 'oauth2_landing.html'
    else:
      page = 'oauth2_landing_error.html'
    return [pkg_resources.GetResource(__name__, page)]
