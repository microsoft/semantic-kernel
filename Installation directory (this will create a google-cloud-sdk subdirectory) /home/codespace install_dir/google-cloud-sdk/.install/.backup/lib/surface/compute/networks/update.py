# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for updating networks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks import flags
from googlecloudsdk.command_lib.compute.networks import network_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update a Compute Engine Network.

  *{command}* is used to update virtual networks. The updates that
  cabe be performed on a network are changing the BGP routing mode
  and switching from auto subnet mode to custom subnet mode. Switching
  from auto subnet mode to custom subnet mode cannot be undone.

  ## EXAMPLES

  To update regional network with the name 'network-name' to global, run:

    $ {command} network-name \
      --bgp-routing-mode=global

  To update an auto subnet mode network with the name 'network-name' to custom
  subnet mode, run:

    $ {command} network-name \
      --switch-to-custom-subnet-mode

  """

  NETWORK_ARG = None
  _support_firewall_order = True

  MIGRATION_STAGES = dict(
      VALIDATING_NETWORK='Validating Network',
      CREATING_SUBNETWORK='Creating Subnetwork',
      UPDATING_INSTANCES='Updating Instances',
      UPDATING_INSTANCE_GROUPS='Updating Instance Groups',
      UPDATING_FORWARDING_RULES='Updating Forwarding Rules',
      CONVERTING_NETWORK_TO_SUBNET_MODE='Converting Network to Subnet Mode')

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_ARG = flags.NetworkArgument()
    cls.NETWORK_ARG.AddArgument(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    network_utils.AddUpdateArgs(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    service = holder.client.apitools_client.networks

    network_ref = self.NETWORK_ARG.ResolveAsResource(args, holder.resources)

    if args.switch_to_custom_subnet_mode:
      prompt_msg = 'Network [{0}] will be switched to custom mode. '.format(
          network_ref.Name()) + 'This operation cannot be undone.'
      console_io.PromptContinue(
          message=prompt_msg, default=True, cancel_on_no=True)
      result = service.SwitchToCustomMode(
          messages.ComputeNetworksSwitchToCustomModeRequest(
              project=network_ref.project, network=network_ref.Name()))

      operation_ref = resources.REGISTRY.Parse(
          result.name,
          params={'project': network_ref.project},
          collection='compute.globalOperations')

      if args.async_:
        log.UpdatedResource(
            operation_ref,
            kind='network {0}'.format(network_ref.Name()),
            is_async=True,
            details='Run the [gcloud compute operations describe] command '
            'to check the status of this operation.')
        return result

      operation_poller = poller.Poller(service, network_ref)

      if result.operationType == 'switchLegacyToCustomModeBeta':
        return self._WaitForLegacyNetworkMigration(operation_poller,
                                                   operation_ref)

      return waiter.WaitFor(
          poller=operation_poller,
          operation_ref=operation_ref,
          message='Switching network to custom-mode')

    network_resource = messages.Network()
    should_patch = False
    if getattr(args, 'mtu', None) is not None:
      msg = ('This might cause connectivity issues when ' +
             'there are running VMs attached.')
      console_io.PromptContinue(message=msg, default=False, cancel_on_no=True)

      network_resource.mtu = args.mtu
      should_patch = True

    if hasattr(args, 'enable_ula_internal_ipv6'):
      network_resource.enableUlaInternalIpv6 = args.enable_ula_internal_ipv6
      should_patch = True

    if hasattr(args, 'internal_ipv6_range'):
      network_resource.internalIpv6Range = args.internal_ipv6_range
      should_patch = True

    if args.bgp_routing_mode:
      should_patch = True
      network_resource.routingConfig = messages.NetworkRoutingConfig()
      network_resource.routingConfig.routingMode = (
          messages.NetworkRoutingConfig.RoutingModeValueValuesEnum(
              args.bgp_routing_mode.upper()))

    if getattr(args, 'bgp_best_path_selection_mode', None) is not None:
      should_patch = True
      if getattr(network_resource, 'routingConfig', None) is None:
        network_resource.routingConfig = messages.NetworkRoutingConfig()
      network_resource.routingConfig.bgpBestPathSelectionMode = (
          messages.NetworkRoutingConfig.BgpBestPathSelectionModeValueValuesEnum(
              args.bgp_best_path_selection_mode
          )
      )

    if getattr(args, 'bgp_bps_always_compare_med', None) is not None:
      should_patch = True
      if getattr(network_resource, 'routingConfig', None) is None:
        network_resource.routingConfig = messages.NetworkRoutingConfig()
      network_resource.routingConfig.bgpAlwaysCompareMed = (
          args.bgp_bps_always_compare_med
      )

    if getattr(args, 'bgp_bps_inter_region_cost', None) is not None:
      should_patch = True
      if getattr(network_resource, 'routingConfig', None) is None:
        network_resource.routingConfig = messages.NetworkRoutingConfig()
      network_resource.routingConfig.bgpInterRegionCost = (
          messages.NetworkRoutingConfig.BgpInterRegionCostValueValuesEnum(
              args.bgp_bps_inter_region_cost
          )
      )

    if self._support_firewall_order and args.network_firewall_policy_enforcement_order:
      should_patch = True
      network_resource.networkFirewallPolicyEnforcementOrder = (
          messages.Network.NetworkFirewallPolicyEnforcementOrderValueValuesEnum(
              args.network_firewall_policy_enforcement_order))

    if should_patch:
      resource = service.Patch(
          messages.ComputeNetworksPatchRequest(
              project=network_ref.project,
              network=network_ref.Name(),
              networkResource=network_resource))

    return resource

  def _WaitForLegacyNetworkMigration(self, operation_poller, operation_ref):
    progress_stages = []
    for key, label in self.MIGRATION_STAGES.items():
      progress_stages.append(progress_tracker.Stage(label, key=key))

    tracker = progress_tracker.StagedProgressTracker(
        message='Migrating Network from Legacy to Custom Mode',
        stages=progress_stages)
    first_status_message = list(self.MIGRATION_STAGES.keys())[0]
    tracker.last_status_message = first_status_message

    return waiter.WaitFor(
        poller=operation_poller,
        operation_ref=operation_ref,
        custom_tracker=tracker,
        tracker_update_func=self._LegacyNetworkMigrationTrackerUpdateFunc)

  def _LegacyNetworkMigrationTrackerUpdateFunc(self, tracker, operation,
                                               unused_status):
    latest_status_message = operation.statusMessage
    self._MarkStagesCompleted(tracker, latest_status_message)
    tracker.StartStage(latest_status_message)
    tracker.last_status_message = latest_status_message


# Mark all stages between last and latest status messages as completed

  def _MarkStagesCompleted(self, tracker, latest_status_message):
    ordered_stages = list(self.MIGRATION_STAGES.keys())
    last_status_message_idx = ordered_stages.index(tracker.last_status_message)
    latest_status_message_idx = ordered_stages.index(latest_status_message)
    stages_to_update = list(self.MIGRATION_STAGES.keys()
                           )[last_status_message_idx:latest_status_message_idx]

    for stage_to_update in stages_to_update:
      tracker.CompleteStage(stage_to_update)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update a Compute Engine Network."""
  _support_firewall_order = True

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_ARG = flags.NetworkArgument()
    cls.NETWORK_ARG.AddArgument(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    network_utils.AddUpdateArgs(parser)
    network_utils.AddBgpBestPathSelectionArgGroup(parser)


Update.detailed_help = {
    'brief':
        'Update a Compute Engine network',
    'DESCRIPTION':
        """\

        *{command}* is used to update Compute Engine networks."""
}
