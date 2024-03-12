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
"""Command to create a configuration file to allow authentication from 3rd party user identities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import flags
from googlecloudsdk.command_lib.iam.byoid_utilities import cred_config


class CreateCredConfig(base.CreateCommand):
  """Create a configuration file for generated credentials.

  This command creates a configuration file to allow access to authenticated
  Google Cloud actions from a variety of external user accounts.
  """

  detailed_help = {
      'EXAMPLES': textwrap.dedent(
          """\
          To create a file-sourced credential configuration for your project, run:

            $ {command} locations/$REGION/workforcePools/$WORKFORCE_POOL_ID/providers/$PROVIDER_ID --credential-source-file=$PATH_TO_OIDC_ID_TOKEN --workforce-pool-user-project=$PROJECT_NUMBER --output-file=credentials.json

          To create a URL-sourced credential configuration for your project, run:

            $ {command} locations/$REGION/workforcePools/$WORKFORCE_POOL_ID/providers/$PROVIDER_ID --credential-source-url=$URL_FOR_OIDC_TOKEN --credential-source-headers=Key=Value --workforce-pool-user-project=$PROJECT_NUMBER --output-file=credentials.json

          To create an executable-source credential configuration for your project, run the following command:

            $ {command} locations/$REGION/workforcePools/$WORKFORCE_POOL_ID/providers/$PROVIDER_ID --executable-command=$EXECUTABLE_COMMAND --executable-timeout-millis=30000 --executable-output-file=$CACHE_FILE --workforce-pool-user-project=$PROJECT_NUMBER --output-file=credentials.json

          To use the resulting file for any of these commands, set the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to the generated file.
          """
      ),
  }

  _use_pluggable_auth = False

  @classmethod
  def Args(cls, parser):
    # Add args common between workload and workforce.
    flags.AddCommonByoidCreateConfigFlags(
        parser, cred_config.ConfigType.WORKFORCE_POOLS)

    # Required args. The audience is a positional arg, meaning it is required.
    parser.add_argument(
        'audience', help='The workforce pool provider resource name.')

    # The credential source must be specified (file-sourced or URL-sourced).
    credential_types = parser.add_group(
        mutex=True, required=True, help='Credential types.')
    credential_types.add_argument(
        '--credential-source-file',
        help='The location of the file which stores the credential.')
    credential_types.add_argument(
        '--credential-source-url',
        help='The URL to obtain the credential from.')
    credential_types.add_argument(
        '--executable-command',
        help=(
            'The full command to run to retrieve the credential. Must be an'
            ' absolute path for the program including arguments.'
        ),
    )

    parser.add_argument(
        '--workforce-pool-user-project',
        help='The client project number used to identify the application ' +
        '(client project) to the server when calling Google APIs. The user ' +
        'principal must have serviceusage.services.use IAM permission to use ' +
        'the specified project.',
        required=True)

    # Optional args.
    parser.add_argument(
        '--subject-token-type',
        help='The type of token being used for authorization. ' +
        'This defaults to urn:ietf:params:oauth:token-type:id_token.')

    parser.add_argument(
        '--enable-mtls',
        help='Use mTLS for STS endpoints.',
        action='store_true',
        hidden=True)

  def Run(self, args):
    cred_config.create_credential_config(args,
                                         cred_config.ConfigType.WORKFORCE_POOLS)
