# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Command for setting named ports in instance groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags


class SetNamedPortsAlpha(base.SilentCommand):
  """Sets named ports for instance groups."""

  @staticmethod
  def Args(parser):
    flags.MULTISCOPE_INSTANCE_GROUP_ARG.AddArgument(parser)
    flags.AddNamedPortsArgs(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    group_ref = flags.MULTISCOPE_INSTANCE_GROUP_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    ports = instance_groups_utils.ValidateAndParseNamedPortsArgs(
        client.messages, args.named_ports)
    # service could be zonal or regional
    request, service = instance_groups_utils.GetSetNamedPortsRequestForGroup(
        client, group_ref, ports)
    return client.MakeRequests([(service, 'SetNamedPorts', request)])

  detailed_help = instance_groups_utils.SET_NAMED_PORTS_HELP
