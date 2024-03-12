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
"""Set up flags for creating or updating a Github Enterprise config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.builds import flags as build_flags


def AddGitHubEnterpriseConfigArgs(parser, update=False):
  """Sets up all the argparse flags for creating or updating a GHE config.

  Args:
    parser: An argparse.ArgumentParser-like object.
    update: If true, use the version of the flags for updating a config.
      Otherwise, use the version for creating a config.

  Returns:
    The parser argument with GitHub Enterprise config flags added in.
  """
  parser.add_argument(
      '--host-uri',
      required=not update,
      help='The host uri of the GitHub Enterprise Server.')
  parser.add_argument(
      '--app-id',
      type=int,
      required=not update,
      help=(
          'The app id of the GitHub app that should be associated with this'
          ' config.'
      ),
  )
  if not update:
    parser.add_argument(
        '--peered-network',
        help="""\
VPC network that should be used when making calls to the GitHub Enterprise Server.

If not specified, calls will be made over the public internet.
""")
  if update:
    parser.add_argument(
        'CONFIG',
        help=
        'The unique identifier of the GitHub Enterprise Config to be updated.'
    )
  parser.add_argument(
      '--webhook-key',
      help="""\
The unique identifier that Cloud Build expects to be set as the value for
the query field `webhook_key` on incoming webhook requests.

If this is not set, Cloud Build will generate one on the user's behalf.
""")
  gcs_or_secretmanager = parser.add_mutually_exclusive_group(
      required=not update)
  gcs = gcs_or_secretmanager.add_argument_group(
      'Cloud Storage location of the GitHub App credentials:')
  gcs.add_argument(
      '--gcs-bucket',
      required=True,
      help='The Cloud Storage bucket containing the credential payload.')
  gcs.add_argument(
      '--gcs-object',
      required=True,
      help='The Cloud Storage object containing the credential payload.')
  gcs.add_argument(
      '--generation',
      type=int,
      help="""\
The object generation to read the credential payload from.

If this is not set, Cloud Build will read the latest version.
""")
  secretmanager = gcs_or_secretmanager.add_argument_group(
      'Secret Manager resources of the GitHub App credentials:')
  secretmanager.add_argument(
      '--private-key-name',
      required=True,
      help='Secret Manager resource containing the private key.')
  secretmanager.add_argument(
      '--webhook-secret-name',
      required=True,
      help='Secret Manager resource containing the webhook key.')
  secretmanager.add_argument(
      '--oauth-secret-name',
      required=True,
      help='Secret Manager resource containing the oauth secret.')
  secretmanager.add_argument(
      '--oauth-client-id-name',
      required=True,
      help='Secret Manager resource containing the oauth client id.')
  secretmanager.add_argument(
      '--private-key-version-name',
      help='Secret Manager SecretVersion resource containing the private key.'
  )
  secretmanager.add_argument(
      '--webhook-secret-version-name',
      help='Secret Manager SecretVersion resource containing the webhook key.'
  )
  secretmanager.add_argument(
      '--oauth-secret-version-name',
      help='Secret Manager SecretVersion resource containing the oauth secret.'
  )
  secretmanager.add_argument(
      '--oauth-client-id-version-name',
      help=
      'Secret Manager SecretVersion resource containing the oauth client id.',
  )
  return parser


def AddGitHubEnterpriseConfigCreateArgs(parser):
  """Sets up all the argparse flags for creating a GitHub Enterprise Config.

  Args:
    parser: An argparse.ArgumentParser-like object.

  Returns:
    The parser argument with GitHub Enterprise Config flags added in.
  """
  # Making region and name required together as name is only needed for creating
  # regional GHE configs.
  region = parser.add_argument_group()
  region.add_argument(
      '--name',
      required=True,
      help='The name of the GitHub Enterprise config.',
  )
  region.add_argument(
      '--region',
      required=True,
      help=("""\
The region of the Cloud Build Service to use.\nMust be set to a supported region
name (e.g. `us-central1`).\nIf unset, `builds/region`, which is the default
region to use when working with Cloud Build resources, is used. If builds/region
is unset, region is set to `global`.
"""),
  )
  return AddGitHubEnterpriseConfigArgs(parser, update=False)


def AddGitHubEnterpriseConfigUpdateArgs(parser):
  """Sets up all the argparse flags for updating a GitHub Enterprise Config.

  Args:
    parser: An argparse.ArgumentParser-like object.

  Returns:
    The parser argument with GitHub Enterprise Config flags added in.
  """
  build_flags.AddRegionFlag(parser)
  return AddGitHubEnterpriseConfigArgs(parser, update=True)
