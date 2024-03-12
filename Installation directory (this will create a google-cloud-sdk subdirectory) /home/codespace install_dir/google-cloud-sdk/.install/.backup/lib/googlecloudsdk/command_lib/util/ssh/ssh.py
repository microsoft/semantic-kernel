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

"""SSH client utilities for key-generation, dispatching the ssh commands etc."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import enum
import errno
import getpass
import os
import re
import string
import subprocess
import tempfile
import textwrap

from googlecloudsdk.api_lib.oslogin import client as oslogin_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.oslogin import oslogin_utils
from googlecloudsdk.command_lib.util import gaia
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import exceptions as creds_exceptions
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from googlecloudsdk.core.util import retry
import six
from six.moves.urllib.parse import quote


PER_USER_SSH_CONFIG_FILE = os.path.join('~', '.ssh', 'config')
SECURITY_KEY_DIR = os.path.join('~', '.ssh', 'google_compute_engine_sk')
CERTIFICATE_DIR = os.path.join('~', '.ssh', 'google_compute_engine_cert')
OSLOGIN_ENABLE_METADATA_KEY = 'enable-oslogin'
OSLOGIN_ENABLE_2FA_METADATA_KEY = 'enable-oslogin-2fa'
OSLOGIN_ENABLE_SK_METADATA_KEY = 'enable-oslogin-sk'
OSLOGIN_REQUIRE_CERTIFICATES_METADATA_KEY = 'require-oslogin-certificates'


class InvalidKeyError(core_exceptions.Error):
  """Indicates a key file was not found."""


class MissingCommandError(core_exceptions.Error):
  """Indicates that an external executable couldn't be found."""


class CommandError(core_exceptions.Error):
  """Raise for a failure when invoking ssh, scp, or similar."""

  def __init__(self, cmd, message=None, return_code=None):
    if not (message or return_code):
      raise ValueError('One of message or return_code is required.')

    self.cmd = cmd

    message_text = '[{0}]'.format(message) if message else None
    return_code_text = (
        'return code [{0}]'.format(return_code) if return_code else None
    )
    why_failed = ' and '.join(
        [f for f in [message_text, return_code_text] if f]
    )

    super(CommandError, self).__init__(
        '[{0}] exited with {1}.'.format(self.cmd, why_failed),
        exit_code=return_code,
    )


class InvalidConfigurationError(core_exceptions.Error):
  """When arguments provided have misconfigured sources/destinations."""

  def __init__(self, msg, sources, destination):
    super(InvalidConfigurationError, self).__init__(
        msg + '  Got sources: {}, destination: {}'.format(sources, destination)
    )


class BadCharacterError(core_exceptions.Error):
  """Indicates a character was found that couldn't be escaped."""


class Suite(enum.Enum):
  """Represents an SSH implementation suite."""

  OPENSSH = 'OpenSSH'
  PUTTY = 'PuTTY'


class Environment(object):
  """Environment maps SSH commands to executable location on file system.

    Recommended usage:

    env = Environment.Current()
    env.RequireSSH()
    cmd = [env.ssh, 'user@host']

  An attribute which is None indicates that the executable couldn't be found.

  Attributes:
    suite: Suite, The suite for this environment.
    bin_path: str, The path where the commands are located. If None, use
      standard `$PATH`.
    ssh: str, Location of ssh command (or None if not found).
    ssh_term: str, Location of ssh terminal command (or None if not found), for
      interactive sessions.
    scp: str, Location of scp command (or None if not found).
    keygen: str, Location of the keygen command (or None if not found).
    ssh_exit_code: int, Exit code indicating SSH command failure.
  """

  # Each suite supports ssh and non-interactive ssh, scp and keygen.
  COMMANDS = {
      Suite.OPENSSH: {
          'ssh': 'ssh',
          'ssh_term': 'ssh',
          'scp': 'scp',
          'keygen': 'ssh-keygen',
      },
      Suite.PUTTY: {
          'ssh': 'plink',
          'ssh_term': 'putty',
          'scp': 'pscp',
          'keygen': 'winkeygen',
      },
  }

  # Exit codes indicating that the `ssh` command (not remote) failed
  SSH_EXIT_CODES = {
      Suite.OPENSSH: 255,
      Suite.PUTTY: 1,  # Only `plink`, `putty` always gives 0
  }

  def __init__(self, suite, bin_path=None):
    """Create a new environment by supplying a suite and command directory.

    Args:
      suite: Suite, the suite for this environment.
      bin_path: str, the path where the commands are located. If None, use
        standard $PATH.
    """
    self.suite = suite
    self.bin_path = bin_path
    self.ssh = None
    self.ssh_term = None
    self.scp = None
    self.keygen = None
    for key, cmd in six.iteritems(self.COMMANDS[suite]):
      setattr(self, key, files.FindExecutableOnPath(cmd, path=self.bin_path))
    self.ssh_exit_code = self.SSH_EXIT_CODES[suite]

  def SupportsSSH(self):
    """Whether all SSH commands are supported.

    Returns:
      True if and only if all commands are supported, else False.
    """
    return all((self.ssh, self.ssh_term, self.scp, self.keygen))

  def RequireSSH(self):
    """Simply raises an error if any SSH command is not supported.

    Raises:
      MissingCommandError: One or more of the commands were not found.
    """
    if not self.SupportsSSH():
      raise MissingCommandError('Your platform does not support SSH.')

  @classmethod
  def Current(cls):
    """Retrieve the current environment.

    Returns:
      Environment, the active and current environment on this machine.
    """
    if platforms.OperatingSystem.IsWindows():
      suite = Suite.PUTTY
      bin_path = _SdkHelperBin()
    else:
      suite = Suite.OPENSSH
      bin_path = None
    return Environment(suite, bin_path)


def _IsValidSshUsername(user):
  # All characters must be ASCII, and no spaces are allowed
  # This may grant false positives, but will prevent backwards-incompatible
  # behavior.
  return all(ord(c) < 128 and c != ' ' for c in user)


class KeyFileStatus(enum.Enum):
  PRESENT = 'OK'
  ABSENT = 'NOT FOUND'
  BROKEN = 'BROKEN'


class _KeyFileKind(enum.Enum):
  """List of supported (by gcloud) key file kinds."""

  PRIVATE = 'private'
  PUBLIC = 'public'
  PPK = 'PuTTY PPK'


