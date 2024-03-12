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

"""A docker credential helper that provides credentials for GCR registries."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import exceptions as creds_exceptions
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.docker import credential_utils


TOKEN_MIN_LIFETIME = '3300s'  # 55 minutes


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class DockerHelper(base.Command):
  """A Docker credential helper to provide access to GCR repositories."""

  GET = 'get'
  LIST = 'list'

  @staticmethod
  def Args(parser):
    parser.add_argument('method', help='The docker credential helper method.')
    # Docker expects the result in json format.
    parser.display_info.AddFormat('json')

  def Run(self, args):
    """Run the helper command."""

    if args.method == DockerHelper.LIST:
      return {
          # This tells Docker that the secret will be an access token, not a
          # username/password.
          # Docker normally expects a prefixed 'https://' for auth configs.
          ('https://' + url): '_dcgcloud_token'
          for url in credential_utils.DefaultAuthenticatedRegistries()
      }

    elif args.method == DockerHelper.GET:
      # docker credential helper protocol expects that error is printed to
      # stdout.
      try:
        cred = c_store.Load(use_google_auth=True)
      except creds_exceptions.NoActiveAccountException:
        log.Print('You do not currently have an active account selected. '
                  'See https://cloud.google.com/sdk/docs/authorizing for more '
                  'information.')
        sys.exit(1)

      c_store.RefreshIfExpireWithinWindow(cred, window=TOKEN_MIN_LIFETIME)
      url = sys.stdin.read().strip()
      if (url.replace('https://', '',
                      1) not in credential_utils.SupportedRegistries()):
        raise exceptions.Error(
            'Repository url [{url}] is not supported'.format(url=url))
      # Putting an actual username in the response doesn't work. Docker will
      # then prompt for a password instead of using the access token.
      token = (
          cred.token
          if c_creds.IsGoogleAuthCredentials(cred) else cred.access_token)

      return {
          'Secret': token,
          'Username': '_dcgcloud_token',
      }

    # Don't print anything if we are not supporting the given action.
    # The credential helper protocol also support 'store' and 'erase' actions
    # that don't apply here. The full spec can be found here:
    # https://github.com/docker/docker-credential-helpers#development
    args.GetDisplayInfo().AddFormat('none')
    return None
