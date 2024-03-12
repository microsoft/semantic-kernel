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

"""Command for getting a Cloud Security Command Center BigQuery export."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.bqexports import bqexport_util
from googlecloudsdk.command_lib.scc.bqexports import flags as bqexports_flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Get(base.DescribeCommand):
  """Get a Security Command Center BigQuery export."""

  detailed_help = {
      'DESCRIPTION': """\
      Get a Security Command Center BigQuery export.

      BigQuery exports that are created with Security Command Center API V2 and
      later include a `location` attribute. If the `location` attribute is
      included in the resource name of a BigQuery export, you must specify it
      when referencing the export. For example, the following BigQuery export
      name has `location=eu`:
      `organizations/123/locations/eu/bigQueryExports/test-bq-export`.
      """,
      'EXAMPLES': """\
      To get a BigQuery export under given organization `123` with id
      `test-bq-export`,
      run:

        $ gcloud scc bqexports get test-bq-export \
            --organization=123

      To get a BigQuery export under given folder `456` with id `test-bq-export`,
      run:

        $ gcloud scc bqexports get test-bq-export --folder=456

      To get a BigQuery export under given project `789` with id `test-bq-export,`
      run:

        $ gcloud scc bqexports get test-bq-export --project=789

      To get a BigQuery export under given organization `123` with id
      `test-bq-export`, and `location=global` run:

        $ gcloud scc bqexports get test-bq-export \
            --organization=123 \
            --location=global
      """,
      'API REFERENCE': """\
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)
      """,
  }

  @staticmethod
  def Args(parser):
    bqexports_flags.AddBigQueryPositionalArgument(parser)
    bqexports_flags.AddParentGroup(parser)

    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):

    # Determine what version to call from --location and --api-version. The
    # BigQueryExport is a version_specific_existing_resource that may not be
    # accessed through v2 if it currently exists in v1, and vice versa.
    version = scc_util.GetVersionFromArguments(
        args, args.BIG_QUERY_EXPORT, version_specific_existing_resource=True
    )
    messages = securitycenter_client.GetMessages(version)
    client = securitycenter_client.GetClient(version)

    if version == 'v1':
      req = messages.SecuritycenterOrganizationsBigQueryExportsGetRequest()
      req.name = bqexport_util.ValidateAndGetBigQueryExportV1Name(args)
      bq_export_response = client.organizations_bigQueryExports.Get(req)
    else:
      req = (
          messages.SecuritycenterOrganizationsLocationsBigQueryExportsGetRequest()
      )
      req.name = bqexport_util.ValidateAndGetBigQueryExportV2Name(args)
      bq_export_response = client.organizations_locations_bigQueryExports.Get(
          req
      )
    return bq_export_response