class Keys(object):
  """Manages private and public SSH key files.

  This class manages the SSH public and private key files, and verifies
  correctness of them. A Keys object is instantiated with a path to a
  private key file. The public key locations are inferred by the private
  key file by simply appending a different file ending (`.pub` and `.ppk`).

  If the keys are broken or do not yet exist, the EnsureKeysExist method
  can be utilized to shell out to the system SSH keygen and write new key
  files.

  By default, there is an SSH key for the gcloud installation,
  `DEFAULT_KEY_FILE` which should likely be used. Note that SSH keys are
  generated and managed on a per-installation basis. Strictly speaking,
  there is no 1:1 relationship between installation and user account.

  Verifies correctness of key files:
   - Populates list of SSH key files (key pair, ppk key on Windows).
   - Checks if files are present and (to basic extent) correct.
   - Can remove broken key (if permitted by user).
   - Provides status information.
  """

  DEFAULT_KEY_FILE = os.path.join('~', '.ssh', 'google_compute_engine')

  class PublicKey(object):
    """Represents a public key.

    Attributes:
      key_type: str, Key generation type, e.g. `ssh-rsa` or `ssh-dss`.
      key_data: str, Base64-encoded key data.
      comment: str, Non-semantic comment, may be empty string or contain spaces.
    """

    def __init__(self, key_type, key_data, comment=''):
      self.key_type = key_type
      self.key_data = key_data
      self.comment = comment

    @classmethod
    def FromKeyString(cls, key_string):
      """Construct a public key from a typical OpenSSH-style key string.

      Args:
        key_string: str, on the format `TYPE DATA [COMMENT]`. Example: `ssh-rsa
          ABCDEF me@host.com`.

      Raises:
        InvalidKeyError: The public key file does not contain key (heuristic).

      Returns:
        Keys.PublicKey, the parsed public key.
      """
      # We get back a unicode list of keys for the remaining metadata, so
      # convert to unicode. Assume UTF 8, but if we miss a character we can just
      # replace it with a '?'. The only source of issues would be the hostnames,
      # which are relatively inconsequential.
      decoded_key = key_string.strip()
      if isinstance(key_string, six.binary_type):
        decoded_key = decoded_key.decode('utf-8', 'replace')
      parts = decoded_key.split(' ', 2)
      if len(parts) < 2:
        raise InvalidKeyError('Public key [{}] is invalid.'.format(key_string))
      comment = parts[2].strip() if len(parts) > 2 else ''  # e.g. `me@host`
      return cls(parts[0], parts[1], comment)

    def ToEntry(self, include_comment=False):
      """Format this key into a text entry.

      Args:
        include_comment: str, Include the comment part in this entry.

      Returns:
        str, A key string on the form `TYPE DATA` or `TYPE DATA COMMENT`.
      """
      out_format = '{type} {data}'
      if include_comment and self.comment:
        out_format += ' {comment}'
      return out_format.format(
          type=self.key_type, data=self.key_data, comment=self.comment
      )

  class KeyFileData(object):

    def __init__(self, filename):
      # We keep filename as file handle. Filesystem race is impossible to avoid
      # in this design as we spawn a subprocess and pass in filename.
      # TODO(b/33288605) fix it.
      self.filename = filename
      self.status = None

  def __init__(self, key_file, env=None):
    """Create a Keys object which manages the given files.

    Args:
      key_file: str, The file path to the private SSH key file (other files are
        derived from this name). Automatically handles symlinks and user
        expansion.
      env: Environment, Current environment or None to infer from current.
    """
    private_key_file = os.path.realpath(files.ExpandHomeDir(key_file))
    self.dir = os.path.dirname(private_key_file)
    self.env = env or Environment.Current()
    self.keys = {
        _KeyFileKind.PRIVATE: self.KeyFileData(private_key_file),
        _KeyFileKind.PUBLIC: self.KeyFileData(private_key_file + '.pub'),
    }
    if self.env.suite is Suite.PUTTY:
      self.keys[_KeyFileKind.PPK] = self.KeyFileData(private_key_file + '.ppk')

  @classmethod
  def FromFilename(cls, filename=None, env=None):
    """Create Keys object given a file name.

    Args:
      filename: str or None, the name to the file or DEFAULT_KEY_FILE if None
      env: Environment, Current environment or None to infer from current.

    Returns:
      Keys, an instance which manages the keys with the given name.
    """
    return cls(filename or Keys.DEFAULT_KEY_FILE, env)

  @property
  def key_file(self):
    """Filename of the private key file."""
    return self.keys[_KeyFileKind.PRIVATE].filename

  def _StatusMessage(self):
    """Prepares human readable SSH key status information."""
    messages = []
    key_padding = 0
    status_padding = 0
    for kind in self.keys:
      data = self.keys[kind]
      key_padding = max(key_padding, len(kind.value))
      status_padding = max(status_padding, len(data.status.value))
    for kind in self.keys:
      data = self.keys[kind]
      messages.append(
          '{} {} [{}]\n'.format(
              (kind.value + ' key').ljust(key_padding + 4),
              ('(' + data.status.value + ')').ljust(status_padding + 2),
              data.filename,
          )
      )
    messages.sort()
    return ''.join(messages)

  def Validate(self):
    """Performs minimum key files validation.

    Note that this is a simple best-effort parser intended for machine
    generated keys. If the file has been user modified, there's a risk
    of both false positives and false negatives.

    Returns:
      KeyFileStatus.PRESENT if key files meet minimum requirements.
      KeyFileStatus.ABSENT if neither private nor public keys exist.
      KeyFileStatus.BROKEN if there is some key, but it is broken or incomplete.
    """

    def ValidateFile(kind):
      status_or_line = self._WarnOrReadFirstKeyLine(
          self.keys[kind].filename, kind.value
      )
      if isinstance(status_or_line, KeyFileStatus):
        return status_or_line
      else:  # returned line - present
        self.keys[kind].first_line = status_or_line
        return KeyFileStatus.PRESENT

    for file_kind in self.keys:
      self.keys[file_kind].status = ValidateFile(file_kind)

    # The remaining checks are for the public key file.

    # Additional validation for public keys.
    if self.keys[_KeyFileKind.PUBLIC].status is KeyFileStatus.PRESENT:
      try:
        self.GetPublicKey()
      except InvalidKeyError:
        log.warning(
            'The public SSH key file [{}] is corrupt.'.format(
                self.keys[_KeyFileKind.PUBLIC]
            )
        )
        self.keys[_KeyFileKind.PUBLIC].status = KeyFileStatus.BROKEN

    # Summary
    collected_values = [x.status for x in six.itervalues(self.keys)]
    if all(x == KeyFileStatus.ABSENT for x in collected_values):
      return KeyFileStatus.ABSENT
    elif all(x == KeyFileStatus.PRESENT for x in collected_values):
      return KeyFileStatus.PRESENT
    else:
      return KeyFileStatus.BROKEN

  def RemoveKeyFilesIfPermittedOrFail(self, force_key_file_overwrite=None):
    """Removes all SSH key files if user permitted this behavior.

    Precondition: The SSH key files are currently in a broken state.

    Depending on `force_key_file_overwrite`, delete all SSH key files:

    - If True, delete key files.
    - If False, cancel immediately.
    - If None and
      - interactive, prompt the user.
      - non-interactive, cancel.

    Args:
      force_key_file_overwrite: bool or None, overwrite broken key files.

    Raises:
      console_io.OperationCancelledError: Operation intentionally cancelled.
      OSError: Error deleting the broken file(s).
    """
    message = 'Your SSH key files are broken.\n' + self._StatusMessage()
    if force_key_file_overwrite is False:
      raise console_io.OperationCancelledError(message + 'Operation aborted.')
    message += 'We are going to overwrite all above files.'
    log.warning(message)
    if force_key_file_overwrite is None:
      # - Interactive when pressing 'Y', continue
      # - Interactive when pressing enter or 'N', raise OperationCancelledError
      # - Non-interactive, raise OperationCancelledError
      console_io.PromptContinue(default=False, cancel_on_no=True)

    # Remove existing broken key files.
    for key_file in six.viewvalues(self.keys):
      try:
        os.remove(key_file.filename)
      except OSError as e:
        if e.errno == errno.EISDIR:
          # key_file.filename points to a directory
          raise

  def _WarnOrReadFirstKeyLine(self, path, kind):
    """Returns the first line from the key file path.

    A None return indicates an error and is always accompanied by a log.warning
    message.

    Args:
      path: The path of the file to read from.
      kind: The kind of key file, 'private' or 'public'.

    Returns:
      None (and prints a log.warning message) if the file does not exist, is not
      readable, or is empty. Otherwise returns the first line utf8 decoded.
    """
    try:
      with files.FileReader(path) as f:
        line = f.readline().strip()
        if line:
          return line
        msg = 'is empty'
        status = KeyFileStatus.BROKEN
    except files.MissingFileError:
      msg = 'does not exist'
      status = KeyFileStatus.ABSENT
    except files.Error:
      msg = 'is not readable'
      status = KeyFileStatus.BROKEN
    log.warning('The %s SSH key file for gcloud %s.', kind, msg)
    return status

  def GetPublicKey(self):
    """Returns the public key verbatim from file as a string.

    Precondition: The public key must exist. Run Keys.EnsureKeysExist() prior.

    Raises:
      InvalidKeyError: If the public key file does not contain key (heuristic).

    Returns:
      Keys.PublicKey, a public key (that passed primitive validation).
    """
    filepath = self.keys[_KeyFileKind.PUBLIC].filename
    with files.FileReader(filepath) as f:
      # TODO(b/33467618): Currently we enforce that key exists on the first
      # line, but OpenSSH does not enforce that.
      first_line = f.readline()
      return self.PublicKey.FromKeyString(first_line)

  def EnsureKeysExist(self, overwrite, allow_passphrase=True):
    """Generate ssh key files if they do not yet exist.

    Precondition: Environment.SupportsSSH()

    Args:
      overwrite: bool or None, overwrite key files if they are broken.
      allow_passphrase: bool, if keygeneration occurs, let the user specfiy a
        passphrase for private key encryption. See `ssh.KeygenCommand` for
        details on when this is possible.

    Raises:
      console_io.OperationCancelledError: if interrupted by user
      CommandError: if the ssh-keygen command failed.
    """
    key_files_validity = self.Validate()

    if key_files_validity is KeyFileStatus.BROKEN:
      self.RemoveKeyFilesIfPermittedOrFail(overwrite)
      # Fallthrough
    if key_files_validity is not KeyFileStatus.PRESENT:
      if key_files_validity is KeyFileStatus.ABSENT:
        # If key is broken, message is already displayed
        log.warning('You do not have an SSH key for gcloud.')
        log.warning('SSH keygen will be executed to generate a key.')

      if not os.path.exists(self.dir):
        msg = (
            'This tool needs to create the directory [{0}] before being '
            'able to generate SSH keys.'.format(self.dir)
        )
        console_io.PromptContinue(
            message=msg,
            cancel_on_no=True,
            cancel_string='SSH key generation aborted by user.',
        )
        files.MakeDir(self.dir, 0o700)

      cmd = KeygenCommand(self.key_file, allow_passphrase=allow_passphrase)
      cmd.Run(self.env)

    if self.env.suite is Suite.PUTTY:
      # This is to fix an encoding issue with PPK's we generated that was
      # ignored in versions of PuTTY <=0.70, but became invalid in version 0.71.
      # Since this only affects the PPK, we don't need to generate a new key; we
      # can just correct the encoding of the PPK if necessary. We use a sentinel
      # file in the config dir to check if the encoding is already correct.
      valid_ppk_sentinel = config.Paths().valid_ppk_sentinel_file
      if not os.path.exists(valid_ppk_sentinel):
        if key_files_validity is KeyFileStatus.PRESENT:  # Initial validity
          cmd = KeygenCommand(
              self.key_file, allow_passphrase=False, reencode_ppk=True
          )
          cmd.Run(self.env)
        try:
          files.WriteFileContents(valid_ppk_sentinel, '')
        except files.Error as e:
          # It's possible that writing the sentinel file fails, which means
          # we'll potentially have to re-encode the PPK again the next time an
          # SSH/SCP command is run. But we shouldn't let this prevent the user
          # from running their current command.
          log.debug('Failed to create sentinel file: [{}]'.format(e))


