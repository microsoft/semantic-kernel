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
"""Command for deleting disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete Compute Engine persistent disks.

  *{command}* deletes one or more Compute Engine
  persistent disks. Disks can be deleted only if they are not
  being used by any virtual machine instances.
  """

  @staticmethod
  def Args(parser):
    Delete.disks_arg = disks_flags.MakeDiskArg(plural=True)
    Delete.disks_arg.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(completers.DisksCompleter)

  def _GetCommonScopeNameForRefs(self, refs):
    """Gets common scope for references."""
    has_zone = any(hasattr(ref, 'zone') for ref in refs)
    has_region = any(hasattr(ref, 'region') for ref in refs)

    if has_zone and not has_region:
      return 'zone'
    elif has_region and not has_zone:
      return 'region'
    else:
      return None

  def _CreateDeleteRequests(self, client, disk_refs):
    """Returns a list of delete messages for disks."""

    messages = client.MESSAGES_MODULE
    requests = []
    for disk_ref in disk_refs:
      if disk_ref.Collection() == 'compute.disks':
        service = client.disks
        request = messages.ComputeDisksDeleteRequest(
            disk=disk_ref.Name(),
            project=disk_ref.project,
            zone=disk_ref.zone)
      elif disk_ref.Collection() == 'compute.regionDisks':
        service = client.regionDisks
        request = messages.ComputeRegionDisksDeleteRequest(
            disk=disk_ref.Name(),
            project=disk_ref.project,
            region=disk_ref.region)
      else:
        raise ValueError('Unknown reference type {0}'.
                         format(disk_ref.Collection()))

      requests.append((service, 'Delete', request))
    return requests

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    disk_refs = Delete.disks_arg.ResolveAsResource(
        args, holder.resources,
        default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=flags.GetDefaultScopeLister(holder.client))

    scope_name = self._GetCommonScopeNameForRefs(disk_refs)

    utils.PromptForDeletion(
        disk_refs, scope_name=scope_name, prompt_title=None)

    requests = list(self._CreateDeleteRequests(
        holder.client.apitools_client, disk_refs))

    return holder.client.MakeRequests(requests)

Delete.detailed_help = {
    'brief': 'Delete a Compute Engine disk',
    'DESCRIPTION':
        """\
        *{command}* deletes a Compute Engine disk. A disk can be
        deleted only if it is not attached to any virtual machine instances.
        """,
    'EXAMPLES':
        """\
        To delete the disk 'my-disk' in zone 'us-east1-a', run:

            $ {command} my-disk --zone=us-east1-a
        """,
}
