# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex content create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import content
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Create(base.Command):
  """Creating a content."""

  detailed_help = {
      'EXAMPLES':
          """\

          To create a Dataplex content `test-content` of type notebook  within lake `test-lake` in location `us-central1`.

           $ {command} --project=test-project --location=us-central1 --lake=test-lake --kernel-type=PYTHON3 --data-text='' --path='test-content'

          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    # Content resource does not take a Content ID and auto-generates it.
    # Hence we add Lake Resource Args here and not Content Resource args.
    resource_args.AddLakeResourceArg(
        parser, 'to create a Content to.', positional=False)
    parser.add_argument('--description', help='Description of the Content')
    parser.add_argument(
        '--data-text', help='Content data in string format', required=True)
    parser.add_argument(
        '--path',
        help='The path for the Content file, represented as directory structure',
        required=True)

    sqlscript_or_notebook = parser.add_group(
        required=True,
        mutex=True,
        help='Sql script or notebook related configurations.')

    notebook = sqlscript_or_notebook.add_group(
        required=False, help='Notebook related configurations.')

    notebook.add_argument(
        '--kernel-type',
        choices={'PYTHON3': 'python3'},
        type=arg_utils.ChoiceToEnumName,
        help='Kernel Type of the notebook.',
        required=True)

    sql_script = sqlscript_or_notebook.add_group(
        required=False, help='Sql script related configurations.')

    sql_script.add_argument(
        '--query-engine',
        choices={'SPARK': 'spark'},
        type=arg_utils.ChoiceToEnumName,
        help='Query Engine to be used for the Sql Query.',
        required=True)

    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the create action, but don\'t actually perform it.')
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
    """
    # We extract lake reference, instead of content reference as content id
    # is not provided at the time of create content and is auto-generated
    # and returned in response.
    lake_ref = args.CONCEPTS.lake.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    content_response = dataplex_client.projects_locations_lakes_contentitems.Create(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesContentitemsCreateRequest(
            parent=lake_ref.RelativeName(),
            validateOnly=args.validate_only,
            googleCloudDataplexV1Content=content
            .GenerateContentForCreateRequest(args)))

    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    log.CreatedResource(
        content_response.name,
        details='Content created in lake [{0}] in project [{1}] with location [{2}]'
        .format(lake_ref.lakesId, lake_ref.projectsId, lake_ref.locationsId))
