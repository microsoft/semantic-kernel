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

"""`gcloud iot devices configs get-value` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.command_lib.iot import util


class GetValue(base.Command):
  """Show the binary data of a device's latest configuration."""

  detailed_help = {
      'EXAMPLES':
          """\
          To show the binary data of the latest configuration of a device in region 'us-central1', run:

            $ {command} --region=us-central1 --registry=my-registry --device=my-device
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('get[terminator=""](.)')
    resource_args.AddDeviceResourceArg(
        parser,
        'for the configuration to get the value of',
        positional=False)

  def Run(self, args):
    client = devices.DevicesClient()

    device_ref = args.CONCEPTS.device.Parse()

    device = client.Get(device_ref)
    try:
      data = device.config.binaryData
    except AttributeError:
      # This shouldn't happen, as the API puts in a config for each device.
      raise util.BadDeviceError(
          'Device [{}] is missing configuration data.'.format(
              device_ref.Name()))
    return data
