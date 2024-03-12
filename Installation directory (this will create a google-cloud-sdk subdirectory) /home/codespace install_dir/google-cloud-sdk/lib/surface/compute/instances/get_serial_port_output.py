# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for reading the serial port output of an instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class GetSerialPortOutputException(exceptions.Error):
  """An error occurred while tailing the serial port."""


class GetSerialPortOutput(base.Command):
  """Read output from a virtual machine instance's serial port.

  {command} is used to get the output from a Compute
  Engine virtual machine's serial port. The serial port output
  from the virtual machine will be printed to standard output. This
  information can be useful for diagnostic purposes.
  """

  detailed_help = {
      'EXAMPLES': """
  To get the output from instance's serial port, run:

    $ {command} example-instance --zone=us-central1-b
  """}

  @staticmethod
  def Args(parser):
    """Add expected arguments."""
    parser.display_info.AddFormat('value[no-quote](contents)')
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
    parser.add_argument(
        '--start',
        type=int,
        help="""\
        Specifies the byte index (zero-based) of the first byte you want
        returned.  Use this flag if you want to continue getting the output from
        a previous request that was too long to return in one attempt.  The last
        byte returned in a request will be reported on STDERR.
        """)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    request = (client.apitools_client.instances,
               'GetSerialPortOutput',
               client.messages.ComputeInstancesGetSerialPortOutputRequest(
                   instance=instance_ref.Name(),
                   project=instance_ref.project,
                   port=args.port,
                   start=args.start,
                   zone=instance_ref.zone))

    errors = []
    objects = client.MakeRequests(
        requests=[request],
        errors_to_collect=errors)
    if errors:
      raise GetSerialPortOutputException(
          'Could not fetch serial port output: ' +
          ','.join([error[1] for error in errors]))

    response = objects[0]
    self._start = args.start
    self._response = response
    return response

  def Epilog(self, unused_resources_were_displayed):
    if self._start and self._response.start != self._start:
      log.warning(
          'Some serial port output was lost due to a limited buffer. The '
          'oldest byte of output returned was at offset {0}.'.format(
              self._response.start))
    log.status.Print(
        '\nSpecify --start={0} in the next get-serial-port-output invocation '
        'to get only the new output starting from here.'.format(
            self._response.next))
