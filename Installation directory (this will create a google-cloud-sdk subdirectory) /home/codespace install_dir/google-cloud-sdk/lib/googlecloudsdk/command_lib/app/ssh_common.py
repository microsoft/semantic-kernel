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

"""Utilities for `app instances *` commands using SSH."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.compute import base_classes as compute_base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import exceptions as command_exceptions
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


_ENABLE_DEBUG_WARNING = """\
This instance is serving live application traffic.  Any changes made could
result in downtime or unintended consequences."""

# Used by OpenSSH for naming a logical host in the known_hosts file, rather than
# relying on IP or DNS. Flexible instance IDs are unique per project.
_HOST_KEY_ALIAS = 'gae.{project}.{instance_id}'

DETAILED_HELP = """

*{command}* resolves the instance's IP address and pre-populates the
VM with a public key managed by gcloud. If the gcloud managed key pair
does not exist, it is generated the first time an SSH command is run,
which may prompt you for a passphrase for the private key encryption.

All SSH commands require the OpenSSH client suite to be installed on
Linux and Mac OS X. On Windows, the Google Cloud CLI comes with a bundled
PuTTY suite instead, so it has no external dependencies."""


class ConnectionDetails(object):
  """Details about an SSH connection, for assembling an SSH command."""

  def __init__(self, remote, options):
    self.remote = remote
    self.options = options

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__dict__ == other.__dict__
    return False

  def __ne__(self, other):
    return not self.__eq__(other)

  def __repr__(self):
    return 'ConnectionDetails(**{})'.format(self.__dict__)


def _GetComputeProject(release_track):
  holder = compute_base_classes.ComputeApiHolder(release_track)
  client = holder.client

  project_ref = projects_util.ParseProject(
      properties.VALUES.core.project.GetOrFail())

  return client.MakeRequests([(client.apitools_client.projects, 'Get',
                               client.messages.ComputeProjectsGetRequest(
                                   project=project_ref.projectId))])[0]


def _ContainsPort22(allowed_ports):
  """Checks if the given list of allowed ports contains port 22.

  Args:
    allowed_ports:

  Returns:

  Raises:
    ValueError:Port value must be of type string.
  """

  for port in allowed_ports:
    try:
      if not isinstance(port, str):
        raise ValueError('Port value must be of type string')
    except ValueError as e:
      print(e)
    if port == '22':
      return True
    if '-' in port:
      start = int(port.split('-')[0])
      end = int(port.split('-')[1])
      if start <= 22 <= end:
        return True
  return False


def PopulatePublicKey(api_client, service_id, version_id, instance_id,
                      public_key, release_track):
  """Enable debug mode on and send SSH keys to a flex instance.

  Common method for SSH-like commands, does the following:
  - Makes sure that the service/version/instance specified exists and is of the
    right type (Flexible).
  - If not already done, prompts and enables debug on the instance.
  - Populates the public key onto the instance.

  Args:
    api_client: An appengine_api_client.AppEngineApiClient.
    service_id: str, The service ID.
    version_id: str, The version ID.
    instance_id: str, The instance ID.
    public_key: ssh.Keys.PublicKey, Public key to send.
    release_track: calliope.base.ReleaseTrack, The current release track.

  Raises:
    InvalidInstanceTypeError: The instance is not supported for SSH.
    MissingVersionError: The version specified does not exist.
    MissingInstanceError: The instance specified does not exist.
    UnattendedPromptError: Not running in a tty.
    OperationCancelledError: User cancelled the operation.

  Returns:
    ConnectionDetails, the details to use for SSH/SCP for the SSH
    connection.
  """
  try:
    version = api_client.GetVersionResource(
        service=service_id, version=version_id)
  except apitools_exceptions.HttpNotFoundError:
    raise command_exceptions.MissingVersionError(
        '{}/{}'.format(service_id, version_id))
  version = version_util.Version.FromVersionResource(version, None)
  if version.environment is not env.FLEX:
    if version.environment is env.MANAGED_VMS:
      environment = 'Managed VMs'
      msg = 'Use `gcloud compute ssh` for Managed VMs instances.'
    else:
      environment = 'Standard'
      msg = None
    raise command_exceptions.InvalidInstanceTypeError(environment, msg)
  res = resources.REGISTRY.Parse(
      instance_id,
      params={
          'appsId': properties.VALUES.core.project.GetOrFail,
          'versionsId': version_id,
          'instancesId': instance_id,
          'servicesId': service_id,
      },
      collection='appengine.apps.services.versions.instances')
  rel_name = res.RelativeName()
  try:
    instance = api_client.GetInstanceResource(res)
  except apitools_exceptions.HttpNotFoundError:
    raise command_exceptions.MissingInstanceError(rel_name)

  if not instance.vmDebugEnabled:
    log.warning(_ENABLE_DEBUG_WARNING)
    console_io.PromptContinue(cancel_on_no=True, throw_if_unattended=True)
  user = ssh.GetDefaultSshUsername()
  project = _GetComputeProject(release_track)
  oslogin_state = ssh.GetOsloginState(
      None,
      project,
      user,
      public_key.ToEntry(),
      None,
      release_track,
      messages=compute_base_classes.ComputeApiHolder(
          release_track).client.messages)
  user = oslogin_state.user
  instance_ip_mode_enum = (
      api_client.messages.Network.InstanceIpModeValueValuesEnum)
  host = (
      instance.id if
      version.version.network.instanceIpMode is instance_ip_mode_enum.INTERNAL
      else instance.vmIp)
  remote = ssh.Remote(host=host, user=user)
  if not oslogin_state.oslogin_enabled:
    ssh_key = '{user}:{key} {user}'.format(user=user, key=public_key.ToEntry())
    log.status.Print('Sending public key to instance [{}].'.format(rel_name))
    api_client.DebugInstance(res, ssh_key)
  options = {
      'IdentitiesOnly': 'yes',  # No ssh-agent as of yet
      'UserKnownHostsFile': ssh.KnownHosts.DEFAULT_PATH,
      'CheckHostIP': 'no',
      'HostKeyAlias': _HOST_KEY_ALIAS.format(project=api_client.project,
                                             instance_id=instance_id)}
  return ConnectionDetails(remote, options)


def FetchFirewallRules():
  """Fetches the firewall rules for the current project.

  Returns:
    A list of firewall rules.
  """
  holder = compute_base_classes.ComputeApiHolder(base.ReleaseTrack.GA)
  client = holder.client
  # pylint: disable=protected-access
  request_data = lister._Frontend(
      None,
      None,
      lister.GlobalScope([
          holder.resources.Parse(
              properties.VALUES.core.project.GetOrFail(),
              collection='compute.projects',
          )
      ]),
  )
  list_implementation = lister.GlobalLister(
      client, client.apitools_client.firewalls
  )
  result = lister.Invoke(request_data, list_implementation)
  return result


def FilterFirewallRules(firewall_rules):
  """Filters firewall rules that allow ingress to port 22."""
  filtered_firewall_rules = []
  for firewall_rule in firewall_rules:
    if firewall_rule.get('direction') == 'INGRESS':
      allowed_dict = firewall_rule.get('allowed')
      if not allowed_dict:
        continue
      allowed_ports = allowed_dict[0].get('ports')
      if not allowed_ports:
        continue
      if _ContainsPort22(allowed_ports):
        filtered_firewall_rules.append(firewall_rule)
  return filtered_firewall_rules
