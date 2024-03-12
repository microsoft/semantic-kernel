# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""A command that prints identity token.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.command_lib.auth import flags
from googlecloudsdk.command_lib.config import config_helper
from googlecloudsdk.core import config
from googlecloudsdk.core.credentials import store as c_store
from oauth2client import client


def _Run(args):
  """Run the print_identity_token command."""
  do_impersonation = args.IsSpecified('impersonate_service_account')
  cred = c_store.Load(
      args.account,
      allow_account_impersonation=do_impersonation,
      use_google_auth=True)
  is_impersonated_account = auth_util.IsImpersonationCredential(cred)
  if args.audiences:
    if not auth_util.ValidIdTokenCredential(cred):
      raise auth_exceptions.WrongAccountTypeError(
          'Invalid account Type for `--audiences`. '
          'Requires valid service account.')
    # TODO(b/170394261): Avoid changing constant values.
    config.CLOUDSDK_CLIENT_ID = args.audiences

  if args.IsSpecified('token_format') or args.IsSpecified('include_license'):
    if not auth_util.IsGceAccountCredentials(cred):
      raise auth_exceptions.WrongAccountTypeError(
          'Invalid account type for `--token-format` or `--include-license`. '
          'Requires a valid GCE service account.')

  if args.token_format == 'standard':
    if args.include_license:
      raise auth_exceptions.GCEIdentityTokenError(
          '`--include-license` can only be specified when '
          '`--token-format=full`.')

  if args.IsSpecified('include_email'):
    if not auth_util.IsImpersonationCredential(cred):
      raise auth_exceptions.WrongAccountTypeError(
          'Invalid account type for `--include-email`. '
          'Requires an impersonate service account.')

  c_store._RefreshGoogleAuthIdToken(  # pylint: disable=protected-access
      cred,
      is_impersonated_credential=is_impersonated_account,
      include_email=args.include_email,
      gce_token_format=args.token_format,
      gce_include_license=args.include_license,
      refresh_user_account_credentials=True,
  )

  credential = config_helper.Credential(cred)
  if not credential.id_token:
    raise auth_exceptions.InvalidIdentityTokenError(
        'No identity token can be obtained from the current credentials.')
  return credential


class IdentityToken(base.Command):
  """Print an identity token for the specified account."""
  detailed_help = {
      'DESCRIPTION':
          """\
        {description}
        """,
      'EXAMPLES':
          """\
        To print identity tokens:

          $ {command}

        To print identity token for account 'foo@example.com' whose audience
        is 'https://service-hash-uc.a.run.app', run:

          $ {command} foo@example.com --audiences="https://service-hash-uc.a.run.app"

        To print identity token for an impersonated service account 'my-account@example.iam.gserviceaccount.com'
        whose audience is 'https://service-hash-uc.a.run.app', run:

          $ {command} --impersonate-service-account="my-account@example.iam.gserviceaccount.com" --audiences="https://service-hash-uc.a.run.app"

        To print identity token of a Compute Engine instance, which includes
        project and instance details as well as license codes for images
        associated with the instance, run:

          $ {command} --token-format=full --include-license

        To print identity token for an impersonated service account
        'my-account@example.iam.gserviceaccount.com', which includes the email
        address of the service account, run:

          $ {command} --impersonate-service-account="my-account@example.iam.gserviceaccount.com" --include-email
        """,
  }

  @staticmethod
  def Args(parser):
    flags.AddAccountArg(parser)
    flags.AddAudienceArg(parser)
    flags.AddGCESpecificArgs(parser)
    flags.AddIncludeEmailArg(parser)
    parser.display_info.AddFormat('value(id_token)')

  @c_exc.RaiseErrorInsteadOf(auth_exceptions.AuthenticationError, client.Error)
  def Run(self, args):
    """Run the print_identity_token command."""
    credential = _Run(args)
    return credential
