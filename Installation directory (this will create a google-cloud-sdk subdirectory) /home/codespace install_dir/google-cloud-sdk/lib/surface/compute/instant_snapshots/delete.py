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
"""Delete instant snapshot command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instant_snapshots import flags as ips_flags


def _CommonArgs(parser):
  """A helper function to build args based on different API version."""
  Delete.ips_arg = ips_flags.MakeInstantSnapshotArg(plural=True)
  Delete.ips_arg.AddArgument(parser, operation_type='delete')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete Compute Engine instant snapshots."""

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

  def _CreateDeleteRequests(self, client, ips_refs):
    """Returns a list of delete messages for instant snapshots."""

    messages = client.MESSAGES_MODULE
    requests = []
    for ips_ref in ips_refs:
      if ips_ref.Collection() == 'compute.instantSnapshots':
        service = client.instantSnapshots
        request = messages.ComputeInstantSnapshotsDeleteRequest(
            instantSnapshot=ips_ref.Name(),
            project=ips_ref.project,
            zone=ips_ref.zone)
      elif ips_ref.Collection() == 'compute.regionInstantSnapshots':
        service = client.regionInstantSnapshots
        request = messages.ComputeRegionInstantSnapshotsDeleteRequest(
            instantSnapshot=ips_ref.Name(),
            project=ips_ref.project,
            region=ips_ref.region)
      else:
        raise ValueError('Unknown reference type {0}'.format(
            ips_ref.Collection()))

      requests.append((service, 'Delete', request))
    return requests

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def _Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    ips_refs = Delete.ips_arg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
    )

    scope_name = self._GetCommonScopeNameForRefs(ips_refs)

    utils.PromptForDeletion(ips_refs, scope_name=scope_name, prompt_title=None)

    requests = list(
        self._CreateDeleteRequests(holder.client.apitools_client, ips_refs))

    return holder.client.MakeRequests(requests)

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  """Delete Compute Engine instant snapshots in beta."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(Delete):
  """Delete Compute Engine instant snapshots in alpha."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


Delete.detailed_help = {
    'brief': 'Delete a Compute Engine instant snapshot',
    'DESCRIPTION': """\
        *{command}* deletes a Compute Engine instant snapshot. A disk can be
        deleted only if it is not attached to any virtual machine instances.
        """,
    'EXAMPLES': """\
        To delete Compute Engine instant snapshots with the names 'instant-snapshot-1'
        and 'instant-snapshot-2', run:

          $ {command} instant-snapshot-1 instant-snapshot-2

        To list all instant snapshots that were created before a specific date, use
        the --filter flag with the `{parent_command} list` command.

          $ {parent_command} list --filter="creationTimestamp<'2017-01-01'"

        For more information on how to use --filter with the list command,
        run $ gcloud topic filters.
        """,
}
