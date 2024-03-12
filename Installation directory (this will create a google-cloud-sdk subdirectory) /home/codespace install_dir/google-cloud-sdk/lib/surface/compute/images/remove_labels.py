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
"""Command for adding labels to images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import labels_doc_helper
from googlecloudsdk.command_lib.compute import labels_flags
from googlecloudsdk.command_lib.compute.images import flags as images_flags
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class ImagesRemoveLabels(base.UpdateCommand):

  DISK_IMAGE_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.DISK_IMAGE_ARG = images_flags.MakeDiskImageArg(plural=False)
    cls.DISK_IMAGE_ARG.AddArgument(parser)
    labels_flags.AddArgsForRemoveLabels(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    image_ref = self.DISK_IMAGE_ARG.ResolveAsResource(
        args, holder.resources)

    remove_labels = labels_util.GetUpdateLabelsDictFromArgs(args)

    image = client.images.Get(
        messages.ComputeImagesGetRequest(**image_ref.AsDict()))

    if args.all:
      # removing all existing labels from the image.
      remove_labels = {}
      if image.labels:
        for label in image.labels.additionalProperties:
          remove_labels[label.key] = label.value

    labels_update = labels_util.Diff(subtractions=remove_labels).Apply(
        messages.GlobalSetLabelsRequest.LabelsValue,
        image.labels)
    if not labels_update.needs_update:
      return image

    request = messages.ComputeImagesSetLabelsRequest(
        project=image_ref.project,
        resource=image_ref.image,
        globalSetLabelsRequest=
        messages.GlobalSetLabelsRequest(
            labelFingerprint=image.labelFingerprint,
            labels=labels_update.labels))

    operation = client.images.SetLabels(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.globalOperations')

    operation_poller = poller.Poller(client.images)
    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Updating labels of image [{0}]'.format(
            image_ref.Name()))


ImagesRemoveLabels.detailed_help = (
    labels_doc_helper.GenerateDetailedHelpForRemoveLabels('image'))
