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
"""`gcloud dataplex data-taxonomies atttributes update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import data_taxonomy
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions

from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Update a Dataplex Data Attribute."""

  detailed_help = {
      'EXAMPLES':
          """\

          To update Data Attribute `test-attribute` for Data Taxonomy `test-datataxonomy` in project `test-dataplex`
          at location `us-central1` with description as `test description` ,  display name as `displayName`,
          resource-readers as user:test@google.com, resource-writers as user:test@google.com, resource-owner as user:test@google.com run:
          data-readers as user:test@google.com and parent as `test-attribute-parent`, run:

              $ {command} test-attribute --location=us-central1 --project=test-dataplex'
              --data_taxonomy=test-datataxonomy --description='test description'
              --display-name='displayName' --resource-readers='user:test@google.com'
              --resource-writers='user:test@google.com' --resource-owners='user:test@google.com'
              --data-readers='user:test@google.com'
              --parent='test-attribute-parent'

          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddAttributeResourceArg(parser, 'to update.')
    parser.add_argument(
        '--description',
        required=False,
        help='Description of the Data Attribute.')
    parser.add_argument(
        '--display-name',
        required=False,
        help='Display Name of the Data Attribute.')
    parser.add_argument(
        '--etag',
        required=False,
        help='etag value for particular Data Attribute resource.')
    parser.add_argument(
        '--parent',
        required=False,
        help='Parent Data Attribute for the defined Data Attribute. It can be attribute name or fully qualified attribute name.')
    resource_acces_sepc = parser.add_group(
        required=False,
        help='Spec related to Dataplex Resource.Specified when applied to a resource (eg: Google Cloud Storage bucket, BigQuery, dataset, BigQuery table).'
    )
    resource_acces_sepc.add_argument(
        '--resource-readers',
        metavar='RESOURCE_READERS',
        default=[],
        required=False,
        type=arg_parsers.ArgList(),
        help='The set of principals to be granted reader role on the resource. Expected principal formats are user:$userEmail, group:$groupEmail'
        )
    resource_acces_sepc.add_argument(
        '--resource-writers',
        metavar='RESOURCE_WRITERS',
        default=[],
        required=False,
        type=arg_parsers.ArgList(),
        help='The set of principals to be granted writer role on the resource. Expected principal formats are user:$userEmail, group:$groupEmail'
        )
    resource_acces_sepc.add_argument(
        '--resource-owners',
        metavar='RESOURCE_OWNERS',
        default=[],
        required=False,
        type=arg_parsers.ArgList(),
        help='The set of principals to be granted owner role on the resource. Expected principal formats are user:$userEmail, group:$groupEmail'
        )
    dataacces_sepc = parser.add_group(
        required=False,
        help='Specified when applied to data stored on the resource (eg: rows,columns in BigQuery Tables).'
    )
    dataacces_sepc.add_argument(
        '--data-readers',
        metavar='DATA_READERS',
        default=[],
        required=False,
        type=arg_parsers.ArgList(),
        help='The set of principals to be granted reader role on the resource. Expected principal formats are user:$userEmail, group:$groupEmail'
    )
    async_group = parser.add_group(
        mutex=True,
        required=False,
        help='At most one of --async | --validate-only can be specified.')
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
    update_mask = data_taxonomy.GenerateAttributeUpdateMask(args)
    if len(update_mask) < 1:
      raise exceptions.HttpException(
          'Update commands must specify at least one additional parameter to change.'
      )

    data_attribute_ref = args.CONCEPTS.data_attribute.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    update_req_op = dataplex_client.projects_locations_dataTaxonomies_attributes.Patch(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsDataTaxonomiesAttributesPatchRequest(
            name=data_attribute_ref.RelativeName(),
            updateMask=u','.join(update_mask),
            validateOnly=args.validate_only,
            googleCloudDataplexV1DataAttribute=data_taxonomy
            .GenerateDataAttributeForUpdateRequest(data_attribute_ref, args)))

    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      response = data_taxonomy.WaitForOperation(update_req_op)
      log.UpdatedResource(data_attribute_ref,
                          details='Operation was successful.')
      return response

    log.status.Print(
        'Updating Data Attribute [{0}] with operation [{1}].'.format(
            data_attribute_ref, update_req_op.name))
    return update_req_op
