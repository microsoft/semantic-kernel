# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""A library to support auth commands."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import json
import textwrap

from google.auth import external_account_authorized_user
from google.oauth2 import credentials as oauth2_credentials
from googlecloudsdk.command_lib.util import check_browser
from googlecloudsdk.core import config
from googlecloudsdk.core import context_aware
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import flow as c_flow
from googlecloudsdk.core.credentials import google_auth_credentials as c_google_auth
from googlecloudsdk.core.util import files
import six

# Client ID from project "usable-auth-library", configured for
# general purpose API testing
# pylint: disable=g-line-too-long
DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID = '764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com'
DEFAULT_CREDENTIALS_DEFAULT_CLIENT_SECRET = 'd-FL95Q19q7MQmFpd7hHD0Ty'
CLOUD_PLATFORM_SCOPE = 'https://www.googleapis.com/auth/cloud-platform'
SQL_LOGIN_SCOPE = 'https://www.googleapis.com/auth/sqlservice.login'
GOOGLE_DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'
USER_EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'
OPENID = 'openid'

DEFAULT_SCOPES = [
    OPENID,
    USER_EMAIL_SCOPE,
    CLOUD_PLATFORM_SCOPE,
    SQL_LOGIN_SCOPE
]

CLIENT_SECRET_INSTALLED_TYPE = 'installed'


class Error(exceptions.Error):
  """A base exception for this class."""
  pass


class InvalidClientSecretsError(Error):
  """An error for when we fail to load the client secrets file."""
  pass


class BadCredentialFileException(Error):
  """Raised when credentials file cannot be read."""
  pass


def GetCredentialsConfigFromFile(filename):
  """Returns the JSON content of a credentials config file.

  This function is useful when the content of a file need to be inspected first
  before determining how to handle it (how to initialize the underlying
  credentials). Only UTF-8 JSON files are supported.

  Args:
    filename (str): The filepath to the ADC file representing credentials.

  Returns:
    Optional(Mapping): The JSON content.

  Raises:
    BadCredentialFileException: If JSON parsing of the file fails.
  """

  try:
    # YAML is a superset of JSON.
    content = yaml.load_path(filename)
  except UnicodeDecodeError as e:
    raise BadCredentialFileException(
        'File {0} is not utf-8 encoded: {1}'.format(filename, e))
  except yaml.YAMLParseError as e:
    raise BadCredentialFileException('Could not read json file {0}: {1}'.format(
        filename, e))

  # Require the JSON content to be an object.
  # Credentials and configs are always objects.
  if not isinstance(content, dict):
    raise BadCredentialFileException(
        'Could not read json file {0}'.format(filename))
  return content


def _HandleFlowError(exc, default_help_msg):
  """Prints help messages when auth flow throws errors."""
  if context_aware.IsContextAwareAccessDeniedError(exc):
    log.error(context_aware.CONTEXT_AWARE_ACCESS_HELP_MSG)
  else:
    log.error(default_help_msg)


class FlowRunner(six.with_metaclass(abc.ABCMeta, object)):
  """Base auth flow runner class.

  Attributes:
     _scopes: [str], The list of scopes to authorize.
     _client_config: The client configuration in the Google client secrets
       format.
  """

  _FLOW_ERROR_HELP_MSG = 'There was a problem with web authentication.'

  def __init__(self, scopes, client_config, redirect_uri=None):
    self._scopes = scopes
    self._client_config = client_config
    self._redirect_uri = redirect_uri
    self._flow = self._CreateFlow()

  @abc.abstractmethod
  def _CreateFlow(self):
    pass

  def Run(self, **kwargs):
    try:
      return self._flow.Run(**kwargs)
    except c_flow.Error as e:
      _HandleFlowError(e, self._FLOW_ERROR_HELP_MSG)
      raise


class OobFlowRunner(FlowRunner):
  """A flow runner to run OobFlow."""

  def _CreateFlow(self):
    return c_flow.OobFlow.from_client_config(
        self._client_config,
        self._scopes,
        autogenerate_code_verifier=not properties.VALUES.auth
        .disable_code_verifier.GetBool())


class NoBrowserFlowRunner(FlowRunner):
  """A flow runner to run NoBrowserFlow."""

  def _CreateFlow(self):
    return c_flow.NoBrowserFlow.from_client_config(
        self._client_config,
        self._scopes,
        autogenerate_code_verifier=not properties.VALUES.auth
        .disable_code_verifier.GetBool())


