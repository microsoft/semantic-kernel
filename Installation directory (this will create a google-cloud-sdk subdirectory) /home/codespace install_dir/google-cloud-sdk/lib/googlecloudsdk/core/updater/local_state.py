# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Manages the state of what is installed in the cloud SDK.

This tracks the installed modules along with the files they created.  It also
provides functionality like extracting tar files into the installation and
tracking when we check for updates.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import compileall
import errno
import logging
import os
import posixpath
import re
import shutil
import sys

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.updater import installers
from googlecloudsdk.core.updater import snapshots
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files as file_utils

import six


class Error(exceptions.Error):
  """Base exception for the local_state module."""
  pass


class InvalidSDKRootError(Error):
  """Error for when the root of the Cloud SDK is invalid or cannot be found."""

  def __init__(self):
    super(InvalidSDKRootError, self).__init__(
        'The components management action could not be performed because the '
        'installation root of the Cloud SDK could not be located. '
        'If you previously used the Cloud SDK installer, '
        'you could re-install the SDK and retry again.')


class InvalidDownloadError(Error):
  """Exception for when the SDK that was download was invalid."""

  def __init__(self):
    super(InvalidDownloadError, self).__init__(
        'The Cloud SDK download was invalid.')


class PermissionsError(Error):
  """Error for when a file operation cannot complete due to permissions."""

  def __init__(self, message, path):
    """Initialize a PermissionsError.

    Args:
      message: str, The message from the underlying error.
      path: str, The absolute path to a file or directory that needs to be
          operated on, but can't because of insufficient permissions.
    """
    super(PermissionsError, self).__init__(
        '{message}: [{path}]\n\nEnsure you have the permissions to access the '
        'file and that the file is not in use.'
        .format(message=message, path=path))


