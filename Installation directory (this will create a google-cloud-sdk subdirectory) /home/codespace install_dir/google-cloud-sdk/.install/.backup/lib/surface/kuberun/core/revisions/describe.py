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
"""Describe a KubeRun revision."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.command_lib.kuberun import revision_printer
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.resource import resource_printer

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To show all the data about a KubeRun revision in the default namespace, run:

            $ {command} REVISION

        To show all the data about a KubeRun revision in a specific namespace
        ``NAMESPACE'', run:

            $ {command} REVISION --namespace=NAMESPACE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(kuberun_command.KubeRunCommand, base.DescribeCommand):
  """Describes a KubeRun revision."""

  detailed_help = _DETAILED_HELP
  flags = [flags.ClusterConnectionFlags(), flags.NamespaceFlag()]

  @classmethod
  def Args(cls, parser):
    super(Describe, cls).Args(parser)
    parser.add_argument(
        'revision', help='The KubeRun revision to show details for.')
    resource_printer.RegisterFormatter(
        revision_printer.REVISION_PRINTER_FORMAT,
        revision_printer.RevisionPrinter,
        hidden=True)
    parser.display_info.AddFormat(revision_printer.REVISION_PRINTER_FORMAT)

  def BuildKubeRunArgs(self, args):
    return [args.revision] + super(Describe, self).BuildKubeRunArgs(args)

  def Command(self):
    return ['core', 'revisions', 'describe']

  def SuccessResult(self, out, args):
    if out:
      return json.loads(out)
    else:
      raise exceptions.Error('Cannot find revision [{}]'.format(args.revision))