def CertFileFromRegion(region):
  cert_dir = os.path.realpath(files.ExpandHomeDir(CERTIFICATE_DIR))
  return os.path.join(cert_dir, '{}-cert.pub'.format(region))


def WriteCertificate(region, cert):
  """Writes a certificate associated with the key pair.

  Args:
    region: string, The region where the SSH certificate may be used.
    cert: string, The SSH certificate data.
  """
  cert_dir = os.path.realpath(files.ExpandHomeDir(CERTIFICATE_DIR))
  files.MakeDir(cert_dir, mode=0o700)

  filepath = CertFileFromRegion(region)
  try:
    files.WriteFileContents(filepath, cert)
  except files.Error as e:
    log.debug('Failed to update the certificate {}: [{}]'.format(filepath, e))


def ValidateCertificate(oslogin_state, region):
  """Checks if the certificate is currently valid.

  Args:
    oslogin_state: An OsloginState object.
    region: string, The region where the SSH certificate may be used.
  """
  def IsCertValid(cert):
    time_format = '%Y-%m-%dT%H:%M:%S'
    match = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', cert)
    if not match:
      return
    start = datetime.datetime.strptime(match[0], time_format)
    end = datetime.datetime.strptime(match[1], time_format)
    now = datetime.datetime.now()
    oslogin_state.signed_ssh_key = now > start and now < end

  cmd = KeygenCommand(CertFileFromRegion(region), print_cert=True)
  try:
    cmd.Run(out_func=IsCertValid)
  except CommandError as e:
    log.debug(
        'Cert File [{0}] could not be opened: {1}'.format(
            CertFileFromRegion(region), e
        )
    )


def WriteSecurityKeys(oslogin_state):
  """Writes temporary files from a list of key data.

  Args:
    oslogin_state: An OsloginState object.

  Returns:
    List of file paths for security keys or None if security keys are not
    supported.
  """
  # PuTTY does not support security keys, so don't attempt to write any keys.
  if oslogin_state.environment == 'putty':
    return None

  security_keys = oslogin_state.security_keys

  # If there are no security keys, just return.
  if not security_keys:
    return None

  key_dir = os.path.realpath(files.ExpandHomeDir(SECURITY_KEY_DIR))

  files.MakeDir(key_dir, mode=0o700)
  key_files = []

  # Remove existing keys
  for filename in os.listdir(key_dir):
    if filename.startswith('tmp_sk'):
      file_path = os.path.join(key_dir, filename)
      os.remove(file_path)

  # Write new keys
  for num, key in enumerate(security_keys):
    filename = 'tmp_sk_{0}'.format(num)
    file_path = os.path.join(key_dir, filename)
    files.WriteFileContents(file_path, key, private=True)
    key_files.append(file_path)

  return key_files


class KnownHosts(object):
  """Represents known hosts file, supports read, write and basic key management.

  Currently a very naive, but sufficient, implementation where each entry is
  simply a string, and all entries are list of those strings.
  """

  # TODO(b/33467618): Rename the file itself
  DEFAULT_PATH = os.path.realpath(
      files.ExpandHomeDir(
          os.path.join('~', '.ssh', 'google_compute_known_hosts')
      )
  )

  def __init__(self, known_hosts, file_path):
    """Construct a known hosts representation based on a list of key strings.

    Args:
      known_hosts: str, list each corresponding to a line in known_hosts_file.
      file_path: str, path to the known_hosts_file.
    """
    self.known_hosts = known_hosts
    self.file_path = file_path

  @classmethod
  def FromFile(cls, file_path):
    """Create a KnownHosts object given a known_hosts_file.

    Args:
      file_path: str, path to the known_hosts_file.

    Returns:
      KnownHosts object corresponding to the file. If the file could not be
      opened, the KnownHosts object will have no entries.
    """
    try:
      known_hosts = files.ReadFileContents(file_path).splitlines()
    except files.Error as e:
      known_hosts = []
      log.debug(
          'SSH Known Hosts File [{0}] could not be opened: {1}'.format(
              file_path, e
          )
      )
    return KnownHosts(known_hosts, file_path)

  @classmethod
  def FromDefaultFile(cls):
    """Create a KnownHosts object from the default known_hosts_file.

    Returns:
      KnownHosts object corresponding to the default known_hosts_file.
    """
    return KnownHosts.FromFile(KnownHosts.DEFAULT_PATH)

  def ContainsAlias(self, host_key_alias):
    """Check if a host key alias exists in one of the known hosts.

    Args:
      host_key_alias: str, the host key alias

    Returns:
      bool, True if host_key_alias is in the known hosts file. If the known
      hosts file couldn't be opened it will be treated as if empty and False
      returned.
    """
    return any(host_key_alias in line for line in self.known_hosts)

  def Add(self, hostname, host_key, overwrite=False):
    """Add or update the entry for the given hostname.

    If there is no entry for the given hostname, it will be added. If there is
    an entry already and overwrite_keys is False, nothing will be changed. If
    there is an entry and overwrite_keys is True, the key will be updated if it
    has changed.

    Args:
      hostname: str, The hostname for the known_hosts entry.
      host_key: str, The host key for the given hostname.
      overwrite: bool, If true, will overwrite the entry corresponding to
        hostname with the new host_key if it already exists. If false and an
        entry already exists for hostname, will ignore the new host_key value.
    """
    new_key_entry = '{0} {1}'.format(hostname, host_key)
    for i, key in enumerate(self.known_hosts):
      if key.startswith(hostname):
        if overwrite:
          self.known_hosts[i] = new_key_entry
        break
    else:
      self.known_hosts.append(new_key_entry)

  def AddMultiple(self, hostname, host_keys, overwrite=False):
    """Add or update multiple entries for the given hostname.

    If there is no entry for the given hostname, the keys will be added. If
    there is an entry already, and overwrite keys is False, nothing will be
    changed. If there is an entry and overwrite_keys is True, all  current
    entries for the given hostname will be removed and the new keys added.

    Args:
      hostname: str, The hostname for the known_hosts entry.
      host_keys: list, A list of host keys for the given hostname.
      overwrite: bool, If true, will overwrite the entries corresponding to
        hostname with the new host_key if it already exists. If false and an
        entry already exists for hostname, will ignore the new host_key values.

    Returns:
      bool, True if new keys were added.
    """
    new_keys_added = False
    new_key_entries = [
        '{0} {1}'.format(hostname, host_key) for host_key in host_keys
    ]
    if not new_key_entries:
      return new_keys_added
    existing_entries = [
        key for key in self.known_hosts if key.startswith(hostname)
    ]
    if existing_entries:
      if overwrite:
        self.known_hosts = [
            key for key in self.known_hosts if not key.startswith(hostname)
        ]
        self.known_hosts.extend(new_key_entries)
        new_keys_added = True
    else:
      self.known_hosts.extend(new_key_entries)
      new_keys_added = True

    return new_keys_added

  def Write(self):
    """Writes the file to disk."""
    files.WriteFileContents(
        self.file_path, '\n'.join(self.known_hosts) + '\n', private=True
    )


def GetDefaultSshUsername(warn_on_account_user=False):
  """Returns the default username for ssh.

  The default username is the local username, unless that username is invalid.
  In that case, the default username is the username portion of the current
  account.

  Emits a warning if it's not using the local account username.

  Args:
    warn_on_account_user: bool, whether to warn if using the current account
      instead of the local username.

  Returns:
    str, the default SSH username.
  """
  user = getpass.getuser()
  if not _IsValidSshUsername(user):
    full_account = properties.VALUES.core.account.Get(required=True)
    account_user = gaia.MapGaiaEmailToDefaultAccountName(full_account)
    if warn_on_account_user:
      log.warning(
          'Invalid characters in local username [{0}]. '
          'Using username corresponding to active account: [{1}]'.format(
              user, account_user
          )
      )
    user = account_user
  return user