def _RaisesPermissionsError(func):
  """Use this decorator for functions that deal with files.

  If an exception indicating file permissions is raised, this decorator will
  raise a PermissionsError instead, so that the caller only has to watch for
  one type of exception.

  Args:
    func: The function to decorate.

  Returns:
    A decorator.
  """

  def _TryFunc(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except shutil.Error as e:
      args = e.args[0][0]
      # unfortunately shutil.Error *only* has formatted strings to inspect.
      # Looking for this substring is looking for errno.EACCES, which has
      # a numeric value of 13.
      if args[2].startswith('[Errno 13]'):
        exceptions.reraise(
            PermissionsError(message=args[2],
                             path=os.path.abspath(args[0])))
      raise
    except (OSError, IOError) as e:
      if e.errno == errno.EACCES:
        exceptions.reraise(
            PermissionsError(
                message=encoding.Decode(e.strerror),
                path=encoding.Decode(os.path.abspath(e.filename))))
      raise
  return _TryFunc


class InstallationState(object):
  """The main class for checking / updating local installation state."""

  STATE_DIR_NAME = config.Paths.CLOUDSDK_STATE_DIR
  BACKUP_DIR_NAME = '.backup'
  TRASH_DIR_NAME = '.trash'
  STAGING_ROOT_SUFFIX = '.staging'
  COMPONENT_SNAPSHOT_FILE_SUFFIX = '.snapshot.json'
  DEPRECATED_DIRS = ('lib/third_party/grpc',)

  @staticmethod
  def ForCurrent():
    """Gets the installation state for the SDK that this code is running in.

    Returns:
      InstallationState, The state for this area.

    Raises:
      InvalidSDKRootError: If this code is not running under a valid SDK.
    """
    sdk_root = config.Paths().sdk_root
    if not sdk_root:
      raise InvalidSDKRootError()
    return InstallationState(os.path.realpath(sdk_root))

  def BackupInstallationState(self):
    """Gets the installation state for the backup of this  state, if it exists.

    Returns:
      InstallationState, The state for this area or None if the backup does not
          exist.
    """
    if not self.HasBackup():
      return None
    return InstallationState(os.path.realpath(self.__backup_directory))

  @staticmethod
  def VersionForInstalledComponent(component_id):
    """Gets the version string for the given installed component.

    This function is to be used to get component versions for metrics reporting.
    If it fails in any way or if the component_id is unknown, it will return
    None.  This prevents errors from surfacing when the version is needed
    strictly for reporting purposes.

    Args:
      component_id: str, The component id of the component you want the version
        for.

    Returns:
      str, The installed version of the component, or None if it is not
        installed or if an error occurs.
    """
    try:
      state = InstallationState.ForCurrent()
      # pylint: disable=protected-access, This is the same class.
      return InstallationManifest(
          state._state_directory, component_id).VersionString()
    # pylint: disable=bare-except, We never want to fail because of metrics.
    except:
      logging.debug('Failed to get installed version for component [%s]: [%s]',
                    component_id, sys.exc_info())
    return None

  @_RaisesPermissionsError
  def __init__(self, sdk_root):
    """Initializes the installation state for the given sdk install.

    Args:
      sdk_root: str, The file path of the root of the SDK installation.

    Raises:
      ValueError: If the given SDK root does not exist.
    """
    if not os.path.isdir(sdk_root):
      raise ValueError('The given Cloud SDK root does not exist: [{0}]'
                       .format(sdk_root))

    self.__sdk_root = encoding.Decode(sdk_root)
    self._state_directory = os.path.join(self.__sdk_root,
                                         InstallationState.STATE_DIR_NAME)
    self.__backup_directory = os.path.join(self._state_directory,
                                           InstallationState.BACKUP_DIR_NAME)
    self.__trash_directory = os.path.join(self._state_directory,
                                          InstallationState.TRASH_DIR_NAME)

    self.__sdk_staging_root = (os.path.normpath(self.__sdk_root) +
                               InstallationState.STAGING_ROOT_SUFFIX)

  @_RaisesPermissionsError
  def _CreateStateDir(self):
    """Creates the state directory if it does not exist."""
    if not os.path.isdir(self._state_directory):
      file_utils.MakeDir(self._state_directory)

  @property
  def sdk_root(self):
    """Gets the root of the SDK that this state corresponds to.

    Returns:
      str, the path to the root directory.
    """
    return self.__sdk_root

  def _FilesForSuffix(self, suffix):
    """Returns the files in the state directory that have the given suffix.

    Args:
      suffix: str, The file suffix to match on.

    Returns:
      list of str, The file names that match.
    """
    if not os.path.isdir(self._state_directory):
      return []

    files = os.listdir(self._state_directory)
    matching = [f for f in files
                if os.path.isfile(os.path.join(self._state_directory, f))
                and f.endswith(suffix)]
    return matching

  @_RaisesPermissionsError
  def InstalledComponents(self):
    """Gets all the components that are currently installed.

    Returns:
      A dictionary of component id string to InstallationManifest.
    """
    snapshot_files = self._FilesForSuffix(
        InstallationState.COMPONENT_SNAPSHOT_FILE_SUFFIX)
    manifests = {}
    for f in snapshot_files:
      component_id = f[:-len(InstallationState.COMPONENT_SNAPSHOT_FILE_SUFFIX)]
      manifests[component_id] = InstallationManifest(self._state_directory,
                                                     component_id)
    return manifests

  @_RaisesPermissionsError
  def Snapshot(self):
    """Generates a ComponentSnapshot from the currently installed components."""
    return snapshots.ComponentSnapshot.FromInstallState(self)

  def DiffCurrentState(self, latest_snapshot, platform_filter=None,):
    """Generates a ComponentSnapshotDiff from current state and the given state.

    Args:
      latest_snapshot:  snapshots.ComponentSnapshot, The current state of the
        world to diff against.
      platform_filter: platforms.Platform, A platform that components must
        match in order to be considered for any operations.

    Returns:
      A ComponentSnapshotDiff.
    """
    return self.Snapshot().CreateDiff(latest_snapshot,
                                      platform_filter=platform_filter)

  @_RaisesPermissionsError
  def CloneToStaging(self, progress_callback=None):
    """Clones this state to the temporary staging area.

    This is used for making temporary copies of the entire Cloud SDK
    installation when doing updates.  The entire installation is cloned, but
    doing so removes any backups and trash from this state before doing the
    copy.

    Args:
      progress_callback: f(float), A function to call with the fraction of
        completeness.

    Returns:
      An InstallationState object for the cloned install.
    """
    self._CreateStateDir()
    (rm_staging_cb, rm_backup_cb, rm_trash_cb, copy_cb) = (
        console_io.SplitProgressBar(progress_callback, [1, 1, 1, 7]))

    self._ClearStaging(progress_callback=rm_staging_cb)
    self.ClearBackup(progress_callback=rm_backup_cb)
    self.ClearTrash(progress_callback=rm_trash_cb)

    class Counter(object):

      def __init__(self, progress_callback, total):
        self.count = 0
        self.progress_callback = progress_callback
        self.total = total

      # This function must match the signature that shutil expects for the
      # ignore function.
      def Tick(self, *unused_args):
        self.count += 1
        self.progress_callback(self.count / self.total)
        return []

    if progress_callback:
      # This takes a little time, so only do it if we are going to report
      # progress.
      dirs = set()
      for _, manifest in six.iteritems(self.InstalledComponents()):
        dirs.update(manifest.InstalledDirectories())
      # There is always the root directory itself and the .install directory.
      # In general, there could be in the SDK (if people just put stuff in there
      # but this is fine for an estimate.  The progress bar will at worst stay
      # at 100% for slightly longer.
      total_dirs = len(dirs) + 2
      ticker = Counter(copy_cb, total_dirs).Tick if total_dirs else None
    else:
      ticker = None

    shutil.copytree(self.__sdk_root, self.__sdk_staging_root, symlinks=True,
                    ignore=ticker)
    staging_state = InstallationState(self.__sdk_staging_root)
    # pylint: disable=protected-access, This is an instance of InstallationState
    staging_state._CreateStateDir()
    return staging_state

  @_RaisesPermissionsError
  def CreateStagingFromDownload(self, url, progress_callback=None):
    """Creates a new staging area from a fresh download of the Cloud SDK.

    Args:
      url: str, The url to download the new SDK from.
      progress_callback: f(float), A function to call with the fraction of
        completeness.

    Returns:
      An InstallationState object for the new install.

    Raises:
      installers.URLFetchError: If the new SDK could not be downloaded.
      InvalidDownloadError: If the new SDK was malformed.
    """
    self._ClearStaging()

    with file_utils.TemporaryDirectory() as t:
      download_dir = os.path.join(t, '.download')
      extract_dir = os.path.join(t, '.extract')
      installers.DownloadAndExtractTar(
          url, download_dir, extract_dir, progress_callback=progress_callback,
          command_path='components.reinstall')
      files = os.listdir(extract_dir)
      if len(files) != 1:
        raise InvalidDownloadError()
      sdk_root = os.path.join(extract_dir, files[0])
      file_utils.MoveDir(sdk_root, self.__sdk_staging_root)

    staging_sdk = InstallationState(self.__sdk_staging_root)
    # pylint: disable=protected-access, This is an instance of InstallationState
    staging_sdk._CreateStateDir()
    self.CopyMachinePropertiesTo(staging_sdk)
    return staging_sdk

  @_RaisesPermissionsError
  def ReplaceWith(self, other_install_state, progress_callback=None):
    """Replaces this installation with the given other installation.

    This moves the current installation to the backup directory of the other
    installation.  Then, it moves the entire second installation to replace
    this one on the file system.  The result is that the other installation
    completely replaces the current one, but the current one is snapshotted and
    stored as a backup under the new one (and can be restored later).

    Args:
      other_install_state: InstallationState, The other state with which to
        replace this one.
      progress_callback: f(float), A function to call with the fraction of
        completeness.
    """
    self._CreateStateDir()
    self.ClearBackup()
    self.ClearTrash()
    # pylint: disable=protected-access, This is an instance of InstallationState
    other_install_state._CreateStateDir()
    other_install_state.ClearBackup()
    # pylint: disable=protected-access, This is an instance of InstallationState
    file_utils.MoveDir(self.__sdk_root, other_install_state.__backup_directory)
    if progress_callback:
      progress_callback(0.5)
    file_utils.MoveDir(other_install_state.__sdk_root, self.__sdk_root)
    if progress_callback:
      progress_callback(1.0)

  @_RaisesPermissionsError
  def RestoreBackup(self):
    """Restore the backup from this install state if it exists.

    If this installation has a backup stored in it (created by and update that
    used ReplaceWith(), above), it replaces this installation with the backup,
    using a temporary staging area.  This installation is moved to the trash
    directory under the installation that exists after this is done.  The trash
    directory can be removed at any point in the future.  We just don't want to
    delete code that is running since some platforms have a problem with that.

    Returns:
      bool, True if there was a backup to restore, False otherwise.
    """
    if not self.HasBackup():
      return False

    self._ClearStaging()

    file_utils.MoveDir(self.__backup_directory, self.__sdk_staging_root)
    staging_state = InstallationState(self.__sdk_staging_root)
    # pylint: disable=protected-access, This is an instance of InstallationState
    staging_state._CreateStateDir()
    staging_state.ClearTrash()
    # pylint: disable=protected-access, This is an instance of InstallationState
    file_utils.MoveDir(self.__sdk_root, staging_state.__trash_directory)
    file_utils.MoveDir(staging_state.__sdk_root, self.__sdk_root)
    return True

  def HasBackup(self):
    """Determines if this install has a valid backup that can be restored.

    Returns:
      bool, True if there is a backup, False otherwise.
    """
    return os.path.isdir(self.__backup_directory)

  def BackupDirectory(self):
    """Gets the backup directory of this installation if it exists.

    Returns:
      str, The path to the backup directory or None if it does not exist.
    """
    if self.HasBackup():
      return self.__backup_directory
    return None

  @_RaisesPermissionsError
  def _ClearStaging(self, progress_callback=None):
    """Deletes the current staging directory if it exists.

    Args:
      progress_callback: f(float), A function to call with the fraction of
        completeness.
    """
    if os.path.exists(self.__sdk_staging_root):
      file_utils.RmTree(self.__sdk_staging_root)
    if progress_callback:
      progress_callback(1)

  @_RaisesPermissionsError
  def ClearBackup(self, progress_callback=None):
    """Deletes the current backup if it exists.

    Args:
      progress_callback: f(float), A function to call with the fraction of
        completeness.
    """
    if os.path.isdir(self.__backup_directory):
      file_utils.RmTree(self.__backup_directory)
    if progress_callback:
      progress_callback(1)

  @_RaisesPermissionsError
  def ClearTrash(self, progress_callback=None):
    """Deletes the current trash directory if it exists.

    Args:
      progress_callback: f(float), A function to call with the fraction of
        completeness.
    """
    if os.path.isdir(self.__trash_directory):
      file_utils.RmTree(self.__trash_directory)
    if progress_callback:
      progress_callback(1)

  def _GetInstaller(self, snapshot):
    """Gets a component installer based on the given snapshot.

    Args:
      snapshot: snapshots.ComponentSnapshot, The snapshot that describes the
        component to install.

    Returns:
      The installers.ComponentInstaller.
    """
    return installers.ComponentInstaller(self.__sdk_root,
                                         self._state_directory,
                                         snapshot)

  @_RaisesPermissionsError
  def Install(self, snapshot, component_id, progress_callback=None,
              command_path='unknown'):
    """Installs the given component based on the given snapshot.

    Args:
      snapshot: snapshots.ComponentSnapshot, The snapshot that describes the
        component to install.
      component_id: str, The component to install from the given snapshot.
      progress_callback: f(float), A function to call with the fraction of
        completeness.
      command_path: the command path to include in the User-Agent header if the
        URL is HTTP

    Raises:
      installers.URLFetchError: If the component associated with the provided
        component ID has a URL that is not fetched correctly.
    """
    self._CreateStateDir()

    files = self._GetInstaller(snapshot).Install(
        component_id, progress_callback=progress_callback,
        command_path=command_path)
    manifest = InstallationManifest(self._state_directory, component_id)
    manifest.MarkInstalled(snapshot, files)

  @_RaisesPermissionsError
  def Uninstall(self, component_id, progress_callback=None):
    """Uninstalls the given component.

    Deletes all the files for this component and marks it as no longer being
    installed.

    Args:
      component_id: str, The id of the component to uninstall.
      progress_callback: f(float), A function to call with the fraction of
        completeness.
    """
    manifest = InstallationManifest(self._state_directory, component_id)
    paths = manifest.InstalledPaths()
    total_paths = len(paths)
    root = self.__sdk_root

    dirs_to_remove = set()
    pycache_dirs = set()
    for num, p in enumerate(paths, start=1):
      path = os.path.join(root, p)
      if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
        dir_path = os.path.dirname(os.path.normpath(p))
        if p.endswith('.py'):
          # Python 2 processes leave behind .pyc files adjacent to the .py file;
          # clean these up for any .py files being removed.
          pyc_path = path + 'c'
          if os.path.isfile(pyc_path):
            os.remove(pyc_path)
          # Python 3 processes leave behind __pycache__ folders in the .py
          # file's directory; clean these up as well. Since the .pyc files
          # within have different suffixes depending on the Python version, and
          # the version of Python that compiled the file may differ from the
          # current one running, it's faster to just delete the whole folder
          # later instead of trying to match the file(s) here.
          pycache_dirs.add(os.path.join(root, dir_path, '__pycache__'))
        while dir_path:
          dirs_to_remove.add(os.path.join(root, dir_path))
          dir_path = os.path.dirname(dir_path)
      elif os.path.isdir(path):
        dirs_to_remove.add(os.path.normpath(path))
      if progress_callback:
        progress_callback(num / total_paths)

    for d in pycache_dirs:
      if os.path.isdir(d) and not os.path.islink(d):
        file_utils.RmTree(d)

    # Remove dirs from the bottom up.  Subdirs will always have a longer path
    # than it's parent.
    for d in sorted(dirs_to_remove, key=len, reverse=True):
      if os.path.isdir(d) and not os.path.islink(d) and not os.listdir(d):
        os.rmdir(d)

    manifest.MarkUninstalled()

  @_RaisesPermissionsError
  def ClearDeprecatedDirs(self):
    """Clear deprecated directories that were not removed correctly."""
    for d in self.DEPRECATED_DIRS:
      path = os.path.join(self.sdk_root, d)
      if os.path.isdir(path):
        file_utils.RmTree(path)

  def CopyMachinePropertiesTo(self, other_state):
    """Copy this state's properties file to another state.

    This is primarily intended to be used to maintain the machine properties
    file during a schema-change-induced reinstall.

    Args:
      other_state: InstallationState, The installation state of the fresh
          Cloud SDK that needs the properties file mirrored in.
    """
    my_properties = os.path.join(
        self.sdk_root, config.Paths.CLOUDSDK_PROPERTIES_NAME)
    other_properties = os.path.join(
        other_state.sdk_root, config.Paths.CLOUDSDK_PROPERTIES_NAME)
    if not os.path.exists(my_properties):
      return
    shutil.copyfile(my_properties, other_properties)

  def CompilePythonFiles(self, force=False, workers=None):
    """Attempts to compile all the python files into .pyc files.

    Args:
      force: boolean, passed to force option of compileall.compiledir,
      workers: int, can be used to explicitly set number of worker processes;
        otherwise we determine it automatically. Only set for testing.

    This does not raise exceptions if compiling a given file fails.
    """
    # Some python code shipped in the SDK is not 2 + 3 compatible.
    # Create execlusion patterns to avoid compilation errors.
    # This is pretty hacky, ideally we would have this information in the
    # component metadata and derive the exclusion patterns from that.
    # However, this is an ok short-term solution until we have bundled python.
    if six.PY2:
      regex_exclusion = re.compile('(httplib2/python3|typing/python3'
                                   '|platform/bq/third_party/yaml/lib3'
                                   '|third_party/google/api_core'
                                   '|third_party/google/auth'
                                   '|third_party/google/oauth2'
                                   '|third_party/overrides'
                                   '|third_party/proto'
                                   '|dulwich'
                                   '|gapic'
                                   '|pubsublite'
                                   '|pubsub/lite_subscriptions.py'
                                   '|logging_v2'
                                   '|platform/bundledpythonunix'
                                   '|pubsub_v1/services)')
    else:
      # Do not compile anything on python 3.4.x
      if sys.version_info[1] == 4:
        regex_exclusion = re.compile('.*')
      elif sys.version_info[1] >= 7:
        regex_exclusion = re.compile(
            '(kubernetes/utils/create_from_yaml.py'
            '|platform/google_appengine'
            '|gslib/vendored/boto/boto/iam/connection.py'
            '|gslib/vendored/boto/tests/'
            '|third_party/.*/python2/'
            '|third_party/yaml/[a-z]*.py'
            '|third_party/yaml/lib2/'
            '|third_party/appengine/'
            '|third_party/fancy_urllib/'
            '|platform/bq/third_party/gflags'
            '|platform/ext-runtime/nodejs/test/'
            '|platform/gsutil/third_party/apitools/ez_setup'
            '|platform/gsutil/third_party/crcmod_osx/crcmod/test)')
      else:
        regex_exclusion = None

    # The self.sdk_root pathname could contain unicode chars and py_compile
    # chokes on unicode paths. Using relative paths from self.sdk_root works
    # around the problem.
    with file_utils.ChDir(self.sdk_root):
      to_compile = [
          os.path.join('bin', 'bootstrapping'),
          os.path.join('data', 'cli'),
          'lib',
          'platform',
      ]
      # There are diminishing returns to using more worker processes past a
      # certain point, so we cap it to a reasonable amount here.
      num_workers = min(os.cpu_count(), 8) if workers is None else workers
      for d in to_compile:
        # Using 2 for quiet, in python 2.7 this value is used as a bool in the
        # implementation and bool(2) is True. Starting in python 3.5 this
        # parameter was changed to a multilevel value, where 1 hides files
        # being processed and 2 suppresses output.
        compileall.compile_dir(
            d, rx=regex_exclusion, quiet=2, force=force, workers=num_workers)


class InstallationManifest(object):
  """Class to encapsulate the data stored in installation manifest files."""

  MANIFEST_SUFFIX = '.manifest'

  def __init__(self, state_dir, component_id):
    """Creates a new InstallationManifest.

    Args:
      state_dir: str, The directory path where install state is stored.
      component_id: str, The component id that you want to get the manifest for.
    """
    self.state_dir = state_dir
    self.id = component_id
    self.snapshot_file = os.path.join(
        self.state_dir,
        component_id + InstallationState.COMPONENT_SNAPSHOT_FILE_SUFFIX)
    self.manifest_file = os.path.join(
        self.state_dir,
        component_id + InstallationManifest.MANIFEST_SUFFIX)

  def MarkInstalled(self, snapshot, files):
    """Marks this component as installed with the given snapshot and files.

    This saves the ComponentSnapshot and writes the installed files to a
    manifest so they can be removed later.

    Args:
      snapshot: snapshots.ComponentSnapshot, The snapshot that was the source
        of the install.
      files: list of str, The files that were created by the installation.
    """
    with file_utils.FileWriter(self.manifest_file) as fp:
      for f in _NormalizeFileList(files):
        fp.write(f + '\n')
    snapshot.WriteToFile(self.snapshot_file, component_id=self.id)

  def MarkUninstalled(self):
    """Marks this component as no longer being installed.

    This does not actually uninstall the component, but rather just removes the
    snapshot and manifest.
    """
    for f in [self.manifest_file, self.snapshot_file]:
      if os.path.isfile(f):
        os.remove(f)

  def ComponentSnapshot(self):
    """Loads the local ComponentSnapshot for this component.

    Returns:
      The snapshots.ComponentSnapshot for this component.
    """
    return snapshots.ComponentSnapshot.FromFile(self.snapshot_file)

  def ComponentDefinition(self):
    """Loads the ComponentSnapshot and get the schemas.Component this component.

    Returns:
      The schemas.Component for this component.
    """
    return self.ComponentSnapshot().ComponentFromId(self.id)

  def VersionString(self):
    """Gets the version string of this component as it was installed.

    Returns:
      str, The installed version of this component.
    """
    return self.ComponentDefinition().version.version_string

  def InstalledPaths(self):
    """Gets the list of files and dirs created by installing this component.

    Returns:
      list of str, The files and directories installed by this component.
    """
    with file_utils.FileReader(self.manifest_file) as f:
      files = [line.rstrip() for line in f]
    return files

  def InstalledDirectories(self):
    """Gets the set of directories created by installing this component.

    Returns:
      set(str), The directories installed by this component.
    """
    with file_utils.FileReader(self.manifest_file) as f:
      dirs = set()
      for line in f:
        norm_file_path = os.path.dirname(line.rstrip())
        prev_file = norm_file_path + '/'
        while len(prev_file) > len(norm_file_path) and norm_file_path:
          dirs.add(norm_file_path)
          prev_file = norm_file_path
          norm_file_path = os.path.dirname(norm_file_path)

    return dirs


def _NormalizeFileList(file_list):
  """Removes non-empty directory entries and sorts resulting list."""
  parent_directories = set([])
  directories = set([])
  files = set([])
  for f in file_list:
    # Drops any trailing /.
    norm_file_path = posixpath.normpath(f)
    if f.endswith('/'):
      directories.add(norm_file_path + '/')
    else:
      files.add(norm_file_path)
    norm_file_path = os.path.dirname(norm_file_path)
    while norm_file_path:
      parent_directories.add(norm_file_path + '/')
      norm_file_path = os.path.dirname(norm_file_path)

  return sorted((directories - parent_directories) | files)
