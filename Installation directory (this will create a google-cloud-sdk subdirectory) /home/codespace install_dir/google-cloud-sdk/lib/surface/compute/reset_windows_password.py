# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Implements the command for resetting a password in a Windows instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import textwrap

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import openssl_encryption_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.util import gaia
from googlecloudsdk.command_lib.util import time_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import encoding as core_encoding
from googlecloudsdk.core.util import files

# This will only succeed on Windows machines.
try:
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.api_lib.compute import windows_encryption_utils
except ImportError:
  windows_encryption_utils = None

EXPIRATION_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S+0000'
WINDOWS_PASSWORD_TIMEOUT_SEC = 30
RSA_KEY_EXPIRATION_TIME_SEC = 300
METADATA_KEY = 'windows-keys'
OLD_METADATA_KEYS = ['gce-initial-windows-user', 'gce-initial-windows-password']
POLLING_SEC = 2

TIMEOUT_ERROR = textwrap.dedent("""\
    Did not receive password in a reasonable amount of time. Please try again.
    If this persists, confirm that the clock on your local system is correct.
    Current UTC time on your system: [{0}]""")

NOT_READY_ERROR = textwrap.dedent("""
    The instance may not be ready for use. This can occur if the instance was
    recently created or if the instance is not running Windows.
    Please wait a few minutes and try again.""")

OLD_WINDOWS_BUILD_ERROR = textwrap.dedent("""
    This Windows instance appears to be too old and does not support the
    reset-windows-password command. Please run the following command and look
    for the keys "gce-initial-windows-user" and "gce-initial-windows-password"
    in the metadata:
      [gcloud compute instances describe {0} --zone {1}]
    Alternatively, you can recreate the instance and update it to take
    advantage of reset-windows-password. More information can be found here:
    https://cloud.google.com/compute/docs/operating-systems/windows#upgrade_existing_instances
    """)

MACHINE_USERNAME_SAME_ERROR = textwrap.dedent("""
    User [{0}] cannot be created on instance [{1}].
    The user name and instance name must differ on Windows instances.
    Please use the "--user" flag to select a different username for this
    instance.""")

NO_IP_WARNING = textwrap.dedent("""\
    Instance [{0}] does not appear to have an external IP
    address, so it will not be able to accept external connections.
    To add an external IP address to the instance, use
    gcloud compute instances add-access-config.""")

OLD_KEYS_WARNING = textwrap.dedent("""\
    Instance [{0}] appears to have been created with an older
    version of gcloud (or another tool that is still setting legacy credentials
    for Windows instances) and the metadata for this instance contains insecure
    (and likely invalid) authentication credentials. It is recommended that
    they be removed with the following command:
    [gcloud compute instances remove-metadata {1} --zone {2} --keys {3}]
    """)

RESET_PASSWORD_WARNING = textwrap.dedent("""
    This command creates an account and sets an initial password for the
    user [{0}] if the account does not already exist.
    If the account already exists, resetting the password can cause the
    LOSS OF ENCRYPTED DATA secured with the current password, including
    files and stored passwords.

    For more information, see:
    https://cloud.google.com/compute/docs/operating-systems/windows#reset""")


