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
"""Command for simulating maintenance events on virtual machine instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

SIMULATE_MAINTENANCE_EVENT_TIMEOUT_MS = 7200000


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class SimulateMaintenanceEvent(base.UpdateCommand):
  """Simulate maintenance of virtual machine instances."""

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCES_ARG.AddArgument(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        '--with-extended-notifications',
        type=arg_parsers.ArgBoolean(),
        required=False,
        help=(
            'Send an extended notification before simulating a host '
            'maintenance event on a Compute Engine VM.'
        ),
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    instance_refs = instance_flags.INSTANCES_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetDefaultScopeLister(holder.client),
    )

    requests = []

    if args.with_extended_notifications:
      for instance_ref in instance_refs:
        request = messages.ComputeInstancesSimulateMaintenanceEventRequest(
            instance=instance_ref.Name(),
            project=instance_ref.project,
            withExtendedNotifications=args.with_extended_notifications,
            zone=instance_ref.zone,
        )
        requests.append((client.instances, 'SimulateMaintenanceEvent', request))
    else:
      for instance_ref in instance_refs:
        request = messages.ComputeInstancesSimulateMaintenanceEventRequest(
            **instance_ref.AsDict()
        )
        requests.append((client.instances, 'SimulateMaintenanceEvent', request))

    errors_to_collect = []
    responses = holder.client.AsyncRequests(requests, errors_to_collect)
    for r in responses:
      err = getattr(r, 'error', None)
      if err:
        errors_to_collect.append(poller.OperationErrors(err.errors))
    if errors_to_collect:
      raise core_exceptions.MultiError(errors_to_collect)

    operation_refs = [holder.resources.Parse(r.selfLink) for r in responses]

    if args.async_:
      for i, operation_ref in enumerate(operation_refs):
        log.UpdatedResource(
            operation_ref,
            kind='gce instance [{0}]'.format(instance_refs[i].Name()),
            is_async=True,
            details=(
                'Use [gcloud compute operations describe] command '
                'to check the status of this operation.'
            ),
        )
      return responses

    operation_poller = poller.BatchPoller(
        holder.client, client.instances, instance_refs
    )
    return waiter.WaitFor(
        operation_poller,
        poller.OperationBatch(operation_refs),
        'Simulating maintenance on instance(s) [{0}]'.format(
            ', '.join(i.SelfLink() for i in instance_refs)
        ),
        max_wait_ms=SIMULATE_MAINTENANCE_EVENT_TIMEOUT_MS,
        wait_ceiling_ms=SIMULATE_MAINTENANCE_EVENT_TIMEOUT_MS,
    )


SimulateMaintenanceEvent.detailed_help = {
    'brief': 'Simulate host maintenance of VM instances',
    'DESCRIPTION': """\
        *{command}* simulates a host maintenance event on a
        Compute Engine VM. For more information, see
        https://cloud.google.com/compute/docs/instances/simulating-host-maintenance.
        """,
    'EXAMPLES': """\
        To simulate a maintenance event on an instance named ``{0}''
        located in zone ``{1}'', run:

          $ {2} {0} --zone={1}
        """.format('test-instance', 'us-east1-d', '{command}'),
}
