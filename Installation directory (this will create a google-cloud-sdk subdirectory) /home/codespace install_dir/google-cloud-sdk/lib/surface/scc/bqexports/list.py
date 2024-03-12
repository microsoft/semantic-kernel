# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Command for listing Cloud Security Command Center BigQuery exports."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.bqexports import flags as bqexports_flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Security Command Center BigQuery exports."""

  detailed_help = {
      'DESCRIPTION': """List Security Command Center BigQuery exports.

      BigQuery exports that are created with Security Command Center API V2 and
      later include a `location` attribute. Include the `--location` flag to
      list BigQuery exports with `location` attribute other than `global`.
      """,
      'EXAMPLES': """\
      List BigQuery exports under organization `123`:

          $ gcloud scc bqexports list --organization=123

      List BigQuery exports under folder `456`:

          $ gcloud scc bqexports list --folder=456

      List BigQuery exports under project `789`:

          $ gcloud scc bqexports list --project=789

      List BigQuery exports under organization `123` and location `global`:

          $ gcloud scc bqexports list --organization=123 \
              --location=global

      List BigQuery exports under organization `123` and `location=eu`:

          $ gcloud scc bqexports list --organization=123 \
              --location=eu
      """,
      'API REFERENCE': """\
      This command uses the Security Command Center API. For more information, see
      [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)
          """,
  }

  @staticmethod
  def Args(parser):
    # Remove URI flag.
    base.URI_FLAG.RemoveFromParser(parser)

    bqexports_flags.AddParentGroup(parser, required=True)

    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):
    # Determine what version to call from --api-version.
    version = scc_util.GetVersionFromArguments(
        args, version_specific_existing_resource=True
    )
    messages = securitycenter_client.GetMessages(version)
    client = securitycenter_client.GetClient(version)

    if version == 'v1':
      request = messages.SecuritycenterOrganizationsBigQueryExportsListRequest()
      request.parent = scc_util.GetParentFromNamedArguments(args)
      endpoint = client.organizations_bigQueryExports
    else:
      request = (
          messages.SecuritycenterOrganizationsLocationsBigQueryExportsListRequest()
      )
      parent = scc_util.GetParentFromNamedArguments(args)
      location = scc_util.ValidateAndGetLocation(args, 'v2')
      request.parent = f'{parent}/locations/{location}'
      endpoint = client.organizations_locations_bigQueryExports

    request.pageSize = args.page_size

    # Automatically handle pagination. All BigQuery exports are returned
    # regardless of --page-size argument.
    return list_pager.YieldFromList(
        endpoint,
        request,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='bigQueryExports',
    )
