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

"""Command for deleting managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute import path_simplifier
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import text
from six.moves import zip


class Delete(base.DeleteCommand):
  """Delete Compute Engine managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGERS_ARG.AddArgument(
        parser, operation_type='delete')

  def _GenerateAutoscalerDeleteRequests(self, holder, project, mig_requests):
    """Generates Delete requestes for autoscalers attached to instance groups.

    Args:
      holder: ComputeApiHolder, object encapsulating compute api.
      project: str, project this request should apply to.
      mig_requests: Messages which will be sent to delete instance group
        managers.

    Returns:
      Messages, which will be sent to delete autoscalers.
    """
    mig_requests = list(zip(*mig_requests))[2] if mig_requests else []
    zone_migs = [(request.instanceGroupManager, 'zone',
                  managed_instance_groups_utils.CreateZoneRef(
                      holder.resources, request)) for request in mig_requests
                 if hasattr(request, 'zone') and request.zone is not None]
    region_migs = [(request.instanceGroupManager, 'region',
                    managed_instance_groups_utils.CreateRegionRef(
                        holder.resources, request)) for request in mig_requests
                   if hasattr(request, 'region') and request.region is not None]

    zones = list(zip(*zone_migs))[2] if zone_migs else []
    regions = list(zip(*region_migs))[2] if region_migs else []

    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE
    autoscalers_to_delete = managed_instance_groups_utils.AutoscalersForMigs(
        migs=zone_migs + region_migs,
        autoscalers=managed_instance_groups_utils.AutoscalersForLocations(
            zones=zones,
            regions=regions,
            client=holder.client))
    requests = []
    for autoscaler in autoscalers_to_delete:
      if autoscaler.zone:
        service = client.autoscalers
        request = messages.ComputeAutoscalersDeleteRequest(
            zone=path_simplifier.Name(autoscaler.zone))
      else:
        service = client.regionAutoscalers
        request = messages.ComputeRegionAutoscalersDeleteRequest(
            region=path_simplifier.Name(autoscaler.region))

      request.autoscaler = autoscaler.name
      request.project = project
      requests.append((service, 'Delete', request))
    return requests

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

  def _CreateDeleteRequests(self, client, igm_refs):
    """Returns a list of delete messages for instance group managers."""

    messages = client.MESSAGES_MODULE
    requests = []
    for ref in igm_refs:
      if ref.Collection() == 'compute.instanceGroupManagers':
        service = client.instanceGroupManagers
        request = messages.ComputeInstanceGroupManagersDeleteRequest(
            instanceGroupManager=ref.Name(),
            project=ref.project,
            zone=ref.zone)
      elif ref.Collection() == 'compute.regionInstanceGroupManagers':
        service = client.regionInstanceGroupManagers
        request = messages.ComputeRegionInstanceGroupManagersDeleteRequest(
            instanceGroupManager=ref.Name(),
            project=ref.project,
            region=ref.region)
      else:
        raise ValueError('Unknown reference type {0}'.format(ref.Collection()))

      requests.append((service, 'Delete', request))
    return requests

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    project = properties.VALUES.core.project.Get(required=True)
    igm_refs = (
        instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGERS_ARG.
        ResolveAsResource)(
            args, holder.resources, default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=flags.GetDefaultScopeLister(holder.client, project))

    scope_name = self._GetCommonScopeNameForRefs(igm_refs)

    utils.PromptForDeletion(
        igm_refs, scope_name=scope_name, prompt_title=None)

    requests = list(self._CreateDeleteRequests(
        holder.client.apitools_client, igm_refs))

    resources = []
    # Delete autoscalers first.
    errors = []
    autoscaler_delete_requests = self._GenerateAutoscalerDeleteRequests(
        holder, project, mig_requests=requests)
    if autoscaler_delete_requests:
      with progress_tracker.ProgressTracker(
          'Deleting ' + text.Pluralize(
              len(autoscaler_delete_requests), 'autoscaler'),
          autotick=False,
      ) as tracker:
        resources = holder.client.MakeRequests(
            autoscaler_delete_requests,
            errors,
            progress_tracker=tracker)
      if errors:
        utils.RaiseToolException(errors)

    # Now delete instance group managers.
    errors = []
    with progress_tracker.ProgressTracker(
        'Deleting ' + text.Pluralize(len(requests), 'Managed Instance Group'),
        autotick=False,
    ) as tracker:
      resources += holder.client.MakeRequests(
          requests, errors, progress_tracker=tracker
      )
    if errors:
      utils.RaiseToolException(errors)
    return resources


Delete.detailed_help = {
    'brief': 'Delete Compute Engine managed instance groups',
    'DESCRIPTION': """\
        *{command}* deletes one or more Compute Engine managed instance
groups.
        """,
}
