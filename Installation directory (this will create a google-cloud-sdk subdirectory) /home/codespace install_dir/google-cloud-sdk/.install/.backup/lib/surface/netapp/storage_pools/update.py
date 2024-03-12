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
"""Updates a Cloud NetApp Storage Pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.storage_pools import client as storagepools_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.storage_pools import flags as storagepools_flags
from googlecloudsdk.command_lib.util.args import labels_util

from googlecloudsdk.core import log


def _CommonArgs(parser):
  storagepools_flags.AddStoragePoolUpdateArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Cloud NetApp Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Updates a Storage Pool with given arguments
          """,
      'EXAMPLES': """\
          The following command updates a Storage Pool named NAME in the given location

              $ {command} NAME --location=us-central1 --capacity=4096 --active-directory=ad-2 --description="new description" --update-labels=key1=val1
          """,
  }

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    """Update a Cloud NetApp Storage Pool in the current project."""
    storagepool_ref = args.CONCEPTS.storage_pool.Parse()
    client = storagepools_client.StoragePoolsClient(self._RELEASE_TRACK)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    orig_storagepool = client.GetStoragePool(storagepool_ref)
    capacity_in_gib = args.capacity >> 30 if args.capacity else None
    ## Update labels
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(
          client.messages.StoragePool.LabelsValue, orig_storagepool.labels
      ).GetOrNone()
    else:
      labels = None

    storage_pool = client.ParseUpdatedStoragePoolConfig(
        orig_storagepool,
        capacity=capacity_in_gib,
        description=args.description,
        labels=labels,
    )

    updated_fields = []
    if args.IsSpecified('capacity'):
      updated_fields.append('capacityGib')
    if args.IsSpecified('active_directory'):
      updated_fields.append('activeDirectory')
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (
        args.IsSpecified('update_labels')
        or args.IsSpecified('remove_labels')
        or args.IsSpecified('clear_labels')
    ):
      updated_fields.append('labels')
    update_mask = ','.join(updated_fields)

    result = client.UpdateStoragePool(
        storagepool_ref, storage_pool, update_mask, args.async_
    )
    if args.async_:
      command = 'gcloud {} netapp storage-pools list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the updated storage pool by listing all storage'
          ' pools:\n  $ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Cloud NetApp Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update a Cloud NetApp Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

