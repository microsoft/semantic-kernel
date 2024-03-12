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
"""Command for setting metadata on project zonal metadata."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_settings_metadata_utils as metadata_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.project_zonal_metadata import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class RemoveMetadata(base.UpdateCommand):
  # pylint:disable=line-too-long
  """Remove project zonal metadata.

  *{command}* is used to remove project zonal metadata from all VMs within the
  specified zone. For information about metadata, see
  [](https://cloud.google.com/compute/docs/metadata).

  Only the metadata keys that you provide in the command get removed. All other
  existing metadata entries remain the same.

  After you remove a specific project zonal metadata entry, if that metadata key
  has any project-wide value configured, then the VMs in the zone automatically
  inherit that project-wide value.
  """
  # pylint:enable=line-too-long

  detailed_help = {'EXAMPLES': """\
        To remove the project zonal metadata with key=value in the zone ``us-central1-a''
        for the project ``my-gcp-project'', run:

        $ {command} --keys=key --zone=us-central1-a --project=my-gcp-project

        For more information and examples about how to remove project zonal
        metadata, see [](https://cloud.google.com/compute/docs/metadata/setting-custom-metadata#remove-custom-project-zonal-metadata)
      """}

  @staticmethod
  def Args(parser):
    flags.ProjectZonalMetadataRemoveMetadataFlags(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    service = client.apitools_client.instanceSettings
    get_request = client.messages.ComputeInstanceSettingsGetRequest(
        project=properties.VALUES.core.project.GetOrFail(), zone=args.zone
    )
    existing_instance_settings = client.MakeRequests(
        [(service, 'Get', get_request)]
    )[0]
    fingerprint = existing_instance_settings.fingerprint
    existing_metadata = metadata_utils.ConstructMetadataDict(
        existing_instance_settings.metadata
    )
    keys_not_in_existing_metadata = set(args.keys) - set(
        existing_metadata.keys()
    )
    if keys_not_in_existing_metadata:
      log.status.Print(
          'Provide only valid keys. Keys that do not exist in current project'
          ' zonal metadata in zone [{0}] are {1}.'.format(
              existing_instance_settings.zone, keys_not_in_existing_metadata
          )
      )
      return existing_instance_settings.metadata
    request = client.messages.ComputeInstanceSettingsPatchRequest(
        instanceSettings=client.messages.InstanceSettings(
            fingerprint=fingerprint,
            metadata=client.messages.InstanceSettingsMetadata(),
        ),
        project=properties.VALUES.core.project.GetOrFail(),
        updateMask=metadata_utils.ConstructUpdateMask(
            existing_metadata.keys() if args.all else set(args.keys)
        ),
        zone=args.zone,
    )
    return client.MakeRequests(
        [(service, 'Patch', request)],
        no_followup=True,
    )[0]
