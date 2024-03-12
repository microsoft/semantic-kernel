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
"""`gcloud dataplex data-attribute-bindings update` command."""

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
  """Update a Dataplex Data Attribute Binding."""

  detailed_help = {
      'EXAMPLES':
          """\

          To Update Data Attribute Binding `test-attribute-binding` in project
          `test-dataplex` at location `us-central1` with resource attributes
          a1 and a2. Test column 'testColumn1' attached to attribute 'a1' and 'testColumn2' attached to attribute 'a2' , run:

            $ {command} test-attribute-binding --project=test-dataplex --location=us-central1
            --resource-attributes='a1,a2'
            --paths=name=testColumn1,attributes=a1
            --paths=name=testColumn2,attributes=a2
            --etag=Etag_Received_From_Get

          """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDataAttributeBindingResourceArg(parser,
                                                     'to update.')
    parser.add_argument(
        '--description',
        required=False,
        help='Description of the Data Attribute Binding.')
    parser.add_argument(
        '--display-name',
        required=False,
        help='Display Name of the Data Attribute Binding.')
    parser.add_argument(
        '--etag',
        required=True,
        help='etag value for particulat Data Attribute Binding resource.')
    parser.add_argument(
        '--resource-attributes',
        metavar='ATTRIBUTES',
        default=[],
        required=False,
        type=arg_parsers.ArgList(),
        help='List of Data Attributes to be associated with the resource')

    group = parser.add_group(mutex=True, help='Creation options.')

    group.add_argument(
        '--paths',
        metavar='PATH',
        action='append',
        required=False,
        type=arg_parsers.ArgDict(
            spec={
                'name': str,
                'attributes': arg_parsers.ArgList()
            },
            required_keys=['name', 'attributes'],
        ),
        help='The list of paths for items within the associated resource '
        '(eg. columns within a table) along with attribute bindings. '
        'The args can be passed as key value pair. Supported Keys are '
        '--path=name=value1,attributes=value2 '
        ',See https://cloud.google.com/sdk/gcloud/reference/topic/escaping for details on '
        'using a delimiter other than a comma.')

    group.add_argument(
        '--path-file-name',
        help=('The name of the JSON or YAML file to define Path '
              'config from.'))

    parser.add_argument(
        '--path-file-format',
        choices=['json', 'yaml'],
        help=(
            'The format of the file to create the path. '
            'Specify either yaml or json. Defaults to yaml if not specified. '
            'Will be ignored if --file-name is not specified.'))

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
    update_mask = data_taxonomy.GenerateAttributeBindingUpdateMask(args)
    if len(update_mask) < 1:
      raise exceptions.HttpException(
          'Update commands must specify at least one additional parameter to change.'
      )

    attribute_binding_ref = args.CONCEPTS.data_attribute_binding.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    update_req_op = dataplex_client.projects_locations_dataAttributeBindings.Patch(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsDataAttributeBindingsPatchRequest(
            name=attribute_binding_ref.RelativeName(),
            updateMask=u','.join(update_mask),
            validateOnly=args.validate_only,
            googleCloudDataplexV1DataAttributeBinding=data_taxonomy
            .GenerateDataAttributeBindingForUpdateRequest(args)))

    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      response = data_taxonomy.WaitForOperation(update_req_op)
      log.UpdatedResource(attribute_binding_ref,
                          details='Operation was successful.')
      return response

    log.status.Print(
        'Updating Data Attribute Binding [{0}] with operation [{1}].'.format(
            attribute_binding_ref, update_req_op.name))
    return update_req_op
