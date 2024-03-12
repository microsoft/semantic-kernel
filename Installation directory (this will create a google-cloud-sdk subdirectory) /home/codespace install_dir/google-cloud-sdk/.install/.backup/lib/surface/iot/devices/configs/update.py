# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""`gcloud iot devices configs update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import flags
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.command_lib.iot import util
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  """Update a specific device configuration.

  This command updates the current configuration of the device.

  It *always* creates a new config with a new version number; if
  `--version-to-update` is provided, the config at that version is used as a
  base.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To update the latest configuration of a device in region 'us-central1', run:

            $ {command} --region=us-central1 --registry=my-registry --device=my-device --config-data="job_timeout:300"

          To update the latest configuration of a device in region 'us-central1' only if the latest configuration version is 11, run:

            $ {command} --region=us-central1 --registry=my-registry --device=my-device --config-file=/path/to/config.base64 --version-to-update=11
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDeviceResourceArg(parser,
                                       'for the configuration to update',
                                       positional=False)
    flags.AddDeviceConfigFlagsToParser(parser)

  def Run(self, args):
    client = devices.DevicesClient()

    device_ref = args.CONCEPTS.device.Parse()
    data = util.ReadConfigData(args)

    response = client.ModifyConfig(device_ref, data, args.version_to_update)
    log.UpdatedResource(device_ref.Name(), 'configuration for device')
    return response
