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

import argparse
import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import exceptions as command_exceptions
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.command_lib.app import iap_tunnel
from googlecloudsdk.command_lib.app import ssh_common
from googlecloudsdk.command_lib.util.ssh import containers
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _ArgsCommon(parser):
  parser.add_argument(
      'instance',
      help='The instance ID.')
  parser.add_argument(
      '--container',
      help='Name of the container within the VM to connect to.')
  parser.add_argument(
      'command',
      nargs=argparse.REMAINDER,
      help='Remote command to execute on the VM.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SshGa(base.Command):
  """SSH into the VM of an App Engine Flexible instance."""

  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""\
        *{command}* lets you remotely log in to your running App Engine Flexible
        instances under two conditions:
        * The instance is running.
        * The instance has an external IP address. To check from the Cloud
        Console, go to the Instances page and confirm that there is an IP
        address listed in the VM IP column. To check from your app.yaml, open
        your app.yaml and look at the network settings. The *instance_ip_mode*
        field must be either not listed or set to ``external''.""") +
          ssh_common.DETAILED_HELP,
      'EXAMPLES':
          """\
          To SSH into an App Engine Flexible instance, run:

              $ {command} --service=s1 --version=v1 i1

          To SSH into the app container within an instance, run:

              $ {command} --service=s1 --version=v1 i1 --container=gaeapp

          To SSH into the app container and run a remote command, run:

              $ {command} --service=s1 --version=v1 i1 --container=gaeapp -- echo hello
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddServiceVersionSelectArgs(parser)
    _ArgsCommon(parser)
    iap_tunnel.AddSshTunnelArgs(parser)

  def Run(self, args):
    """Connect to a running App Engine flexible instance.

    Args:
      args: argparse.Namespace, the args the command was invoked with.

    Raises:
      InvalidInstanceTypeError: The instance is not supported for SSH.
      MissingVersionError: The version specified does not exist.
      MissingInstanceError: The instance specified does not exist.
      UnattendedPromptError: Not running in a tty.
      OperationCancelledError: User cancelled the operation.
      ssh.CommandError: The SSH command exited with SSH exit code, which
        usually implies that a connection problem occurred.

    Returns:
      int, The exit code of the SSH command.
    """
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())

    try:
      res = resources.REGISTRY.Parse(
          args.instance,
          collection='appengine.apps.services.versions.instances')
      service = res.servicesId
      version = res.versionsId
      instance = res.instancesId
    except resources.RequiredFieldOmittedException:
      service = args.service
      version = args.version
      instance = args.instance

    env = ssh.Environment.Current()
    env.RequireSSH()
    keys = ssh.Keys.FromFilename()
    keys.EnsureKeysExist(overwrite=False)
    connection_details = ssh_common.PopulatePublicKey(api_client, service,
                                                      version, instance,
                                                      keys.GetPublicKey(),
                                                      self.ReleaseTrack())
    remote_command = containers.GetRemoteCommand(args.container, args.command)
    tty = containers.GetTty(args.container, args.command)

    try:
      version_resource = api_client.GetVersionResource(service, version)
    except apitools_exceptions.HttpNotFoundError:
      raise command_exceptions.MissingVersionError('{}/{}'.format(
          service, version))

    project = properties.VALUES.core.project.GetOrFail()
    res = resources.REGISTRY.Parse(
        instance,
        params={
            'appsId': project,
            'versionsId': version,
            'instancesId': instance,
            'servicesId': service,
        },
        collection='appengine.apps.services.versions.instances',
    )
    try:
      instance_resource = api_client.GetInstanceResource(res)
    except apitools_exceptions.HttpNotFoundError:
      raise command_exceptions.MissingInstanceError(res.RelativeName())
    iap_tunnel_args = iap_tunnel.CreateSshTunnelArgs(
        args,
        api_client,
        self.ReleaseTrack(),
        project,
        version_resource,
        instance_resource,
    )
    try:
      filtered_firewall_rules = ssh_common.FilterFirewallRules(
          ssh_common.FetchFirewallRules()
      )
      if not filtered_firewall_rules:
        log.warning(
            'No ingress firewall rule that allows ingress to port 22. '
            'User should add a firewall rule that allows ingress to port 22.'
        )
    except apitools_exceptions.NotFoundError:
      raise log.exception('Unable to fetch firewall rules')
    return ssh.SSHCommand(
        connection_details.remote,
        identity_file=keys.key_file,
        tty=tty,
        remote_command=remote_command,
        options=connection_details.options,
        iap_tunnel_args=iap_tunnel_args).Run(env)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SshBeta(SshGa):
  """SSH into the VM of an App Engine Flexible instance."""

  @staticmethod
  def Args(parser):
    flags.AddServiceVersionSelectArgs(parser, short_flags=True)
    _ArgsCommon(parser)
    iap_tunnel.AddSshTunnelArgs(parser)

  def Run(self, args):
    """Connect to a running App Engine flexible instance.

    Args:
      args: argparse.Namespace, the args the command was invoked with.

    Raises:
      InvalidInstanceTypeError: The instance is not supported for SSH.
      MissingVersionError: The version specified does not exist.
      MissingInstanceError: The instance specified does not exist.
      UnattendedPromptError: Not running in a tty.
      OperationCancelledError: User cancelled the operation.
      ssh.CommandError: The SSH command exited with SSH exit code, which
        usually implies that a connection problem occurred.

    Returns:
      int, The exit code of the SSH command.
    """
    log.warning(
        'For `gcloud beta app instances ssh`, the short flags `-s` and `-v` '
        'are deprecated and will be removed 2017-09-27. For the GA command, '
        'they are not available. Please use `--service` and `--version` '
        'instead.')
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())

    try:
      res = resources.REGISTRY.Parse(
          args.instance,
          collection='appengine.apps.services.versions.instances')
      service = res.servicesId
      version = res.versionsId
      instance = res.instancesId
    except resources.RequiredFieldOmittedException:
      service = args.service
      version = args.version
      instance = args.instance

    env = ssh.Environment.Current()
    env.RequireSSH()
    keys = ssh.Keys.FromFilename()
    keys.EnsureKeysExist(overwrite=False)
    connection_details = ssh_common.PopulatePublicKey(api_client, service,
                                                      version, instance,
                                                      keys.GetPublicKey(),
                                                      self.ReleaseTrack())
    remote_command = containers.GetRemoteCommand(args.container, args.command)
    tty = containers.GetTty(args.container, args.command)

    try:
      version_resource = api_client.GetVersionResource(service, version)
    except apitools_exceptions.HttpNotFoundError:
      raise command_exceptions.MissingVersionError('{}/{}'.format(
          service, version))

    project = properties.VALUES.core.project.GetOrFail()
    res = resources.REGISTRY.Parse(
        instance,
        params={
            'appsId': project,
            'versionsId': version,
            'instancesId': instance,
            'servicesId': service,
        },
        collection='appengine.apps.services.versions.instances')
    try:
      instance_resource = api_client.GetInstanceResource(res)
    except apitools_exceptions.HttpNotFoundError:
      raise command_exceptions.MissingInstanceError(res.RelativeName())
    iap_tunnel_args = iap_tunnel.CreateSshTunnelArgs(args, api_client,
                                                     self.ReleaseTrack(),
                                                     project, version_resource,
                                                     instance_resource)
    return ssh.SSHCommand(
        connection_details.remote,
        identity_file=keys.key_file,
        tty=tty,
        remote_command=remote_command,
        options=connection_details.options,
        iap_tunnel_args=iap_tunnel_args).Run(env)
