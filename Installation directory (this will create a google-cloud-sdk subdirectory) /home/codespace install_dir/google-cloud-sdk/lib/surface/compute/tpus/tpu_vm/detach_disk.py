# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for detaching a persistent disk to a TPU VM.

Allows TPU VM users to detach persistent disks to TPUs
in a form that is decoupled from the Create and Delete
lifecycle of the actual TPU VM.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import resource_args
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import util as tpu_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


DETAILED_HELP = {
    'DESCRIPTION':
        """
        *{command}* is used to detach a disk from a TPU VM. For example,

          $ gcloud compute tpus tpu-vm detach-disk example-tpu --disk=example-disk --zone=us-central1-a

        detaches the disk named `example-disk` from the TPU VM named
        `example-tpu` in zone ``us-central1-a''.

        """,
    'EXAMPLES':
        """
        To detach a disk named `my-disk` from a TPU named `my-tpu`, run:

          $ {command} my-tpu --disk=my-disk

        To detach a regional disk with the below path from a TPU named `my-tpu`, run:

          $ {command} my-tpu --disk=projects/tpu-test-env-one-vm/region/us-central1/disks/example-disk
        """,
}


def AddTPUResourceArg(parser, verb):
  """Adds a TPU Name resource argument.

  NOTE: May be used only if it's the only resource arg in the command.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'to detach'.
  """

  concept_parsers.ConceptParser.ForResource(
      'tpu',
      resource_args.GetTPUResourceSpec('TPU'),
      'The TPU {} from.'.format(verb),
      required=True).AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DetachDisk(base.Command):
  """Detach a disk from an instance."""

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """

    parser.add_argument(
        '--disk',
        help='Name of the disk to detach from the TPU VM.',
        required=True)

    AddTPUResourceArg(parser, 'to detach disk')

  def Run(self, args):
    # If zone is not set, retrieve the one from the config.
    if args.zone is None:
      args.zone = properties.VALUES.compute.zone.Get(required=True)

    # Retrieve the TPU node.
    tpu_name_ref = args.CONCEPTS.tpu.Parse()
    tpu = tpu_utils.TPUNode(self.ReleaseTrack())
    node = tpu.Get(tpu_name_ref.Name(), args.zone)

    if not tpu_utils.IsTPUVMNode(node):
      raise exceptions.BadArgumentException(
          'TPU',
          'this command is only available for Cloud TPU VM nodes. To access '
          'this node, please see '
          'https://cloud.google.com/tpu/docs/creating-deleting-tpus.')

    if not node.dataDisks:
      raise exceptions.BadArgumentException(
          'TPU', 'no data disks to detach from current TPU VM.')

    source_path_match = re.match(r'projects/.+/(zones|regions)/.+/disks/.+',
                                 args.disk)
    if source_path_match:
      source_path = args.disk
    else:
      project = properties.VALUES.core.project.Get(required=True)
      source_path = (
          'projects/' + project + '/zones/' + args.zone + '/disks/' + args.disk
      )

    source_disk_list = []
    for disk in node.dataDisks:
      source_disk_list.append(disk.sourceDisk)
    for i, source_disk in enumerate(source_disk_list):
      if source_path != source_disk:
        continue
      if source_path == source_disk:
        del node.dataDisks[i]
        break
    else:
      raise exceptions.BadArgumentException(
          'TPU',
          'error: specified data disk is not currently attached to the TPU VM.',
      )

    return tpu.UpdateNode(
        tpu_name_ref.Name(),
        args.zone,
        node,
        'data_disks',
        'Detaching disk from TPU VM',
    )

DetachDisk.detailed_help = DETAILED_HELP
