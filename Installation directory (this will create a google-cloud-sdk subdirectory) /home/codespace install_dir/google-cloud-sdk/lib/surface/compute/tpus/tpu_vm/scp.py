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
"""Command to SCP to/from a Cloud TPU VM Node."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from argcomplete.completers import FilesCompleter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import ssh as tpu_ssh_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import properties


def AddSCPArgs(parser):
  """Additional flags and positional args to be passed to *scp(1)*."""
  parser.add_argument(
      '--scp-flag',
      action='append',
      help="""\
      Additional flags to be passed to *scp(1)*. This flag may be repeated.
      """)

  parser.add_argument(
      'sources',
      completer=FilesCompleter,
      help='Specifies the files to copy.',
      metavar='[[USER@]INSTANCE:]SRC',
      nargs='+')

  parser.add_argument(
      'destination',
      help='Specifies a destination for the source files.',
      metavar='[[USER@]INSTANCE:]DEST')

  parser.add_argument(
      '--recurse', action='store_true', help='Upload directories recursively.')

  parser.add_argument(
      '--compress', action='store_true', help='Enable compression.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Scp(base.Command):
  """Copy files to and from a Cloud TPU VM via SCP."""

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
    tpu_ssh_utils.AddTPUSSHArgs(parser, cls._ENABLE_IAP, cls._ENABLE_BATCHING)
    AddSCPArgs(parser)
    flags.AddZoneFlag(parser, resource_type='tpu', operation_type='scp')

  def Run(self, args):
    dst = ssh.FileReference.FromPath(args.destination)
    srcs = [ssh.FileReference.FromPath(src) for src in args.sources]
    ssh.SCPCommand.Verify(srcs, dst, single_remote=True)

    remote = dst.remote or srcs[0].remote
    tpu_name = remote.host
    if not dst.remote:  # Make sure all remotes point to the same ref.
      for src in srcs:
        src.remote = remote

    username_requested = True
    if not remote.user:
      username_requested = False
      remote.user = ssh.GetDefaultSshUsername(warn_on_account_user=True)

    # If zone is not set, retrieve the one from the config.
    if args.zone is None:
      args.zone = properties.VALUES.compute.zone.Get(required=True)

    prepped_node = [None]
    tpu_ssh_utils.PrepareNodeForSCP(
        tpu_name,
        args,
        self.ReleaseTrack(),
        self._ENABLE_BATCHING,
        username_requested,
        prepped_node,
        0,
        srcs,
        dst,
        remote,
    )

    scp_batch_size = 1
    if self._ENABLE_BATCHING and prepped_node[0]:
      scp_batch_size = tpu_ssh_utils.ParseBatchSize(
          args.batch_size, len(prepped_node[0].worker_ips)
      )

    tpu_ssh_utils.SCPIntoPreppedNodes(prepped_node, args, scp_batch_size)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ScpAlpha(Scp):
  """Copy files to and from a Cloud TPU VM via SCP (Alpha)."""
  _ENABLE_IAP = True
  _ENABLE_BATCHING = True


Scp.detailed_help = {
    'brief':
        'Copy files to and from a Cloud TPU VM via SCP.',
    'EXAMPLES':
        """
        To copy a file (for example, a text file in the local home directory) to
        a Cloud TPU VM, run:

            $ {command} ~/my-file my-tpu:

        To copy a file into all workers in a Cloud TPU VM, run:

            $ {command} ~/my-file my-tpu: --worker=all

        To copy a file from a Cloud TPU VM to the home directory of the local
        computer, run:

            $ {command} my-tpu:~/my-file ~/

        To copy all files in a folder to a Cloud TPU VM, run:

            $ {command} ~/my-folder/ my-tpu: --recurse
        """
}
