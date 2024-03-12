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
"""Command to update a Dataplex lake resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import lake
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Update(base.Command):
  """Update a Dataplex lake resource."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Dataplex Lake `test-lake` in location `us-central1` to
          have the display name `first-dataplex-lake` and metastore service \
          `projects/test-lake/locations/us-central1/service/test-service`, run:

            $ {command} test-lake --location=us-central1 --display-name="first-dataplex-lake" --metastore-service="projects/test-lake/locations/us-central1/service/test-service"
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddLakeResourceArg(parser, 'to update.')
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the update action, but don\'t actually perform it.')
    parser.add_argument('--description', help='Description of the lake')
    parser.add_argument('--display-name', help='Display Name')
    metastore = parser.add_group(
        help='Settings to manage metadata publishing to a Hive Metastore from a lake.'
    )
    metastore.add_argument(
        '--metastore-service',
        help=""" A relative reference to the Dataproc Metastore
        (https://cloud.google.com/dataproc-metastore/docs) service instance into
        which metadata will be published. This is of the form:
        `projects/{project_number}/locations/{location_id}/services/{service_id}`
        where the location matches the location of the lake.""")
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    update_mask = lake.GenerateUpdateMask(args)
    if len(update_mask) < 1:
      raise exceptions.HttpException(
          'Update commands must specify at least one additional parameter to change.'
      )

    lake_ref = args.CONCEPTS.lake.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    message = dataplex_util.GetMessageModule()
    update_req_op = dataplex_client.projects_locations_lakes.Patch(
        message.DataplexProjectsLocationsLakesPatchRequest(
            name=lake_ref.RelativeName(),
            validateOnly=args.validate_only,
            updateMask=u','.join(update_mask),
            googleCloudDataplexV1Lake=message.GoogleCloudDataplexV1Lake(
                description=args.description,
                displayName=args.display_name,
                metastore=message.GoogleCloudDataplexV1LakeMetastore(
                    service=args.metastore_service),
                labels=dataplex_util.CreateLabels(
                    message.GoogleCloudDataplexV1Lake, args))))
    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete with errors:')
      return update_req_op

    async_ = getattr(args, 'async_', False)
    if not async_:
      lake.WaitForOperation(update_req_op)
      log.UpdatedResource(lake_ref, details='Operation was sucessful.')
      return

    log.status.Print('Updating [{0}] with operation [{1}].'.format(
        lake_ref, update_req_op.name))
