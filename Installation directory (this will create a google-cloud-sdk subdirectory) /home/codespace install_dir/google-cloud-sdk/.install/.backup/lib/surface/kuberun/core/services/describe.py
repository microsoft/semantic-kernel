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
"""Describe a KubeRun service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.command_lib.kuberun import service_printer
from googlecloudsdk.core.resource import resource_printer

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To show all the data about a KubeRun service in the default namespace,
        run:

            $ {command} SERVICE

        To show all the data about a KubeRun service in a specific namespace
        ``NAMESPACE'', run:

            $ {command} SERVICE --namespace=NAMESPACE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(kuberun_command.KubeRunCommand, base.DescribeCommand):
  """Describes a KubeRun service."""

  detailed_help = _DETAILED_HELP
  flags = [flags.NamespaceFlag(), flags.ClusterConnectionFlags()]

  @classmethod
  def Args(cls, parser):
    super(Describe, cls).Args(parser)
    parser.add_argument(
        'service', help='The KubeRun service for which to show details.')
    resource_printer.RegisterFormatter(
        service_printer.SERVICE_PRINTER_FORMAT,
        service_printer.ServicePrinter,
        hidden=True)
    parser.display_info.AddFormat(service_printer.SERVICE_PRINTER_FORMAT)

  def BuildKubeRunArgs(self, args):
    return [args.service] + super(Describe, self).BuildKubeRunArgs(args)

  def Command(self):
    return ['core', 'services', 'describe']

  def SuccessResult(self, out, args):
    return json.loads(out)
