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
"""Creates a Cloud NetApp Storage Pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.storage_pools import client as storagepools_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.storage_pools import flags as storagepools_flags
from googlecloudsdk.command_lib.util.args import labels_util

from googlecloudsdk.core import log


def _CommonArgs(parser, release_track):
  storagepools_flags.AddStoragePoolCreateArgs(
      parser, release_track=release_track
  )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Cloud NetApp Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Creates a Storage Pool to contain Volumes with a specified Service Level and capacity.
          """,
      'EXAMPLES': """\
          The following command creates a Storage Pool named NAME using all possible arguments with a VPC network in the same project

              $ {command} NAME --location=us-central1 --service-level=standard --capacity=2048 --network=name=default --active-directory=ad1 --kms-config=kms-config1 --enable-ldap=true --description="example description"

          The following command creates a Storage pool named NAME using all possible arguments with a shared VPC network in a separate project called VPC_PROJECT

              $ {command} NAME --location=us-central1 --service-level=standard --capacity=2048 --network=name=projects/VPC_PROJECT/locations/us-central1/networks/default --active-directory=ad1 --kms-config=kms-config1 --enable-ldap=true --description="example description"

          """,
  }

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, Create._RELEASE_TRACK)

  def Run(self, args):
    """Create a Cloud NetApp Storage Pool in the current project."""
    storagepool_ref = args.CONCEPTS.storage_pool.Parse()
    client = storagepools_client.StoragePoolsClient(self._RELEASE_TRACK)
    service_level = storagepools_flags.GetStoragePoolServiceLevelArg(
        client.messages, self._RELEASE_TRACK
    ).GetEnumForChoice(args.service_level)
    labels = labels_util.ParseCreateArgs(
        args, client.messages.StoragePool.LabelsValue)
    capacity_in_gib = args.capacity >> 30
    storage_pool = client.ParseStoragePoolConfig(
        name=storagepool_ref.RelativeName(),
        service_level=service_level,
        network=args.network,
        active_directory=args.active_directory,
        kms_config=args.kms_config,
        enable_ldap=args.enable_ldap,
        capacity=capacity_in_gib,
        description=args.description,
        labels=labels,
    )
    result = client.CreateStoragePool(
        storagepool_ref, args.async_, storage_pool
    )
    if args.async_:
      command = 'gcloud {} netapp storage-pools list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the new storage pool by listing all storage'
          ' pools:\n  $ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Cloud NetApp Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, CreateBeta._RELEASE_TRACK)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a Cloud NetApp Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, CreateAlpha._RELEASE_TRACK)
