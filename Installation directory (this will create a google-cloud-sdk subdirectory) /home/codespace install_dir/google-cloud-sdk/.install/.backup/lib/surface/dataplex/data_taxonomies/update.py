# -*- coding: utf-8 -*- #
# Copyright 2022 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex data-taxonomies update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import data_taxonomy
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Update a Dataplex Data Taxonomy."""

  detailed_help = {
      'EXAMPLES':
          """\

          To update Data Taxonomy `test-taxonomy` in project `test-dataplex` at location `us-central1`,
          with description `updated description` and displayName `displayName`

            $ {command} test-taxonomy --location=us-central1 --project=test-dataplex --description='updated description'

          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDataTaxonomyResourceArg(parser,
                                             'to update.')
    parser.add_argument(
        '--description',
        required=False,
        help='Description of the Data Taxonomy.')
    parser.add_argument(
        '--display-name',
        required=False,
        help='Display Name of the Data Taxonomy.')
    parser.add_argument(
        '--etag',
        required=False,
        help='etag value for particular Data Taxonomy.')
    async_group = parser.add_group(
        mutex=True,
        required=False)
    async_group.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the update action, but don\'t actually perform it.')
    base.ASYNC_FLAG.AddToParser(async_group)
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    update_mask = data_taxonomy.GenerateUpdateMask(args)
    if len(update_mask) < 1:
      raise exceptions.HttpException(
          'Update commands must specify at least one additional parameter to change.'
      )

    taxonomy_ref = args.CONCEPTS.data_taxonomy.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    update_req_op = dataplex_client.projects_locations_dataTaxonomies.Patch(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsDataTaxonomiesPatchRequest(
            name=taxonomy_ref.RelativeName(),
            validateOnly=args.validate_only,
            updateMask=u','.join(update_mask),
            googleCloudDataplexV1DataTaxonomy=data_taxonomy
            .GenerateDataTaxonomyForUpdateRequest(args)))

    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      response = data_taxonomy.WaitForOperation(update_req_op)
      log.UpdatedResource(taxonomy_ref, details='Operation was successful.')
      return response

    log.status.Print(
        'Updating Data Taxonomy [{0}] with operation [{1}].'.format(
            taxonomy_ref, update_req_op.name))
    return update_req_op
