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

"""`gcloud iot devices delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a device."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To delete a device from device registry 'my-registry', run:

          $ {command} my-device --region=us-central1 --registry=my-registry
        """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDeviceResourceArg(parser, 'to delete')

  def Run(self, args):
    client = devices.DevicesClient()

    device_ref = args.CONCEPTS.device.Parse()

    console_io.PromptContinue(
        'You are about to delete device: [{}]'.format(device_ref.Name()),
        throw_if_unattended=True, cancel_on_no=True)
    response = client.Delete(device_ref)
    log.DeletedResource(device_ref.Name(), 'device')
    return response
