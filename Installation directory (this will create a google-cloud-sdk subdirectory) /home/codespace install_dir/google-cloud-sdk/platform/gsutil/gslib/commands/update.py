# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Implementation of update command for updating gsutil."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import shutil
import signal
import stat
import sys
import tarfile
import tempfile
import textwrap

from six.moves import input
import gslib
from gslib.command import Command
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.metrics import CheckAndMaybePromptForAnalyticsEnabling
from gslib.sig_handling import RegisterSignalHandler
from gslib.utils import system_util
from gslib.utils.boto_util import GetConfigFilePaths
from gslib.utils.boto_util import CERTIFICATE_VALIDATION_ENABLED
from gslib.utils.constants import RELEASE_NOTES_URL
from gslib.utils.text_util import CompareVersions
from gslib.utils.update_util import DisallowUpdateIfDataInGsutilDir
from gslib.utils.update_util import LookUpGsutilVersion
from gslib.utils.update_util import GsutilPubTarball

_SYNOPSIS = """
  gsutil update [-f] [-n] [url]
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  NOTE: This command is not available if you're using a gsutil installation
  from a package manager or the Cloud SDK. When using the Cloud SDK, use
  ``gcloud components update``.

  The gsutil update command downloads the latest gsutil release, checks its
  version, and offers to let you update to it if it differs from the version
  you're currently running.

  Once you say "Y" to the prompt of whether to install the update, the gsutil
  update command locates where the running copy of gsutil is installed,
  unpacks the new version into an adjacent directory, moves the previous version
  aside, moves the new version to where the previous version was installed,
  and removes the moved-aside old version. Because of this, users are cautioned
  not to store data in the gsutil directory, since that data will be lost
  when you update gsutil. (Some users change directories into the gsutil
  directory to run the command. We advise against doing that, for this reason.)
  Note also that the gsutil update command will refuse to run if it finds user
  data in the gsutil directory.

  By default gsutil update will retrieve the new code from
  %s, but you can optionally specify a URL to use
  instead. This is primarily used for distributing pre-release versions of
  the code to a small group of early test users.

  NOTE: gsutil periodically checks whether a more recent software update is
  available. By default this check is performed every 30 days; you can change
  (or disable) this check by editing the software_update_check_period variable
  in the .boto config file. Note also that gsutil will only check for software
  updates if stdin, stdout, and stderr are all connected to a TTY, to avoid
  interfering with cron jobs, streaming transfers, and other cases where gsutil
  input or output are redirected from/to files or pipes. Software update
  periodic checks are also disabled by the gsutil -q option (see
  'gsutil help options')


<B>OPTIONS</B>
  -f          Forces the update command to offer to let you update, even if you
              have the most current copy already. This can be useful if you have
              a corrupted local copy.

  -n          Causes update command to run without prompting [Y/n] whether to
              continue if an update is available.
""" % GsutilPubTarball())