def MetadataHasEnable(metadata, key_name):
  """Return true if the metadata has the supplied key and it is set to 'true'.

  Args:
    metadata: Instance or Project metadata.
    key_name: The name of the metadata key to check. e.g. 'oslogin-enable'.

  Returns:
    True if Enabled, False if Disabled, None if key is not presesnt.
  """
  if not (metadata and metadata.items):
    return None
  matching_values = [
      item.value for item in metadata.items if item.key == key_name
  ]
  if not matching_values:
    return None
  return matching_values[0].lower() == 'true'


def FeatureEnabledInMetadata(
    instance, project, key_name, instance_override=None
):
  """Return True if the feature associated with the supplied key is enabled.

  If the key is set to 'true' in instance metadata, will return True.
  If the key is set to 'false' in instance metadata, will return False.
  If key is not set in instance metadata, will return the value in project
  metadata unless instance_override is not None (set to True or False).

  Args:
    instance: The current instance object.
    project: The current project object.
    key_name: The name of metadata key to check. e.g. 'oslogin-enable'.
    instance_override: The value of the instance metadata key. Used if the
      instance object cannot be passed in. None if not set.

  Returns:
    bool, True if the feature associated with the supplied key is enabled
      in instance/project metadata.
  """
  feature_enabled = None
  if instance is not None:
    feature_enabled = MetadataHasEnable(instance.metadata, key_name)
  elif instance_override is not None:
    feature_enabled = instance_override
  if feature_enabled is None:
    project_metadata = project.commonInstanceMetadata
    feature_enabled = MetadataHasEnable(project_metadata, key_name)

  return feature_enabled


def CheckSshSecurityKeySupport():
  """Check the local SSH installation for security key support.

  Runs 'ssh -Q key' and looks for keys starting with 'sk-'.
  PuTTY on Windows will return False.

  Returns:
    True if SSH supports security keys, False if not, and None if support
    cannot be determined.
  """
  env = Environment.Current()

  # Security Keys are not currently supported in PuTTy.
  if env.suite == Suite.PUTTY:
    return False

  ssh_flags = ['-Q', 'key']

  cmd = SSHCommand(None, extra_flags=ssh_flags, tty=False)
  cmd_list = cmd.Build()
  log.debug(cmd_list)

  try:
    output = six.ensure_str(
        subprocess.check_output(cmd_list, stderr=subprocess.STDOUT)
    )
    log.debug(output)
  except subprocess.CalledProcessError:
    log.debug(
        'Cannot determine SSH supported key types using command: {0}'.format(
            ' '.join(cmd_list)
        )
    )
    return None

  keys_supported = output.splitlines()
  log.debug('Supported SSH key types: {0}'.format(keys_supported))

  for key in keys_supported:
    if key.startswith('sk-'):
      return True

  # Keys starting with 'sk-' not found.
  return False


class OsloginState(object):
  """Class for holding OS Login State.

  Attributes:
    oslogin_enabled: bool, True if OS Login is enabled on the instance.
    oslogin_2fa_enabled: bool, True if OS Login 2FA is enabled on the instance.
    security_keys_enabled: bool, True if Security Keys should be used for SSH
      authentication.
    user: str, The username that SSH should use for connecting.
    third_party_user: bool, True if the authenticated user is an external
      account user.
    ssh_security_key_support: bool, True if the SSH client supports security
      keys.
    environment: str, A hint about the current enviornment. ('ssh' or 'putty')
    security_keys: list, A list of 'private' keys associated with the security
      keys configured in the user's account.
    signed_ssh_key: bool, True if a valid signed ssh key exists.
    require_certificates: bool, True if passing a certificate is required.
  """

  def __init__(
      self,
      oslogin_enabled=False,
      oslogin_2fa_enabled=False,
      security_keys_enabled=False,
      user=None,
      third_party_user=False,
      ssh_security_key_support=None,
      environment=None,
      security_keys=None,
      signed_ssh_key=False,
      require_certificates=False,
  ):
    self.oslogin_enabled = oslogin_enabled
    self.oslogin_2fa_enabled = oslogin_2fa_enabled
    self.security_keys_enabled = security_keys_enabled
    self.user = user
    self.third_party_user = third_party_user
    self.ssh_security_key_support = ssh_security_key_support
    self.environment = environment
    if security_keys is None:
      self.security_keys = []
    else:
      self.security_keys = security_keys
    self.signed_ssh_key = signed_ssh_key
    self.require_certificates = require_certificates

  def __str__(self):
    return textwrap.dedent("""\
        OS Login Enabled: {0}
        2FA Enabled: {1}
        Security Keys Enabled: {2}
        Username: {3}
        Third Party User: {4}
        SSH Security Key Support: {5}
        Environment: {6}
        Security Keys:
        {7}
        Signed SSH Key: {8}
        Require Certificates: {9}
        """).format(
        self.oslogin_enabled,
        self.oslogin_2fa_enabled,
        self.security_keys_enabled,
        self.user,
        self.third_party_user,
        self.ssh_security_key_support,
        self.environment,
        '\n'.join(self.security_keys),
        self.signed_ssh_key,
        self.require_certificates,
    )

  def __repr__(self):
    return (
        'OsloginState(oslogin_enabled={0}, oslogin_2fa_enabled={1}, '
        'security_keys_enabled={2}, user={3}, third_party_user={4}'
        'ssh_security_key_support={5}, environment={6}, '
        'security_keys={7}, signed_ssh_key={8}, '
        'require_certificates={9})'.format(
            self.oslogin_enabled,
            self.oslogin_2fa_enabled,
            self.security_keys_enabled,
            self.user,
            self.third_party_user,
            self.ssh_security_key_support,
            self.environment,
            self.security_keys,
            self.signed_ssh_key,
            self.require_certificates,
        )
    )


def _IsInstanceWindows(instance, messages=None):
  if not instance or not instance.disks or not messages:
    return False

  boot_disk = next(iter(filter(lambda disk: disk.boot, instance.disks)), None)
  guest_os_features = boot_disk.guestOsFeatures if boot_disk else []
  features = [feature.type for feature in guest_os_features or []]
  return (
      features
      and messages.GuestOsFeature.TypeValueValuesEnum.WINDOWS in features
  )


