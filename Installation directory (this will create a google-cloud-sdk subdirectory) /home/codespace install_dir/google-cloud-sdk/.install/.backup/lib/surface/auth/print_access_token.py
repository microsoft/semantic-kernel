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

"""A command that prints access tokens."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from google.auth import credentials
from google.auth import exceptions as google_auth_exceptions
from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import store as c_store
from oauth2client import client


class FakeCredentials(object):
  """An access token container.

  oauth2client and google-auth are both supported by gcloud as the auth library.
  credentials in oauth2client store the access token in the "access_token"
  filed. google-auth stores it in the "token" filed. We use this fake
  credentials class to unify them.
  """

  def __init__(self, token):
    self.token = token


class AccessToken(base.Command):
  """Print an access token for the specified account."""
  detailed_help = {
      'DESCRIPTION': """\
        {description}
        See [RFC6749](https://tools.ietf.org/html/rfc6749) for more
        information about access tokens.

        Note that token itself may not be enough to access some services.
        If you use the token with curl or similar tools, you may see
        permission errors similar to "API has not been used in
        project 32555940559 before or it is disabled.". If it happens, you may
        need to provide a quota project in the "X-Goog-User-Project" header.
        For example,

          $ curl -H "X-Goog-User-Project: your-project" -H "Authorization: Bearer $(gcloud auth print-access-token)" foo.googleapis.com

        The identity that granted the token must have the
        serviceusage.services.use permission on the provided project. See
        https://cloud.google.com/apis/docs/system-parameters for more
        information.
        """,
      'EXAMPLES': """\
        To print access tokens:

          $ {command}
        """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'account', nargs='?',
        help=('Account to get the access token for. If not specified, '
              'the current active account will be used.'))
    parser.add_argument(
        '--lifetime',
        type=arg_parsers.Duration(upper_bound='43200s'),
        help=('Access token lifetime. The default access token '
              'lifetime is 3600 seconds, but you can use this flag to reduce '
              'the lifetime or extend it up to 43200 seconds (12 hours). The '
              'org policy constraint '
              '`constraints/iam.allowServiceAccountCredentialLifetimeExtension`'
              ' must be set if you want to extend the lifetime beyond 3600 '
              'seconds. Note that this flag is for service account '
              'impersonation only, so it must be used together with the '
              '`--impersonate-service-account` flag.'))
    parser.add_argument(
        '--scopes',
        hidden=True,
        type=arg_parsers.ArgList(min_length=1),
        metavar='SCOPE',
        help='The scopes to authorize for. This flag is supported for user '
        'accounts and service accounts only. '
        'The list of possible scopes can be found at: '
        '[](https://developers.google.com/identity/protocols/googlescopes).\n\n'
        'For end-user accounts the provided '
        'scopes must from [{0}]'.format(config.CLOUDSDK_SCOPES))
    parser.display_info.AddFormat('value(token)')

  @c_exc.RaiseErrorInsteadOf(auth_exceptions.AuthenticationError, client.Error,
                             google_auth_exceptions.GoogleAuthError)
  def Run(self, args):
    """Run the helper command."""
    if args.lifetime and not args.impersonate_service_account:
      raise c_exc.InvalidArgumentException(
          '--lifetime',
          'Lifetime flag is for service account impersonation only. It must be '
          'used together with the --impersonate-service-account flag.')

    # Do not auto cache the custom scoped access token. Otherwise, it'll
    # affect other gcloud CLIs that depends on cloud-platform scopes.
    with_access_token_cache = not args.scopes
    cred = c_store.Load(
        args.account,
        allow_account_impersonation=True,
        use_google_auth=True,
        with_access_token_cache=with_access_token_cache)

    # c_store.Load already refreshed the cred, so we don't need to refresh the
    # cred unless we need to alter the cred in the code below, for example,
    # changing the scopes.
    should_refresh_again = False

    if args.scopes:
      # refresh again due to altered scopes
      should_refresh_again = True
      cred_type = c_creds.CredentialTypeGoogleAuth.FromCredentials(cred)
      if cred_type not in [
          c_creds.CredentialTypeGoogleAuth.USER_ACCOUNT,
          c_creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT
      ]:
        # TODO(b/223649175): Add support for other credential types(e.g GCE).
        log.warning(
            '`--scopes` flag may not working as expected and will be ignored '
            'for account type {}.'.format(cred_type.key)
        )
      scopes = args.scopes + [auth_util.OPENID, auth_util.USER_EMAIL_SCOPE]

      # non user account credential types
      if isinstance(cred, credentials.Scoped):
        cred = cred.with_scopes(scopes)
      else:
        requested_scopes = set(args.scopes)
        trusted_scopes = set(config.CLOUDSDK_SCOPES)
        if not requested_scopes.issubset(trusted_scopes):
          raise c_exc.InvalidArgumentException(
              '--scopes',
              'Invalid scopes value. Please make sure the scopes are from [{0}]'
              .format(config.CLOUDSDK_SCOPES))
        # pylint:disable=protected-access
        cred._scopes = scopes

    if c_creds.IsImpersonatedAccountCredentials(cred) and args.lifetime:
      # refresh again due to altered lifetime
      should_refresh_again = True
      cred._lifetime = args.lifetime  # pylint: disable=protected-access

    if should_refresh_again:
      c_store.Refresh(cred)

    if c_creds.IsOauth2ClientCredentials(cred):
      token = cred.access_token
    else:
      token = cred.token
    if not token:
      raise auth_exceptions.InvalidCredentialsError(
          'No access token could be obtained from the current credentials.')
    return FakeCredentials(token)
