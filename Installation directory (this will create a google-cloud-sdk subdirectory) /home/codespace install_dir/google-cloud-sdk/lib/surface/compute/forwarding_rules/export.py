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
"""Export forwarding rules command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import forwarding_rules_utils as utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files


DETAILED_HELP = {
    'DESCRIPTION':
        """\
        Exports a forwarding rule's configuration to a file.
        """,
    'EXAMPLES':
        """\
        A forwarding rule can be exported by running:

          $ {command} NAME --destination=<path-to-file>
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Export(base.Command):
  """Export a forwarding rule.

  Exports a forwarding rule's configuration to a file.
  This configuration can be imported at a later time.
  """

  FORWARDING_RULE_ARG = None
  detailed_help = DETAILED_HELP

  @classmethod
  def GetApiVersion(cls):
    """Returns the API version based on the release track."""
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif cls.ReleaseTrack() == base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  @classmethod
  def GetSchemaPath(cls, for_help=False):
    """Returns the resource schema path."""
    return export_util.GetSchemaPath(
        'compute', cls.GetApiVersion(), 'ForwardingRule', for_help=for_help)

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    cls.FORWARDING_RULE_ARG.AddArgument(parser, operation_type='export')
    export_util.AddExportFlags(parser, cls.GetSchemaPath(for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    forwarding_rule_ref = self.FORWARDING_RULE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    forwarding_rule = utils.SendGetRequest(client, forwarding_rule_ref)

    if args.destination:
      with files.FileWriter(args.destination) as stream:
        export_util.Export(message=forwarding_rule,
                           stream=stream,
                           schema_path=self.GetSchemaPath())
    else:
      export_util.Export(message=forwarding_rule,
                         stream=sys.stdout,
                         schema_path=self.GetSchemaPath())
