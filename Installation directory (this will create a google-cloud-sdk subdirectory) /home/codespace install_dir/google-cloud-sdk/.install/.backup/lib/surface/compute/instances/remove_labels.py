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
"""Command for removing labels from instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import labels_doc_helper
from googlecloudsdk.command_lib.compute import labels_flags
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class InstancesRemoveLabels(base.UpdateCommand):
  """remove-labels command for instances."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)
    labels_flags.AddArgsForRemoveLabels(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(holder.client))

    remove_labels = labels_util.GetUpdateLabelsDictFromArgs(args)

    instance = client.instances.Get(
        messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))

    if args.all:
      # removing all existing labels from the instance.
      remove_labels = {}
      if instance.labels:
        for label in instance.labels.additionalProperties:
          remove_labels[label.key] = label.value

    labels_update = labels_util.Diff(subtractions=remove_labels).Apply(
        messages.InstancesSetLabelsRequest.LabelsValue,
        instance.labels)
    if not labels_update.needs_update:
      return instance

    request = messages.ComputeInstancesSetLabelsRequest(
        project=instance_ref.project,
        instance=instance_ref.instance,
        zone=instance_ref.zone,
        instancesSetLabelsRequest=
        messages.InstancesSetLabelsRequest(
            labelFingerprint=instance.labelFingerprint,
            labels=labels_update.labels))

    operation = client.instances.SetLabels(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')
    operation_poller = poller.Poller(client.instances)
    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Changing labels of instance [{0}]'.format(
            instance_ref.Name()))


InstancesRemoveLabels.detailed_help = (
    labels_doc_helper.GenerateDetailedHelpForRemoveLabels('instance'))