def GetOsloginState(
    instance,
    project,
    requested_user,
    public_key,
    expiration_time,
    release_track,
    username_requested=False,
    instance_enable_oslogin=None,
    instance_enable_2fa=None,
    instance_enable_security_keys=None,
    instance_require_certificates=None,
    messages=None,
):
  """Check instance/project metadata for oslogin and return updated username.

  Check to see if OS Login is enabled in metadata and if it is, return
  the OS Login user and a boolean value indicating if OS Login is being used.

  Args:
    instance: instance, The object representing the instance we are connecting
      to. If None, instance metadata will be ignored.
    project: project, The object representing the current project.
    requested_user: str, The default or requested username to connect as.
    public_key: str, The public key of the user connecting.
    expiration_time: int, Microseconds after epoch when the ssh key should
      expire. If None, an existing key will not be modified and a new key will
      not be set to expire.  If not None, an existing key may be modified with
      the new expiry.
    release_track: release_track, The object representing the release track.
    username_requested: bool, True if the user has passed a specific username in
      the args.
    instance_enable_oslogin: True if the instance's metadata indicates that OS
      Login is enabled, and False if not enabled. Used when the instance cannot
      be passed through the instance argument. None if not specified.
    instance_enable_2fa: True if the instance's metadata indicates that OS Login
      2FA is enabled, and False if not enabled. Used when the instance cannot be
      passed through the instance argument. None if not specified.
    instance_enable_security_keys: True if the instance's metadata indicates
      that OS Login security keys are enabled, and False if not enabled. Used
      when the instance cannot be passed through the instance argument. None if
      not specified.
    instance_require_certificates: True if the instance's metadata indicates
      that OS Login SSH certificates are to be used exclusively, False
      otherwise. An override to be used when the instance cannot be passed
      through the "instance" argument. None if not specified.
    messages: API messages class, The compute API messages.

  Returns:
    object, An object containing the OS Login state, with values indicating
      whether OS Login is enabled, Security Keys are enabled, the username to
      connect as and a list of security keys.
  """
  oslogin_state = OsloginState(user=requested_user)

  oslogin_enabled = FeatureEnabledInMetadata(
      instance,
      project,
      OSLOGIN_ENABLE_METADATA_KEY,
      instance_override=instance_enable_oslogin,
  )

  if not oslogin_enabled:
    # OS Login is disabled by default.
    return oslogin_state

  if _IsInstanceWindows(instance, messages=messages):
    log.status.Print(
        'OS Login is not available on Windows VMs.\nUsing ssh metadata.'
    )
    return oslogin_state

  oslogin_state.oslogin_enabled = oslogin_enabled
  oslogin_state.oslogin_2fa_enabled = FeatureEnabledInMetadata(
      instance,
      project,
      OSLOGIN_ENABLE_2FA_METADATA_KEY,
      instance_override=instance_enable_2fa,
  )
  oslogin_state.security_keys_enabled = FeatureEnabledInMetadata(
      instance,
      project,
      OSLOGIN_ENABLE_SK_METADATA_KEY,
      instance_override=instance_enable_security_keys,
  )
  oslogin_state.third_party_user = IsThirdPartyUser()
  oslogin_state.require_certificates = FeatureEnabledInMetadata(
      instance,
      project,
      OSLOGIN_REQUIRE_CERTIFICATES_METADATA_KEY,
      instance_override=instance_require_certificates,
  )

  env = Environment.Current()
  if env.suite == Suite.PUTTY:
    oslogin_state.environment = 'putty'
  else:
    oslogin_state.environment = 'ssh'

  if oslogin_state.security_keys_enabled:
    oslogin_state.ssh_security_key_support = CheckSshSecurityKeySupport()
  oslogin = oslogin_client.OsloginClient(release_track)
  user_email = (
      properties.VALUES.auth.impersonate_service_account.Get()
      or properties.VALUES.core.account.Get()
  )

  if (
      release_track
      in [
          base.ReleaseTrack.ALPHA,
          base.ReleaseTrack.BETA,
      ]
      and oslogin_state.third_party_user
      or oslogin_state.require_certificates
  ):
    if oslogin_state.third_party_user:
      # Only escape 3PI usernames; 1P identities must retain the '@' symbol.
      user_email = quote(user_email, safe=':')
    zone = instance.zone.split('/').pop()
    # Inclusively trim suffix from last '-' to convert a zone into a region.
    region = zone[:zone.rindex('-')]
    ValidateCertificate(oslogin_state, region)
    if not oslogin_state.signed_ssh_key:
      sign_response = oslogin.SignSshPublicKey(
          user_email,
          public_key,
          project.name,
          region,
      )
      WriteCertificate(region, sign_response.signedSshPublicKey)
    login_profile = oslogin.GetLoginProfile(
        user_email,
        project.name,
        include_security_keys=oslogin_state.security_keys_enabled,
    )
  # Check to see if public key is already in profile and POSIX information
  # exists associated with the project. If either are not set, import an SSH
  # public key. Otherwise update the expiration time if needed.
  else:
    login_profile = oslogin.GetLoginProfile(
        user_email,
        project.name,
        include_security_keys=oslogin_state.security_keys_enabled,
    )
    if oslogin_state.security_keys_enabled:
      oslogin_state.security_keys = oslogin_utils.GetSecurityKeysFromProfile(
          user_email, oslogin, profile=login_profile
      )
      if not login_profile.posixAccounts:
        import_response = oslogin.ImportSshPublicKey(user_email, '')
        login_profile = import_response.loginProfile
    else:
      keys = oslogin_utils.GetKeyDictionaryFromProfile(
          user_email, oslogin, profile=login_profile
      )
      fingerprint = oslogin_utils.FindKeyInKeyList(public_key, keys)
      if not fingerprint or not login_profile.posixAccounts:
        import_response = oslogin.ImportSshPublicKey(
            user_email, public_key, expiration_time
        )
        login_profile = import_response.loginProfile
      elif expiration_time:
        oslogin.UpdateSshPublicKey(
            user_email,
            fingerprint,
            keys[fingerprint],
            'expirationTimeUsec',
            expiration_time=expiration_time,
        )

  # Get the username for the oslogin user. If the username is the same as the
  # default user, return that one. Otherwise, return the 'primary' username.
  # If no 'primary' exists, return the first username.
  oslogin_user = None
  for pa in login_profile.posixAccounts:
    oslogin_user = oslogin_user or pa.username
    if pa.username == requested_user:
      return oslogin_state
    elif pa.primary:
      oslogin_user = pa.username

  oslogin_state.user = oslogin_user

  # If the user passed in a specific username to the command, show a message
  # to the user, otherwise just add a message to the log.
  if username_requested:
    log.status.Print(
        'Using OS Login user [{0}] instead of requested user [{1}]'.format(
            oslogin_user, requested_user
        )
    )
  else:
    log.info(
        'Using OS Login user [{0}] instead of default user [{1}]'.format(
            oslogin_user, requested_user
        )
    )
  return oslogin_state


def IsThirdPartyUser():
  """Checks if the Authenticated User is a BYOID User."""
  try:
    creds = c_store.LoadFreshCredential(use_google_auth=True)
  except creds_exceptions.Error:
    log.debug('Failed to load fresh credentials.')
    return False
  creds_type = c_creds.CredentialTypeGoogleAuth.FromCredentials(creds)
  return creds_type in (
      c_creds.CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT,
      c_creds.CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_USER,
      c_creds.CredentialTypeGoogleAuth.EXTERNAL_ACCOUNT_AUTHORIZED_USER,
  )


def ParseAndSubstituteSSHFlags(
    args, remote, instance_address, internal_address
):
  """Obtain extra flags from the command arguments."""
  extra_flags = []
  if args.ssh_flag:
    for flag in args.ssh_flag:
      if flag:  # Skip any empty flags.
        for flag_part in flag.split():  # We want grouping here
          deref_flag = flag_part

          # Call replace only when it is necessary. It will lower the chance
          # replace crashes because the replacing value is None.

          if '%USER%' in deref_flag:
            deref_flag = deref_flag.replace('%USER%', remote.user)

          if '%INSTANCE%' in deref_flag:
            deref_flag = deref_flag.replace('%INSTANCE%', instance_address)

          if '%INTERNAL%' in deref_flag:
            deref_flag = deref_flag.replace('%INTERNAL%', internal_address)

          extra_flags.append(deref_flag)
  return extra_flags


def _SdkHelperBin():
  """Returns the SDK helper executable bin directory."""
  # TODO(b/33467618): Remove this method?
  return os.path.join(config.Paths().sdk_root, 'bin', 'sdk')


class Remote(object):
  """A reference to an SSH remote, consisting of a host and user.

  Hashing and equality methods are implemented for this class,
  so remotes can be put in sets for de-duplication.

  Attributes:
    user: str or None, SSH user name (optional).
    host: str or None, Host name.
  """

  # A remote has two parts `[user@]host`, where `user` is optional.
  #   A user:
  #   - cannot contain ':', '@'
  #   A host:
  #   - cannot start with '.'
  #   - cannot contain ':', '/', '\\', '@'
  # This regular expression matches if and only if the above requirements are
  # satisfied. The capture groups are (user, host) where `user` will be
  # None if omitted.
  _REMOTE_REGEX = re.compile(r'^(?:([^:@]+)@)?([^.:/\\@][^:/\\@]*)$')

  def __init__(self, host, user=None):
    """Constructor for FileReference.

    Args:
      host: str or None, Host name.
      user: str or None, SSH user name.
    """
    self.host = host
    self.user = user

  def ToArg(self):
    """Convert to a positional argument, in the form expected by `ssh`/`plink`.

    Returns:
      str, A string on the form `[user@]host`.
    """
    return self.user + '@' + self.host if self.user else self.host

  @classmethod
  def FromArg(cls, arg):
    """Convert an SSH-style positional argument to a remote.

    Args:
      arg: str, A path on the canonical ssh form `[user@]host`.

    Returns:
      Remote, the constructed object or None if arg is malformed.
    """
    match = cls._REMOTE_REGEX.match(arg)
    if match:
      user, host = match.groups()
      return cls(host, user=user)
    else:
      return None

  def __hash__(self):
    return hash(self.ToArg())

  def __eq__(self, other):
    return type(self) is type(other) and self.ToArg() == other.ToArg()

  def __ne__(self, other):
    return not self.__eq__(other)

  def __repr__(self):
    return self.ToArg()


def _EscapeProxyCommandArg(s, env):
  """Returns s escaped such that it can be a ProxyCommand arg.

  Args:
    s: str, Argument to escape. Must be non-empty.
    env: Environment, data about the ssh client.

  Raises:
    BadCharacterError: If s contains a bad character.
  """
  for c in s:
    if not 0x20 <= ord(c) < 0x7F:
      # For ease of implementation we ban control characters and non-ASCII.
      raise BadCharacterError(
          (
              "Special character %r (part of %r) couldn't be escaped for "
              'ProxyCommand'
          )
          % (c, s)
      )
  if env.suite is Suite.PUTTY:
    # When using proxycmd with putty or plink, 3 unescapes happen:
    # 1 putty/plink does command line -> argv unescape.
    # 2 putty/plink does backslash and percent unescape.
    # 3 Inner gcloud python binary does command line -> argv unescape.
    #
    # We reverse this, doing escapes in reverse order, doing 3, 2.
    # We don't do the 1 escape here because that's done later inside the
    # subprocess.Popen() function.
    s = _EscapeWindowsArgvElement(s)
    s = _EscapePuttyBackslashPercent(s)
    return s
  # When using ProxyCommand with OpenSSH, 2 unescapes happen:
  # 1 OpenSSH does percent unescape.
  # 2 bash does unescape.
  # We do the corresponding escapes in reverse.
  return _EscapeForBash(s).replace('%', '%%')