class ResetWindowsPassword(base.UpdateCommand):
  """Reset and return a password for a Windows machine instance.

  *{command}* allows a user to reset and retrieve a password for
  a Windows virtual machine instance. If the Windows account does not
  exist, this command will cause the account to be created and the
  password for that new account will be returned.

  For Windows instances that are running a domain controller, running
  this command creates a new domain user if the user does not exist,
  or resets the password if the user does exist. It is not possible to
  use this command to create a local user on a domain-controller
  instance.

  NOTE: When resetting passwords or adding a new user to a Domain Controller
  in this way, the user will be added to the built in Admin Group on the
  Domain Controller. This will give the user wide reaching permissions. If
  this is not the desired outcome then Active Directory Users and Computers
  should be used instead.

  For all other instances, including domain-joined instances, running
  this command creates a local user or resets the password for a local
  user.

  WARNING: Resetting a password for an existing user can cause the
  loss of data encrypted with the current Windows password, such as
  encrypted files or stored passwords.

  The user running this command must have write permission for the
  Google Compute Engine project containing the Windows instance.

  ## EXAMPLES

  To reset the password for user 'foo' on a Windows instance 'my-instance' in
  zone 'us-central1-f', run:

    $ {command} my-instance --zone=us-central1-f --user=foo
  """

  category = base.TOOLS_CATEGORY

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('[private]text')

    parser.add_argument(
        '--user',
        help="""\
        ``USER'' specifies the username to get the password for.
        If omitted, the username is derived from your authenticated
        account email address.
        """)
    instance_flags.INSTANCE_ARG.AddArgument(parser)

  def GetGetRequest(self, client, instance_ref):
    return (client.apitools_client.instances,
            'Get',
            client.messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))

  def GetSetRequest(self, client, instance_ref, replacement):
    return (client.apitools_client.instances,
            'SetMetadata',
            client.messages.ComputeInstancesSetMetadataRequest(
                metadata=replacement.metadata,
                **instance_ref.AsDict()))

  def CreateReference(self, client, resources, args):
    return instance_flags.INSTANCE_ARG.ResolveAsResource(
        args, resources,
        scope_lister=instance_flags.GetInstanceZoneScopeLister(client))

  def Modify(self, client, existing):
    new_object = encoding.CopyProtoMessage(existing)

    existing_metadata = getattr(existing, 'metadata', None)

    new_metadata = metadata_utils.ConstructMetadataMessage(
        message_classes=client.messages,
        metadata={
            METADATA_KEY:
            self._UpdateWindowsKeysValue(existing_metadata)},
        existing_metadata=existing_metadata)

    new_object.metadata = new_metadata
    return new_object

  def _ConstructWindowsKeyEntry(self, user, modulus, exponent, email):
    """Return a JSON formatted entry for 'windows-keys'."""
    expire_str = time_util.CalculateExpiration(RSA_KEY_EXPIRATION_TIME_SEC)
    windows_key_data = {'userName': user,
                        'modulus': core_encoding.Decode(modulus),
                        'exponent': core_encoding.Decode(exponent),
                        'email': email,
                        'expireOn': expire_str}

    windows_key_entry = json.dumps(windows_key_data, sort_keys=True)
    return windows_key_entry

  def _UpdateWindowsKeysValue(self, existing_metadata):
    """Returns a string appropriate for the metadata.

    Values are removed if they have expired and non-expired keys are removed
    from the head of the list only if the total key size is greater than
    MAX_METADATA_VALUE_SIZE_IN_BYTES.

    Args:
      existing_metadata: The existing metadata for the instance to be updated.

    Returns:
      A new-line-joined string of Windows keys.
    """
    # Get existing keys from metadata.
    windows_keys = []
    self.old_metadata_keys = []
    for item in existing_metadata.items:
      if item.key == METADATA_KEY:
        windows_keys = [key.strip() for key in item.value.split('\n') if key]
      if item.key in OLD_METADATA_KEYS:
        self.old_metadata_keys.append(item.key)

    # Append new key.
    windows_keys.append(self.windows_key_entry)

    # Remove expired and excess key entries.
    keys = []
    bytes_consumed = 0

    for key in reversed(windows_keys):  # Keys should be removed in FIFO order.
      num_bytes = len(key + '\n')
      key_expired = False

      # Try to determine if key is expired. Ignore any errors.
      try:
        key_data = json.loads(key)
        if time_util.IsExpired(key_data['expireOn']):
          key_expired = True
      # Errors should come in two forms: Invalid JSON (ValueError) or missing
      # 'expireOn' key (KeyError).
      except (ValueError, KeyError):
        pass

      if key_expired:
        log.debug('The following Windows key has expired and will be removed '
                  'from your project: {0}'.format(key))
      elif (bytes_consumed + num_bytes
            > constants.MAX_METADATA_VALUE_SIZE_IN_BYTES):
        log.debug('The following Windows key will be removed from your project '
                  'because your windows keys metadata value has reached its '
                  'maximum allowed size of {0} bytes: {1}'
                  .format(constants.MAX_METADATA_VALUE_SIZE_IN_BYTES, key))
      else:
        keys.append(key)
        bytes_consumed += num_bytes

    log.debug('Number of Windows Keys: {0}'.format(len(keys)))
    keys.reverse()
    return '\n'.join(keys)

  def _GetSerialPortOutput(self, client, instance_ref, port=4):
    """Returns the serial port output for self.instance_ref."""
    request = (client.apitools_client.instances,
               'GetSerialPortOutput',
               client.messages.ComputeInstancesGetSerialPortOutputRequest(
                   port=port,
                   **instance_ref.AsDict()))
    objects = client.MakeRequests([request])
    return objects[0].contents

  def _GetEncryptedPasswordFromSerialPort(self, client, instance_ref,
                                          search_modulus):
    """Returns the decrypted password from the data in the serial port."""
    encrypted_password_data = {}
    start_time = time_util.CurrentTimeSec()
    count = 1
    agent_ready = False
    while not encrypted_password_data:
      log.debug('Get Serial Port Output, Try {0}'.format(count))
      if (time_util.CurrentTimeSec()
          > (start_time + WINDOWS_PASSWORD_TIMEOUT_SEC)):
        raise utils.TimeoutError(
            TIMEOUT_ERROR.format(time_util.CurrentDatetimeUtc()))
      serial_port_output = self._GetSerialPortOutput(
          client, instance_ref, port=4).split('\n')
      for line in reversed(serial_port_output):
        try:
          encrypted_password_dict = json.loads(line)
        # Sometimes the serial port output only contains a partial entry.
        except ValueError:
          continue

        modulus = encrypted_password_dict.get('modulus')
        if modulus or encrypted_password_dict.get('ready'):
          agent_ready = True

        # Ignore any output that doesn't contain an encrypted password.
        if not encrypted_password_dict.get('encryptedPassword'):
          continue

        if (core_encoding.Decode(search_modulus) == core_encoding.Decode(
            modulus)):
          encrypted_password_data = encrypted_password_dict
          break
      if not agent_ready:
        if self.old_metadata_keys:
          message = OLD_WINDOWS_BUILD_ERROR.format(instance_ref.instance,
                                                   instance_ref.zone)
          raise utils.WrongInstanceTypeError(message)
        else:
          message = NOT_READY_ERROR
          raise utils.InstanceNotReadyError(message)
      time_util.Sleep(POLLING_SEC)
      count += 1
    encrypted_password = encrypted_password_data['encryptedPassword']
    return encrypted_password

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    start = time_util.CurrentTimeSec()

    # Set up Encryption utilities.
    openssl_executable = files.FindExecutableOnPath('openssl')
    if windows_encryption_utils:
      crypt = windows_encryption_utils.WinCrypt()
    elif openssl_executable:
      crypt = openssl_encryption_utils.OpensslCrypt(openssl_executable)
    else:
      raise utils.MissingDependencyError(
          'Your platform does not support OpenSSL.')

    # Get Authenticated email address and default username.
    email = properties.VALUES.core.account.GetOrFail()
    if args.user:
      user = args.user
    else:
      user = gaia.MapGaiaEmailToDefaultAccountName(email)

    if args.instance_name == user:
      raise utils.InvalidUserError(
          MACHINE_USERNAME_SAME_ERROR.format(user, args.instance_name))

    # Warn user (This warning doesn't show for non-interactive sessions).
    message = RESET_PASSWORD_WARNING.format(user)
    prompt_string = ('Would you like to set or reset the password for [{0}]'
                     .format(user))
    console_io.PromptContinue(
        message=message,
        prompt_string=prompt_string,
        cancel_on_no=True)

    log.status.Print('Resetting and retrieving password for [{0}] on [{1}]'
                     .format(user, args.instance_name))

    # Get Encryption Keys.
    key = crypt.GetKeyPair()
    modulus, exponent = crypt.GetModulusExponentFromPublicKey(
        crypt.GetPublicKey(key))

    # Create Windows key entry.
    self.windows_key_entry = self._ConstructWindowsKeyEntry(
        user, modulus, exponent, email)

    # Call ReadWriteCommad.Run() which will fetch the instance and update
    # the metadata (using the data in self.windows_key_entry).
    instance_ref = self.CreateReference(client, holder.resources, args)
    get_request = self.GetGetRequest(client, instance_ref)

    objects = client.MakeRequests([get_request])

    new_object = self.Modify(client, objects[0])

    # If existing object is equal to the proposed object or if
    # Modify() returns None, then there is no work to be done, so we
    # print the resource and return.
    if objects[0] == new_object:
      log.status.Print(
          'No change requested; skipping update for [{0}].'.format(
              objects[0].name))
      return objects

    updated_instance = client.MakeRequests(
        [self.GetSetRequest(client, instance_ref, new_object)])[0]

    # Retrieve and Decrypt the password from the serial console.
    enc_password = self._GetEncryptedPasswordFromSerialPort(
        client, instance_ref, modulus)
    password = crypt.DecryptMessage(key, enc_password)

    # Get External IP address.
    try:
      access_configs = updated_instance.networkInterfaces[0].accessConfigs
      external_ip_address = access_configs[0].natIP
    except (KeyError, IndexError) as _:
      log.warning(NO_IP_WARNING.format(updated_instance.name))
      external_ip_address = None

    # Check for old Windows credentials.
    if self.old_metadata_keys:
      log.warning(OLD_KEYS_WARNING.format(instance_ref.instance,
                                          instance_ref.instance,
                                          instance_ref.zone,
                                          ','.join(self.old_metadata_keys)))

    log.info('Total Elapsed Time: {0}'
             .format(time_util.CurrentTimeSec() - start))

    # The connection info resource.
    connection_info = {'username': user,
                       'password': password,
                       'ip_address': external_ip_address}
    return connection_info
