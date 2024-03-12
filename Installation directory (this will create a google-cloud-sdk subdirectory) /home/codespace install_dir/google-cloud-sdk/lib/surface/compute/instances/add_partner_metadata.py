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

"""Command for adding or updating or patching partner metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import partner_metadata_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.instances import flags


DETAILED_HELP = {
    'DESCRIPTION': """\
          {command} can be used to add or update or patch partner metadata of a
        virtual machine instance. Every instance has access to a
        metadata server that can be used to query partner metadata that has
        been set through this tool. For information on metadata, see

        Only Namespaces keys that are provided are mutated. Existing
        Namespaces entries will remain unaffected.

        In order to retrieve partner metadata, run:

            $ gcloud compute instances describe example-instance --zone
            us-central1-a --format="value(partnerMetadata)"

        where example-instance is the name of the virtual machine instance
        you're querying partner metadata from.

        """,
    'EXAMPLES': """\
        To add partner metadata under namespace ``gcar.googleapis.com/engine''
        to instance ``TEST_INSTANCE'' run:

          $ gcloud alpha compute instances add-partner-metadata TEST_INSTANCE \\
          --partner-metadata=gcar.googleapis.com/engine="{ \"engine\": { \"type\": V8 } }"

        To add partner metadata from a file:

          $ gcloud alpha compute instances add-partner-metadata TEST_INSTANCE \\
          --partner-metadata-from-file=examples/engine.json

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class InstancesAddPartnerMetadata(base.UpdateCommand):
  """add or update or patch partner metadata."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(
        parser, operation_type='set partner metadata on'
    )
    partner_metadata_utils.AddPartnerMetadataArgs(parser)

  def _MakePatchPartnerMetadataRequest(self, client, instance_ref, args):
    partner_metadata_dict = partner_metadata_utils.CreatePartnerMetadataDict(
        args
    )
    partner_metadata_utils.ValidatePartnerMetadata(partner_metadata_dict)
    partner_metadata_message = (
        partner_metadata_utils.ConvertPartnerMetadataDictToMessage(
            partner_metadata_dict
        )
    )
    return (
        client.apitools_client.instances,
        'PatchPartnerMetadata',
        client.messages.ComputeInstancesPatchPartnerMetadataRequest(
            partnerMetadata=client.messages.PartnerMetadata(
                partnerMetadata=partner_metadata_message
            ),
            **instance_ref.AsDict()
        ),
    )

  def Run(self, args):
    if not args.partner_metadata and not args.partner_metadata_from_file:
      raise calliope_exceptions.OneOfArgumentsRequiredException(
          ['--partner-metadata', '--partner-metadata-from-file'],
          'At least one of [--partner-metadata] or'
          ' [--partner-metadata-from-file] must be provided.',
      )
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client),
    )
    patch_request = self._MakePatchPartnerMetadataRequest(
        client, instance_ref, args
    )
    return client.MakeRequests([patch_request])


InstancesAddPartnerMetadata.detailed_help = DETAILED_HELP
