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

"""`gcloud iot devices credentials clear` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Clear(base.Command):
  """Delete all credentials from a device."""

  detailed_help = {
      'EXAMPLES':
          """\
          To delete all credentials from a device in region 'us-central1', run:

            $ {command} --region=us-central1 --registry=my-registry --device=my-device
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDeviceResourceArg(parser, 'for which to clear credentials',
                                       positional=False)

  def Run(self, args):
    client = devices.DevicesClient()
    device_ref = args.CONCEPTS.device.Parse()
    console_io.PromptContinue(
        message='This will delete ALL CREDENTIALS for device [{}]'.format(
            device_ref.Name()),
        cancel_on_no=True)
    response = client.Patch(device_ref, credentials=[])
    log.status.Print(
        'Cleared all credentials for device [{}].'.format(device_ref.Name()))
    return response
