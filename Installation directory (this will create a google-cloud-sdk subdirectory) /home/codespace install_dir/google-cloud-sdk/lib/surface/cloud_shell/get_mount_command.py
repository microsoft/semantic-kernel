# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""cloud-shell get-mount-command command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from argcomplete.completers import FilesCompleter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloud_shell import util
from googlecloudsdk.core import log
from googlecloudsdk.core.util import platforms


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class GetMountCommand(base.Command):
  """Prints a command to mount the Cloud Shell home directory via sshfs."""

  detailed_help = {
      'DESCRIPTION':
          """\
        *{command}* starts your Cloud Shell if it is not already running, then
        prints out a command that allows you to mount the Cloud Shell home
        directory onto your local file system using *sshfs*. You must install
        and run sshfs yourself.

        After mounting the Cloud Shell home directory, any changes you make
        under the mount point on your local file system will be reflected in
        Cloud Shell and vice-versa.
        """,
      'EXAMPLES':
          """\
        To print a command that mounts a remote directory onto your local file
        system, run:

            $ {command} REMOTE-DIR
        """,
  }

  @staticmethod
  def Args(parser):
    util.ParseCommonArgs(parser)
    parser.add_argument(
        'mount_dir',
        completer=FilesCompleter,
        help="""\
        Local directory onto which the Cloud Shell home directory should be
        mounted.
        """)

  def Run(self, args):
    if platforms.OperatingSystem.IsWindows():
      raise util.UnsupportedPlatform(
          'get-mount-command is not currently supported on Windows')
    else:
      connection_info = util.PrepareEnvironment(args)
      log.Print('sshfs {user}@{host}: {mount_dir} -p {port} '
                '-oIdentityFile={key_file} -oStrictHostKeyChecking=no'.format(
                    user=connection_info.user,
                    host=connection_info.host,
                    mount_dir=args.mount_dir,
                    port=connection_info.port,
                    key_file=connection_info.key,
                ))
