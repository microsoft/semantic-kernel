# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Utilities for subcommands that need to SSH into virtual machine guests.

This module provides the following things:
  Errors used by various SSH-based commands.
  Various helper functions.
  BaseSSHHelper: The primary purpose of the BaseSSHHelper class is to
      get the instance and project information, determine whether the user's
      SSH public key is in the metadata, determine if the SSH public key
      needs to be added to the instance/project metadata, and then add the
      key if necessary.
  BaseSSHCLIHelper: An additional wrapper around BaseSSHHelper that adds
      common flags needed by the various SSH-based commands.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import binascii
import collections
import datetime
import json
import os

from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import path_simplifier
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import times
from googlecloudsdk.core.util.files import FileReader
from googlecloudsdk.core.util.files import FileWriter
import six

# The maximum amount of time to wait for a newly-added SSH key to
# propagate before giving up.
SSH_KEY_PROPAGATION_TIMEOUT_MS = 60 * 1000

_TROUBLESHOOTING_URL = (
    'https://cloud.google.com/compute/docs/troubleshooting/troubleshooting-ssh')

GUEST_ATTRIBUTES_METADATA_KEY = 'enable-guest-attributes'
SUPPORTED_HOSTKEY_TYPES = ['ssh-rsa', 'ssh-ed25519', 'ecdsa-sha2-nistp256']


class UnallocatedIPAddressError(core_exceptions.Error):
  """An exception to be raised when a network interface's IP address is yet

     to be allocated.
  """


class MissingExternalIPAddressError(core_exceptions.Error):
  """An exception to be raised when a network interface does not have an

     external IP address.
  """


class MissingNetworkInterfaceError(core_exceptions.Error):
  """Network interface was not found."""


class CommandError(core_exceptions.Error):
  """Wraps ssh.CommandError, primarly for adding troubleshooting info."""

  def __init__(self, original_error, message=None):
    if message is None:
      message = 'See {url} for troubleshooting hints.'.format(
          url=_TROUBLESHOOTING_URL)

    super(CommandError, self).__init__(
        '{0}\n{1}'.format(original_error, message),
        exit_code=original_error.exit_code)


class ArgumentError(core_exceptions.Error):
  """Invalid combinations of, or malformed, arguments."""
  pass


class SetProjectMetadataError(core_exceptions.Error):
  pass


class SecurityKeysNotSupportedError(core_exceptions.Error):
  pass


class SecurityKeysNotPresentError(core_exceptions.Error):
  pass


class NetworkError(core_exceptions.Error):
  """Indicates that an SSH connection couldn't be established right now."""

  def __init__(self):
    super(NetworkError, self).__init__(
        'Could not SSH into the instance.  It is possible that your SSH key '
        'has not propagated to the instance yet. Try running this command '
        'again.  If you still cannot connect, verify that the firewall and '
        'instance are set to accept ssh traffic.')


def GetExternalInterface(instance_resource, no_raise=False):
  """Returns the network interface of the instance with an external IP address.

  Args:
    instance_resource: An instance resource object.
    no_raise: A boolean flag indicating whether or not to return None instead of
      raising.

  Raises:
    UnallocatedIPAddressError: If the instance_resource's external IP address
      has yet to be allocated.
    MissingExternalIPAddressError: If no external IP address is found for the
      instance_resource and no_raise is False.

  Returns:
    A network interface resource object or None if no_raise and a network
    interface with an external IP address does not exist.
  """
  no_ip = False
  if instance_resource.networkInterfaces:
    for network_interface in instance_resource.networkInterfaces:
      access_configs = network_interface.accessConfigs
      ipv6_access_configs = network_interface.ipv6AccessConfigs
      if access_configs:
        if access_configs[0].natIP:
          return network_interface
        elif not no_raise:
          no_ip = True
      if ipv6_access_configs:
        if ipv6_access_configs[0].externalIpv6:
          return network_interface
        elif not no_raise:
          no_ip = True
      if no_ip:
        raise UnallocatedIPAddressError(
            'Instance [{0}] in zone [{1}] has not been allocated an external '
            'IP address yet. Try rerunning this command later.'.format(
                instance_resource.name,
                path_simplifier.Name(instance_resource.zone)))

  if no_raise:
    return None

  raise MissingExternalIPAddressError(
      'Instance [{0}] in zone [{1}] does not have an external IP address, '
      'so you cannot SSH into it. To add an external IP address to the '
      'instance, use [gcloud compute instances add-access-config].'.format(
          instance_resource.name, path_simplifier.Name(instance_resource.zone)))


