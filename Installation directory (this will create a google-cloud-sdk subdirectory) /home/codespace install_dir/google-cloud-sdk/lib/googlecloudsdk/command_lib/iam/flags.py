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

"""Common flags for iam commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam.byoid_utilities import cred_config
from googlecloudsdk.command_lib.util.args import common_args


def GetRoleFlag(verb):
  return base.Argument(
      'role',
      metavar='ROLE_ID',
      help='ID of the role to {0}. '
      'Curated roles example: roles/viewer. '
      'Custom roles example: CustomRole. '
      'For custom roles, you must also specify the `--organization` '
      'or `--project` flag.'.format(verb))


def GetCustomRoleFlag(verb):
  return base.Argument(
      'role',
      metavar='ROLE_ID',
      help='ID of the custom role to {0}. '
      'You must also specify the `--organization` or `--project` '
      'flag.'.format(verb))


def GetOrgFlag(verb):
  return base.Argument(
      '--organization',
      help='Organization of the role you want to {0}.'.format(verb))


def GetProjectFlag(verb):
  help_text = 'Project of the role you want to {0}.'.format(verb)
  return common_args.ProjectArgument(help_text_to_prepend=help_text)


def AddParentFlags(parser, verb, required=True):
  parent_group = parser.add_mutually_exclusive_group(required=required)
  GetOrgFlag(verb).AddToParser(parent_group)
  GetProjectFlag(verb).AddToParser(parent_group)


_RESOURCE_NAME_HELP = """\
The full resource name or URI to {verb}.

See ["Resource Names"](https://cloud.google.com/apis/design/resource_names) for
details. To get a URI from most `list` commands in `gcloud`, pass the `--uri`
flag. For example:

```
$ gcloud compute instances list --project prj --uri \\
https://compute.googleapis.com/compute/v1/projects/prj/zones/us-east1-c/instances/i1 \\
https://compute.googleapis.com/compute/v1/projects/prj/zones/us-east1-d/instances/i2
```

"""


def GetResourceNameFlag(verb):
  return base.Argument('resource', help=_RESOURCE_NAME_HELP.format(verb=verb))


def AddCommonByoidCreateConfigFlags(parser, config_type):
  """Adds parser arguments that are common to both workload identity federation and workforce pools."""
  parser.add_argument(
      '--output-file',
      help='Location to store the generated credential configuration file.',
      required=True)

  parser.add_argument(
      '--universe-domain', help='Universe domain.', hidden=True
  )

  service_account_impersonation_options = parser.add_group(
      help='Service account impersonation options.')
  service_account_impersonation_options.add_argument(
      '--service-account',
      help='Email of the service account to impersonate.',
      required=True)
  service_account_impersonation_options .add_argument(
      '--service-account-token-lifetime-seconds',
      type=arg_parsers.Duration(
          default_unit='s',
          lower_bound='600',
          upper_bound='43200',
          parsed_unit='s'),
      help=('Lifetime duration of the service account access token in seconds. '
            'Defaults to one hour if not specified. If a lifetime greater than '
            'one hour is required, the service account must be added as an '
            'allowed value in an Organization Policy that enforces the '
            '`constraints/iam.allowServiceAccountCredentialLifetimeExtension` '
            'constraint.')
    )

  parser.add_argument(
      '--credential-source-headers',
      type=arg_parsers.ArgDict(),
      metavar='key=value',
      help='Headers to use when querying the credential-source-url.')
  parser.add_argument(
      '--credential-source-type',
      help='Format of the credential source (JSON or text).')
  parser.add_argument(
      '--credential-source-field-name',
      help='Subject token field name (key) in a JSON credential source.')

  executable_args = parser.add_group(
      help='Arguments for an executable type credential source.')
  executable_args.add_argument(
      '--executable-timeout-millis',
      type=arg_parsers.Duration(
          default_unit='ms',
          lower_bound='5s',
          upper_bound='120s',
          parsed_unit='ms'),
      help=('Timeout duration, in milliseconds, to '
            'wait for the executable to finish.')
  )
  executable_args.add_argument(
      '--executable-output-file',
      help='Absolute path to the file storing the executable response.')

  if config_type == cred_config.ConfigType.WORKFORCE_POOLS:
    executable_args.add_argument(
        '--executable-interactive-timeout-millis',
        type=arg_parsers.Duration(
            default_unit='ms',
            lower_bound='30s',
            upper_bound='1800s',
            parsed_unit='ms'),
        help='Timeout duration, in milliseconds, to wait for the ' +
        'executable to finish when the command is running in interactive mode.')