class RemoteLoginWithAuthProxyFlowRunner(FlowRunner):
  """A flow runner to run RemoteLoginWithAuthProxyFlow."""

  def _CreateFlow(self):
    return c_flow.RemoteLoginWithAuthProxyFlow.from_client_config(
        self._client_config,
        self._scopes,
        autogenerate_code_verifier=not properties.VALUES.auth
        .disable_code_verifier.GetBool(),
        redirect_uri=self._redirect_uri)


class NoBrowserHelperRunner(FlowRunner):
  """A flow runner to run NoBrowserHelperFlow."""

  def _CreateFlow(self):
    try:
      return c_flow.NoBrowserHelperFlow.from_client_config(
          self._client_config,
          self._scopes,
          autogenerate_code_verifier=not properties.VALUES.auth
          .disable_code_verifier.GetBool())
    except c_flow.LocalServerCreationError:
      log.error('Cannot start a local server to handle authorization '
                'redirection. Please run this command on a machine where '
                'gcloud can start a local server.')
      raise


class BrowserFlowWithOobFallbackRunner(FlowRunner):
  """A flow runner to try normal web flow and fall back to oob flow."""

  _FLOW_ERROR_HELP_MSG = ('There was a problem with web authentication. '
                          'Try running again with --no-launch-browser.')

  def _CreateFlow(self):
    try:
      return c_flow.FullWebFlow.from_client_config(
          self._client_config,
          self._scopes,
          autogenerate_code_verifier=not properties.VALUES.auth
          .disable_code_verifier.GetBool())
    except c_flow.LocalServerCreationError as e:
      log.warning(e)
      log.warning('Defaulting to URL copy/paste mode.')
      return c_flow.OobFlow.from_client_config(
          self._client_config,
          self._scopes,
          autogenerate_code_verifier=not properties.VALUES.auth
          .disable_code_verifier.GetBool())


class BrowserFlowWithNoBrowserFallbackRunner(FlowRunner):
  """A flow runner to try normal web flow and fall back to NoBrowser flow."""

  _FLOW_ERROR_HELP_MSG = ('There was a problem with web authentication. '
                          'Try running again with --no-browser.')

  def _CreateFlow(self):
    try:
      return c_flow.FullWebFlow.from_client_config(
          self._client_config,
          self._scopes,
          autogenerate_code_verifier=not properties.VALUES.auth
          .disable_code_verifier.GetBool())
    except c_flow.LocalServerCreationError as e:
      log.warning(e)
      log.warning('Defaulting to --no-browser mode.')
      return c_flow.NoBrowserFlow.from_client_config(
          self._client_config,
          self._scopes,
          autogenerate_code_verifier=not properties.VALUES.auth
          .disable_code_verifier.GetBool())


def _CreateGoogleAuthClientConfig(client_id_file=None):
  """Creates a client config from a client id file or gcloud's properties."""
  if client_id_file:
    with files.FileReader(client_id_file) as f:
      return json.load(f)
  return _CreateGoogleAuthClientConfigFromProperties()


def _CreateGoogleAuthClientConfigFromProperties():
  """Creates a client config from gcloud's properties."""
  auth_uri = properties.VALUES.auth.auth_host.Get(required=True)
  token_uri = GetTokenUri()

  client_id = properties.VALUES.auth.client_id.Get(required=True)
  client_secret = properties.VALUES.auth.client_secret.Get(required=True)
  return {
      'installed': {
          'client_id': client_id,
          'client_secret': client_secret,
          'auth_uri': auth_uri,
          'token_uri': token_uri
      }
  }


def _IsGoogleOwnedClientID(client_config):
  return (client_config['installed']['client_id']
          in (config.CLOUDSDK_CLIENT_ID, DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID))


