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
"""Command for removing labels from disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import disks_util as api_util
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import labels_doc_helper
from googlecloudsdk.command_lib.compute import labels_flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.command_lib.util.args import labels_util


class RemoveLabels(base.UpdateCommand):
  """remove-labels command for disks."""

  DISK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.DISK_ARG = disks_flags.MakeDiskArg(plural=False)
    cls.DISK_ARG.AddArgument(parser)
    labels_flags.AddArgsForRemoveLabels(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages
    disk_ref = self.DISK_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetDefaultScopeLister(holder.client))
    remove_labels = labels_util.GetUpdateLabelsDictFromArgs(args)
    disk_info = api_util.GetDiskInfo(disk_ref, client, messages)
    disk = disk_info.GetDiskResource()

    if args.all:
      # removing all existing labels from the disk.
      remove_labels = {}
      if disk.labels:
        for label in disk.labels.additionalProperties:
          remove_labels[label.key] = label.value
    labels_diff = labels_util.Diff(subtractions=remove_labels)

    set_label_req = disk_info.GetSetLabelsRequestMessage()
    labels_update = labels_diff.Apply(set_label_req.LabelsValue, disk.labels)
    request = disk_info.GetSetDiskLabelsRequestMessage(
        disk, labels_update.GetOrNone())
    if not labels_update.needs_update:
      return disk

    service = disk_info.GetService()
    operation = service.SetLabels(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection=disk_info.GetOperationCollection())

    operation_poller = poller.Poller(service)
    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Updating labels of disk [{0}]'.format(
            disk_ref.Name()))


RemoveLabels.detailed_help = (
    labels_doc_helper.GenerateDetailedHelpForRemoveLabels('disk'))
