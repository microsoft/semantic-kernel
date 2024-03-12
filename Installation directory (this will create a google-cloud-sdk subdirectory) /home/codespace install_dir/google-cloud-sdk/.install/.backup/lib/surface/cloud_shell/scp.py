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
"""cloud-shell scp command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloud_shell import util
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log
import six

FILE_TYPE = arg_parsers.RegexpValidator(
    r'^(cloudshell|localhost):.*$', 'must start with cloudshell: or localhost:')


def ToFileReference(path, remote):
  if path.startswith('cloudshell:'):
    return ssh.FileReference.FromPath(
        path.replace('cloudshell', six.text_type(remote), 1))
  elif path.startswith('localhost:'):
    return ssh.FileReference.FromPath(path.replace('localhost:', '', 1))
  else:
    raise Exception('invalid path: ' + path)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Scp(base.Command):
  """Copies files between Cloud Shell and the local machine."""

  detailed_help = {
      'DESCRIPTION':
          """\
        *{command}* copies files between your Cloud Shell instance and your
        local machine using the scp command.
        """,
      'EXAMPLES':
          """\
        To denote a file in Cloud Shell, prefix the file name with the string
        "cloudshell:" (e.g. _cloudshell:_~/_FILE_). To denote a local file,
        prefix the file name with the string "localhost:" (e.g.
        _localhost:_~/_FILE_). For example, to copy a remote directory to your
        local machine, run:

            $ {command} cloudshell:~/REMOTE-DIR localhost:~/LOCAL-DIR

        In the above example, *_~/REMOTE-DIR_* from your Cloud Shell instance is
        copied into the ~/_LOCAL-DIR_ directory.

        Conversely, files from your local computer can be copied into Cloud
        Shell:

            $ {command} localhost:~/LOCAL-FILE-1 localhost:~/LOCAL-FILE-2 \
cloudshell:~/REMOTE-DIR

        Under the covers, *scp(1)* or pscp (on Windows) is used to facilitate
        the transfer.
        """,
  }

  @staticmethod
  def Args(parser):
    util.ParseCommonArgs(parser)
    parser.add_argument(
        'sources',
        help='Specifies the files to copy.',
        type=FILE_TYPE,
        metavar='(cloudshell|localhost):SRC',
        nargs='+')
    parser.add_argument(
        'destination',
        help='Specifies a destination for the source files.',
        type=FILE_TYPE,
        metavar='(cloudshell|localhost):DEST')
    parser.add_argument(
        '--dry-run',
        help="""\
        If provided, prints the command that would be run to standard out
        instead of executing it.
        """,
        action='store_true')
    parser.add_argument(
        '--recurse',
        help='Upload directories recursively.',
        action='store_true')
    parser.add_argument(
        '--scp-flag',
        help='Extra flag to be sent to scp. This flag may be repeated.',
        action='append')

  def Run(self, args):
    connection_info = util.PrepareEnvironment(args)
    remote = ssh.Remote(host=connection_info.host, user=connection_info.user)
    command = ssh.SCPCommand(
        sources=[ToFileReference(src, remote) for src in args.sources],
        destination=ToFileReference(args.destination, remote),
        recursive=args.recurse,
        compress=False,
        port=str(connection_info.port),
        identity_file=connection_info.key,
        extra_flags=args.scp_flag,
        options={'StrictHostKeyChecking': 'no'},
    )

    if args.dry_run:
      log.Print(' '.join(command.Build(connection_info.ssh_env)))
    else:
      command.Run(connection_info.ssh_env)
