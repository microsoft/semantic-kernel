# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Bare Metal Solution NFS share create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a Bare Metal Solution NFS share.
        """,
    'EXAMPLES':
        """
          To create an NFS share called ``my-share'' in region ``us-central1'', with
          requested size of 256 Gib, SSD storage and 2 allowed clients, run:

          $ {command} my-share  --region=us-central1 --size-gib=256 --storage-type=SSD --allowed-client=network=my-network,network-project-id=some-other-project,cidr=10.130.240.24/29,mount-permissions=READ_ONLY,allow-dev=yes,allow-suid=no,enable-root-squash=yes --allowed-client=network=my-network2,cidr=10.130.240.26/28,mount-permissions=READ_WRITE,allow-dev=yes,allow-suid=yes,enable-root-squash=no
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Bare Metal Solution NFS share."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNfsShareArgToParser(parser, positional=True)
    flags.AddNfsSizeGibArg(parser=parser)
    flags.AddNfsStorageTypeArg(parser=parser)
    flags.AddNfsAllowedClientArg(parser=parser)
    labels_util.AddCreateLabelsFlags(parser=parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    nfs_share = args.CONCEPTS.nfs_share.Parse()
    client = BmsClient()
    labels = labels_util.ParseCreateArgs(
        args=args, labels_cls=client.messages.NfsShare.LabelsValue)
    op_ref = client.CreateNfsShare(
        nfs_share_resource=nfs_share,
        size_gib=args.size_gib,
        storage_type=args.storage_type,
        allowed_clients_dicts=args.allowed_client,
        labels=labels)
    if op_ref.done:
      log.CreatedResource(nfs_share.Name(), kind='NFS share')
      return op_ref

    if args.async_:
      log.status.Print('Create request issued for: [{}]\nCheck operation '
                       '[{}] for status.'.format(nfs_share.Name(),
                                                 op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='baremetalsolution.projects.locations.operations',
        api_version='v2')
    poller = waiter.CloudOperationPollerNoResources(client.operation_service)
    res = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))
    log.CreatedResource(nfs_share.Name(), kind='NFS share')
    return res


Create.detailed_help = DETAILED_HELP
