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
"""Command to update a Dataplex asset resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import asset
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataplex import flags
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _CommonArgs(parser):
  """Create a common args."""
  resource_args.AddAssetResourceArg(parser, 'to update.')
  parser.add_argument(
      '--validate-only',
      action='store_true',
      default=False,
      help="Validate the update action, but don't actually perform it.",
  )
  parser.add_argument('--description', help='Description of the asset')
  parser.add_argument('--display-name', help='Display Name')
  flags.AddDiscoveryArgs(parser)
  base.ASYNC_FLAG.AddToParser(parser)
  labels_util.AddCreateLabelsFlags(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update a Dataplex asset resource."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Dataplex asset `test-asset` in zone `test-zone` in lake
          `test-lake` in location `us-central1` to have the display name
          `first-dataplex-asset` and discovery include patterns `abc`, `def`,
          run:

            $ {command} test-asset --location=us-central1 --lake=test-lake --zone=test-zone --display-name="first-dataplex-asset" --discovery-include-patterns=abc,def
          """,
  }

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)
    resource_spec = parser.add_group(
        required=False,
        help='Specification of the resource that is referenced by this asset.',
    )
    resource_spec.add_argument(
        '--resource-read-access-mode',
        required=False,
        choices={
            'DIRECT': 'Data is accessed directly using storage APIs',
            'MANAGED': (
                'Data is accessed through a managed interface using BigQuery'
                ' APIs.'
            ),
        },
        type=arg_utils.ChoiceToEnumName,
        help='Read access mode',
    )

  def GenerateUpdateMask(self, args):
    return asset.GenerateUpdateMask(args)

  def GenerateUpdateRequest(self, args):
    return asset.GenerateAssetForUpdateRequest(args)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args):
    update_mask = self.GenerateUpdateMask(args)
    if len(update_mask) < 1:
      raise exceptions.HttpException(
          'Update commands must specify at least one additional parameter to'
          ' change.'
      )

    asset_ref = args.CONCEPTS.asset.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    message = dataplex_util.GetMessageModule()
    update_req_op = dataplex_client.projects_locations_lakes_zones_assets.Patch(
        message.DataplexProjectsLocationsLakesZonesAssetsPatchRequest(
            name=asset_ref.RelativeName(),
            validateOnly=args.validate_only,
            updateMask=','.join(update_mask),
            googleCloudDataplexV1Asset=self.GenerateUpdateRequest(args),
        )
    )
    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      asset.WaitForOperation(update_req_op)
      log.UpdatedResource(asset_ref, details='Operation was sucessful.')
      return

    log.status.Print('Updating [{0}] with operation [{1}].'.format(
        asset_ref, update_req_op.name))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update a Dataplex asset resource."""

  detailed_help = {
      'EXAMPLES': """\
          To update a Dataplex asset `test-asset` in zone `test-zone` in lake
          `test-lake` in location `us-central1` to have the display name
          `first-dataplex-asset` and discovery include patterns `abc`, `def`,
          run:

            $ {command} test-asset --location=us-central1 --lake=test-lake --zone=test-zone --display-name="first-dataplex-asset" --discovery-include-patterns=abc,def
          """,
  }

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)
    resource_spec = parser.add_group(
        required=False,
        help='Specification of the resource that is referenced by this asset.',
    )
    resource_spec.add_argument(
        '--resource-read-access-mode',
        required=False,
        choices={
            'DIRECT': 'Data is accessed directly using storage APIs',
            'MANAGED': (
                'Data is accessed through a managed interface using BigQuery'
                ' APIs.'
            ),
        },
        type=arg_utils.ChoiceToEnumName,
        help='Read access mode',
    )

  def GenerateUpdateMask(self, args):
    return asset.GenerateUpdateMaskAlpha(args)

  def GenerateUpdateRequest(self, args):
    return asset.GenerateAssetForUpdateRequestAlpha(args)