def _EscapeWindowsArgvElement(s):
  """Returns s escaped such that it can be passed to a windows executable.

  Args:
    s: str, What to escape. Must be ASCII and non-control.
  """
  # Each Windows binary can unescape its commandline arguments to argv how it
  # wants, but they tend to behave like this:
  # https://docs.microsoft.com/en-us/cpp/cpp/parsing-cpp-command-line-arguments?view=vs-2017
  # We escape in that format because that format is similar to how python (of
  # the inner gcloud) does it. The primary difference is what happens when
  # inside a doublequoted string there is an even number of backslashes
  # (possibly 0) then at least 2 doublequotes. This function never returns a
  # string like that, so it avoids the ambiguity.
  #
  # We escape in reverse, because that's easiest.
  result = []
  # Whether (in the reversed input) we are following a non-broken chain of
  # backslashes (possibly 0-length) after a doublequote.
  # The final output will have a doublequote appended to the end, so the first
  # character of the reversed input is considered to follow a doublequote.
  following_quote = True
  for c in s[::-1]:
    if c == '"':
      result.append('"\\')
      following_quote = True
    elif c == '\\':
      if following_quote:
        result.append('\\\\')
      else:
        result.append('\\')
    else:
      result.append(c)
      following_quote = False
  return '"' + ''.join(result)[::-1] + '"'


def _EscapePuttyBackslashPercent(s):
  # s must be ASCII and non-control.
  # The putty unescaping is documented at
  # https://the.earth.li/~sgtatham/putty/0.70/htmldoc/Chapter4.html#config-proxy-command
  return s.replace('\\', '\\\\').replace('%', '%%')


def _EscapeForBash(s):
  """Returns s escaped so it can be used as a single bash argument.

  Args:
    s: str, What to escape. Must be ASCII, non-control, and non-empty.
  """
  # From https://stackoverflow.com/q/15783701
  good_chars = set(string.ascii_letters + string.digits + '%+-./:=@_')
  result = []
  for c in s:
    if c in good_chars:
      result.append(c)
    else:
      result.append('\\' + c)
  return ''.join(result)


def _BuildIapTunnelProxyCommandArgs(iap_tunnel_args, env):
  """Calculate the ProxyCommand flags for IAP Tunnel if necessary.

  IAP Tunnel with ssh runs an second inner version of gcloud by passing a
  command to do so as a ProxyCommand argument to OpenSSH/Putty.

  Args:
    iap_tunnel_args: iap_tunnel.SshTunnelArgs or None, options about IAP Tunnel.
    env: Environment, data about the ssh client.

  Raises:
    BadCharacterError: If instance arg contains any invalid characters.

  Returns:
    [str], the additional arguments for OpenSSH or Putty.
  """
  if not iap_tunnel_args:
    return []

  # A relaxed validation of the passed in instance name / IP / hostname.
  # Mostly so potentially malicious names don't get passed in the resulting
  # generated command.
  allowed_non_alnum_chars = {'-', '_', '.'}
  for char in iap_tunnel_args.instance:
    if not char.isalnum() and char not in allowed_non_alnum_chars:
      raise BadCharacterError(
          'Instance name/IP/hostname contains illegal characters.'
      )

  gcloud_command = execution_utils.ArgsForGcloud()
  # Applying _EscapeProxyCommandArg to the first item (the python executable
  # path) doesn't make 100% sense on Windows, because the full unescaping only
  # happens to arguments, not to the executable path. But this escaping will be
  # correct as long as the python executable path doesn't contain a doublequote
  # or end with a backslash, which should never happen.
  gcloud_command = [_EscapeProxyCommandArg(x, env) for x in gcloud_command]
  # track, project, zone, instance, verbosity should only contain
  # characters that don't need escaping, so don't bother escaping them.
  if iap_tunnel_args.track:
    gcloud_command.append(iap_tunnel_args.track)
  # Windows CMD only accepts double quotes.
  port_token, quotation = (
      ('%port', '\"') if env.suite is Suite.PUTTY else ('%p', '\'')
  )
  gcloud_command.extend([
      'compute',
      'start-iap-tunnel',
      quotation + iap_tunnel_args.instance + quotation,
      quotation + port_token + quotation,
      '--listen-on-stdin',
      '--project=' + iap_tunnel_args.project,
  ])
  if iap_tunnel_args.zone:
    gcloud_command.append('--zone=' + iap_tunnel_args.zone)
  if iap_tunnel_args.region:
    gcloud_command.append('--region=' + iap_tunnel_args.region)
  if iap_tunnel_args.network:
    gcloud_command.append('--network=' + iap_tunnel_args.network)
  for arg in iap_tunnel_args.pass_through_args:
    gcloud_command.append(_EscapeProxyCommandArg(arg, env))

  verbosity = log.GetVerbosityName()
  if verbosity:
    gcloud_command.append('--verbosity=' + verbosity)

  if env.suite is Suite.PUTTY:
    return ['-proxycmd', ' '.join(gcloud_command)]
  else:
    return [
        '-o',
        ' '.join(['ProxyCommand'] + gcloud_command),
        '-o',
        'ProxyUseFdpass=no',
    ]


class KeygenCommand(object):
  """Platform independent SSH client key generation command.

  For OpenSSH, we use `ssh-keygen(1)`. For PuTTY, we use a custom binary.
  Currently, the only supported algorithm is 'rsa'. The command generates the
  following files:
  - `<identity_file>`: Private key, on OpenSSH format (possibly encrypted).
  - `<identity_file>.pub`: Public key, on OpenSSH format.
  - `<identity_file>.ppk`: Unencrypted PPK key-pair, on PuTTY format.

  The PPK-file is only generated from a PuTTY environment, and encodes the same
  private- and public keys as the other files.

  Attributes:
    identity_file: str, path to private key file.
    allow_passphrase: bool, If True, attempt at prompting the user for a
      passphrase for private key encryption, given that the following conditions
      are also true: - Running in an OpenSSH environment (Linux and Mac) -
      Running in interactive mode (from an actual TTY) - Prompts are enabled in
      gcloud
    reencode_ppk: bool, If True, reencode the PPK file if it was generated with
      a bad encoding, instead of generating a new key. This is only valid for
      PuTTY.
    print_cert: bool, If True, ssh-keygen will print certificate information.
  """

  def __init__(self, identity_file, allow_passphrase=True, reencode_ppk=False,
               print_cert=False):
    """Construct a suite independent `ssh-keygen` command."""
    self.identity_file = identity_file
    self.allow_passphrase = allow_passphrase
    self.reencode_ppk = reencode_ppk
    self.print_cert = print_cert

  def Build(self, env=None):
    """Construct the actual command according to the given environment.

    Args:
      env: Environment, to construct the command for (or current if None).

    Raises:
      MissingCommandError: If keygen command was not found.

    Returns:
      [str], the command args (where the first arg is the command itself).
    """
    env = env or Environment.Current()
    if not env.keygen:
      raise MissingCommandError(
          'Keygen command not found in the current environment.'
      )
    args = [env.keygen]
    if env.suite is Suite.OPENSSH:
      if self.print_cert:
        args.extend(['-L', '-f', self.identity_file])
      else:
        prompt_passphrase = self.allow_passphrase and console_io.CanPrompt()
        if not prompt_passphrase:
          args.extend(['-N', ''])  # Empty passphrase
        args.extend(['-t', 'rsa', '-f', self.identity_file])
    else:
      if self.reencode_ppk:
        args.append('--reencode-ppk')
      args.append(self.identity_file)

    return args

  def Run(self, env=None, out_func=None):
    """Run the keygen command in the given environment.

    Args:
      env: Environment, environment to run in (or current if None).
      out_func: str->None: A function call with the stdout of ssh-keygen.

    Raises:
      MissingCommandError: Keygen command not found.
      CommandError: Keygen command failed.
    """
    args = self.Build(env)
    log.debug('Running command [{}].'.format(' '.join(args)))
    status = execution_utils.Exec(args, no_exit=True, out_func=out_func)
    if status:
      raise CommandError(args[0], return_code=status)


