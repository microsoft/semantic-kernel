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
"""Command for adding labels to snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import labels_doc_helper
from googlecloudsdk.command_lib.compute import labels_flags
from googlecloudsdk.command_lib.compute.snapshots import flags as snapshots_flags
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class SnapshotsAddLabels(base.UpdateCommand):
  """Add labels to Compute Engine snapshots.

  *{command}* adds labels to a Compute Engine snapshot.
  For example, running:

    $ {command} example-snapshot --labels=k0=v0,k1=v1

  will add key-value pairs ``k0''=``v0'' and ``k1''=``v1'' to
  'example-snapshot'.

  Labels can be used to identify the snapshot and to filter them as in

    $ {parent_command} list --filter='labels.k1:value2'

  To list existing labels

    $ {parent_command} describe example-snapshot --format="default(labels)"
  """

  @staticmethod
  def Args(parser):
    SnapshotsAddLabels.SnapshotArg = snapshots_flags.MakeSnapshotArg()
    SnapshotsAddLabels.SnapshotArg.AddArgument(parser)
    labels_flags.AddArgsForAddLabels(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    snapshot_ref = SnapshotsAddLabels.SnapshotArg.ResolveAsResource(
        args, holder.resources)

    add_labels = labels_util.GetUpdateLabelsDictFromArgs(args)

    snapshot = client.snapshots.Get(
        messages.ComputeSnapshotsGetRequest(**snapshot_ref.AsDict()))

    labels_update = labels_util.Diff(additions=add_labels).Apply(
        messages.GlobalSetLabelsRequest.LabelsValue,
        snapshot.labels)

    if not labels_update.needs_update:
      return snapshot

    request = messages.ComputeSnapshotsSetLabelsRequest(
        project=snapshot_ref.project,
        resource=snapshot_ref.snapshot,
        globalSetLabelsRequest=
        messages.GlobalSetLabelsRequest(
            labelFingerprint=snapshot.labelFingerprint,
            labels=labels_update.labels))

    operation = client.snapshots.SetLabels(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.globalOperations')

    operation_poller = poller.Poller(client.snapshots)
    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Updating labels of snapshot [{0}]'.format(
            snapshot_ref.Name()))


SnapshotsAddLabels.detailed_help = (
    labels_doc_helper.GenerateDetailedHelpForAddLabels('snapshot'))
