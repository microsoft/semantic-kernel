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
"""Command for stopping an instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ast

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {
    'brief':
        'Stop a virtual machine instance.',
    'DESCRIPTION':
        """\
        *{command}* is used to stop a Compute Engine virtual machine.
        Stopping a VM performs a clean shutdown, much like invoking the shutdown
        functionality of a workstation or laptop.

        If a VM has any attached Local SSD disks, you must use the
        `--discard-local-ssd` flag to indicate whether or not the Local SSD
        data should be discarded. To stop the VM and preserve the Local SSD
        data when you stop the VM by setting `--discard-local-ssd=False`.

        To stop the VM and discard the Local SSD data, specify
        `--discard-local-ssd=True`.

        Preserving the Local SSD disk data incurs costs and is subject to
        limitations. See
        https://cloud.google.com/compute/docs/disks/local-ssd#stop_instance
        for more information.

        Stopping a VM which is already stopped will return without errors.
        """,
    'EXAMPLES':
        """\
        To stop an instance named `test-instance`, run:

          $ {command} test-instance

        To stop an instance named `test-instance` that has a Local SSD, run:

          $ {command} test-instance --discard-local-ssd=True

        Using '--discard-local-ssd' without a value defaults to True.
      """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA,
                    base.ReleaseTrack.BETA)
class Stop(base.SilentCommand):
  """Stop a virtual machine instance."""

  @classmethod
  def Args(cls, parser):
    flags.INSTANCES_ARG.AddArgument(parser)
    parser.add_argument(
        '--discard-local-ssd',
        nargs='?',
        default=None,
        const=True,
        # If absent, the flag is evaluated to None.
        # If present without a value, defaults to True.
        type=lambda x: ast.literal_eval(x.lower().capitalize()),
        help=('If set to true, local SSD data is discarded.'))
    base.ASYNC_FLAG.AddToParser(parser)
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      parser.add_argument(
          '--no-graceful-shutdown',
          default=None,
          action='store_true',
          help='If specified, skips graceful shutdown.',
      )

  def _CreateStopRequest(self, client, instance_ref, args):
    if self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return client.messages.ComputeInstancesStopRequest(
          discardLocalSsd=args.discard_local_ssd,
          instance=instance_ref.Name(),
          project=instance_ref.project,
          zone=instance_ref.zone,
          noGracefulShutdown=args.no_graceful_shutdown,
      )
    return client.messages.ComputeInstancesStopRequest(
        discardLocalSsd=args.discard_local_ssd,
        instance=instance_ref.Name(),
        project=instance_ref.project,
        zone=instance_ref.zone,
    )

  def _CreateRequests(self, client, instance_refs, args):
    return [(client.apitools_client.instances, 'Stop',
             self._CreateStopRequest(client, instance_ref, args))
            for instance_ref in instance_refs]

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_refs = flags.INSTANCES_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    requests = self._CreateRequests(client, instance_refs, args)

    errors_to_collect = []
    responses = client.AsyncRequests(requests, errors_to_collect)
    if errors_to_collect:
      raise core_exceptions.MultiError(errors_to_collect)

    operation_refs = [holder.resources.Parse(r.selfLink) for r in responses]

    if args.async_:
      for operation_ref in operation_refs:
        log.status.Print('Stop instance in progress for [{}].'.format(
            operation_ref.SelfLink()))
      log.status.Print(
          'Use [gcloud compute operations describe URI] command to check the '
          'status of the operation(s).')
      return responses

    # Why DeleteBatchPoller for stop operation?
    # instance might get deleted while stopping is in progress due to change in
    # targetState caused by new incoming delete requests while gracefully
    # shutting down
    operation_poller = poller.DeleteBatchPoller(
        client, client.apitools_client.instances, instance_refs
    )
    waiter.WaitFor(
        operation_poller,
        poller.OperationBatch(operation_refs),
        'Stopping instance(s) {0}'.format(', '.join(
            i.Name() for i in instance_refs)),
        max_wait_ms=None)

    for instance_ref in instance_refs:
      log.status.Print('Updated [{0}].'.format(instance_ref))


Stop.detailed_help = DETAILED_HELP
