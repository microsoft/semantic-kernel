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

"""Command for updating a Cloud Security Command Center BigQuery export."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.bqexports import bqexport_util
from googlecloudsdk.command_lib.scc.bqexports import flags as bqexport_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Security Command Center BigQuery export."""

  detailed_help = {
      'DESCRIPTION': """\
      Update a Security Command Center BigQuery export.

      BigQuery exports that are created with Security Command Center API V2 and
      later include a `location` attribute. If the `location` attribute is
      included in the resource name of a BigQuery export, you must specify it
      when referencing the export. For example, the following BigQuery export
      name has `location=eu`:
      `organizations/123/locations/eu/bigQueryExports/test-bq-export`.
      """,
      'EXAMPLES': """\
      Update a BigQuery export with id `test-bq-export` under organization `123`
      with a dataset `abc` in project `234` and a filter on category that equals
      to `XSS_SCRIPTING`:

        $ gcloud scc bqexports update test-bq-export \
          --organization=123 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""

      Update a BigQuery export with id `test-bq-export` under folder `456` with
      a dataset `abc` in project `234` and a filter on category that equals to
      `XSS_SCRIPTING`:

        $ gcloud scc bqexports update test-bq-export --folder=456 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""

      Update a BigQuery export with id `test-bq-export` under project `789` with
      a dataset `abc` in project `234` and a filter on category that equals to
      `XSS_SCRIPTING`:

        $ gcloud scc bqexports update test-bq-export \
          --project=789 --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""

      Update a BigQuery export `test-bq-export` in organization `123` and
      `location=global`. This command updates the target dataset to
      `projects/234/datasets/abc`, the export description to `This is a test
      BigQuery export` and the export filter to `XSS_SCRIPTING`:

        $ gcloud scc bqexports update test-bq-export \
          --organization=123 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\"" \
          --location=global
      """,
      'API REFERENCE': """\
      This command uses the Security Command Center API. For more information,
      see [Security Command Center API.](https://cloud.google.com/security-command-center/docs/reference/rest)
      """,
  }

  @staticmethod
  def Args(parser):
    bqexport_flags.DATASET_FLAG_OPTIONAL.AddToParser(parser)
    bqexport_flags.DESCRIPTION_FLAG.AddToParser(parser)
    bqexport_flags.FILTER_FLAG.AddToParser(parser)
    bqexport_flags.UPDATE_MASK_FLAG.AddToParser(parser)

    bqexport_flags.AddBigQueryPositionalArgument(parser)
    bqexport_flags.AddParentGroup(parser)

    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):

    # Determine what version to call from --location and --api-version. The
    # BigQuery export is a version_specific_existing_resource that may not be
    # accessed through v2 if it currently exists in v1, and vice versa.
    version = scc_util.GetVersionFromArguments(
        args, args.BIG_QUERY_EXPORT, version_specific_existing_resource=True
    )
    messages = securitycenter_client.GetMessages(version)
    client = securitycenter_client.GetClient(version)

    if version == 'v1':
      req = messages.SecuritycenterOrganizationsBigQueryExportsPatchRequest()
      req.name = bqexport_util.ValidateAndGetBigQueryExportV1Name(args)
      export = messages.GoogleCloudSecuritycenterV1BigQueryExport()
      req.googleCloudSecuritycenterV1BigQueryExport = export
      endpoint = client.organizations_bigQueryExports
    else:
      req = (
          messages.SecuritycenterOrganizationsLocationsBigQueryExportsPatchRequest()
      )
      req.name = bqexport_util.ValidateAndGetBigQueryExportV2Name(args)
      export = messages.GoogleCloudSecuritycenterV2BigQueryExport()
      req.googleCloudSecuritycenterV2BigQueryExport = export
      endpoint = client.organizations_locations_bigQueryExports

    computed_update_mask = []

    if args.IsKnownAndSpecified('dataset'):
      computed_update_mask.append('dataset')
      export.dataset = args.dataset
    if args.IsKnownAndSpecified('description'):
      computed_update_mask.append('description')
      export.description = args.description
    if args.IsKnownAndSpecified('filter'):
      computed_update_mask.append('filter')
      export.filter = args.filter

    # If the user supplies an update mask, use that regardless of the supplied
    # fields.
    if args.IsKnownAndSpecified('update_mask'):
      req.updateMask = args.update_mask
    else:
      req.updateMask = ','.join(computed_update_mask)

    # Set the args' filter to None to avoid downstream naming conflicts.
    args.filter = None

    bq_export_response = endpoint.Patch(req)
    log.status.Print('Updated.')
    return bq_export_response
