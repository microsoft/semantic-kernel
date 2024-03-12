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

"""Command return config and auth context for use by external tools."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.config import config_helper
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.credentials import store


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class ConfigurationHelper(base.Command):
  """A helper for providing auth and config data to external tools."""

  detailed_help = {
      'DESCRIPTION':
          """\
            {description}

            Tools can call out to this command to get gcloud's current auth and
            configuration context when needed. This is appropriate when external
            tools want to operate within the context of the user's current
            gcloud session.

            This command returns a nested data structure with the following
            schema:

            *  credential
               *  access_token - string, The current OAuth2 access token
               *  token_expiry - string, The time the token will expire. This
                  can be empty for some credential types. It is a UTC time
                  formatted as: '%Y-%m-%dT%H:%M:%SZ'
            *  configuration
               *  active_configuration - string, The name of the active gcloud
                  configuration
               *  properties - {string: {string: string}}, The full set of
                  active gcloud properties
        """,
      'EXAMPLES':
          """\
            This command should always be used with the --format flag to get the
            output in a structured format.

            To get the current gcloud context:

              $ {command} --format=json

            To get the current gcloud context after forcing a refresh of the
            OAuth2 credentials:

              $ {command} --format=json --force-auth-refresh

            To set MIN_EXPIRY amount of time that if given, refresh the
            credentials if they are within MIN_EXPIRY from expiration:

              $ {command} --format=json --min-expiry=MIN_EXPIRY

            By default, MIN_EXPIRY is set to be 0 second.
        """,
  }

  @staticmethod
  def Args(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--force-auth-refresh',
        action='store_true',
        help='Force a refresh of the credentials even if they have not yet '
             'expired. By default, credentials will only refreshed when '
             'necessary.')
    group.add_argument(
        '--min-expiry',
        type=arg_parsers.Duration(lower_bound='0s', upper_bound='1h'),
        help='If given, refresh the credentials if they are within MIN_EXPIRY '
             'from expiration.',
        default='0s')

  def Run(self, args):
    cred = store.Load(use_google_auth=True)

    if args.force_auth_refresh:
      store.Refresh(cred)
    else:
      store.RefreshIfExpireWithinWindow(cred, '{}'.format(args.min_expiry))

    config_name = named_configs.ConfigurationStore.ActiveConfig().name
    props = properties.VALUES.AllValues()

    return config_helper.ConfigHelperResult(
        credential=cred,
        active_configuration=config_name,
        properties=props,
    )
