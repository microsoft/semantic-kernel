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
"""Utilities for job submission preparation.

The main entry point is UploadPythonPackages, which takes in parameters derived
from the command line arguments and returns a list of URLs to be given to the
AI Platform API. See its docstring for details.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import collections
import contextlib
import io
import os
import sys
import textwrap

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.ml_engine import uploads
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
import six
from six.moves import map


DEFAULT_SETUP_FILE = """\
from setuptools import setup, find_packages

if __name__ == '__main__':
    setup(
        name='{package_name}',
        packages=find_packages(include=['{package_name}'])
    )
"""


class UploadFailureError(exceptions.Error):
  """Generic error with the packaging/upload process."""
  pass


class SetuptoolsFailedError(UploadFailureError):
  """Error indicating that setuptools itself failed."""

  def __init__(self, output, generated):
    msg = ('Packaging of user Python code failed with message:\n\n'
           '{}\n\n').format(output)
    if generated:
      msg += ('Try manually writing a setup.py file at your package root and '
              'rerunning the command.')
    else:
      msg += ('Try manually building your Python code by running:\n'
              '  $ python setup.py sdist\n'
              'and providing the output via the `--packages` flag (for '
              'example, `--packages dist/package.tar.gz,dist/package2.whl)`')
    super(SetuptoolsFailedError, self).__init__(msg)


class SysExecutableMissingError(UploadFailureError):
  """Error indicating that sys.executable was empty."""

  def __init__(self):
    super(SysExecutableMissingError, self).__init__(
        textwrap.dedent("""\
        No Python executable found on path. A Python executable with setuptools
        installed on the PYTHONPATH is required for building AI Platform training jobs.
        """))


class MissingInitError(UploadFailureError):
  """Error indicating that the package to build had no __init__.py file."""

  def __init__(self, package_dir):
    super(MissingInitError, self).__init__(textwrap.dedent("""\
        [{}] is not a valid Python package because it does not contain an \
        `__init__.py` file. Please create one and try again. Also, please \
        ensure that --package-path refers to a local directory.
        """).format(package_dir))


class UncopyablePackageError(UploadFailureError):
  """Error with copying the package."""


class DuplicateEntriesError(UploadFailureError):
  """Error indicating that multiple files with the same name were provided."""

  def __init__(self, duplicates):
    super(DuplicateEntriesError, self).__init__(
        'Cannot upload multiple packages with the same filename: [{}]'.format(
            ', '.join(duplicates)))


class NoStagingLocationError(UploadFailureError):
  """No staging location was provided but one was required."""


class InvalidSourceDirError(UploadFailureError):
  """Error indicating that the source directory is invalid."""

  def __init__(self, source_dir):
    super(InvalidSourceDirError, self).__init__(
        'Source directory [{}] is not a valid directory.'.format(source_dir))


def _CopyIfNotWritable(source_dir, temp_dir):
  """Returns a writable directory with the same contents as source_dir.

  If source_dir is writable, it is used. Otherwise, a directory 'dest' inside of
  temp_dir is used.

  Args:
    source_dir: str, the directory to (potentially) copy
    temp_dir: str, the path to a writable temporary directory in which to store
      any copied code.

  Returns:
    str, the path to a writable directory with the same contents as source_dir
      (i.e. source_dir, if it's writable, or a copy otherwise).

  Raises:
    UploadFailureError: if the command exits non-zero.
    InvalidSourceDirError: if the source directory is not valid.
  """
  if not os.path.isdir(source_dir):
    raise InvalidSourceDirError(source_dir)
  # A race condition may cause a ValueError while checking for write access
  # even if the directory was valid before.
  try:
    writable = files.HasWriteAccessInDir(source_dir)
  except ValueError:
    raise InvalidSourceDirError(source_dir)

  if writable:
    return source_dir

  if files.IsDirAncestorOf(source_dir, temp_dir):
    raise UncopyablePackageError(
        'Cannot copy directory since working directory [{}] is inside of '
        'source directory [{}].'.format(temp_dir, source_dir))

  dest_dir = os.path.join(temp_dir, 'dest')
  log.debug('Copying local source tree from [%s] to [%s]', source_dir, dest_dir)
  try:
    files.CopyTree(source_dir, dest_dir)
  except OSError:
    raise UncopyablePackageError(
        'Cannot write to working location [{}]'.format(dest_dir))
  return dest_dir


def _GenerateSetupPyIfNeeded(setup_py_path, package_name):
  """Generates a temporary setup.py file if there is none at the given path.

  Args:
    setup_py_path: str, a path to the expected setup.py location.
    package_name: str, the name of the Python package for which to write a
      setup.py file (used in the generated file contents).

  Returns:
    bool, whether the setup.py file was generated.
  """
  log.debug('Looking for setup.py file at [%s]', setup_py_path)
  if os.path.isfile(setup_py_path):
    log.info('Using existing setup.py file at [%s]', setup_py_path)
    return False

  setup_contents = DEFAULT_SETUP_FILE.format(package_name=package_name)
  log.info('Generating temporary setup.py file:\n%s', setup_contents)
  files.WriteFileContents(setup_py_path, setup_contents)
  return True


@contextlib.contextmanager
def _TempDirOrBackup(default_dir):
  """Yields a temporary directory or a backup temporary directory.

  Prefers creating a temporary directory (which will be cleaned up when the
  context manager is closed), but falls back to default_dir. There are systems
  where users can't write to temp, but we still need to copy.

  Args:
    default_dir: str, the backup temporary directory.

  Yields:
    str, the temporary directory.
  """
  try:
    temp_dir = files.TemporaryDirectory()
    # We can't use the context manager form of files.TemporaryDirectory()
    # because it makes it hard to distinguish between an OSError that occurred
    # during the creation of the temporary directory and one that occurred in
    # the middle of *this* context manager's body.
    path = temp_dir.__enter__()
  except OSError:
    temp_dir = None
    # Some systems don't allow access to '/tmp'
    path = default_dir

  try:
    yield path
  finally:
    if temp_dir:
      temp_dir.__exit__(*sys.exc_info())


class _SetupPyCommand(six.with_metaclass(abc.ABCMeta, object)):
  """A command to run setup.py in a given environment.

  Includes the Python version to use and the arguments with which to run
  setup.py.

  Attributes:
    setup_py_path: str, the path to the setup.py file
    setup_py_args: list of str, the arguments with which to call setup.py
    package_root: str, path to the directory containing the package to build
      (must be writable, or setuptools will fail)
  """

  def __init__(self, setup_py_path, setup_py_args, package_root):
    self.setup_py_path = setup_py_path
    self.setup_py_args = setup_py_args
    self.package_root = package_root

  @abc.abstractmethod
  def GetArgs(self):
    """Returns arguments to use for execution (including Python executable)."""
    raise NotImplementedError()

  @abc.abstractmethod
  def GetEnv(self):
    """Returns the environment dictionary to use for Python execution."""
    raise NotImplementedError()

  def Execute(self, out):
    """Run the configured setup.py command.

    Args:
      out: a stream to which the command output should be written.

    Returns:
      int, the return code of the command.
    """
    return execution_utils.Exec(
        self.GetArgs(),
        no_exit=True, out_func=out.write, err_func=out.write,
        cwd=self.package_root, env=self.GetEnv())


class _CloudSdkPythonSetupPyCommand(_SetupPyCommand):
  """A command that uses the Cloud SDK Python environment.

  It uses the same OS environment, plus the same PYTHONPATH.

  This is preferred, since it's more controlled.
  """

  def GetArgs(self):
    return execution_utils.ArgsForPythonTool(self.setup_py_path,
                                             *self.setup_py_args,
                                             python=GetPythonExecutable())

  def GetEnv(self):
    exec_env = os.environ.copy()
    exec_env['PYTHONPATH'] = os.pathsep.join(sys.path)
    return exec_env


class _SystemPythonSetupPyCommand(_SetupPyCommand):
  """A command that uses the system Python environment.

  Uses the same executable as the Cloud SDK.

  Important in case of e.g. a setup.py file that has non-stdlib dependencies.
  """

  def GetArgs(self):
    return [GetPythonExecutable(), self.setup_py_path] + self.setup_py_args

  def GetEnv(self):
    return None


def GetPythonExecutable():
  python_executable = None
  try:
    python_executable = execution_utils.GetPythonExecutable()
  except ValueError:
    raise SysExecutableMissingError()
  return python_executable


def _RunSetupTools(package_root, setup_py_path, output_dir):
  """Executes the setuptools `sdist` command.

  Specifically, runs `python setup.py sdist` (with the full path to `setup.py`
  given by setup_py_path) with arguments to put the final output in output_dir
  and all possible temporary files in a temporary directory. package_root is
  used as the working directory.

  May attempt to run setup.py multiple times with different
  environments/commands if any execution fails:

  1. Using the Cloud SDK Python environment, with a full setuptools invocation
     (`egg_info`, `build`, and `sdist`).
  2. Using the system Python environment, with a full setuptools invocation
     (`egg_info`, `build`, and `sdist`).
  3. Using the Cloud SDK Python environment, with an intermediate setuptools
     invocation (`build` and `sdist`).
  4. Using the system Python environment, with an intermediate setuptools
     invocation (`build` and `sdist`).
  5. Using the Cloud SDK Python environment, with a simple setuptools
     invocation which will also work for plain distutils-based setup.py (just
     `sdist`).
  6. Using the system Python environment, with a simple setuptools
     invocation which will also work for plain distutils-based setup.py (just
     `sdist`).

  The reason for this order is that it prefers first the setup.py invocations
  which leave the fewest files on disk. Then, we prefer the Cloud SDK execution
  environment as it will be the most stable.

  package_root must be writable, or setuptools will fail (there are
  temporary files from setuptools that get put in the CWD).

  Args:
    package_root: str, the directory containing the package (that is, the
      *parent* of the package itself).
    setup_py_path: str, the path to the `setup.py` file to execute.
    output_dir: str, path to a directory in which the built packages should be
      created.

  Returns:
    list of str, the full paths to the generated packages.

  Raises:
    SysExecutableMissingError: if sys.executable is None
    RuntimeError: if the execution of setuptools exited non-zero.
  """
  # Unfortunately, there doesn't seem to be any easy way to move *all*
  # temporary files out of the current directory, so we'll fail here if we
  # can't write to it.
  with _TempDirOrBackup(package_root) as working_dir:
    # Simpler, but more messy (leaves artifacts on disk) command. This will work
    # for both distutils- and setuputils-based setup.py files.
    sdist_args = ['sdist', '--dist-dir', output_dir]
    # The 'build' and 'egg_info commands (which are invoked anyways as a
    # subcommands of 'sdist') are included to ensure that the fewest possible
    # artifacts are left on disk.
    build_args = [
        'build', '--build-base', working_dir, '--build-temp', working_dir]
    # Some setuptools versions don't support directly running the egg_info
    # command
    egg_info_args = ['egg_info', '--egg-base', working_dir]
    setup_py_arg_sets = (
        egg_info_args + build_args + sdist_args,
        build_args + sdist_args,
        sdist_args)

    # See docstring for the reasoning behind this order.
    setup_py_commands = []
    for setup_py_args in setup_py_arg_sets:
      setup_py_commands.append(_CloudSdkPythonSetupPyCommand(
          setup_py_path, setup_py_args, package_root))
      setup_py_commands.append(_SystemPythonSetupPyCommand(
          setup_py_path, setup_py_args, package_root))

    for setup_py_command in setup_py_commands:
      out = io.StringIO()
      return_code = setup_py_command.Execute(out)
      if not return_code:
        break
    else:
      raise RuntimeError(out.getvalue())

  local_paths = [os.path.join(output_dir, rel_file)
                 for rel_file in os.listdir(output_dir)]
  log.debug('Python packaging resulted in [%s]', ', '.join(local_paths))
  return local_paths


def BuildPackages(package_path, output_dir):
  """Builds Python packages from the given package source.

  That is, builds Python packages from the code in package_path, using its
  parent directory (the 'package root') as its context using the setuptools
  `sdist` command.

  If there is a `setup.py` file in the package root, use that. Otherwise,
  use a simple, temporary one made for this package.

  We try to be as unobstrustive as possible (see _RunSetupTools for details):

  - setuptools writes some files to the package root--we move as many temporary
    generated files out of the package root as possible
  - the final output gets written to output_dir
  - any temporary setup.py file is written outside of the package root.
  - if the current directory isn't writable, we silenly make a temporary copy

  Args:
    package_path: str. Path to the package. This should be the path to
      the directory containing the Python code to be built, *not* its parent
      (which optionally contains setup.py and other metadata).
    output_dir: str, path to a long-lived directory in which the built packages
      should be created.

  Returns:
    list of str. The full local path to all built Python packages.

  Raises:
    SetuptoolsFailedError: If the setup.py file fails to successfully build.
    MissingInitError: If the package doesn't contain an `__init__.py` file.
    InvalidSourceDirError: if the source directory is not valid.
  """
  package_path = os.path.abspath(package_path)
  package_root = os.path.dirname(package_path)
  with _TempDirOrBackup(package_path) as working_dir:
    package_root = _CopyIfNotWritable(package_root, working_dir)
    if not os.path.exists(os.path.join(package_path, '__init__.py')):
      # We could drop `__init__.py` in here, but it's pretty likely that this
      # indicates an incorrect directory or some bigger problem and we don't
      # want to obscure that.
      #
      # Note that we could more strictly validate here by checking each package
      # in the `--module-name` argument, but this should catch most issues.
      raise MissingInitError(package_path)

    setup_py_path = os.path.join(package_root, 'setup.py')
    package_name = os.path.basename(package_path)
    generated = _GenerateSetupPyIfNeeded(setup_py_path, package_name)
    try:
      return _RunSetupTools(package_root, setup_py_path, output_dir)
    except RuntimeError as err:
      raise SetuptoolsFailedError(six.text_type(err), generated)
    finally:
      if generated:
        # For some reason, this artifact gets generated in the package root by
        # setuptools, even after setting PYTHONDONTWRITEBYTECODE or running
        # `python setup.py clean --all`. It's weird to leave someone a .pyc for
        # a file they never knew they had, so we clean it up.
        pyc_file = os.path.join(package_root, 'setup.pyc')
        for path in (setup_py_path, pyc_file):
          try:
            os.unlink(path)
          except OSError:
            log.debug(
                "Couldn't remove file [%s] (it may never have been created).",
                pyc_file)


def _UploadFilesByPath(paths, staging_location):
  """Uploads files after validating and transforming input type."""
  if not staging_location:
    raise NoStagingLocationError()
  counter = collections.Counter(list(map(os.path.basename, paths)))
  duplicates = [name for name, count in six.iteritems(counter) if count > 1]
  if duplicates:
    raise DuplicateEntriesError(duplicates)

  upload_pairs = [(path, os.path.basename(path)) for path in paths]
  return uploads.UploadFiles(upload_pairs, staging_location.bucket_ref,
                             staging_location.name)


def UploadPythonPackages(packages=(), package_path=None, staging_location=None):
  """Uploads Python packages (if necessary), building them as-specified.

  An AI Platform job needs one or more Python packages to run. These Python
  packages can be specified in one of three ways:

    1. As a path to a local, pre-built Python package file.
    2. As a path to a Cloud Storage-hosted, pre-built Python package file (paths
       beginning with 'gs://').
    3. As a local Python source tree (the `--package-path` flag).

  In case 1, we upload the local files to Cloud Storage[1] and provide their
  paths. These can then be given to the AI Platform API, which can fetch
  these files.

  In case 2, we don't need to do anything. We can just send these paths directly
  to the AI Platform API.

  In case 3, we perform a build using setuptools[2], and upload the resulting
  artifacts to Cloud Storage[1]. The paths to these artifacts can be given to
  the AI Platform API. See the `BuildPackages` method.

  These methods of specifying Python packages may be combined.


  [1] Uploads are to a specially-prefixed location in a user-provided Cloud
  Storage staging bucket. If the user provides bucket `gs://my-bucket/`, a file
  `package.tar.gz` is uploaded to
  `gs://my-bucket/<job name>/<checksum>/package.tar.gz`.

  [2] setuptools must be installed on the local user system.

  Args:
    packages: list of str. Path to extra tar.gz packages to upload, if any. If
      empty, a package_path must be provided.
    package_path: str. Relative path to source directory to be built, if any. If
      omitted, one or more packages must be provided.
    staging_location: storage_util.ObjectReference. Cloud Storage prefix to
      which archives are uploaded. Not necessary if only remote packages are
      given.

  Returns:
    list of str. Fully qualified Cloud Storage URLs (`gs://..`) from uploaded
      packages.

  Raises:
    ValueError: If packages is empty, and building package_path produces no
      tar archives.
    SetuptoolsFailedError: If the setup.py file fails to successfully build.
    MissingInitError: If the package doesn't contain an `__init__.py` file.
    DuplicateEntriesError: If multiple files with the same name were provided.
    ArgumentError: if no packages were found in the given path or no
      staging_location was but uploads were required.
  """
  remote_paths = []
  local_paths = []
  for package in packages:
    if storage_util.ObjectReference.IsStorageUrl(package):
      remote_paths.append(package)
    else:
      local_paths.append(package)

  if package_path:
    package_root = os.path.dirname(os.path.abspath(package_path))
    with _TempDirOrBackup(package_root) as working_dir:
      local_paths.extend(BuildPackages(package_path,
                                       os.path.join(working_dir, 'output')))
      remote_paths.extend(_UploadFilesByPath(local_paths, staging_location))
  elif local_paths:
    # Can't combine this with above because above requires the temporary
    # directory to still be around
    remote_paths.extend(_UploadFilesByPath(local_paths, staging_location))

  return remote_paths


def GetStagingLocation(job_id=None, staging_bucket=None, job_dir=None):
  """Get the appropriate staging location for the job given the arguments."""
  staging_location = None
  if staging_bucket:
    staging_location = storage_util.ObjectReference.FromBucketRef(
        staging_bucket, job_id)
  elif job_dir:
    staging_location = storage_util.ObjectReference.FromName(
        job_dir.bucket, '/'.join([f for f in [job_dir.name.rstrip('/'),
                                              'packages'] if f]))
  return staging_location