def GetExternalIPAddress(instance_resource, no_raise=False):
  """Returns the external IP address of the instance.

  Args:
    instance_resource: An instance resource object.
    no_raise: A boolean flag indicating whether or not to return None instead of
      raising.

  Raises:
    UnallocatedIPAddressError: If the instance_resource's external IP address
      has yet to be allocated.
    MissingExternalIPAddressError: If no external IP address is found for the
      instance_resource and no_raise is False.

  Returns:
    A string IPv4 address or IPv6 address if the IPv4 address does not exit
    or None if no_raise is True and no external IP exists.
  """
  network_interface = GetExternalInterface(instance_resource, no_raise=no_raise)
  if network_interface:
    if (hasattr(network_interface, 'accessConfigs')
        and network_interface.accessConfigs):
      return network_interface.accessConfigs[0].natIP
    elif (hasattr(network_interface, 'ipv6AccessConfigs')
          and network_interface.ipv6AccessConfigs):
      return network_interface.ipv6AccessConfigs[0].externalIpv6


def GetInternalInterface(instance_resource):
  """Returns the a network interface of the instance.

  Args:
    instance_resource: An instance resource object.

  Raises:
    MissingNetworkInterfaceError: If instance has no network interfaces.

  Returns:
    A network interface resource object.
  """
  if instance_resource.networkInterfaces:
    return instance_resource.networkInterfaces[0]
  raise MissingNetworkInterfaceError(
      'Instance [{0}] in zone [{1}] has no network interfaces.'.format(
          instance_resource.name,
          path_simplifier.Name(instance_resource.zone)))


def GetInternalIPAddress(instance_resource):
  """Returns the internal IP address of the instance.

  Args:
    instance_resource: An instance resource object.

  Raises:
    ToolException: If instance has no network interfaces.

  Returns:
    A string IPv4 address or IPv6 address if there is no IPv4 address.
  """
  interface = GetInternalInterface(instance_resource)
  return interface.networkIP or interface.ipv6Address


def GetSSHKeyExpirationFromArgs(args):
  """Converts flags to an ssh key expiration in datetime and micros."""
  if args.ssh_key_expiration:
    # this argument is checked in ParseFutureDatetime to be sure that it
    # is not already expired.  I.e. the expiration should be in the future.
    expiration = args.ssh_key_expiration
  elif args.ssh_key_expire_after:
    expiration = times.Now() + datetime.timedelta(
        seconds=args.ssh_key_expire_after)
  else:
    return None, None

  expiration_micros = times.GetTimeStampFromDateTime(expiration) * 1e6
  return expiration, int(expiration_micros)


def _GetSSHKeyListFromMetadataEntry(metadata_entry):
  """Returns a list of SSH keys (without whitespace) from a metadata entry."""
  keys = []
  for line in metadata_entry.split('\n'):
    line_strip = line.strip()
    if line_strip:
      keys.append(line_strip)
  return keys


def _GetSSHKeysFromMetadata(metadata):
  """Returns the ssh-keys and legacy sshKeys metadata values.

  This function will return all of the SSH keys in metadata, stored in
  the default metadata entry ('ssh-keys') and the legacy entry ('sshKeys').

  Args:
    metadata: An instance or project metadata object.

  Returns:
    A pair of lists containing the SSH public keys in the default and
    legacy metadata entries.
  """
  ssh_keys = []
  ssh_legacy_keys = []

  if not metadata:
    return ssh_keys, ssh_legacy_keys

  for item in metadata.items:
    if item.key == constants.SSH_KEYS_METADATA_KEY:
      ssh_keys = _GetSSHKeyListFromMetadataEntry(item.value)
    elif item.key == constants.SSH_KEYS_LEGACY_METADATA_KEY:
      ssh_legacy_keys = _GetSSHKeyListFromMetadataEntry(item.value)

  return ssh_keys, ssh_legacy_keys


def _MetadataHasGuestAttributesEnabled(metadata):
  """Returns true if the metadata has 'enable-guest-attributes' set to 'true'.

  Args:
    metadata: Instance or Project metadata

  Returns:
    True if Enabled, False if Disabled, None if key is not present.
  """
  if not (metadata and metadata.items):
    return None
  matching_values = [item.value for item in metadata.items
                     if item.key == GUEST_ATTRIBUTES_METADATA_KEY]

  if not matching_values:
    return None
  return matching_values[0].lower() == 'true'


