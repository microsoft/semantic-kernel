# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Generate an IAM login token for Cloud SQL."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.command_lib.sql import generate_login_token_util

_SQL_LOGIN = 'https://www.googleapis.com/auth/sqlservice.login'

_SCOPES = [auth_util.OPENID, auth_util.USER_EMAIL_SCOPE, _SQL_LOGIN]


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class GenerateLoginToken(base.Command):
  """Generate an IAM login token for Cloud SQL."""

  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""\
          {command} generates an IAM token to use for logging in to Cloud SQL instances.
          """),
      'EXAMPLES':
          textwrap.dedent("""\
          To generate an IAM login token using gcloud credentials, run:

            $ {command}

          To generate an IAM login token using application default credentials, run:

            $ {command} --application-default-credential

          To generate an IAM login token using gcloud credentials for instance `my-instance`, run:

            $ {command} --instance=my-instance

          To generate an IAM login token using application default credentials for instance `my-instance`, run:

            $ {command} --instance=my-instance --application-default-credential
          """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    flags.AddOptionalInstance(parser)
    parser.add_argument(
        '--application-default-credential',
        action='store_true',
        help='Use application default credentials to generate the login token.')
    parser.display_info.AddFormat('value(token)')

  def Run(self, args):
    """Runs the command to reschedule maintenance for a Cloud SQL instance."""
    if args.application_default_credential:
      return generate_login_token_util.generate_login_token_from_adc(_SCOPES)
    else:
      token = generate_login_token_util.generate_login_token_from_gcloud_auth(
          _SCOPES)
      return {'token': token}
