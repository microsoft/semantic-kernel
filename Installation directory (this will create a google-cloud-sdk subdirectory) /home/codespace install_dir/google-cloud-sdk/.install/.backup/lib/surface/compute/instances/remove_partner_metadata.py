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


from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import partner_metadata_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.instances import flags


DETAILED_HELP = {
    'DESCRIPTION': """\
          {command} can be used to remove instance metadata entries.
        """,
    'EXAMPLES': """\
        To remove partner metadata namespace ``gcar.googleapis.com/engine''
        and ``gcar.googleapis.com/body'' along with their data from
        an instance named ``INSTANCE_NAME'', run:

          $ {command} INSTANCE_NAME \\
          --keys=gcar.googleapis.com/engine,gcar.googleapis.com/body

        To remove all namespaces, run:
          $ {command} INSTANCE_NAME --all

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class InstancesRemovePartnerMetadata(base.UpdateCommand):
  """remove partner metadata namespace."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(
        parser, operation_type='set partner metadata on'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--all',
        action='store_true',
        default=False,
        help='If provided, all partner metadata namespaces are removed.',
    )
    group.add_argument(
        '--keys',
        type=arg_parsers.ArgList(min_length=1),
        metavar='KEY',
        help='The namespaces partner metadata to remove.',
    )

  def GetGetPartnerMetadataRequest(self, client, instance_ref):
    return (
        client.apitools_client.instances,
        'GetPartnerMetadata',
        client.messages.ComputeInstancesGetPartnerMetadataRequest(
            **instance_ref.AsDict()
        ),
    )

  def Run(self, args):
    if not args.all and not args.keys:
      raise calliope_exceptions.OneOfArgumentsRequiredException(
          ['--keys', '--all'],
          'One of [--all] or [--keys] must be provided.',
      )
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client),
    )
    get_request = self.GetGetPartnerMetadataRequest(client, instance_ref)
    partner_metadata_message = client.MakeRequests([get_request])[0]
    partner_metadata_dict = encoding.MessageToDict(partner_metadata_message)[
        'partnerMetadata'
    ]
    if args.all:
      partner_metadata_dict = {k: None for k in partner_metadata_dict.keys()}
    else:
      for key in args.keys:
        namespace, *entries = key.split('/')
        if entries:
          deleted_entry = entries.pop()
          curr_dict = partner_metadata_dict[namespace]['entries']
          for entry in entries:
            curr_dict = curr_dict[entry]
          curr_dict[deleted_entry] = None
        else:
          partner_metadata_dict[namespace] = None
    partner_metadata_message = (
        partner_metadata_utils.ConvertPartnerMetadataDictToMessage(
            partner_metadata_dict
        )
    )
    patch_request = (
        client.apitools_client.instances,
        'PatchPartnerMetadata',
        client.messages.ComputeInstancesPatchPartnerMetadataRequest(
            partnerMetadata=client.messages.PartnerMetadata(
                partnerMetadata=partner_metadata_message
            ),
            **instance_ref.AsDict()
        ),
    )
    return client.MakeRequests([patch_request])


InstancesRemovePartnerMetadata.detailed_help = DETAILED_HELP
