# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for suspending an instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ast

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {
    'brief':
        'Suspend a virtual machine instance.',
    'DESCRIPTION':
        """\
        *{command}* is used to suspend a Compute Engine virtual machine.
        Suspending a VM is the equivalent of sleep or standby mode: the guest
        receives an ACPI S3 suspend signal, after which all VM state is saved to
        temporary storage. An instance can only be suspended while it is in the
        RUNNING state. A suspended instance will be put in SUSPENDED state.

        Note: A suspended instance can be resumed by running the gcloud compute
        instances resume command.

        If a VM has any attached Local SSD disks, you can preserve the Local SSD
        data when you suspend the VM by setting `--discard-local-ssd=False`.
        Preserving the Local SSD disk data incurs costs and is subject to
        limitations.

        Limitations:

         - Limitations for suspending a VM: https://cloud.google.com/compute/docs/instances/suspend-resume-instance#limitations
         - Limitations for preserving Local SSD data: https://cloud.google.com/compute/docs/disks/local-ssd#stop_instance
        """,
    'EXAMPLES':
        """\
        To suspend an instance named ``test-instance'', run:

          $ {command} test-instance

        To suspend an instance named `test-instance` that has a Local SSD, run:

          $ {command} test-instance --discard-local-ssd=True

        Using `--discard-local-ssd` without a value defaults to `True`.
      """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Suspend(base.SilentCommand):
  """Suspend a virtual machine instance.

  *{command}* is used to suspend a Compute Engine virtual machine.
  Suspending a VM is the equivalent of sleep or standby mode:
  the guest receives an ACPI S3 suspend signal, after which all VM state
  is saved to temporary storage.  An instance can only be suspended while
  it is in the RUNNING state.  A suspended instance will be put in
  SUSPENDED state.

  Note: A suspended instance can be resumed by running the
  `gcloud compute instances resume` command.

  Limitations: See this feature's restrictions at
  https://cloud.google.com/compute/docs/instances/suspend-resume-instance#limitations
  """

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

  def _CreateSuspendRequest(self, client, instance_ref, discard_local_ssd):
    return client.messages.ComputeInstancesSuspendRequest(
        discardLocalSsd=discard_local_ssd,
        instance=instance_ref.Name(),
        project=instance_ref.project,
        zone=instance_ref.zone)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_refs = flags.INSTANCES_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    requests = []
    for instance_ref in instance_refs:
      requests.append((client.apitools_client.instances, 'Suspend',
                       self._CreateSuspendRequest(client, instance_ref,
                                                  args.discard_local_ssd)))

    errors_to_collect = []
    responses = client.AsyncRequests(requests, errors_to_collect)
    if errors_to_collect:
      raise exceptions.MultiError(errors_to_collect)

    operation_refs = [holder.resources.Parse(r.selfLink) for r in responses]

    if args.async_:
      for operation_ref in operation_refs:
        log.status.Print('Suspend instance in progress for [{}].'.format(
            operation_ref.SelfLink()))
      log.status.Print(
          'Use [gcloud compute operations describe URI] command to check the '
          'status of the operation(s).')
      return responses

    operation_poller = poller.BatchPoller(client,
                                          client.apitools_client.instances,
                                          instance_refs)

    result = waiter.WaitFor(
        operation_poller,
        poller.OperationBatch(operation_refs),
        'Suspending instance(s) {0}'.format(', '.join(
            i.Name() for i in instance_refs)),
        max_wait_ms=None)

    for instance_ref in instance_refs:
      log.status.Print('Updated [{0}].'.format(instance_ref))

    return result


Suspend.detailed_help = DETAILED_HELP
