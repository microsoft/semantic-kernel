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
"""`gcloud tasks cmek-config update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import log


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class UpdateCmekConfig(base.Command):
  """Enable, disable, or edit CMEK configuration for Cloud Tasks in the specified location."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To update a CMEK config:

              $ {command} --kms-key-name=projects/my-project/locations/my-location/keyRings/my-keyring/cryptoKeys/key
         """,
  }

  @staticmethod
  def Args(parser):
    flags.AddCmekConfigResourceFlag(parser)

  def Run(self, args):
    api = GetApiAdapter(self.ReleaseTrack())
    cmek_config_client = api.cmek_config
    if args.clear_kms_key:
      # When clearing, we only need to have location and _PROJECT()
      project_id, location_id = parsers.ParseKmsClearArgs(args)
      full_kms_key_name = ''
    else:
      project_id, full_kms_key_name, location_id = parsers.ParseKmsUpdateArgs(
          args
      )

    cmek_config = cmek_config_client.UpdateCmekConfig(
        project_id, location_id, full_kms_key_name, args.clear_kms_key
    )
    log.status.Print(
        'Updated Cmek config for KMS key: [{}].'.format(
            parsers.GetConsolePromptString(full_kms_key_name)
        )
    )
    return cmek_config