def _SSHKeyExpiration(ssh_key):
  """Returns a datetime expiration time for an ssh key entry from metadata.

  Args:
    ssh_key: A single ssh key entry.

  Returns:
    None if no expiration set or a datetime object of the expiration (in UTC).

  Raises:
    ValueError: If the ssh key entry could not be parsed for expiration (invalid
      format, missing expected entries, etc).
    dateutil.DateTimeSyntaxError: The found expiration could not be parsed.
    dateutil.DateTimeValueError: The found expiration could not be parsed.
  """
  # Valid format of a key with expiration is:
  # <user>:<protocol> <key> google-ssh {... "expireOn": "<iso-8601>" ...}
  #        0            1        2                  json @ 3+
  key_parts = ssh_key.split()
  if len(key_parts) < 4 or key_parts[2] != 'google-ssh':
    return None
  expiration_json = ' '.join(key_parts[3:])
  expiration = json.loads(expiration_json)
  try:
    expireon = times.ParseDateTime(expiration['expireOn'])
  except KeyError:
    raise ValueError('Unable to find expireOn entry')
  return times.LocalizeDateTime(expireon, times.UTC)


def _PrepareSSHKeysValue(ssh_keys):
  """Returns a string appropriate for the metadata.

  Expired SSH keys are always removed.
  Then Values are taken from the tail until either all values are taken or
  _MAX_METADATA_VALUE_SIZE_IN_BYTES is reached, whichever comes first. The
  selected values are then reversed. Only values at the head of the list will be
  subject to removal.

  Args:
    ssh_keys: A list of keys. Each entry should be one key.

  Returns:
    A new-line-joined string of SSH keys.
  """
  keys = []
  bytes_consumed = 0

  now = times.LocalizeDateTime(times.Now(), times.UTC)

  for key in reversed(ssh_keys):
    try:
      expiration = _SSHKeyExpiration(key)
      expired = expiration is not None and expiration < now
      if expired:
        continue
    except (ValueError, times.DateTimeSyntaxError,
            times.DateTimeValueError) as exc:
      # Unable to get expiration, so treat it like it is unexpiring.
      log.warning(
          'Treating {0!r} as unexpiring, since unable to parse: {1}'.format(
              key, exc))

    num_bytes = len(key + '\n')
    if bytes_consumed + num_bytes > constants.MAX_METADATA_VALUE_SIZE_IN_BYTES:
      prompt_message = ('The following SSH key will be removed from your '
                        'project because your SSH keys metadata value has '
                        'reached its maximum allowed size of {0} bytes: {1}')
      prompt_message = prompt_message.format(
          constants.MAX_METADATA_VALUE_SIZE_IN_BYTES, key)
      console_io.PromptContinue(message=prompt_message, cancel_on_no=True)
    else:
      keys.append(key)
      bytes_consumed += num_bytes

  keys.reverse()
  return '\n'.join(keys)


def _AddSSHKeyToMetadataMessage(message_classes, user, public_key, metadata,
                                expiration=None, legacy=False):
  """Adds the public key material to the metadata if it's not already there.

  Args:
    message_classes: An object containing API message classes.
    user: The username for the SSH key.
    public_key: The SSH public key to add to the metadata.
    metadata: The existing metadata.
    expiration: If provided, a datetime after which the key is no longer valid.
    legacy: If true, store the key in the legacy "sshKeys" metadata entry.

  Returns:
    An updated metadata API message.
  """
  if expiration is None:
    entry = '{user}:{public_key}'.format(
        user=user, public_key=public_key.ToEntry(include_comment=True))
  else:
    # The client only supports a specific format. See
    # https://github.com/GoogleCloudPlatform/compute-image-packages/blob/master/packages/python-google-compute-engine/google_compute_engine/accounts/accounts_daemon.py#L118
    expire_on = times.FormatDateTime(expiration, '%Y-%m-%dT%H:%M:%S+0000',
                                     times.UTC)
    entry = '{user}:{public_key} google-ssh {jsondict}'.format(
        user=user, public_key=public_key.ToEntry(include_comment=False),
        # The json blob has strict encoding requirements by some systems.
        # Order entries to meet requirements.
        # Any spaces produces a Pantheon Invalid Key Required Format error:
        # cs/java/com/google/developers/console/web/compute/angular/ssh_keys_editor_item.ng
        jsondict=json.dumps(collections.OrderedDict([
            ('userName', user),
            ('expireOn', expire_on)])).replace(' ', ''))

  ssh_keys, ssh_legacy_keys = _GetSSHKeysFromMetadata(metadata)
  all_ssh_keys = ssh_keys + ssh_legacy_keys
  log.debug('Current SSH keys in project: {0}'.format(all_ssh_keys))

  if entry in all_ssh_keys:
    return metadata

  if legacy:
    metadata_key = constants.SSH_KEYS_LEGACY_METADATA_KEY
    updated_ssh_keys = ssh_legacy_keys
  else:
    metadata_key = constants.SSH_KEYS_METADATA_KEY
    updated_ssh_keys = ssh_keys
  updated_ssh_keys.append(entry)
  return metadata_utils.ConstructMetadataMessage(
      message_classes=message_classes,
      metadata={metadata_key: _PrepareSSHKeysValue(updated_ssh_keys)},
      existing_metadata=metadata)


