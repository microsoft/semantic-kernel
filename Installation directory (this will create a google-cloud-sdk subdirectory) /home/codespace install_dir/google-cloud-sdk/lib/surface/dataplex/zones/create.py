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
"""Command to create a Dataplex zone resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.dataplex import zone
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import flags
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Create(base.Command):
  """Create a zone.

  A zone represents a logical group of related assets within a lake. A zone can
  be used to map to organizational structure or represent stages of data
  readiness from raw to curated. It provides managing behavior that is shared
  or inherited by all contained assets.

  The Zone ID is used to generate names such as database and dataset names
  when publishing metadata to Hive Metastore and BigQuery.
   * Must contain only lowercase letters, numbers, and hyphens.
   * Must start with a letter.
   * Must end with a number or a letter.
   * Must be between 1-63 characters.
   * Must be unique across all lakes from all locations in a project.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To create a Dataplex zone with name `test-zone` within lake
          `test-lake` in location `us-central1` with type `RAW`, and resource
          location type `SINGLE_REGION`, run:

            $ {command} test-zone --location=us-central --lake=test-lake --resource-location-type=SINGLE_REGION --type=RAW

          To create a Dataplex zone with name `test-zone` within lake
          `test-lake` in location `us-central1` with type `RAW`,resource
          location type `SINGLE_REGION` with discovery-enabled and discovery
          schedule `0 * * * *`, run:

            $ {command} test-zone --location=us-central --lake=test-lake --resource-location-type=SINGLE_REGION --type=RAW --discovery-enabled --discovery-schedule="0 * * * *"

          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddZoneResourceArg(parser, 'to create.')
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the create action, but don\'t actually perform it.')
    parser.add_argument('--description', help='Description of the zone.')
    parser.add_argument('--display-name', help='Display name of the zone.')
    parser.add_argument(
        '--type',
        choices={
            'RAW':
                """A zone that contains data that needs further processing
                   before it is considered generally ready for consumption and
                   analytics workloads.""",
            'CURATED':
                """A zone that contains data that is considered to be ready for
                   broader consumption and analytics workloads. Curated
                   structured data stored in Cloud Storage must conform to
                   certain file formats (Parquet, Avro, and Orc) and organized
                   in a hive-compatible directory layout.""",
        },
        type=arg_utils.ChoiceToEnumName,
        help='Type',
        required=True)
    flags.AddDiscoveryArgs(parser)
    resource_spec = parser.add_group(
        required=True,
        help='Settings for resources attached as assets within a zone.')
    resource_spec.add_argument(
        '--resource-location-type',
        choices={
            'SINGLE_REGION':
                'Resources that are associated with a single region.',
            'MULTI_REGION':
                'Resources that are associated with a multi-region location.'
        },
        type=arg_utils.ChoiceToEnumName,
        help='Location type of the resources attached to a zone',
        required=True)
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    zone_ref = args.CONCEPTS.zone.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    create_req_op = dataplex_client.projects_locations_lakes_zones.Create(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesZonesCreateRequest(
            zoneId=zone_ref.Name(),
            parent=zone_ref.Parent().RelativeName(),
            validateOnly=args.validate_only,
            googleCloudDataplexV1Zone=zone.GenerateZoneForCreateRequest(args)))

    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      zone.WaitForOperation(create_req_op)
      log.CreatedResource(
          zone_ref.Name(),
          details='Zone created in [{0}]'
          .format(zone_ref.Parent().RelativeName()))
      return

    log.status.Print('Creating [{0}] with operation [{1}].'.format(
        zone_ref, create_req_op.name))
