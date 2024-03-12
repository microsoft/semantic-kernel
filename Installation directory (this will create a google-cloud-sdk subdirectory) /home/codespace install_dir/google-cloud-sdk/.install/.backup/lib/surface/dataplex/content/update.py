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
"""`gcloud dataplex content update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import content
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Update(base.Command):
  """Update a Dataplex Content Resource with the given configurations."""

  detailed_help = {
      'EXAMPLES':
          """\

          To update a Dataplex content `test-content` in project `test-project` within lake `test-lake` in location `us-central1` and
          change the description to `Updated Description`, run:

            $ {command}  test-content --project=test-project --location=us-central1 --lake=test-lake  --description='Updated Description'

          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddContentitemResourceArg(parser, 'to Update a Content to.')

    parser.add_argument('--description', help='Description of the Content')
    parser.add_argument('--data-text', help='Content data in string format')
    parser.add_argument(
        '--path',
        help='The path for the Content file, represented as directory structure'
    )

    sqlscript_or_notebook = parser.add_group(
        mutex=True, help='Sql script or notebook related configurations.')

    notebook = sqlscript_or_notebook.add_group(
        help='Notebook related configurations.')

    notebook.add_argument(
        '--kernel-type',
        choices={'PYTHON3': 'python3'},
        type=arg_utils.ChoiceToEnumName,
        help='Kernel Type of the notebook.')

    sql_script = sqlscript_or_notebook.add_group(
        help='Sql script related configurations.')

    sql_script.add_argument(
        '--query-engine',
        choices={'SPARK': 'spark'},
        type=arg_utils.ChoiceToEnumName,
        help='Query Engine to be used for the Sql Query.')

    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the update action, but don\'t actually perform it.')
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    update_mask = content.GenerateUpdateMask(args)
    if len(update_mask) < 1:
      raise exceptions.HttpException(
          'Update commands must specify at least one additional parameter to change.'
      )

    content_ref = args.CONCEPTS.content.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    dataplex_client.projects_locations_lakes_contentitems.Patch(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesContentitemsPatchRequest(
            name=content_ref.RelativeName(),
            validateOnly=args.validate_only,
            updateMask=u','.join(update_mask),
            googleCloudDataplexV1Content=content
            .GenerateContentForUpdateRequest(args)))
    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    log.UpdatedResource(content_ref)
