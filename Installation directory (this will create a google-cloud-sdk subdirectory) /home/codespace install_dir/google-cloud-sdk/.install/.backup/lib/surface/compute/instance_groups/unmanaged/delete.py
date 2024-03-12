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
"""Command for deleting unmanaged instance groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instance_groups import flags


class Delete(base.DeleteCommand):
  r"""Delete Compute Engine unmanaged instance groups.

    *{command}* deletes one or more Compute Engine unmanaged
  instance groups. This command just deletes the instance group and does
  not delete the individual virtual machine instances
  in the instance group.
  For example:

    $ {command} example-instance-group-1 example-instance-group-2 \
        --zone us-central1-a

  The above example deletes two instance groups, example-instance-group-1
  and example-instance-group-2, in the ``us-central1-a'' zone.
  """

  @staticmethod
  def Args(parser):
    Delete.ZonalInstanceGroupArg = flags.MakeZonalInstanceGroupArg(plural=True)
    Delete.ZonalInstanceGroupArg.AddArgument(parser, operation_type='delete')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_group_refs = Delete.ZonalInstanceGroupArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    utils.PromptForDeletion(instance_group_refs, 'zone')

    requests = []
    for instance_group_ref in instance_group_refs:
      requests.append((client.apitools_client.instanceGroups, 'Delete',
                       client.messages.ComputeInstanceGroupsDeleteRequest(
                           **instance_group_ref.AsDict())))

    return client.MakeRequests(requests)