class UpdateCommand(Command):
  """Implementation of gsutil update command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'update',
      command_name_aliases=['refresh'],
      usage_synopsis=_SYNOPSIS,
      min_args=0,
      max_args=1,
      supported_sub_args='fn',
      file_url_ok=True,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='update',
      help_name_aliases=['refresh'],
      help_type='command_help',
      help_one_line_summary='Update to the latest gsutil release',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  def _ExplainIfSudoNeeded(self, tf, dirs_to_remove, old_cwd):
    """Explains what to do if sudo needed to update gsutil software.

    Happens if gsutil was previously installed by a different user (typically if
    someone originally installed in a shared file system location, using sudo).

    Args:
      tf: Opened TarFile.
      dirs_to_remove: List of directories to remove.
      old_cwd: Path to the working directory we should chdir back to if sudo is
          needed. It's possible that we've chdir'd to a temp directory that's
          been deleted, which can cause odd behavior (e.g. OSErrors when opening
          the metrics subprocess). If this is not truthy, we won't attempt to
          chdir back to this value.

    Raises:
      CommandException: if errors encountered.
    """
    # If running under Windows or Cygwin we don't need (or have) sudo.
    if system_util.IS_CYGWIN or system_util.IS_WINDOWS:
      return

    user_id = os.getuid()
    if os.stat(gslib.GSUTIL_DIR).st_uid == user_id:
      return

    # Won't fail - this command runs after main startup code that insists on
    # having a config file.
    config_file_list = GetConfigFilePaths()
    config_files = ' '.join(config_file_list)
    self._CleanUpUpdateCommand(tf, dirs_to_remove, old_cwd)

    # Pick current protection of each boto config file for command that restores
    # protection (rather than fixing at 600) to support use cases like how GCE
    # installs a service account with an /etc/boto.cfg file protected to 644.
    chmod_cmds = []
    for config_file in config_file_list:
      mode = oct(stat.S_IMODE((os.stat(config_file)[stat.ST_MODE])))
      chmod_cmds.append('\n\tsudo chmod %s %s' % (mode, config_file))

    raise CommandException('\n'.join(
        textwrap.wrap(
            'Since it was installed by a different user previously, you will need '
            'to update using the following commands. You will be prompted for your '
            'password, and the install will run as "root". If you\'re unsure what '
            'this means please ask your system administrator for help:')) + (
                '\n\tsudo chmod 0644 %s\n\tsudo env BOTO_CONFIG="%s" %s update'
                '%s') % (config_files, config_files, self.gsutil_path,
                         ' '.join(chmod_cmds)),
                           informational=True)

  # This list is checked during gsutil update by doing a lowercased
  # slash-left-stripped check. For example "/Dev" would match the "dev" entry.
  unsafe_update_dirs = [
      'applications',
      'auto',
      'bin',
      'boot',
      'desktop',
      'dev',
      'documents and settings',
      'etc',
      'export',
      'home',
      'kernel',
      'lib',
      'lib32',
      'library',
      'lost+found',
      'mach_kernel',
      'media',
      'mnt',
      'net',
      'null',
      'network',
      'opt',
      'private',
      'proc',
      'program files',
      'python',
      'root',
      'sbin',
      'scripts',
      'srv',
      'sys',
      'system',
      'tmp',
      'users',
      'usr',
      'var',
      'volumes',
      'win',
      'win32',
      'windows',
      'winnt',
  ]

  def _EnsureDirsSafeForUpdate(self, dirs):
    """Raises Exception if any of dirs is known to be unsafe for gsutil update.

    This provides a fail-safe check to ensure we don't try to overwrite
    or delete any important directories. (That shouldn't happen given the
    way we construct tmp dirs, etc., but since the gsutil update cleanup
    uses shutil.rmtree() it's prudent to add extra checks.)

    Args:
      dirs: List of directories to check.

    Raises:
      CommandException: If unsafe directory encountered.
    """
    for d in dirs:
      if not d:
        d = 'null'
      if d.lstrip(os.sep).lower() in self.unsafe_update_dirs:
        raise CommandException('EnsureDirsSafeForUpdate: encountered unsafe '
                               'directory (%s); aborting update' % d)

  def _CleanUpUpdateCommand(self, tf, dirs_to_remove, old_cwd):
    """Cleans up temp files etc. from running update command.

    Args:
      tf: Opened TarFile, or None if none currently open.
      dirs_to_remove: List of directories to remove.
      old_cwd: Path to the working directory we should chdir back to. It's
          possible that we've chdir'd to a temp directory that's been deleted,
          which can cause odd behavior (e.g. OSErrors when opening the metrics
          subprocess). If this is not truthy, we won't attempt to chdir back
          to this value.
    """
    if tf:
      tf.close()
    self._EnsureDirsSafeForUpdate(dirs_to_remove)
    for directory in dirs_to_remove:
      try:
        shutil.rmtree(directory)
      except OSError:
        # Ignore errors while attempting to remove old dirs under Windows. They
        # happen because of Windows exclusive file locking, and the update
        # actually succeeds but just leaves the old versions around in the
        # user's temp dir.
        if not system_util.IS_WINDOWS:
          raise
    if old_cwd:
      try:
        os.chdir(old_cwd)
      except OSError:
        pass

  def RunCommand(self):
    """Command entry point for the update command."""

    if gslib.IS_PACKAGE_INSTALL:
      raise CommandException(
          'The update command is only available for gsutil installed from a '
          'tarball. If you installed gsutil via another method, use the same '
          'method to update it.')

    if system_util.InvokedViaCloudSdk():
      raise CommandException(
          'The update command is disabled for Cloud SDK installs. Please run '
          '"gcloud components update" to update it. Note: the Cloud SDK '
          'incorporates updates to the underlying tools approximately every 2 '
          'weeks, so if you are attempting to update to a recently created '
          'release / pre-release of gsutil it may not yet be available via '
          'the Cloud SDK.')

    https_validate_certificates = CERTIFICATE_VALIDATION_ENABLED
    if not https_validate_certificates:
      raise CommandException(
          'Your boto configuration has https_validate_certificates = False.\n'
          'The update command cannot be run this way, for security reasons.')

    DisallowUpdateIfDataInGsutilDir()

    force_update = False
    no_prompt = False
    if self.sub_opts:
      for o, unused_a in self.sub_opts:
        if o == '-f':
          force_update = True
        if o == '-n':
          no_prompt = True

    dirs_to_remove = []
    tmp_dir = tempfile.mkdtemp()
    dirs_to_remove.append(tmp_dir)
    old_cwd = os.getcwd()
    os.chdir(tmp_dir)

    if not no_prompt:
      self.logger.info('Checking for software update...')
    if self.args:
      update_from_url_str = self.args[0]
      if not update_from_url_str.endswith('.tar.gz'):
        raise CommandException(
            'The update command only works with tar.gz files.')
      for i, result in enumerate(self.WildcardIterator(update_from_url_str)):
        if i > 0:
          raise CommandException(
              'Invalid update URL. Must name a single .tar.gz file.')
        storage_url = result.storage_url
        if storage_url.IsFileUrl() and not storage_url.IsDirectory():
          if not force_update:
            raise CommandException(
                ('"update" command does not support "file://" URLs without the '
                 '-f option.'))
        elif not (storage_url.IsCloudUrl() and storage_url.IsObject()):
          raise CommandException(
              'Invalid update object URL. Must name a single .tar.gz file.')
    else:
      update_from_url_str = GsutilPubTarball()

    # Try to retrieve version info from tarball metadata; failing that; download
    # the tarball and extract the VERSION file. The version lookup will fail
    # when running the update system test, because it retrieves the tarball from
    # a temp file rather than a cloud URL (files lack the version metadata).
    tarball_version = LookUpGsutilVersion(self.gsutil_api, update_from_url_str)
    if tarball_version:
      tf = None
    else:
      tf = self._FetchAndOpenGsutilTarball(update_from_url_str)
      tf.extractall()
      with open(os.path.join('gsutil', 'VERSION'), 'r') as ver_file:
        tarball_version = ver_file.read().strip()

    if not force_update and gslib.VERSION == tarball_version:
      self._CleanUpUpdateCommand(tf, dirs_to_remove, old_cwd)
      if self.args:
        raise CommandException('You already have %s installed.' %
                               update_from_url_str,
                               informational=True)
      else:
        raise CommandException(
            'You already have the latest gsutil release '
            'installed.',
            informational=True)

    if not no_prompt:
      CheckAndMaybePromptForAnalyticsEnabling()
      (_, major) = CompareVersions(tarball_version, gslib.VERSION)
      if major:
        print(('\n'.join(
            textwrap.wrap(
                'This command will update to the "%s" version of gsutil at %s. '
                'NOTE: This a major new version, so it is strongly recommended '
                'that you review the release note details at %s before updating to '
                'this version, especially if you use gsutil in scripts.' %
                (tarball_version, gslib.GSUTIL_DIR, RELEASE_NOTES_URL)))))
      else:
        print(('This command will update to the "%s" version of\ngsutil at %s' %
               (tarball_version, gslib.GSUTIL_DIR)))
    self._ExplainIfSudoNeeded(tf, dirs_to_remove, old_cwd)

    if no_prompt:
      answer = 'y'
    else:
      answer = input('Proceed? [y/N] ')
    if not answer or answer.lower()[0] != 'y':
      self._CleanUpUpdateCommand(tf, dirs_to_remove, old_cwd)
      raise CommandException('Not running update.', informational=True)

    if not tf:
      tf = self._FetchAndOpenGsutilTarball(update_from_url_str)

    # Ignore keyboard interrupts during the update to reduce the chance someone
    # hitting ^C leaves gsutil in a broken state.
    RegisterSignalHandler(signal.SIGINT, signal.SIG_IGN)

    # gslib.GSUTIL_DIR lists the path where the code should end up (like
    # /usr/local/gsutil), which is one level down from the relative path in the
    # tarball (since the latter creates files in ./gsutil). So, we need to
    # extract at the parent directory level.
    gsutil_bin_parent_dir = os.path.normpath(
        os.path.join(gslib.GSUTIL_DIR, '..'))

    # Extract tarball to a temporary directory in a sibling to GSUTIL_DIR.
    old_dir = tempfile.mkdtemp(dir=gsutil_bin_parent_dir)
    new_dir = tempfile.mkdtemp(dir=gsutil_bin_parent_dir)
    dirs_to_remove.append(old_dir)
    dirs_to_remove.append(new_dir)
    self._EnsureDirsSafeForUpdate(dirs_to_remove)
    try:
      tf.extractall(path=new_dir)
    except Exception as e:
      self._CleanUpUpdateCommand(tf, dirs_to_remove, old_cwd)
      raise CommandException('Update failed: %s.' % e)

    # For enterprise mode (shared/central) installation, users with
    # different user/group than the installation user/group must be
    # able to run gsutil so we need to do some permissions adjustments
    # here. Since enterprise mode is not not supported for Windows
    # users, we can skip this step when running on Windows, which
    # avoids the problem that Windows has no find or xargs command.
    if not system_util.IS_WINDOWS:
      # Make all files and dirs in updated area owner-RW and world-R, and make
      # all directories owner-RWX and world-RX.
      for dirname, subdirs, filenames in os.walk(new_dir):
        for filename in filenames:
          fd = os.open(os.path.join(dirname, filename), os.O_RDONLY)
          os.fchmod(fd,
                    stat.S_IWRITE | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
          os.close(fd)
        for subdir in subdirs:
          fd = os.open(os.path.join(dirname, subdir), os.O_RDONLY)
          os.fchmod(
              fd, stat.S_IRWXU | stat.S_IXGRP | stat.S_IXOTH | stat.S_IRGRP |
              stat.S_IROTH)
          os.close(fd)

      # Make main gsutil script owner-RWX and world-RX.
      fd = os.open(os.path.join(new_dir, 'gsutil', 'gsutil'), os.O_RDONLY)
      os.fchmod(
          fd, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH |
          stat.S_IXOTH)
      os.close(fd)

    # Move old installation aside and new into place.
    os.rename(gslib.GSUTIL_DIR, os.path.join(old_dir, 'old'))
    os.rename(os.path.join(new_dir, 'gsutil'), gslib.GSUTIL_DIR)
    self._CleanUpUpdateCommand(tf, dirs_to_remove, old_cwd)
    RegisterSignalHandler(signal.SIGINT, signal.SIG_DFL)
    self.logger.info('Update complete.')
    return 0

  def _FetchAndOpenGsutilTarball(self, update_from_url_str):
    self.command_runner.RunNamedCommand(
        'cp',
        [update_from_url_str, 'file://gsutil.tar.gz'],
        self.headers,
        self.debug,
        skip_update_check=True,
    )
    # Note: tf is closed in _CleanUpUpdateCommand.
    tf = tarfile.open('gsutil.tar.gz')
    tf.errorlevel = 1  # So fatal tarball unpack errors raise exceptions.
    return tf
