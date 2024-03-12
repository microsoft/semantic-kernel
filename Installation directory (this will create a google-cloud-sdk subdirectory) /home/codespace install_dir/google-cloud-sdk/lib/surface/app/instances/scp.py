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

"""The `app instances ssh` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import exceptions as command_exceptions
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.command_lib.app import iap_tunnel
from googlecloudsdk.command_lib.app import ssh_common
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ScpGa(base.Command):
  """SCP from or to the VM of an App Engine Flexible instance."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
        *{command}* lets you remotely copy files to or from an App Engine
        Flexible instance.""") + ssh_common.DETAILED_HELP,
      'EXAMPLES': """\
          To copy one file from a remote instance to the local machine, run:

              $ {command} --service=s1 --version=v1 i1:remote_file local_file

          To copy several local files to a remote instance, run:

              $ {command} --service=s1 --version=v1 local_1 local_1 i1:remote_dir

          To use recursive copy, run:

              $ {command} --service=s1 --version=v1 --recurse local_dir i1:remote_dir
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddServiceVersionSelectArgs(parser)
    iap_tunnel.AddSshTunnelArgs(parser)

    parser.add_argument(
        '--recurse',
        action='store_true',
        help='Upload directories recursively.')

    parser.add_argument(
        '--compress',
        action='store_true',
        help='Enable compression.')

    parser.add_argument(
        'sources',
        help='Specifies the files to copy.',
        metavar='[INSTANCE:]SRC',
        nargs='+')

    parser.add_argument(
        'destination',
        help='Specifies a destination for the source files.',
        metavar='[INSTANCE:]DEST')

  def Run(self, args):
    """Securily copy files from/to a running flex instance.

    Args:
      args: argparse.Namespace, the args the command was invoked with.

    Raises:
      InvalidInstanceTypeError: The instance is not supported for SSH.
      MissingVersionError: The version specified does not exist.
      MissingInstanceError: The instance specified does not exist.
      UnattendedPromptError: Not running in a tty.
      OperationCancelledError: User cancelled the operation.
      ssh.CommandError: The SCP command exited with SCP exit code, which
        usually implies that a connection problem occurred.

    Returns:
      int, The exit code of the SCP command.
    """
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    env = ssh.Environment.Current()
    env.RequireSSH()
    keys = ssh.Keys.FromFilename()
    keys.EnsureKeysExist(overwrite=False)

    # Make sure we have a unique remote
    dst = ssh.FileReference.FromPath(args.destination)
    srcs = [ssh.FileReference.FromPath(source) for source in args.sources]
    ssh.SCPCommand.Verify(srcs, dst, single_remote=True)

    remote = dst.remote or srcs[0].remote
    instance = remote.host
    if not dst.remote:  # Make sure all remotes point to the same ref
      for src in srcs:
        src.remote = remote

    connection_details = ssh_common.PopulatePublicKey(
        api_client, args.service, args.version, remote.host,
        keys.GetPublicKey(), self.ReleaseTrack())

    # Update all remote references
    remote.host = connection_details.remote.host
    remote.user = connection_details.remote.user

    try:
      version_resource = api_client.GetVersionResource(args.service,
                                                       args.version)
    except apitools_exceptions.HttpNotFoundError:
      raise command_exceptions.MissingVersionError('{}/{}'.format(
          args.service, args.version))

    project = properties.VALUES.core.project.GetOrFail()
    res = resources.REGISTRY.Parse(
        instance,
        params={
            'appsId': project,
            'versionsId': args.version,
            'instancesId': instance,
            'servicesId': args.service,
        },
        collection='appengine.apps.services.versions.instances')
    instance_name = res.RelativeName()
    try:
      instance_resource = api_client.GetInstanceResource(res)
    except apitools_exceptions.HttpNotFoundError:
      raise command_exceptions.MissingInstanceError(instance_name)
    iap_tunnel_args = iap_tunnel.CreateSshTunnelArgs(
        args=args,
        api_client=api_client,
        track=self.ReleaseTrack(),
        project=project,
        version=version_resource,
        instance=instance_resource)

    return ssh.SCPCommand(
        srcs,
        dst,
        identity_file=keys.key_file,
        compress=args.compress,
        recursive=args.recurse,
        options=connection_details.options,
        iap_tunnel_args=iap_tunnel_args).Run(env)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ScpBeta(base.Command):
  """SCP from or to the VM of an App Engine Flexible environment instance."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
        *{command}* lets you remotely copy files to or from an App Engine
        Flexible environment instance.""") + ssh_common.DETAILED_HELP,
      'EXAMPLES': """\
          To copy one file from a remote instance to the local machine, run:

              $ {command} --service=s1 --version=v1 i1:remote_file local_file

          To copy several local files to a remote instance, run:

              $ {command} --service=s1 --version=v1 local_1 local_1 i1:remote_dir

          To use recursive copy, run:

              $ {command} --service=s1 --version=v1 --recurse local_dir i1:remote_dir
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddServiceVersionSelectArgs(parser)
    iap_tunnel.AddSshTunnelArgs(parser)

    parser.add_argument(
        '--recurse',
        action='store_true',
        help='Upload directories recursively.')

    parser.add_argument(
        '--compress',
        action='store_true',
        help='Enable compression.')

    parser.add_argument(
        'sources',
        help='Specifies the files to copy.',
        metavar='[INSTANCE:]SRC',
        nargs='+')

    parser.add_argument(
        'destination',
        help='Specifies a destination for the source files.',
        metavar='[INSTANCE:]DEST')

  def Run(self, args):
    """Securily copy files from/to a running flex instance.

    Args:
      args: argparse.Namespace, the args the command was invoked with.

    Raises:
      InvalidInstanceTypeError: The instance is not supported for SSH.
      MissingVersionError: The version specified does not exist.
      MissingInstanceError: The instance specified does not exist.
      UnattendedPromptError: Not running in a tty.
      OperationCancelledError: User cancelled the operation.
      ssh.CommandError: The SCP command exited with SCP exit code, which
        usually implies that a connection problem occurred.

    Returns:
      int, The exit code of the SCP command.
    """
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    env = ssh.Environment.Current()
    env.RequireSSH()
    keys = ssh.Keys.FromFilename()
    keys.EnsureKeysExist(overwrite=False)

    # Make sure we have a unique remote
    dst = ssh.FileReference.FromPath(args.destination)
    srcs = [ssh.FileReference.FromPath(source) for source in args.sources]
    ssh.SCPCommand.Verify(srcs, dst, single_remote=True)

    remote = dst.remote or srcs[0].remote
    instance = remote.host
    if not dst.remote:  # Make sure all remotes point to the same ref
      for src in srcs:
        src.remote = remote

    connection_details = ssh_common.PopulatePublicKey(
        api_client, args.service, args.version, remote.host,
        keys.GetPublicKey(), self.ReleaseTrack())

    # Update all remote references
    remote.host = connection_details.remote.host
    remote.user = connection_details.remote.user

    try:
      version_resource = api_client.GetVersionResource(args.service,
                                                       args.version)
    except apitools_exceptions.HttpNotFoundError:
      raise command_exceptions.MissingVersionError('{}/{}'.format(
          args.service, args.version))

    project = properties.VALUES.core.project.GetOrFail()
    res = resources.REGISTRY.Parse(
        instance,
        params={
            'appsId': project,
            'versionsId': args.version,
            'instancesId': instance,
            'servicesId': args.service,
        },
        collection='appengine.apps.services.versions.instances')
    instance_name = res.RelativeName()
    try:
      instance_resource = api_client.GetInstanceResource(res)
    except apitools_exceptions.HttpNotFoundError:
      raise command_exceptions.MissingInstanceError(instance_name)
    iap_tunnel_args = iap_tunnel.CreateSshTunnelArgs(args, api_client,
                                                     self.ReleaseTrack(),
                                                     project, version_resource,
                                                     instance_resource)

    cmd = ssh.SCPCommand(
        srcs,
        dst,
        identity_file=keys.key_file,
        compress=args.compress,
        recursive=args.recurse,
        options=connection_details.options,
        iap_tunnel_args=iap_tunnel_args)
    return cmd.Run(env)

