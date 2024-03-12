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
"""Implements the command for copying files from and to virtual machines."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import iap_tunnel
from googlecloudsdk.command_lib.compute import scp_utils
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.util.ssh import ip


def _DetailedHelp():
  """Generate detailed help for each version."""
  detailed_help = {
      'brief': ('Copy files to and from Google Compute Engine '
                'virtual machines via scp.'),
      'DESCRIPTION':
          """
*{command}* securely copies files between a virtual machine instance and your
local machine using the scp command.

This command works for Linux VMs and Windows Server 2019 and later VMs that
have [SSH enabled](https://cloud.google.com/compute/docs/connect/windows-ssh).

In order to set up a successful transfer, follow these guidelines:
*   Prefix remote file names with the virtual machine instance
    name (e.g., _example-instance_:~/_FILE_).
*   Local file names can be used as is (e.g., ~/_FILE_).
*   File names containing a colon (``:'') must be invoked by either their
    absolute path or a path that begins with ``./''.
*   When the destination of your transfer is local, all source files must be
    from the same virtual machine.
*   When the destination of your transfer is remote instead, all sources must
    be local.

Under the covers, *scp(1)* is used to facilitate the transfer.

If the `--region` and `--network` flags are provided, then `--plain` and
`--tunnel-through-iap` are implied and any remote file names must be prefixed
with the remote IP address instead of the instance name. This is most useful for
connecting to on-prem resources.""",
      'EXAMPLES':
          """
To copy a remote directory, `~/narnia`, from ``example-instance'' to the
`~/wardrobe` directory of your local host, run:

  $ {command} --recurse example-instance:~/narnia ~/wardrobe

Conversely, files from your local computer can be copied to a virtual machine:

  $ {command} ~/localtest.txt ~/localtest2.txt example-instance:~/narnia

Remote Windows-based virtual machines require you to provide a path using
backslash notation:

  $ {command} ~/localtest.txt ~/localtest2.txt example-windows-instance:"C:\\Users\\Public"

Paths for remote Windows-based virtual machines which contain spaces in
directory name should be appropriately protected with a pair of nested single
and double quotes:

  $ {command} ~/localtest.txt 'example-windows-instance:"C:\\Users\\Public\\Test Folder"'

If the zone cannot be determined, you will be prompted for it.  Use the
`--zone` flag to avoid being prompted:

  $ {command} --recurse example-instance:~/narnia ~/wardrobe --zone=us-central1-a

To specify the project, zone, and recurse all together, run:

  $ {command} --project="my-gcp-project" --zone="us-east1-b" --recurse ~/foo-folder/ gcp-instance-name:~/

You can limit the allowed time to ssh. For example, to allow a key to be used
through 2019:

  $ {command} --recurse example-instance:~/narnia ~/wardrobe --ssh-key-expiration="2020-01-01T00:00:00:00Z"

Or alternatively, allow access for the next two minutes:

  $ {command} --recurse example-instance:~/narnia ~/wardrobe --ssh-key-expire-after=2m

To use the IP address of your remote VM (eg, for on-prem), you must also specify
the `--region` and `--network` flags:

  $ {command} 10.1.2.3:~/narnia ~/wardrobe --region=us-central1 --network=default
""",
  }

  return detailed_help


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Scp(base.Command):
  """Copy files to and from Google Compute Engine virtual machines via scp."""

  category = base.TOOLS_CATEGORY

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    scp_utils.BaseScpHelper.Args(parser)

    parser.add_argument('--port', help='The port to connect to.')

    parser.add_argument(
        '--recurse',
        action='store_true',
        help='Upload directories recursively.')

    parser.add_argument(
        '--compress', action='store_true', help='Enable compression.')

    parser.add_argument(
        '--scp-flag',
        action='append',
        help='Extra flag to be sent to scp. This flag may be repeated.')

    ssh_utils.AddVerifyInternalIpArg(parser)

    routing_group = parser.add_mutually_exclusive_group()
    routing_group.add_argument(
        '--internal-ip',
        default=False,
        action='store_true',
        help="""\
        Connect to instances using their internal IP addresses rather than their
        external IP addresses. Use this to connect from one instance to another
        on the same VPC network, over a VPN connection, or between two peered
        VPC networks.

        For this connection to work, you must configure your networks and
        firewall to allow SSH connections to the internal IP address of
        the instance to which you want to connect.

        To learn how to use this flag, see
        [](https://cloud.google.com/compute/docs/instances/connecting-advanced#sshbetweeninstances).
        """)

    iap_tunnel.AddSshTunnelArgs(parser, routing_group)
    iap_tunnel.AddHostBasedTunnelArgs(parser)

  def Run(self, args):
    """See scp_utils.BaseScpCommand.Run."""

    on_prem = (args.IsSpecified('network') and args.IsSpecified('region'))
    if on_prem:
      args.plain = True

    if args.internal_ip:
      ip_type = ip.IpTypeEnum.INTERNAL
    else:
      ip_type = ip.IpTypeEnum.EXTERNAL

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    scp_helper = scp_utils.BaseScpHelper()

    extra_flags = []

    # TODO(b/33467618): Add -C to SCPCommand
    if args.scp_flag:
      extra_flags.extend(args.scp_flag)
    return scp_helper.RunScp(
        holder,
        args,
        on_prem=on_prem,
        port=args.port,
        recursive=args.recurse,
        compress=args.compress,
        extra_flags=extra_flags,
        release_track=self.ReleaseTrack(),
        ip_type=ip_type)


Scp.detailed_help = _DetailedHelp()
