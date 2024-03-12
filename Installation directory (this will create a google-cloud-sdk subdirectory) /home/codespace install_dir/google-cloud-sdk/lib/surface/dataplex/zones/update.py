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
"""Command to update a Dataplex zone resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.dataplex import zone
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataplex import flags
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Update(base.Command):
  """Update a Dataplex zone resource."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Dataplex zone `test-zone` in lake `test-lake` in location
          `us-central1` to have the display name `first-dataplex-zone` and
          discovery include patterns `abc`, `def`, run:

            $ {command} test-zone --location=us-central1 --lake=test-lake --display-name="first-dataplex-zone" --discovery-include-patterns=abc,def
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddZoneResourceArg(parser, 'to update.')
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the create action, but don\'t actually perform it.')
    parser.add_argument('--description', help='Description of the zone')
    parser.add_argument('--display-name', help='Display Name')
    flags.AddDiscoveryArgs(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    update_mask = zone.GenerateUpdateMask(args)
    if len(update_mask) < 1:
      raise exceptions.HttpException(
          'Update commands must specify at least one additional parameter to change.'
      )

    zone_ref = args.CONCEPTS.zone.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    update_req_op = dataplex_client.projects_locations_lakes_zones.Patch(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesZonesPatchRequest(
            name=zone_ref.RelativeName(),
            validateOnly=args.validate_only,
            updateMask=u','.join(update_mask),
            googleCloudDataplexV1Zone=zone.GenerateZoneForUpdateRequest(args)))
    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      zone.WaitForOperation(update_req_op)
      log.UpdatedResource(zone_ref, details='Operation was sucessful.')
      return

    log.status.Print('Updating [{0}] with operation [{1}].'.format(
        zone_ref, update_req_op.name))