class SSHCommand(object):
  """Represents a platform independent SSH command.

  This class is intended to manage the most important suite- and platform
  specifics. We manage the following data:
  - The executable to call, either `ssh`, `putty` or `plink`.
  - User and host, through the `remote` arg.
  - Potential remote command to execute, `remote_command` arg.

  In addition, it manages these flags:
  -t, -T      Pseudo-terminal allocation
  -p, -P      Port
  -i          Identity file (private key)
  -o Key=Val  OpenSSH specific options that should be added, `options` arg.

  For flexibility, SSHCommand also accepts `extra_flags`. Always use these
  with caution -- they will be added as-is to the command invocation without
  validation. Specifically, do not add any of the above mentioned flags.
  """

  def __init__(
      self,
      remote,
      port=None,
      identity_file=None,
      cert_file=None,
      options=None,
      extra_flags=None,
      remote_command=None,
      tty=None,
      iap_tunnel_args=None,
      remainder=None,
      identity_list=None,
  ):
    """Construct a suite independent SSH command.

    Note that `extra_flags` and `remote_command` arguments are lists of strings:
    `remote_command=['echo', '-e', 'hello']` is different from
    `remote_command=['echo', '-e hello']` -- the former is likely desired.
    For the same reason, `extra_flags` should be passed like `['-k', 'v']`.

    Args:
      remote: Remote, the remote to connect to.
      port: str, port.
      identity_file: str, path to private key file.
      cert_file: str, path to certificate file.
      options: {str: str}, options (`-o`) for OpenSSH, see `ssh_config(5)`.
      extra_flags: [str], extra flags to append to ssh invocation. Both binary
        style flags `['-b']` and flags with values `['-k', 'v']` are accepted.
      remote_command: [str], command to run remotely.
      tty: bool, launch a terminal. If None, determine automatically based on
        presence of remote command.
      iap_tunnel_args: iap_tunnel.SshTunnelArgs or None, options about IAP
        Tunnel.
      remainder: [str], NOT RECOMMENDED. Arguments to be appended directly to
        the native tool invocation, after the `[user@]host` part but prior to
        the remote command. On PuTTY, this can only be a remote command. On
        OpenSSH, this can be flags followed by a remote command. Cannot be
        combined with `remote_command`. Use `extra_flags` and `remote_command`
        instead.
      identity_list: list, A list of paths to private key files. Overrides the
        identity_file argument, and sets multiple `['-i']` flags.
    """
    self.remote = remote
    self.port = port
    self.identity_file = identity_file
    self.cert_file = cert_file
    self.identity_list = identity_list
    self.options = options or {}
    self.extra_flags = extra_flags or []
    self.remote_command = remote_command or []
    self.tty = tty
    self.iap_tunnel_args = iap_tunnel_args
    self.remainder = remainder
    self._remote_command_file = None

  def Build(self, env=None):
    """Construct the actual command according to the given environment.

    Args:
      env: Environment, to construct the command for (or current if None).

    Raises:
      MissingCommandError: If SSH command(s) required were not found.

    Returns:
      [str], the command args (where the first arg is the command itself).
    """
    env = env or Environment.Current()
    if not (env.ssh and env.ssh_term):
      raise MissingCommandError('The current environment lacks SSH.')

    tty = self.tty if self.tty in [True, False] else not self.remote_command
    args = [env.ssh_term, '-t'] if tty else [env.ssh, '-T']

    if self.port:
      port_flag = '-P' if env.suite is Suite.PUTTY else '-p'
      args.extend([port_flag, self.port])

    if self.cert_file:
      args.extend(['-o CertificateFile={}'.format(self.cert_file)])

    if self.identity_list:
      for identity_file in self.identity_list:
        args.extend(['-i', identity_file])
    elif self.identity_file:
      identity_file = self.identity_file
      if env.suite is Suite.PUTTY and not identity_file.endswith('.ppk'):
        identity_file += '.ppk'
      args.extend(['-i', identity_file])

    if env.suite is Suite.OPENSSH:
      # Always, always deterministic order
      for key, value in sorted(six.iteritems(self.options)):
        args.extend(['-o', '{k}={v}'.format(k=key, v=value)])

    args.extend(_BuildIapTunnelProxyCommandArgs(self.iap_tunnel_args, env))
    args.extend(self.extra_flags)
    if self.remote:
      args.append(self.remote.ToArg())

    # TODO(b/38179637): Remove when compute have separated flags from
    # positionals.
    if self.remainder:
      args.extend(self.remainder)

    if self.remote_command:
      if env.suite is Suite.OPENSSH:
        args.append('--')
        args.extend(self.remote_command)
      elif tty:
        # Unlike plink.exe, putty.exe doesn't support passing a remote command
        # with spaces on the command line; however the -m flag lets one pass in
        # a local file from which to read the remote command.
        with tempfile.NamedTemporaryFile(
            mode='w+t', delete=False
        ) as self._remote_command_file:
          self._remote_command_file.write(' '.join(self.remote_command))
        args.extend(['-m', self._remote_command_file.name])
      else:
        args.extend(self.remote_command)
    return args

  def Run(
      self,
      env=None,
      putty_force_connect=False,
      explicit_output_file=None,
      explicit_error_file=None,
      explicit_input_file=None,
  ):
    """Run the SSH command using the given environment.

    Args:
      env: Environment, environment to run in (or current if None).
      putty_force_connect: bool, whether to inject 'y' into the prompts for
        `plink`, which is insecure and not recommended. It serves legacy
        compatibility purposes for existing usages only; DO NOT SET THIS IN NEW
        CODE.
      explicit_output_file: Pipe stdout into this file-like object
      explicit_error_file: Pipe stderr into this file-like object
      explicit_input_file: Pipe stdin from this file-like object

    Raises:
      MissingCommandError: If SSH command(s) not found.
      CommandError: SSH command failed (not to be confused with the eventual
        failure of the remote command).

    Returns:
      int, The exit code of the remote command, forwarded from the client.
    """
    env = env or Environment.Current()
    args = self.Build(env)
    log.debug('Running command [{}].'.format(' '.join(args)))
    # PuTTY and friends always ask on fingerprint mismatch
    if env.suite is Suite.PUTTY and putty_force_connect:
      in_str = 'y\n'
    else:
      in_str = None

    # We pipe stdout to a specific file
    extra_popen_kwargs = {}
    if explicit_output_file:
      extra_popen_kwargs['stdout'] = explicit_output_file
    if explicit_error_file:
      extra_popen_kwargs['stderr'] = explicit_error_file
    if explicit_input_file:
      extra_popen_kwargs['stdin'] = explicit_input_file

    status = execution_utils.Exec(
        args, no_exit=True, in_str=in_str, **extra_popen_kwargs
    )

    # This should only happen if we're using putty.exe with a remote command. In
    # that case the file created earlier via NamedTemporaryFile has to be
    # deleted manually due to https://bugs.python.org/issue14243 on Windows.
    if self._remote_command_file:
      try:
        os.remove(self._remote_command_file.name)
      except OSError:
        # Not worth crashing over.
        log.debug(
            'Failed to delete remote command file [{}]'.format(
                self._remote_command_file.name
            )
        )
        pass

    if status == env.ssh_exit_code:
      raise CommandError(args[0], return_code=status)
    return status


