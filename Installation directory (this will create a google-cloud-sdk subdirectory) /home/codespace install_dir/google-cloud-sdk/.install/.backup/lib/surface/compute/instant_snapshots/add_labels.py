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
"""Command for adding labels to instant snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instant_snapshots_utils as api_util
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import labels_doc_helper
from googlecloudsdk.command_lib.compute import labels_flags
from googlecloudsdk.command_lib.compute.instant_snapshots import flags as ips_flags
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.GA,
                    base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class AddLabels(base.UpdateCommand):
  """add-labels command for instant snapshots."""
  IPS_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.IPS_ARG = ips_flags.MakeInstantSnapshotArg()
    cls.IPS_ARG.AddArgument(parser)
    labels_flags.AddArgsForAddLabels(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    ips_ref = self.IPS_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetDefaultScopeLister(holder.client))

    add_labels = labels_util.GetUpdateLabelsDictFromArgs(args)

    ips_info = api_util.GetInstantSnapshotInfo(ips_ref, client, messages)
    ips = ips_info.GetInstantSnapshotResource()

    set_label_req = ips_info.GetSetLabelsRequestMessage()
    labels_update = labels_util.Diff(additions=add_labels).Apply(
        set_label_req.LabelsValue, ips.labels)

    request = ips_info.GetSetInstantSnapshotLabelsRequestMessage(
        ips, labels_update.GetOrNone())

    if not labels_update.needs_update:
      return ips
    service = ips_info.GetService()
    operation = service.SetLabels(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection=ips_info.GetOperationCollection())

    operation_poller = poller.Poller(service)
    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Updating labels of instant snapshot [{0}]'.format(ips_ref.Name()))


AddLabels.detailed_help = (
    labels_doc_helper.GenerateDetailedHelpForAddLabels('instant-snapshots'))
