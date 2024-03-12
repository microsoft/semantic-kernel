# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Deletes a domain mapping of a KubeRun service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.command_lib.kuberun import pretty_print

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To delete a domain mapping in the default namespace, run:

            $ {command} DOMAIN_MAPPING

        To delete a domain mapping in a specific namespace ``NAMESPACE'', run:

            $ {command} DOMAIN_MAPPING --namespace=NAMESPACE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(kuberun_command.KubeRunCommand, base.DeleteCommand):
  """Deletes a domain mapping."""

  detailed_help = _DETAILED_HELP
  flags = [flags.NamespaceFlag(), flags.ClusterConnectionFlags()]

  @classmethod
  def Args(cls, parser):
    super(Delete, cls).Args(parser)
    parser.add_argument(
        'domain', help='The domain mapping to delete.')

  def BuildKubeRunArgs(self, args):
    return [args.domain] + super(Delete, self).BuildKubeRunArgs(args)

  def Command(self):
    return ['core', 'domain-mappings', 'delete']

  def SuccessResult(self, out, args):
    msg = """Mappings to [{domain}] now have been deleted.""".format(
        domain=args.domain)
    pretty_print.Success(msg)
