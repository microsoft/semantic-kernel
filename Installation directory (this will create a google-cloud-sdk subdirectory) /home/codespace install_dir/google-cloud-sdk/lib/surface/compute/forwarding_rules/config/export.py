# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Export backend service command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags
from googlecloudsdk.command_lib.util.declarative import python_command_util as declarative_python_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Export(base.Command):
  """Export the configuration for a firewall rule."""

  detailed_help = declarative_python_util.BuildHelpText(
      singular='forwarding rule', service='Compute Engine')

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument(required=False)
    declarative_python_util.RegisterArgs(
        parser, cls.FORWARDING_RULE_ARG.AddArgument, operation_type='export')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    resource_ref = str(
        self.FORWARDING_RULE_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(holder.client)))
    return declarative_python_util.RunExport(
        args=args,
        collection='compute.forwardingRules',
        resource_ref=resource_ref)