class SCPCommand(object):
  """Represents a platform independent SCP command.

  This class is intended to manage the most important suite- and platform
  specifics. We manage the following data:
  - The executable to call, either `scp` or `pscp`.
  - User and host, through either `sources` or `destination` arg. Multiple
    remote sources are allowed but not supported under PuTTY. Multiple local
    sources are always allowed.
  - Potential remote command to execute, `remote_command` arg.

  In addition, it manages these flags:
  -r          Recursive copy
  -C          Compression
  -P          Port
  -i          Identity file (private key)
  -o Key=Val  OpenSSH specific options that should be added, `options` arg.

  For flexibility, SCPCommand also accepts `extra_flags`. Always use these
  with caution -- they will be added as-is to the command invocation without
  validation. Specifically, do not add any of the above mentioned flags.
  """

  def __init__(
      self,
      sources,
      destination,
      recursive=False,
      compress=False,
      port=None,
      identity_file=None,
      options=None,
      extra_flags=None,
      iap_tunnel_args=None,
      identity_list=None,
  ):
    """Construct a suite independent SCP command.

    Args:
      sources: [FileReference] or FileReference, the source(s) for this copy. At
        least one source is required. NOTE: Multiple remote sources are not
        supported in PuTTY and is discouraged for consistency.
      destination: FileReference, the destination file or directory. If remote
        source, this must be local, and vice versa.
      recursive: bool, recursive directory copy.
      compress: bool, enable compression.
      port: str, port.
      identity_file: str, path to private key file.
      options: {str: str}, options (`-o`) for OpenSSH, see `ssh_config(5)`.
      extra_flags: [str], extra flags to append to scp invocation. Both binary
        style flags `['-b']` and flags with values `['-k', 'v']` are accepted.
      iap_tunnel_args: iap_tunnel.SshTunnelArgs or None, options about IAP
        Tunnel.
      identity_list: list, A list of paths to private key files. Overrides the
        identity_file argument, and sets multiple `['-i']` flags.
    """
    self.sources = [sources] if isinstance(sources, FileReference) else sources
    self.destination = destination
    self.recursive = recursive
    self.compress = compress
    self.port = port
    self.identity_file = identity_file
    self.identity_list = identity_list
    self.options = options or {}
    self.extra_flags = extra_flags or []
    self.iap_tunnel_args = iap_tunnel_args

  @classmethod
  def Verify(cls, sources, destination, single_remote=False, env=None):
    """Verify that the source- and destination config is sound.

    Checks that sources are remote if destination is local and vice versa,
    plus raises error for multiple remote sources in PuTTY, which is not
    supported by `pscp`.

    Args:
      sources: [FileReference], see SCPCommand.sources.
      destination: FileReference, see SCPCommand.destination.
      single_remote: bool, if True, enforce that all remote sources refer to the
        same Remote (user and host).
      env: Environment, the current environment.

    Raises:
      InvalidConfigurationError: The source/destination configuration is
        invalid.
    """
    env = env or Environment.Current()

    if not sources:
      raise InvalidConfigurationError(
          'No sources provided.', sources, destination
      )

    if destination.remote:  # local -> remote
      if any([src.remote for src in sources]):
        raise InvalidConfigurationError(
            'All sources must be local files when destination is remote.',
            sources,
            destination,
        )
    else:  # remote -> local
      if env.suite is Suite.PUTTY and len(sources) != 1:
        raise InvalidConfigurationError(
            'Multiple remote sources not supported by PuTTY.',
            sources,
            destination,
        )
      if not all([src.remote for src in sources]):
        raise InvalidConfigurationError(
            'Source(s) must be remote when destination is local.',
            sources,
            destination,
        )
      if single_remote and len(set([src.remote for src in sources])) != 1:
        raise InvalidConfigurationError(
            'All sources must refer to the same remote when destination is '
            'local.',
            sources,
            destination,
        )

  def Build(self, env=None):
    """Construct the actual command according to the given environment.

    Args:
      env: Environment, to construct the command for (or current if None).

    Raises:
      InvalidConfigurationError: The source/destination configuration is
        invalid.
      MissingCommandError: If SCP command(s) required were not found.

    Returns:
      [str], the command args (where the first arg is the command itself).
    """
    env = env or Environment.Current()
    if not env.scp:
      raise MissingCommandError(
          'The current environment lacks an SCP (secure copy) client.'
      )
    self.Verify(self.sources, self.destination, env=env)

    args = [env.scp]

    if self.recursive:
      args.append('-r')

    if self.compress:
      args.append('-C')

    if self.port:
      args.extend(['-P', self.port])

    if self.identity_list:
      for identity_file in self.identity_list:
        args.extend(['-i', identity_file])
    elif self.identity_file:
      identity_file = self.identity_file
      if env.suite is Suite.PUTTY and not identity_file.endswith('.ppk'):
        identity_file += '.ppk'
      args.extend(['-i', identity_file])

    # SSH config options
    if env.suite is Suite.OPENSSH:
      # Always, always deterministic order
      for key, value in sorted(six.iteritems(self.options)):
        args.extend(['-o', '{k}={v}'.format(k=key, v=value)])

    args.extend(_BuildIapTunnelProxyCommandArgs(self.iap_tunnel_args, env))
    args.extend(self.extra_flags)

    # Positionals
    args.extend([source.ToArg() for source in self.sources])
    args.append(self.destination.ToArg())
    return args

  def Run(self, env=None, putty_force_connect=False):
    """Run the SCP command using the given environment.

    Args:
      env: Environment, environment to run in (or current if None).
      putty_force_connect: bool, whether to inject 'y' into the prompts for
        `pscp`, which is insecure and not recommended. It serves legacy
        compatibility purposes for existing usages only; DO NOT SET THIS IN NEW
        CODE.

    Raises:
      InvalidConfigurationError: The source/destination configuration is
        invalid.
      MissingCommandError: If SCP command(s) not found.
      CommandError: SCP command failed to copy the file(s).
    """
    env = env or Environment.Current()
    args = self.Build(env)
    log.debug('Running command [{}].'.format(' '.join(args)))
    # pscp asks on (1) first connection and (2) fingerprint mismatch.
    # This ensures pscp will always allow the connection.
    # TODO(b/35355795): Work out a better solution for PuTTY.
    if env.suite is Suite.PUTTY and putty_force_connect:
      in_str = 'y\n'
    else:
      in_str = None
    status = execution_utils.Exec(args, no_exit=True, in_str=in_str)
    if status:
      raise CommandError(args[0], return_code=status)


class SSHPoller(object):
  """Represents an SSH command that polls for connectivity.

  Using a poller is not ideal, because each attempt is a separate connection
  attempt, meaning that the user might be prompted for a passphrase or to
  approve a server identity by the underlying ssh tool that we do not control.
  Always assume that polling for connectivity using this method is an operation
  that requires user action.
  """

  def __init__(
      self,
      remote,
      port=None,
      identity_file=None,
      options=None,
      extra_flags=None,
      max_wait_ms=60 * 1000,
      sleep_ms=5 * 1000,
      iap_tunnel_args=None,
  ):
    """Construct a poller for an SSH connection.

    Args:
      remote: Remote, the remote to poll.
      port: str, port to poll.
      identity_file: str, path to private key file.
      options: {str: str}, options (`-o`) for OpenSSH, see `ssh_config(5)`.
      extra_flags: [str], extra flags to append to ssh invocation. Both binary
        style flags `['-b']` and flags with values `['-k', 'v']` are accepted.
      max_wait_ms: int, number of ms to wait before raising.
      sleep_ms: int, time between trials.
      iap_tunnel_args: iap_tunnel.SshTunnelArgs or None, information about IAP
        Tunnel.
    """
    self.ssh_command = SSHCommand(
        remote,
        port=port,
        identity_file=identity_file,
        options=options,
        extra_flags=extra_flags,
        remote_command=[':'],
        tty=False,
        iap_tunnel_args=iap_tunnel_args,
    )
    self._sleep_ms = sleep_ms
    self._retryer = retry.Retryer(max_wait_ms=max_wait_ms, jitter_ms=0)

  def Poll(self, env=None, putty_force_connect=False):
    """Poll a remote for connectivity within the given timeout.

    The SSH command may prompt the user. It is recommended to wrap this call in
    a progress tracker. If this method returns, a connection was successfully
    established. If not, this method will raise.

    Args:
      env: Environment, environment to run in (or current if None).
      putty_force_connect: bool, whether to inject 'y' into the prompts for
        `plink`, which is insecure and not recommended. It serves legacy
        compatibility purposes for existing usages only; DO NOT SET THIS IN NEW
        CODE.

    Raises:
      MissingCommandError: If SSH command(s) not found.
      core.retry.WaitException: SSH command failed, possibly due to short
        timeout. There is no way to distinguish between a timeout error and a
        misconfigured connection.
    """
    self._retryer.RetryOnException(
        self.ssh_command.Run,
        kwargs={'env': env, 'putty_force_connect': putty_force_connect},
        should_retry_if=lambda exc_type, *args: exc_type is CommandError,
        sleep_ms=self._sleep_ms,
    )


class FileReference(object):
  """A reference to a local or remote file (or directory) for SCP.

  Attributes:
    path: str, The path to the file.
    remote: Remote or None, the remote referred or None if local.
  """

  def __init__(self, path, remote=None):
    """Constructor for FileReference.

    Args:
      path: str, The path to the file.
      remote: Remote or None, the remote referred or None if local.
    """
    self.path = path
    self.remote = remote

  def ToArg(self):
    """Convert to a positional argument, in the form expected by `scp`/`pscp`.

    Returns:
      str, A string on the form `remote:path` if remote or `path` if local.
    """
    if not self.remote:
      return self.path
    return '{remote}:{path}'.format(remote=self.remote.ToArg(), path=self.path)

  @classmethod
  def FromPath(cls, path):
    """Convert an SCP-style positional argument to a file reference.

    Note that this method does not raise. No lookup of either local or remote
    file presence exists.

    Args:
      path: str, A path on the canonical scp form `[remote:]path`. If remote,
        `path` can be empty, e.g. `me@host:`.

    Returns:
      FileReference, the constructed object.
    """
    # If local drive given, it overrides a potential remote pattern match
    local_drive = os.path.splitdrive(path)[0]
    remote_arg, sep, file_path = path.partition(':')
    remote = Remote.FromArg(remote_arg) if sep else None
    if remote and not local_drive:
      return cls(path=file_path, remote=remote)
    else:
      return cls(path=path)

  def __eq__(self, other):
    return type(self) is type(other) and self.ToArg() == other.ToArg()

  def __ne__(self, other):
    return not self.__eq__(other)

  def __repr__(self):
    return self.ToArg()
