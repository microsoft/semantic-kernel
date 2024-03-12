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
"""Command for attaching a persistent disk to a TPU VM.

Allows TPU VM users to attach persistent disks to TPUs
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

MODE_OPTIONS = {
    'read-write':
        ('Read-write. It is an error to attach a disk in read-write mode to '
         'more than one TPU VM.'),
    'read-only':
        'Read-only.',
}

DETAILED_HELP = {
    'DESCRIPTION':
        """
        *{command}* is used to attach a disk to a TPU VM. For example,

          $ gcloud compute tpus tpu-vm attach-disk example-tpu --disk=example-disk --mode=read-only --zone=us-central1-a

        attaches the disk named 'example-disk' to a TPU VM named
        'example-tpu' in read-only mode in zone ``us-central1-a''.

        """,
    'EXAMPLES':
        """
        To attach a disk named 'my-disk' for read-only access to a TPU named
        'my-tpu', run:

          $ {command} my-tpu --disk=my-disk --mode=read-only

        To attach a disk named 'my-read-write-disk' for read-write access to
        a TPU named 'my-tpu', run:

          $ {command} my-tpu --disk=my-read-write-disk

        To attach a regional disk named for read-write access to a TPU named
        'my-tpu', run:

          $ {command} my-tpu --disk=projects/tpu-test-env-one-vm/region/us-central1/disks/example-disk
        """,
}


def AddTPUResourceArg(parser, verb):
  """Adds a TPU Name resource argument.

  NOTE: May be used only if it's the only resource arg in the command.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'to attach'.
  """

  concept_parsers.ConceptParser.ForResource(
      'tpu',
      resource_args.GetTPUResourceSpec('TPU'),
      'The TPU function name {}.'.format(verb),
      required=True).AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AttachDisk(base.Command):
  """Attach disk to TPU VM."""

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """

    parser.add_argument(
        '--disk',
        help='The name of the disk to attach to the TPU VM.',
        required=True)

    parser.add_argument(
        '--mode',
        choices=MODE_OPTIONS,
        default='read-write',
        help='Specifies the mode of the disk.')

    AddTPUResourceArg(parser, 'to attach disk')

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

    if args.mode == 'read-write':
      args.mode = tpu.messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE
    elif args.mode == 'read-only':
      args.mode = tpu.messages.AttachedDisk.ModeValueValuesEnum.READ_ONLY
    else:
      raise exceptions.BadArgumentException(
          'mode', 'can only attach disks in read-write or read-only mode.'
      )

    source_path_match = re.match(r'projects/.+/(zones|regions)/.+/disks/.+',
                                 args.disk)
    if source_path_match:
      source_path = args.disk
    else:
      project = properties.VALUES.core.project.Get(required=True)
      source_path = (
          'projects/' + project + '/zones/' + args.zone + '/disks/' + args.disk
      )

    if not node.dataDisks:
      disk_to_attach = tpu.messages.AttachedDisk(
          mode=args.mode,
          sourceDisk=source_path
      )
      node.dataDisks.append(disk_to_attach)
    else:
      source_disk_list = []
      for disk in node.dataDisks:
        source_disk_list.append(disk.sourceDisk)
      if source_path not in source_disk_list:
        disk_to_attach = tpu.messages.AttachedDisk(
            mode=args.mode,
            sourceDisk=source_path
        )
        node.dataDisks.append(disk_to_attach)
      else:
        raise exceptions.BadArgumentException(
            'TPU', 'disk is already attached to the TPU VM.')

    return tpu.UpdateNode(
        name=tpu_name_ref.Name(),
        zone=args.zone,
        node=node,
        update_mask='data_disks',
        poller_message='Attaching disk to TPU VM',
    )

AttachDisk.detailed_help = DETAILED_HELP
