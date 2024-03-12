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
"""Deletes a Cloud NetApp Active Directory."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.active_directories import client as ad_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.active_directories import flags as activedirectories_flags

from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Cloud NetApp Active Directory."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Deletes an AD (Active Directory) config for Cloud NetApp Volumes.
          """,
      'EXAMPLES': """\
          The following command deletes an AD named AD_NAME with the required arguments:

              $ {command} AD_NAME --location=us-central1

          To delete a AD Config asynchronously, run the following command:

              $ {command} AD_NAME --location=us-central1 --async
          """,
  }

  @staticmethod
  def Args(parser):
    activedirectories_flags.AddActiveDirectoryDeleteArgs(parser)

  def Run(self, args):
    """Delete a Cloud NetApp Active Directory."""

    activedirectory_ref = args.CONCEPTS.active_directory.Parse()
    if not args.quiet:
      delete_warning = ('You are about to delete an Active Directory {}.\n'
                        'Are you sure?'.format(
                            activedirectory_ref.RelativeName()))
      if not console_io.PromptContinue(message=delete_warning):
        return None
    client = ad_client.ActiveDirectoriesClient(
        release_track=self._RELEASE_TRACK)
    result = client.DeleteActiveDirectory(activedirectory_ref, args.async_)

    if args.async_:
      command = 'gcloud {} netapp active-directories list'.format(
          self.ReleaseTrack().prefix)
      log.status.Print(
          'Check the status of the deletion by listing all active directories:'
          '\n $ {} '.format(command))
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  """Delete a Cloud NetApp Active Directory."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(DeleteBeta):
  """Delete a Cloud NetApp Active Directory."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

