# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to send SSH commands into a Cloud TPU Queued Resource's Nodes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import os.path
import threading
import time

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.tpus.queued_resources import ssh as qr_ssh_utils
from googlecloudsdk.command_lib.compute.tpus.queued_resources import util as queued_resource_utils
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import ssh as tpu_ssh_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def AddCommandArgGroup(parser):
  """Argument group for running commands using SSH."""
  command_group = parser.add_argument_group(
      help='These arguments are used to run commands using SSH.'
  )
  command_group.add_argument(
      '--command',
      required=True,
      help="""\
      Command to run on the Cloud TPU VM.

      Runs the command on the target Cloud TPU Queued Resource's nodes and then exits.

      Note: in the case of a TPU Pod, it will only run the command in the
      workers specified with the `--worker` flag (defaults to worker all if not
      set).
      """,
  )
  command_group.add_argument(
      '--output-directory',
      help="""\
      Path to the directory to output the logs of the commands.

      The path can be relative or absolute. The directory must already exist.

      If not specified, standard output will be used.

      The logs will be written in files named {WORKER_ID}.log. For example:
      "2.log".
      """,
  )


def AddSSHArgs(parser):
  """Additional flags and positional args to be passed to *ssh(1)*."""
  parser.add_argument(
      '--ssh-flag',
      action='append',
      help="""\
      Additional flags to be passed to *ssh(1)*. It is recommended that flags
      be passed using an assignment operator and quotes. Example:

        $ {command} example-instance --zone=us-central1-a --ssh-flag="-vvv" --ssh-flag="-L 80:localhost:80"

      This flag will replace occurences of ``%USER%'' and ``%TPU%'' with
      their dereferenced values. For example, passing ``80:%TPU%:80`` into
      the flag is equivalent to passing ``80:162.222.181.197:80'' to *ssh(1)*
      if the external IP address of 'example-instance' is 162.222.181.197.

      If connecting to the instance's external IP, then %TPU% is replaced
      with that, otherwise it is replaced with the internal IP.
      """,
  )

  parser.add_argument(
      'user_queued_resource',
      completer=completers.InstancesCompleter,
      metavar='[USER@]QR',
      help="""\
      Specifies the Cloud TPU Queued Resource to send SSH command to.

      ``USER'' specifies the username with which to SSH. If omitted, the user
      login name is used.

      ``QR'' specifies the name of the Cloud TPU Queued Resource to send SSH command to.
      """,
  )

  parser.add_argument(
      'ssh_args',
      nargs=argparse.REMAINDER,
      help="""\
          Flags and positionals passed to the underlying ssh implementation.
          """,
      example="""\
        $ {command} example-instance --zone=us-central1-a -- -vvv -L 80:%TPU%:80
      """,
  )

  parser.add_argument(
      '--node',
      default='0',
      help="""\
          TPU node(s) to connect to. The supported value is a single 0-based
          index of the node(s) in the case of a TPU Pod. When also using the
          `--command` flag, it additionally supports a comma-separated list
          (e.g. '1,4,6'), range (e.g. '1-3'), or special keyword ``all" to
          run the command concurrently on each of the specified node(s).

          Note that when targeting multiple nodes, you should run 'ssh-add'
          with your private key prior to executing the gcloud command. Default:
          'ssh-add ~/.ssh/google_compute_engine'.
          """,
  )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Ssh(base.Command):
  """Send SSH commands to a Cloud TPU Queued Resource."""

  _ENABLE_IAP = True
  _ENABLE_BATCHING = True
  DEFAULT_BATCH_SIZE = 64

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    ssh_utils.BaseSSHCLIHelper.Args(parser)
    AddSSHArgs(parser)
    tpu_ssh_utils.AddTPUSSHArgs(
        parser,
        enable_iap=cls._ENABLE_IAP,
        enable_batching=cls._ENABLE_BATCHING,
        enable_batching_default=cls.DEFAULT_BATCH_SIZE,
    )
    AddCommandArgGroup(parser)
    flags.AddZoneFlag(parser, resource_type='tpu', operation_type='ssh')

  def Run(self, args):
    start_time = time.time()
    user, qr_name = ssh_utils.GetUserAndInstance(args.user_queued_resource)

    # If zone is not set, retrieve the one from the config.
    if args.zone is None:
      args.zone = properties.VALUES.compute.zone.Get(required=True)
    # Validate the output path.
    if args.output_directory:
      output_directory_path = os.path.abspath(
          os.path.expandvars(os.path.expanduser(args.output_directory))
      )
      if not os.path.isdir(output_directory_path):
        raise exceptions.InvalidArgumentException(
            '--output_directory',
            'Failed to find directory {}. Please create '
            'it or specify another directory'.format(output_directory_path),
        )

    queued_resource_client = queued_resource_utils.TPUQueuedResource(
        self.ReleaseTrack()
    )
    queued_resource = queued_resource_client.Get(qr_name, args.zone)
    username_requested = '@' in args.user_queued_resource

    # Put all the tpu names into the list that we want to send the ssh command
    # to.
    node_specs = qr_ssh_utils.ParseNodeFlag(
        args.node, queued_resource.tpu.nodeSpec
    )

    prep_nodes_threads = []
    current_batch_size = 0
    num_nodes = len(node_specs)
    prep_node_batch_size = tpu_ssh_utils.ParseBatchSize(
        args.batch_size, len(node_specs)
    )
    prepped_nodes = [None] * num_nodes

    for index, node in enumerate(node_specs):
      prep_nodes_threads.append(
          threading.Thread(
              target=tpu_ssh_utils.PrepareNodeForSSH,
              args=(
                  node.nodeId,
                  user,
                  args,
                  self.ReleaseTrack(),
                  self._ENABLE_BATCHING,
                  username_requested,
                  prepped_nodes,
                  index,
              ),
          )
      )
      prep_nodes_threads[-1].start()
      current_batch_size += 1
      if current_batch_size == prep_node_batch_size:
        qr_ssh_utils.WaitForNodeBatchCompletion(
            prep_nodes_threads, prepped_nodes
        )
        current_batch_size = 0
        prep_nodes_threads = []

    if current_batch_size > 0:
      qr_ssh_utils.WaitForNodeBatchCompletion(prep_nodes_threads, prepped_nodes)

    # Filter out Nones
    prepped_nodes = [
        prepped_node
        for prepped_node in prepped_nodes
        if prepped_node is not None
    ]
    if len(prepped_nodes) < num_nodes:
      log.warning(
          'Could not prepare all {} nodes, attempting to ssh into the'
          ' rest.'.format(num_nodes)
      )

    ssh_batch_size = tpu_ssh_utils.ParseBatchSize(
        args.batch_size, self.DEFAULT_BATCH_SIZE
    )
    tpu_ssh_utils.SSHIntoPreppedNodes(
        prepped_nodes,
        args,
        ssh_batch_size,
    )

    log.status.Print(
        'Completed execution in %s seconds' % (time.time() - start_time)
    )


Ssh.detailed_help = {
    'brief': "SSH into a Cloud TPU Queued Resource's node(s).",
    'EXAMPLES': """
        To run an SSH command in a Cloud TPU Queued Resource's first node and
        first worker (for example, to print the time since last boot), run:

            $ {command} my-qr --command="last boot"

        To run the same command in all nodes and workers in a Cloud TPU Queued
        Resource (with the default batch size), run:

            $ {command} my-qr --command="last boot" --worker=all --node=all

        To run the same command in all nodes and workers in a Cloud TPU Queued
        Resource but batching the request in groups of 4, run:

            $ {command} my-qr --command="last boot" --worker=all --node=all --batch-size=4
        """,
}
