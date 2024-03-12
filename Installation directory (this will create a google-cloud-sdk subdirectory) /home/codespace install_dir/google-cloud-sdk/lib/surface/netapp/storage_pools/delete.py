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
"""Delete a Cloud NetApp Storage Pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.storage_pools import client as storagepools_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.storage_pools import flags as storagepools_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Cloud NetApp Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Delete a Storage Pool
          """,
      'EXAMPLES': """\
          The following command deletes a Storage Pool named NAME in the given location

              $ {command} NAME --location=us-central1

          To delete a Storage Pool asynchronously, run the following command:

              $ {command} NAME --location=us-central1 --async
          """,
  }

  @staticmethod
  def Args(parser):
    storagepools_flags.AddStoragePoolDeleteArgs(parser)

  def Run(self, args):
    """Delete a Cloud NetApp Storage Pool."""

    storagepool_ref = args.CONCEPTS.storage_pool.Parse()
    if not args.quiet:
      delete_warning = ('You are about to delete a Storage Pool {}.\n'
                        'Are you sure?'.format(storagepool_ref.RelativeName()))
      if not console_io.PromptContinue(message=delete_warning):
        return None
    client = storagepools_client.StoragePoolsClient(
        release_track=self._RELEASE_TRACK)
    result = client.DeleteStoragePool(storagepool_ref, args.async_)

    if args.async_:
      command = 'gcloud {} netapp storage-pools list'.format(
          self.ReleaseTrack().prefix)
      log.status.Print(
          'Check the status of the deletion by listing all storage pools:\n  '
          '$ {} '.format(command))
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  """Delete a Cloud NetApp Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(DeleteBeta):
  """Delete a Cloud NetApp Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

