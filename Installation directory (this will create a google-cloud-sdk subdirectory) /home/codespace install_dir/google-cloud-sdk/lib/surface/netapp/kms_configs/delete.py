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
"""Delete a Cloud NetApp Volumes KMS Config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.kms_configs import client as kmsconfigs_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.kms_configs import flags as kmsconfigs_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Cloud NetApp Volumes KMS Config."""

  detailed_help = {
      'DESCRIPTION': """\
          Delete a KMS (Key Management System) Config
          """,
      'EXAMPLES': """\
          The following command deletes a KMS Config instance named KMS_CONFIG in the default netapp/location.

              $ {command} KMS_CONFIG

          To delete a KMS Config named KMS_CONFIG asynchronously, run the following command:

              $ {command} KMS_CONFIG --async
          """,
  }

  _RELEASE_TRACK = base.ReleaseTrack.GA

  @staticmethod
  def Args(parser):
    kmsconfigs_flags.AddKMSConfigDeleteArgs(parser)

  def Run(self, args):
    """Delete a Cloud NetApp Volumes KMS Config."""

    kmsconfig_ref = args.CONCEPTS.kms_config.Parse()
    if not args.quiet:
      delete_warning = ('You are about to delete a KMS Config {}.\n'
                        'Are you sure?'.format(kmsconfig_ref.RelativeName()))
      if not console_io.PromptContinue(message=delete_warning):
        return None
    client = kmsconfigs_client.KmsConfigsClient(
        release_track=self._RELEASE_TRACK)
    result = client.DeleteKmsConfig(kmsconfig_ref, args.async_)

    if args.async_:
      command = 'gcloud {} netapp kms-configs list'.format(
          self.ReleaseTrack().prefix)
      log.status.Print(
          'Check the status of the deletion by listing all KMS configs:\n  '
          '$ {} '.format(command))
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  """Delete a Cloud NetApp Volumes KMS Config."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


