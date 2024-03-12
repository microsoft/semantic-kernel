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

"""The auth command gets tokens via oauth2."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.auth import refresh_token
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.Hidden
class ActivateRefreshToken(base.SilentCommand):
  """Get credentials via an existing refresh token.

  Use an oauth2 refresh token to manufacture credentials for Google APIs. This
  token must have been acquired via some legitimate means to work. The account
  provided is only used locally to help the Cloud SDK keep track of the new
  credentials, so you can activate, list, and revoke the credentials in the
  future.
  """

  @staticmethod
  def Args(parser):
    """Set args for gcloud auth activate-refresh-token."""
    parser.add_argument(
        'account',
        help='The account to associate with the refresh token.')
    parser.add_argument(
        'token', nargs='?',
        help=('OAuth2 refresh token. If blank, prompt for value.'))

  def Run(self, args):
    """Run the authentication command."""

    token = args.token or console_io.PromptResponse('Refresh token: ')
    if not token:
      raise c_exc.InvalidArgumentException('token', 'No value provided.')

    refresh_token.ActivateCredentials(args.account, token)

    project = args.project
    if project:
      properties.PersistProperty(properties.VALUES.core.project, project)

    log.status.Print('Activated refresh token credentials: [{0}]'
                     .format(args.account))

