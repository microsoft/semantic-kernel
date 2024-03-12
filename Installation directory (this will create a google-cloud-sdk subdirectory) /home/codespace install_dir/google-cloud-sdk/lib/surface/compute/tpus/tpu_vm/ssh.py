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
"""Command to SSH into a Cloud TPU VM Node."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import os.path

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import ssh as tpu_ssh_utils
from googlecloudsdk.core import properties


def AddCommandArgGroup(parser):
  """Argument group for running commands using SSH."""
  command_group = parser.add_argument_group(
      help='These arguments are used to run commands using SSH.')
  command_group.add_argument(
      '--command',
      help="""\
      Command to run on the Cloud TPU VM.

      Runs the command on the target Cloud TPU VM and then exits.

      Note: in the case of a TPU Pod, it will only run the command in the
      workers specified with the `--worker` flag (defaults to worker 0 if not
      set).
      """)
  command_group.add_argument(
      '--output-directory',
      help="""\
      Path to the directory to output the logs of the commands.

      The path can be relative or absolute. The directory must already exist.

      If not specified, standard output will be used.

      The logs will be written in files named {WORKER_ID}.log. For example:
      "2.log".
      """)


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
      """)

  parser.add_argument(
      'user_tpu',
      completer=completers.InstancesCompleter,
      metavar='[USER@]TPU',
      help="""\
      Specifies the Cloud TPU VM to SSH into.

      ``USER'' specifies the username with which to SSH. If omitted, the user
      login name is used.

      ``TPU'' specifies the name of the Cloud TPU VM to SSH into.
      """)

  parser.add_argument(
      'ssh_args',
      nargs=argparse.REMAINDER,
      help="""\
          Flags and positionals passed to the underlying ssh implementation.
          """,
      example="""\
        $ {command} example-instance --zone=us-central1-a -- -vvv -L 80:%TPU%:80
      """)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Ssh(base.Command):
  """SSH into a Cloud TPU VM."""

  # IAP and Batching are not available for GA.
  _ENABLE_IAP = False
  _ENABLE_BATCHING = False

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    ssh_utils.BaseSSHCLIHelper.Args(parser)
    AddSSHArgs(parser)
    tpu_ssh_utils.AddTPUSSHArgs(parser, enable_iap=cls._ENABLE_IAP,
                                enable_batching=cls._ENABLE_BATCHING)
    AddCommandArgGroup(parser)
    flags.AddZoneFlag(parser, resource_type='tpu', operation_type='ssh')

  def Run(self, args):
    user, tpu_name = ssh_utils.GetUserAndInstance(args.user_tpu)

    # If zone is not set, retrieve the one from the config.
    if args.zone is None:
      args.zone = properties.VALUES.compute.zone.Get(required=True)
    # Validate the output path.
    if args.output_directory:
      if not args.command:
        raise exceptions.InvalidArgumentException(
            '--output_directory', 'cannot be specified without the `--command` '
            'flag. Please specify the `--command` flag or remove the '
            '--output-directory flag.')
      output_directory_path = os.path.abspath(
          os.path.expandvars(os.path.expanduser(args.output_directory)))
      if not os.path.isdir(output_directory_path):
        raise exceptions.InvalidArgumentException(
            '--output_directory', 'Failed to find directory {}. Please create '
            'it or specify another directory'.format(output_directory_path))

    username_requested = '@' in args.user_tpu
    prepped_node = [None]
    tpu_ssh_utils.PrepareNodeForSSH(
        tpu_name,
        user,
        args,
        self.ReleaseTrack(),
        self._ENABLE_BATCHING,
        username_requested,
        prepped_node,
        0,
    )

    ssh_batch_size = 1
    if self._ENABLE_BATCHING and prepped_node[0]:
      ssh_batch_size = tpu_ssh_utils.ParseBatchSize(
          args.batch_size, len(prepped_node[0].worker_ips)
      )

    tpu_ssh_utils.SSHIntoPreppedNodes(
        prepped_node,
        args,
        ssh_batch_size,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SshAlpha(Ssh):
  """SSH into a Cloud TPU VM (Alpha)."""
  _ENABLE_IAP = True
  _ENABLE_BATCHING = True


Ssh.detailed_help = {
    'brief':
        'SSH into a Cloud TPU VM.',
    'EXAMPLES':
        """
        To SSH into a Cloud TPU VM, run:

            $ {command} my-tpu

        To SSH into worker 1 on a Cloud TPU VM Pod, run:

            $ {command} my-tpu --worker=1

        To run an SSH command in a Cloud TPU VM (for example, to print the
        time since last boot), run:

            $ {command} my-tpu --command="last boot"

        To run the same command in all workers in a Cloud TPU VM simultaneously,
        run:

            $ {command} my-tpu --command="last boot" --worker=all
        """
}
