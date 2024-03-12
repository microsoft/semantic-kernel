# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for tailing the serial port output of an instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class TailSerialPortOutputException(exceptions.Error):
  """An error occurred while tailing the serial port."""


class TailSerialPortOutput(base.Command):
  # pylint:disable=line-too-long
  """Periodically fetch new output from a virtual machine instance's serial port and display it as it becomes available.

  {command} is used to tail the output from a Compute
  Engine virtual machine instance's serial port. The serial port output
  from the instance will be printed to standard output. This
  information can be useful for diagnostic purposes.
  """
  detailed_help = {
      'EXAMPLES': """
  To fetch new output from instance's serial port and display it, run:

    $ {command} example-instance --zone=us-central1-b
  """}

  POLL_SLEEP_SECS = 10

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        '--port',
        type=arg_parsers.BoundedInt(1, 4),
        help="""\
        Instances can support up to four serial port outputs, numbered 1 through
        4. By default, this command will return the output of the first serial
        port. Setting this flag will return the output of the requested serial
        port.
        """)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    start = None
    while True:
      request = (client.apitools_client.instances,
                 'GetSerialPortOutput',
                 client.messages.ComputeInstancesGetSerialPortOutputRequest(
                     instance=instance_ref.Name(),
                     project=instance_ref.project,
                     port=args.port,
                     start=start,
                     zone=instance_ref.zone))

      errors = []
      objects = client.MakeRequests(
          requests=[request],
          errors_to_collect=errors)
      if errors:
        raise TailSerialPortOutputException(
            'Could not fetch serial port output: ' +
            ','.join([error[1] for error in errors]))

      result = objects[0]
      log.out.write(result.contents)
      start = result.next

      # If we didn't get any results, we sleep for a short time before the next
      # call.
      if not result.contents:
        time.sleep(self.POLL_SLEEP_SECS)
