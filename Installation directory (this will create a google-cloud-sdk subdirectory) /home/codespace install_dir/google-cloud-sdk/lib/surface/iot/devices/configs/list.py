# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.  #
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
"""Command to list configurations for a device."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import resource_args


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List configs for a device.

  This command lists all available configurations in the history of the device.
  Up to 10 are kept; you may restrict the output to fewer via the `--limit`
  flag.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To list the 3 latest configurations of a device in region 'us-central1', run:

            $ {command} --region=us-central1 --registry=my-registry --device=my-device --limit=3
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        'table(version, cloudUpdateTime, deviceAckTime)')

    base.URI_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    resource_args.AddDeviceResourceArg(parser, 'for which to list configs',
                                       positional=False)

  def Run(self, args):
    """Run the list command."""
    client = devices.DeviceConfigsClient()

    device_ref = args.CONCEPTS.device.Parse()
    return client.List(device_ref, args.limit)