def DoInstalledAppBrowserFlowGoogleAuth(scopes,
                                        client_id_file=None,
                                        client_config=None,
                                        no_launch_browser=False,
                                        no_browser=False,
                                        remote_bootstrap=None,
                                        query_params=None,
                                        auth_proxy_redirect_uri=None):
  """Launches a 3LO oauth2 flow to get google-auth credentials.

  Args:
    scopes: [str], The list of scopes to authorize.
    client_id_file: str, The path to a file containing the client id and secret
      to use for the flow.  If None, the default client id for the Cloud SDK is
      used.
    client_config: Optional[Mapping], the client secrets and urls that should be
      used for the OAuth flow.
    no_launch_browser: bool, True if users specify --no-launch-browser flag to
      use the remote login with auth proxy flow.
    no_browser: bool, True if users specify --no-browser flag to ask another
      gcloud instance to help with authorization.
    remote_bootstrap: str, The auth parameters specified by --remote-bootstrap
      flag. Once used, it means the command is to help authorize another
      gcloud (i.e. gcloud without access to browser).
    query_params: Optional[Mapping], extra params to pass to the flow during
      `Run`. These params end up getting used as query
      params for authorization_url.
    auth_proxy_redirect_uri: str, The uri where OAuth service will redirect the
      user to once the authentication is complete for a remote login with auth
      proxy flow.
  Returns:
    core.credentials.google_auth_credentials.Credentials, The credentials
      obtained from the flow.
  """
  if client_id_file:
    AssertClientSecretIsInstalledType(client_id_file)
  if not client_config:
    client_config = _CreateGoogleAuthClientConfig(client_id_file)
  if not query_params:
    query_params = {}
  can_launch_browser = check_browser.ShouldLaunchBrowser(
      attempt_launch_browser=True)
  if no_browser:
    user_creds = NoBrowserFlowRunner(scopes, client_config).Run(**query_params)
  elif remote_bootstrap:
    if not can_launch_browser:
      raise c_flow.WebBrowserInaccessible(
          'Cannot launch browser. Please run this command on a machine '
          'where gcloud can launch a web browser.')
    user_creds = NoBrowserHelperRunner(scopes, client_config).Run(
        partial_auth_url=remote_bootstrap, **query_params)
  elif no_launch_browser or not can_launch_browser:
    user_creds = RemoteLoginWithAuthProxyFlowRunner(
        scopes, client_config, auth_proxy_redirect_uri).Run(**query_params)
  else:
    user_creds = BrowserFlowWithNoBrowserFallbackRunner(
        scopes, client_config).Run(**query_params)
  if user_creds:
    if isinstance(user_creds, oauth2_credentials.Credentials):
      # c_google_auth.Credentials adds reauth capabilities to oauth2
      # credentials, which is needed as they are long-term credentials.
      return c_google_auth.Credentials.FromGoogleAuthUserCredentials(user_creds)
    if isinstance(user_creds, external_account_authorized_user.Credentials):
      return user_creds


def GetClientSecretsType(client_id_file):
  """Get the type of the client secrets file (web or installed)."""
  invalid_file_format_msg = (
      'Invalid file format. See '
      'https://developers.google.com/api-client-library/'
      'python/guide/aaa_client_secrets')
  try:
    obj = json.loads(files.ReadFileContents(client_id_file))
  except files.Error:
    raise InvalidClientSecretsError(
        'Cannot read file: "%s"' % client_id_file)
  if obj is None:
    raise InvalidClientSecretsError(invalid_file_format_msg)
  if len(obj) != 1:
    raise InvalidClientSecretsError(
        invalid_file_format_msg + ' '
        'Expected a JSON object with a single property for a "web" or '
        '"installed" application')
  return tuple(obj)[0]


def AssertClientSecretIsInstalledType(client_id_file):
  client_type = GetClientSecretsType(client_id_file)
  if client_type != CLIENT_SECRET_INSTALLED_TYPE:
    raise InvalidClientSecretsError(
        'Only client IDs of type \'%s\' are allowed, but encountered '
        'type \'%s\'' % (CLIENT_SECRET_INSTALLED_TYPE, client_type))


def GetTokenUri():
  """Get context dependent Token URI."""
  if properties.VALUES.context_aware.use_client_certificate.GetBool():
    token_uri = properties.VALUES.auth.mtls_token_host.Get(required=True)
  else:
    token_uri = properties.VALUES.auth.token_host.Get(required=True)
  return token_uri


def HandleUniverseDomainConflict(new_universe_domain, account):
  """Prompt the user to update the universe domain if there is conflict.

  If the given universe domain is different from the core/universe_domain
  property, prompt the user to update the core/universe_domain property.

  Args:
    new_universe_domain: str, The given new universe domain.
    account: str, The account name to use.
  """
  current_universe_domain = properties.VALUES.core.universe_domain.Get()
  if current_universe_domain == new_universe_domain:
    return

  message = textwrap.dedent("""\
        WARNING: This account [{0}] is from the universe domain [{1}],
        which does not match the current core/universe property [{2}].\n
        Do you want to set property [core/universe_domain] to [{1}]? [Y/N]
        """).format(account, new_universe_domain, current_universe_domain)
  should_update_universe_domain = console_io.PromptContinue(message=message)

  if should_update_universe_domain:
    properties.PersistProperty(
        properties.VALUES.core.universe_domain, new_universe_domain
    )
    log.status.Print('Updated property [core/universe_domain].')
