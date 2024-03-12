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

"""`gcloud iot devices update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import flags
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.command_lib.iot import util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update an existing device."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        The following command updates the device 'my-device' in device registry 'my-registry' in region 'us-central1'. It blocks the device and sets metadata values.

          $ {command} my-device --region=us-central1 --registry=my-registry --blocked --metadata=key1=value1,key2=value2
        """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDeviceResourceArg(parser, 'to update')
    flags.AddDeviceFlagsToParser(parser, default_for_blocked_flags=False)
    flags.AddLogLevelFlagToParser(parser)

  def Run(self, args):
    client = devices.DevicesClient()

    device_ref = args.CONCEPTS.device.Parse()

    metadata = util.ParseMetadata(args.metadata,
                                  args.metadata_from_file,
                                  client.messages)
    log_level = util.ParseLogLevel(
        args.log_level, client.messages.Device.LogLevelValueValuesEnum)

    device = client.Patch(device_ref,
                          blocked=args.blocked,
                          metadata=metadata,
                          log_level=log_level)
    log.UpdatedResource(device_ref.Name(), 'device')
    return device


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA)
class UpdateAlpha(base.UpdateCommand):
  """Update an existing device."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
      The following command updates the device 'my-device' in device registry 'my-registry' in region 'us-central1'. It blocks the device and sets metadata values.

        $ {command} my-device --region=us-central1 --registry=my-registry --blocked --metadata=key1=value1,key2=value2
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDeviceResourceArg(parser, 'to update')
    flags.AddDeviceFlagsToParser(parser, default_for_blocked_flags=False)
    flags.GATEWAY_AUTH_METHOD_ENUM_MAPPER.choice_arg.AddToParser(parser)
    flags.AddLogLevelFlagToParser(parser)

  def Run(self, args):
    client = devices.DevicesClient()

    device_ref = args.CONCEPTS.device.Parse()

    metadata = util.ParseMetadata(args.metadata,
                                  args.metadata_from_file,
                                  client.messages)
    auth_method = flags.GATEWAY_AUTH_METHOD_ENUM_MAPPER.GetEnumForChoice(
        args.auth_method)
    log_level = util.ParseLogLevel(
        args.log_level, client.messages.Device.LogLevelValueValuesEnum)

    device = client.Patch(device_ref,
                          blocked=args.blocked,
                          metadata=metadata,
                          auth_method=auth_method,
                          log_level=log_level)
    log.UpdatedResource(device_ref.Name(), 'device')
    return device
