# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command to describe a KubeRun Component."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import component_printer
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.core.resource import resource_printer

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To show all the data about a KubeRun Component, run:

            $ {command} COMPONENT
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(kuberun_command.KubeRunCommand, base.DescribeCommand):
  """Describe a KubeRun Component."""

  detailed_help = _DETAILED_HELP
  flags = []

  @classmethod
  def Args(cls, parser):
    super(Describe, cls).Args(parser)
    parser.add_argument('component', help='Name of the component.')
    resource_printer.RegisterFormatter(
        component_printer.COMPONENT_PRINTER_FORMAT,
        component_printer.ComponentPrinter, hidden=True)
    parser.display_info.AddFormat(component_printer.COMPONENT_PRINTER_FORMAT)

  def Command(self):
    return ['components', 'describe']

  def BuildKubeRunArgs(self, args):
    return [args.component]

  def SuccessResult(self, out, args):
    return json.loads(out)
