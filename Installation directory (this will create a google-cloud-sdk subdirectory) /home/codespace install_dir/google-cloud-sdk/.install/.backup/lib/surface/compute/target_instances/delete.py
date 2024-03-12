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
"""Command for deleting target instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.target_instances import flags


class Delete(base.DeleteCommand):
  """Delete target instances.

  *{command}* deletes one or more Compute Engine target
  instances. Target instances can be deleted only if they are
  not being used by any other resources like forwarding rules.
  """

  TARGET_INSTANCE_ARG = None

  @staticmethod
  def Args(parser):
    Delete.TARGET_INSTANCE_ARG = flags.TargetInstanceArgument(plural=True)
    Delete.TARGET_INSTANCE_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.TargetInstancesCompleter)

  def Run(self, args):
    """Issues requests necessary to delete Target Instances."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    target_instance_refs = Delete.TARGET_INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    utils.PromptForDeletion(target_instance_refs, 'zone')

    requests = []
    for target_instance_ref in target_instance_refs:
      requests.append((client.apitools_client.targetInstances, 'Delete',
                       client.messages.ComputeTargetInstancesDeleteRequest(
                           **target_instance_ref.AsDict())))

    return client.MakeRequests(requests)