def _MetadataHasBlockProjectSshKeys(metadata):
  """Return true if the metadata has 'block-project-ssh-keys' set and 'true'."""
  if not (metadata and metadata.items):
    return False
  matching_values = [item.value for item in metadata.items
                     if item.key == constants.SSH_KEYS_BLOCK_METADATA_KEY]
  if not matching_values:
    return False
  return matching_values[0].lower() == 'true'


class BaseSSHHelper(object):
  """Helper class for subcommands that need to connect to instances using SSH.

  Clients can call EnsureSSHKeyIsInProject() to make sure that the
  user's public SSH key is placed in the project metadata before
  proceeding.

  Attributes:
    keys: ssh.Keys, the public/private key pair.
    env: ssh.Environment, the current environment, used by subclasses.
  """

  keys = None

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        '--force-key-file-overwrite',
        action='store_true',
        default=None,
        help="""\
        If enabled, the gcloud command-line tool will regenerate and overwrite
        the files associated with a broken SSH key without asking for
        confirmation in both interactive and non-interactive environments.

        If disabled, the files associated with a broken SSH key will not be
        regenerated and will fail in both interactive and non-interactive
        environments.""")

    # Last line empty to preserve spacing between last paragraph and calliope
    # attachment "Use --no-force-key-file-overwrite to disable."
    parser.add_argument(
        '--ssh-key-file',
        help="""\
        The path to the SSH key file. By default, this is ``{0}''.
        """.format(ssh.Keys.DEFAULT_KEY_FILE))

  def Run(self, args):
    """Sets up resources to be used by concrete subclasses.

    Subclasses must call this in their Run() before continuing.

    Args:
      args: argparse.Namespace, arguments that this command was invoked with.

    Raises:
      ssh.CommandNotFoundError: SSH is not supported.
    """

    self.keys = ssh.Keys.FromFilename(args.ssh_key_file)
    self.env = ssh.Environment.Current()
    self.env.RequireSSH()

  def GetInstance(self, client, instance_ref):
    """Fetch an instance based on the given instance_ref."""
    request = (
        client.apitools_client.instances,
        'Get',
        client.messages.ComputeInstancesGetRequest(
            instance=instance_ref.Name(),
            project=instance_ref.project,
            zone=instance_ref.zone,
        ),
    )

    return client.MakeRequests([request])[0]

  def GetProject(self, client, project):
    """Returns the project object.

    Args:
      client: The compute client.
      project: str, the project we are requesting or None for value from
        from properties

    Returns:
      The project object
    """
    return client.MakeRequests(
        [(client.apitools_client.projects, 'Get',
          client.messages.ComputeProjectsGetRequest(
              project=project or
              properties.VALUES.core.project.Get(required=True),))])[0]

  def GetHostKeysFromGuestAttributes(self, client, instance_ref,
                                     instance=None, project=None):
    """Get host keys from guest attributes.

    Args:
      client: The compute client.
      instance_ref: The instance object.
      instance: The object representing the instance we are connecting to. If
        either project or instance is None, metadata won't be checked to
        determine if Guest Attributes are enabled.
      project: The object representing the current project. If either project
        or instance is None, metadata won't be checked to determine if
        Guest Attributes are enabled.

    Returns:
      A dictionary of host keys, with the type as the key and the host key
      as the value, or None if Guest Attributes is not enabled.
    """
    if instance and project:
      # Instance metadata has priority.
      guest_attributes_enabled = _MetadataHasGuestAttributesEnabled(
          instance.metadata)
      if guest_attributes_enabled is None:
        project_metadata = project.commonInstanceMetadata
        guest_attributes_enabled = _MetadataHasGuestAttributesEnabled(
            project_metadata)
      if not guest_attributes_enabled:
        return None

    requests = [(client.apitools_client.instances,
                 'GetGuestAttributes',
                 client.messages.ComputeInstancesGetGuestAttributesRequest(
                     instance=instance_ref.Name(),
                     project=instance_ref.project,
                     queryPath='hostkeys/',
                     zone=instance_ref.zone))]

    try:
      hostkeys = client.MakeRequests(requests)[0]
    except exceptions.ToolException as e:
      if ('The resource \'hostkeys/\' of type \'Guest Attribute\' was not '
          'found.') in six.text_type(e):
        hostkeys = None
      else:
        raise e

    hostkey_dict = {}

    if hostkeys is not None:
      for item in hostkeys.queryValue.items:
        if (item.namespace == 'hostkeys'
            and item.key in SUPPORTED_HOSTKEY_TYPES):
          # Truncate key value at any whitespace (newlines specifically can
          # be a security issue).
          key_value = item.value.split()[0]

          # Verify that key value is a base64 string
          try:
            decoded_key = base64.b64decode(key_value)
            encoded_key = encoding.Decode(base64.b64encode(decoded_key))
          except (TypeError, binascii.Error):
            encoded_key = ''

          if key_value == encoded_key:
            hostkey_dict[item.key] = key_value

    return hostkey_dict

  def WriteHostKeysToKnownHosts(self, known_hosts, host_keys, host_key_alias):
    """Writes host keys to known hosts file.

    Only writes keys to known hosts file if there are no existing keys for
    the host.

    Args:
      known_hosts: obj, known_hosts file object.
      host_keys: dict, dictionary of host keys.
      host_key_alias: str, alias for host key entries.
    """
    host_key_entries = []
    for key_type, key in host_keys.items():
      host_key_entry = '{0} {1}'.format(key_type, key)
      host_key_entries.append(host_key_entry)
    host_key_entries.sort()
    new_keys_added = known_hosts.AddMultiple(
        host_key_alias, host_key_entries, overwrite=False)
    if new_keys_added:
      log.status.Print('Writing {0} keys to {1}'
                       .format(len(host_key_entries), known_hosts.file_path))
    if host_key_entries and not new_keys_added:
      log.status.Print('Existing host keys found in {0}'
                       .format(known_hosts.file_path))
    known_hosts.Write()

  def _SetProjectMetadata(self, client, new_metadata):
    """Sets the project metadata to the new metadata."""
    errors = []
    client.MakeRequests(
        requests=[
            (client.apitools_client.projects,
             'SetCommonInstanceMetadata',
             client.messages.ComputeProjectsSetCommonInstanceMetadataRequest(
                 metadata=new_metadata,
                 project=properties.VALUES.core.project.Get(
                     required=True),
             ))],
        errors_to_collect=errors)
    if errors:
      utils.RaiseException(
          errors,
          SetProjectMetadataError,
          error_message='Could not add SSH key to project metadata:')

  def SetProjectMetadata(self, client, new_metadata):
    """Sets the project metadata to the new metadata with progress tracker."""
    with progress_tracker.ProgressTracker('Updating project ssh metadata'):
      self._SetProjectMetadata(client, new_metadata)

  def _SetInstanceMetadata(self, client, instance, new_metadata):
    """Sets the instance metadata to the new metadata."""
    errors = []
    # API wants just the zone name, not the full URL
    zone = instance.zone.split('/')[-1]
    client.MakeRequests(
        requests=[
            (client.apitools_client.instances,
             'SetMetadata',
             client.messages.ComputeInstancesSetMetadataRequest(
                 instance=instance.name,
                 metadata=new_metadata,
                 project=properties.VALUES.core.project.Get(
                     required=True),
                 zone=zone
             ))],
        errors_to_collect=errors)
    if errors:
      utils.RaiseToolException(
          errors,
          error_message='Could not add SSH key to instance metadata:')

  def SetInstanceMetadata(self, client, instance, new_metadata):
    """Sets the instance metadata to the new metadata with progress tracker."""
    with progress_tracker.ProgressTracker('Updating instance ssh metadata'):
      self._SetInstanceMetadata(client, instance, new_metadata)

  def EnsureSSHKeyIsInInstance(self, client, user, instance, expiration,
                               legacy=False):
    """Ensures that the user's public SSH key is in the instance metadata.

    Args:
      client: The compute client.
      user: str, the name of the user associated with the SSH key in the
          metadata
      instance: Instance, ensure the SSH key is in the metadata of this instance
      expiration: datetime, If not None, the point after which the key is no
          longer valid.
      legacy: If the key is not present in metadata, add it to the legacy
          metadata entry instead of the default entry.

    Returns:
      bool, True if the key was newly added, False if it was in the metadata
          already
    """
    public_key = self.keys.GetPublicKey()
    new_metadata = _AddSSHKeyToMetadataMessage(
        client.messages, user, public_key, instance.metadata,
        expiration=expiration, legacy=legacy)
    has_new_metadata = new_metadata != instance.metadata
    if has_new_metadata:
      self.SetInstanceMetadata(client, instance, new_metadata)
    return has_new_metadata

  def EnsureSSHKeyIsInProject(self, client, user, project=None,
                              expiration=None):
    """Ensures that the user's public SSH key is in the project metadata.

    Args:
      client: The compute client.
      user: str, the name of the user associated with the SSH key in the
          metadata
      project: Project, the project SSH key will be added to
      expiration: datetime, If not None, the point after which the key is no
          longer valid.

    Returns:
      bool, True if the key was newly added, False if it was in the metadata
          already
    """
    public_key = self.keys.GetPublicKey()
    if not project:
      project = self.GetProject(client, None)
    existing_metadata = project.commonInstanceMetadata
    new_metadata = _AddSSHKeyToMetadataMessage(
        client.messages, user, public_key, existing_metadata,
        expiration=expiration)
    if new_metadata != existing_metadata:
      self.SetProjectMetadata(client, new_metadata)
      return True
    else:
      return False

  def EnsureSSHKeyExists(self, compute_client, user, instance, project,
                         expiration):
    """Controller for EnsureSSHKey* variants.

    Sends the key to the project metadata or instance metadata,
    and signals whether the key was newly added.

    Args:
      compute_client: The compute client.
      user: str, The user name.
      instance: Instance, the instance to connect to.
      project: Project, the project instance is in.
      expiration: datetime, If not None, the point after which the key is no
          longer valid.


    Returns:
      bool, True if the key was newly added.
    """
    # There are two kinds of metadata: project-wide metadata and per-instance
    # metadata. There are five SSH-key related metadata keys:
    #
    # * project['ssh-keys']: shared project-wide list of keys.
    # * project['sshKeys']: legacy, shared project-wide list of keys.
    # * instance['block-project-ssh-keys']: bool, when true indicates that
    #     instance keys should replace project keys rather than being added
    #     to them.
    # * instance['ssh-keys']: instance specific list of keys.
    # * instance['sshKeys']: legacy, instance specific list of keys. When
    #     present, instance keys override project keys as if
    #     instance['block-project-ssh-keys'] was true.
    #
    # SSH-like commands work by copying a relevant SSH key to
    # the appropriate metadata value. The VM grabs keys from the metadata as
    # follows (pseudo-Python):
    #
    #   def GetAllSshKeys(project, instance):
    #       if 'sshKeys' in instance.metadata:
    #           return (instance.metadata['sshKeys'] +
    #                   instance.metadata['ssh-keys'])
    #       elif instance.metadata['block-project-ssh-keys'] == 'true':
    #           return instance.metadata['ssh-keys']
    #       else:
    #           return (instance.metadata['ssh-keys'] +
    #                   project.metadata['ssh-keys'] +
    #                   project.metadata['sshKeys']) # Legacy Project Keys
    #
    _, ssh_legacy_keys = _GetSSHKeysFromMetadata(instance.metadata)
    if ssh_legacy_keys:
      # If we add a key to project-wide metadata but the per-instance
      # 'sshKeys' metadata exists, we won't be able to ssh in because the VM
      # won't check the project-wide metadata. To avoid this, if the instance
      # has per-instance SSH key metadata, we add the key there instead.
      keys_newly_added = self.EnsureSSHKeyIsInInstance(
          compute_client, user, instance, expiration, legacy=True)
    elif _MetadataHasBlockProjectSshKeys(instance.metadata):
      # If the instance 'ssh-keys' metadata overrides the project-wide
      # 'ssh-keys' metadata, we should put our key there.
      keys_newly_added = self.EnsureSSHKeyIsInInstance(
          compute_client, user, instance, expiration)
    else:
      # Otherwise, try to add to the project-wide metadata. If we don't have
      # permissions to do that, add to the instance 'ssh-keys' metadata.
      try:
        keys_newly_added = self.EnsureSSHKeyIsInProject(
            compute_client, user, project, expiration)
      except SetProjectMetadataError:
        log.info('Could not set project metadata:', exc_info=True)
        # If we can't write to the project metadata, it may be because of a
        # permissions problem (we could inspect this exception object further
        # to make sure, but because we only get a string back this would be
        # fragile). If that's the case, we want to try the writing to instance
        # metadata. We prefer this to the per-instance override of the
        # project metadata.
        log.info('Attempting to set instance metadata.')
        keys_newly_added = self.EnsureSSHKeyIsInInstance(
            compute_client, user, instance, expiration)
    return keys_newly_added

  def GetConfig(self, host_key_alias, strict_host_key_checking=None,
                host_keys_to_add=None):
    """Returns a dict of default `ssh-config(5)` options on the OpenSSH format.

    Args:
      host_key_alias: str, Alias of the host key in the known_hosts file.
      strict_host_key_checking: str or None, whether to enforce strict host key
        checking. If None, it will be determined by existence of host_key_alias
        in the known hosts file. Accepted strings are 'yes', 'ask' and 'no'.
      host_keys_to_add: dict, A dictionary of host keys to add to the known
        hosts file.

    Returns:
      Dict with OpenSSH options.
    """
    config = {}
    known_hosts = ssh.KnownHosts.FromDefaultFile()
    config['UserKnownHostsFile'] = known_hosts.file_path
    # Ensure our SSH key trumps any ssh_agent
    config['IdentitiesOnly'] = 'yes'
    config['CheckHostIP'] = 'no'

    if not strict_host_key_checking:
      if known_hosts.ContainsAlias(host_key_alias) or host_keys_to_add:
        strict_host_key_checking = 'yes'
      else:
        strict_host_key_checking = 'no'
    if host_keys_to_add:
      self.WriteHostKeysToKnownHosts(
          known_hosts, host_keys_to_add, host_key_alias)

    config['StrictHostKeyChecking'] = strict_host_key_checking
    config['HostKeyAlias'] = host_key_alias
    # Don't hash the hostkey alias names.
    config['HashKnownHosts'] = 'no'
    return config


