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

"""Command for creating a Cloud Security Command Center BigQuery export."""

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
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Security Command Center BigQuery export."""

  detailed_help = {
      'DESCRIPTION': """\
      Create a Security Command Center BigQuery export.

      BigQuery exports that are created with Security Command Center API V2 and
      later include a `location` attribute. If a location is not specified, the
      default `global` location is used. For example, the following BigQuery
      export name has `location=global` attribute:
      `organizations/123/locations/global/bigQueryExports/test-bq-export`.
      """,
      'EXAMPLES': """\
      To create a BigQuery export `test-bq-export` given organization `123` with a
      dataset `abc` in project `234` and filter on category that equals to
      `XSS_SCRIPTING`, run:

        $ gcloud scc bqexports create test-bq-export \
          --organization=123 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""

      To create a BigQuery export `test-bq-export` given folder `456` with a
      dataset `abc` in project `234` and filter on category that equals to
      `XSS_SCRIPTING`, run:

        $ gcloud scc bqexports create test-bq-export --folder=456 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""

      To create a BigQuery export test-bq-export given project `789` with a
      dataset `abc` in project `234` and filter on category that equals to
      `XSS_SCRIPTING`, run:

        $ gcloud scc bqexports create test-bq-export --project=789 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""

      To create a BigQuery export `test-bq-export` given organization `123` and
      `location=global` to send findings with `category=XSS_SCRIPTING` to the
      BigQuery dataset `abc` in project `234`, run:

        $ gcloud scc bqexports create test-bq-export \
          --organization=123 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""
          --location=global
      """,
      'API REFERENCE': """\
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)
      """,
  }

  @staticmethod
  def Args(parser):
    bqexports_flags.DATASET_FLAG_REQUIRED.AddToParser(parser)
    bqexports_flags.DESCRIPTION_FLAG.AddToParser(parser)
    bqexports_flags.FILTER_FLAG.AddToParser(parser)

    bqexports_flags.AddBigQueryPositionalArgument(parser)
    bqexports_flags.AddParentGroup(parser)

    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):

    # Determine what version to call from --location and --api-version.
    version = scc_util.GetVersionFromArguments(
        args, args.BIG_QUERY_EXPORT, version_specific_existing_resource=True
    )
    messages = securitycenter_client.GetMessages(version)
    client = securitycenter_client.GetClient(version)

    # Set version-specific variables
    if version == 'v1':
      req = messages.SecuritycenterOrganizationsBigQueryExportsCreateRequest()
      config_name = bqexport_util.ValidateAndGetBigQueryExportV1Name(args)
      export = messages.GoogleCloudSecuritycenterV1BigQueryExport()
      req.googleCloudSecuritycenterV1BigQueryExport = export
      endpoint = client.organizations_bigQueryExports
    else:
      req = (
          messages.SecuritycenterOrganizationsLocationsBigQueryExportsCreateRequest()
      )
      config_name = bqexport_util.ValidateAndGetBigQueryExportV2Name(args)
      export = messages.GoogleCloudSecuritycenterV2BigQueryExport()
      req.googleCloudSecuritycenterV2BigQueryExport = export
      endpoint = client.organizations_locations_bigQueryExports

    req.bigQueryExportId = _GetBigQueryExportIdFromFullResourceName(config_name)
    req.parent = _GetParentFromFullResourceName(config_name)

    export.dataset = args.dataset
    export.description = args.description
    export.filter = args.filter

    # Set the args' filter to None to avoid downstream naming conflicts.
    args.filter = None

    bq_export_response = endpoint.Create(req)
    log.status.Print('Created.')
    return bq_export_response


def _GetBigQueryExportIdFromFullResourceName(config_name):
  """Gets BigQuery export id from the full resource name."""
  bq_export_components = config_name.split('/')
  return bq_export_components[len(bq_export_components) - 1]


def _GetParentFromFullResourceName(config_name):
  """Returns the parts of the BigQuery export name before "/bigQueryExports"."""
  return '/'.join(config_name.split('/')[:-2])
