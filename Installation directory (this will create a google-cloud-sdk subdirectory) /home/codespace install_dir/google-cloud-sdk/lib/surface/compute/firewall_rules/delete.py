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
"""Command for deleting firewall rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.firewall_rules import flags


class Delete(base.DeleteCommand):
  """Delete Compute Engine firewall rules.

  *{command}* deletes one or more Compute Engine firewall
  rules.

  ## EXAMPLES

  To delete a firewall rule, run:

    $ {command} my-firewall-rule
  """

  FIREWALL_ARG = None

  @staticmethod
  def Args(parser):
    Delete.FIREWALL_ARG = flags.FirewallRuleArgument(plural=True)
    Delete.FIREWALL_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.FirewallsCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    firewall_refs = Delete.FIREWALL_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    utils.PromptForDeletion(firewall_refs)

    requests = []
    for firewall_ref in firewall_refs:
      requests.append((client.apitools_client.firewalls, 'Delete',
                       client.messages.ComputeFirewallsDeleteRequest(
                           **firewall_ref.AsDict())))

    return client.MakeRequests(requests)