def AddVerifyInternalIpArg(parser):
  parser.add_argument(
      '--verify-internal-ip',
      action=actions.StoreBooleanProperty(
          properties.VALUES.ssh.verify_internal_ip),
      hidden=True,
      help='Whether or not `gcloud` should perform an initial SSH connection '
      'to verify an instance ID is correct when connecting via its internal '
      'IP. Without this check, `gcloud` will simply connect to the internal '
      'IP of the desired instance, which may be wrong if the desired instance '
      'is in a different subnet but happens to share the same internal IP as '
      'an instance in the current subnet. Defaults to True.')


def AddSSHKeyExpirationArgs(parser):
  """Additional flags to handle expiring SSH keys."""
  group = parser.add_mutually_exclusive_group()

  def ParseFutureDatetime(s):
    """Parses a string value into a future Datetime object."""
    dt = arg_parsers.Datetime.Parse(s)
    if dt < times.Now():
      raise arg_parsers.ArgumentTypeError(
          'Date/time must be in the future: {0}'.format(s))
    return dt

  group.add_argument(
      '--ssh-key-expiration',
      type=ParseFutureDatetime,
      help="""\
        The time when the ssh key will be valid until, such as
        "2017-08-29T18:52:51.142Z." This is only valid if the instance is not
        using OS Login. See $ gcloud topic datetimes for information on time
        formats.
        """)
  group.add_argument(
      '--ssh-key-expire-after',
      type=arg_parsers.Duration(lower_bound='1s'),
      help="""\
        The maximum length of time an SSH key is valid for once created and
        installed, e.g. 2m for 2 minutes. See $ gcloud topic datetimes for
        information on duration formats.
      """)


