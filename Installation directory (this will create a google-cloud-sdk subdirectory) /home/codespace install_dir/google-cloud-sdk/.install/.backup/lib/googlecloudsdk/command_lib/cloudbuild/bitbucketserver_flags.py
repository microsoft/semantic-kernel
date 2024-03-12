# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Set up flags for creating or updating a Bitbucket Server config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.builds import flags as build_flags


def AddBitbucketServerConfigArgs(parser, update=False):
  """Set up all the argparse flags for creating or updating a Bitbucket Server config.

  Args:
    parser: An argparse.ArgumentParser-like object.
    update: If true, use the version of the flags for updating a config.
      Otherwise, use the version for creating a config.

  Returns:
    The parser argument with Bitbucket Server config flags added in.
  """
  parser.add_argument(
      '--host-uri',
      required=not update,
      help='The host uri of the Bitbucket Server instance.')
  parser.add_argument(
      '--user-name',
      required=not update,
      help='The Bitbucket Server user name that should be associated with this config.'
  )
  parser.add_argument(
      '--api-key',
      required=not update,
      help='The Cloud Build API key that should be associated with this config.'
  )
  parser.add_argument(
      '--admin-access-token-secret-version',
      required=not update,
      help='Secret Manager resource containing the admin access token. The secret is specified in resource URL format projects/{secret_project}/secrets/{secret_name}/versions/{secret_version}.'
  )
  parser.add_argument(
      '--read-access-token-secret-version',
      required=not update,
      help='Secret Manager resource containing the read access token. The secret is specified in resource URL format projects/{secret_project}/secrets/{secret_name}/versions/{secret_version}.'
  )
  parser.add_argument(
      '--webhook-secret-secret-version',
      required=not update,
      help='Secret Manager resource containing the webhook secret. The secret is specified in resource URL format projects/{secret_project}/secrets/{secret_name}/versions/{secret_version}.'
  )
  parser.add_argument(
      '--ssl-ca-file',
      type=arg_parsers.FileContents(),
      help='Path to a local file that contains SSL certificate to use for requests to Bitbucket Server. The certificate should be in PEM format.'
  )
  build_flags.AddRegionFlag(parser)
  if not update:
    parser.add_argument(
        '--name',
        required=True,
        help='The config name of the Bitbucket Server connection.')
    network = parser.add_argument_group()
    network.add_argument(
        '--peered-network',
        help="""\
VPC network that should be used when making calls to the Bitbucket Server instance.

If not specified, calls will be made over the public internet.
""")
    network.add_argument(
        '--peered-network-ip-range',
        help="""\
IP range within the peered network. This is specified in CIDR notation with a slash and the subnet prefix size. Examples: `192.168.0.0/24` or '/29'.
""")
  if update:
    parser.add_argument(
        'CONFIG',
        help='The unique identifier of the Bitbucket Server Config to be updated.'
    )
  return parser


def AddBitbucketServerConfigCreateArgs(parser):
  """Set up all the argparse flags for creating a Bitbucket Server Config.

  Args:
    parser: An argparse.ArgumentParser-like object.

  Returns:
    The parser argument with Bitbucket Server Config flags added in.
  """
  return AddBitbucketServerConfigArgs(parser, update=False)


def AddBitbucketServerConfigUpdateArgs(parser):
  """Set up all the argparse flags for updating a Bitbucket Server Config.

  Args:
    parser: An argparse.ArgumentParser-like object.

  Returns:
    The parser argument with Bitbucket Server Config flags added in.
  """
  return AddBitbucketServerConfigArgs(parser, update=True)