class BaseSSHCLIHelper(BaseSSHHelper):
  """Helper class for subcommands that use ssh or scp."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    super(BaseSSHCLIHelper, BaseSSHCLIHelper).Args(parser)

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help=('Print the equivalent scp/ssh command that would be run to '
              'stdout, instead of executing it.'))

    parser.add_argument(
        '--plain',
        action='store_true',
        help="""\
        Suppress the automatic addition of *ssh(1)*/*scp(1)* flags. This flag
        is useful if you want to take care of authentication yourself or
        use specific ssh/scp features.
        """)

    parser.add_argument(
        '--strict-host-key-checking',
        choices=['yes', 'no', 'ask'],
        help="""\
        Override the default behavior of StrictHostKeyChecking for the
        connection. By default, StrictHostKeyChecking is set to 'no' the first
        time you connect to an instance, and will be set to 'yes' for all
        subsequent connections.
        """)

    AddSSHKeyExpirationArgs(parser)

  def Run(self, args):
    super(BaseSSHCLIHelper, self).Run(args)
    if not args.plain:
      self.keys.EnsureKeysExist(args.force_key_file_overwrite,
                                allow_passphrase=True)

  def PreliminarilyVerifyInstance(self, instance_id, remote, identity_file,
                                  options, putty_force_connect=False):
    """Verify the instance's identity by connecting and running a command.

    Args:
      instance_id: str, id of the compute instance.
      remote: ssh.Remote, remote to connect to.
      identity_file: str, optional key file.
      options: dict, optional ssh options.
      putty_force_connect: bool, whether to inject 'y' into the prompts for
        `plink`, which is insecure and not recommended. It serves legacy
        compatibility purposes for existing usages only; DO NOT SET THIS IN NEW
        CODE.

    Raises:
      ssh.CommandError: The ssh command failed.
      core_exceptions.NetworkIssueError: The instance id does not match.
    """
    if options.get('StrictHostKeyChecking') == 'yes':
      log.debug('Skipping internal IP verification in favor of strict host '
                'key checking.')
      return

    if not properties.VALUES.ssh.verify_internal_ip.GetBool():
      log.warning(
          'Skipping internal IP verification connection and connecting to [{}] '
          'in the current subnet. This may be the wrong host if the instance '
          'is in a different subnet!'.format(remote.host))
      return

    metadata_id_url = (
        'http://metadata.google.internal/computeMetadata/v1/instance/id')
    # Exit codes 255 and 1 are taken by OpenSSH and PuTTY.
    # 23 chosen by fair dice roll.
    remote_command = [
        '[ `curl "{}" -H "Metadata-Flavor: Google" -q` = {} ] || exit 23'
        .format(metadata_id_url, instance_id)]
    cmd = ssh.SSHCommand(remote, identity_file=identity_file,
                         options=options, remote_command=remote_command)
    # Open the platform-specific null device for stdin and stdout
    # for the subprocess.
    null_in = FileReader(os.devnull)
    null_out = FileWriter(os.devnull)
    null_err = FileWriter(os.devnull)
    return_code = cmd.Run(
        self.env,
        putty_force_connect=putty_force_connect,
        explicit_output_file=null_out,
        explicit_error_file=null_err,
        explicit_input_file=null_in)
    if return_code == 0:
      return
    elif return_code == 23:
      raise core_exceptions.NetworkIssueError(
          'Established connection with host {} but was unable to '
          'confirm ID of the instance.'.format(remote.host))
    raise ssh.CommandError(cmd, return_code=return_code)


def HostKeyAlias(instance):
  return 'compute.{0}'.format(instance.id)


def GetUserAndInstance(user_host):
  """Returns pair consiting of user name and instance name."""
  parts = user_host.split('@')
  if len(parts) == 1:
    user = ssh.GetDefaultSshUsername(warn_on_account_user=True)
    instance = parts[0]
    return user, instance
  if len(parts) == 2:
    return parts
  raise ArgumentError(
      'Expected argument of the form [USER@]INSTANCE; received [{0}].'
      .format(user_host))


def CreateSSHPoller(remote, identity_file, options, iap_tunnel_args,
                    extra_flags=None, port=None):
  """Creates and returns an SSH poller."""

  ssh_poller_args = {'remote': remote,
                     'identity_file': identity_file,
                     'options': options,
                     'iap_tunnel_args': iap_tunnel_args,
                     'extra_flags': extra_flags,
                     'max_wait_ms': SSH_KEY_PROPAGATION_TIMEOUT_MS}

  # Do not include default port since that will prevent users from
  # specifying a custom port (b/121998342).
  if port:
    ssh_poller_args['port'] = six.text_type(port)

  return ssh.SSHPoller(**ssh_poller_args)


def ConfirmSecurityKeyStatus(oslogin_state):
  """Check the OS Login security key state and take approprate action.

  If OS Login security keys are not enabled, continue.
  When security keys are enabled:
    - if no security keys are configured in the user's account, show an error.
    - if the local SSH client doesn't support them, show an error.
    - if the user is using Putty, show an error.
    - if we cannnot determine if the local client supports security keys, show
      a warning and continue.

  Args:
    oslogin_state: An OsloginState object.

  Raises:
    SecurityKeysNotPresentError: If no security keys are registered in the
      user's account.
    SecurityKeysNotSupportedError: If the user's SSH client does not support
      security keys.

  Returns:
    None if no errors are raised.
  """
  # If OS login security keys are not enabled, continue.
  if not oslogin_state.security_keys_enabled:
    return

  # If security keys are enabled, but no security keys are registered in the
  # user's account, raise an error.
  if not oslogin_state.security_keys:
    raise SecurityKeysNotPresentError(
        'Instance requires security key for connection, but no security keys '
        'are registered in Google account.')

  # If security keys are enabled, and the local SSH client supports security
  # keys, all is good, so continue.
  if oslogin_state.ssh_security_key_support:
    return

  # If we cannot determine if the local client supports security keys, show
  # a warning and continue.
  if oslogin_state.ssh_security_key_support is None:
    log.warning('Instance requires security key for connection, but cannot '
                'determine if the SSH client supports security keys. The '
                'connection may fail.')
    return

  # If we are on Windows using PuTTY, raise an error.
  if oslogin_state.environment == 'putty':
    raise SecurityKeysNotSupportedError(
        'Instance requires security key for connection, but security keys '
        'are not supported on Windows using the PuTTY client.')

  # If the local SSH client does not support security keys, raise an error.
  raise SecurityKeysNotSupportedError(
      'Instance requires security key for connection, but security keys are '
      'not supported by the installed SSH version. OpenSSH 8.4 or higher '
      'is required.')

