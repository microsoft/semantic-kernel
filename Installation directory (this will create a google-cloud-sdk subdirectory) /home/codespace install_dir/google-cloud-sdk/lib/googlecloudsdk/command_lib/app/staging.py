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
"""Code to provide a hook for staging.

Some App Engine runtimes require an additional staging step before deployment
(e.g. when deploying compiled artifacts, or vendoring code that normally lives
outside of the app directory). This module contains (1) a registry mapping
runtime/environment combinations to staging commands, and (2) code to run said
commands.

The interface is defined as follows:

- A staging command is an executable (binary or script) that takes two
  positional parameters: the path of the `<service>.yaml` in the directory
  containing the unstaged application code, and the path of an empty directory
  in which to stage the application code.
- On success, the STDOUT and STDERR of the staging command are logged at the
  INFO level. On failure, a StagingCommandFailedError is raised containing the
  STDOUT and STDERR of the staging command (which are surfaced to the user as an
  ERROR message).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import io
import os
import re
import shutil
import tempfile

from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import runtime_registry
from googlecloudsdk.command_lib.app import jarfile
from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
import six

_JAVA_APPCFG_ENTRY_POINT = 'com.google.appengine.tools.admin.AppCfg'

_JAVA_APPCFG_STAGE_FLAGS = ['--enable_new_staging_defaults']

_STAGING_COMMAND_OUTPUT_TEMPLATE = """\
------------------------------------ STDOUT ------------------------------------
{out}\
------------------------------------ STDERR ------------------------------------
{err}\
--------------------------------------------------------------------------------
"""


class StagingCommandNotFoundError(exceptions.Error):
  """Base error indicating that a staging command could not be found."""


class NoSdkRootError(StagingCommandNotFoundError):

  def __init__(self):
    super(NoSdkRootError, self).__init__(
        'No SDK root could be found. Please check your installation.')


class NoMainClassError(exceptions.Error):

  def __init__(self):
    super(NoMainClassError, self).__init__(
        'Invalid jar file: it does not contain a Main-Class Manifest entry.')


class MavenPomNotSupported(exceptions.Error):

  def __init__(self):
    super(MavenPomNotSupported, self).__init__(
        'Maven source deployment is not supported for legacy Java 8/11/17/21'
        ' GAE projects configured with appengine-web.xml. Please read '
        'https://cloud.google.com/appengine/docs/standard/java-gen2/using-maven'
    )


class GradleBuildNotSupported(exceptions.Error):

  def __init__(self):
    super(GradleBuildNotSupported, self).__init__(
        'Gradle source deployment is not supported for legacy Java'
        ' 8/11/17/21 GAE projects configured with appengine-web.xml. Read '
        'https://cloud.google.com/appengine/docs/standard/java-gen2/using-gradle'
    )


class StagingCommandFailedError(exceptions.Error):

  def __init__(self, args, return_code, output_message):
    super(StagingCommandFailedError, self).__init__(
        'Staging command [{0}] failed with return code [{1}].\n\n{2}'.format(
            ' '.join(args), return_code, output_message))


# TODO(b/65026284): eliminate "mappers" entirely by making a shim command
def _JavaStagingMapper(command_path, descriptor, app_dir, staging_dir):
  """Map a java staging request to the right args.

  Args:
    command_path: str, path to the jar tool file.
    descriptor: str, path to the `appengine-web.xml`
    app_dir: str, path to the unstaged app directory
    staging_dir: str, path to the empty staging dir

  Raises:
    java.JavaError, if Java is not installed.

  Returns:
    [str], args for executable invocation.
  """
  del descriptor  # Unused, app_dir is sufficient
  java_bin = java.RequireJavaInstalled('local staging for java')
  args = ([java_bin, '-classpath', command_path, _JAVA_APPCFG_ENTRY_POINT] +
          _JAVA_APPCFG_STAGE_FLAGS + ['stage', app_dir, staging_dir])
  return args


class _Command(six.with_metaclass(abc.ABCMeta, object)):
  """Interface for a staging command to be invoked on the user source.

  This abstract class facilitates running an executable command that conforms to
  the "staging command" interface outlined in the module docstring.

  It implements the parts that are common to any such command while allowing
  interface implementors to swap out how the command is created.
  """

  @abc.abstractmethod
  def EnsureInstalled(self):
    """Ensure that the command is installed and available.

    May result in a command restart if installation is required.
    """
    raise NotImplementedError()

  @abc.abstractmethod
  def GetPath(self):
    """Returns the path to the command.

    Returns:
      str, the path to the command

    Raises:
      StagingCommandNotFoundError: if the staging command could not be found.
    """
    raise NotImplementedError()

  def GetArgs(self, descriptor, app_dir, staging_dir, explicit_appyaml=None):
    """Get the args for the command to execute.

    Args:
      descriptor: str, path to the unstaged <service>.yaml or appengine-web.xml
      app_dir: str, path to the unstaged app directory
      staging_dir: str, path to the directory to stage in.
      explicit_appyaml: str or None, the app.yaml location
      to used for deployment.
    Returns:
      list of str, the args for the command to run
    """
    return [self.GetPath(), descriptor, app_dir, staging_dir]

  def Run(self, staging_area, descriptor, app_dir, explicit_appyaml=None):
    """Invokes a staging command with a given <service>.yaml and temp dir.

    Args:
      staging_area: str, path to the staging area.
      descriptor: str, path to the unstaged <service>.yaml or appengine-web.xml
      app_dir: str, path to the unstaged app directory
      explicit_appyaml: str or None, the app.yaml location
      to used for deployment.

    Returns:
      str, the path to the staged directory or None if staging was not required.

    Raises:
      StagingCommandFailedError: if the staging command process exited non-zero.
    """
    staging_dir = tempfile.mkdtemp(dir=staging_area)
    args = self.GetArgs(descriptor, app_dir, staging_dir)
    log.info('Executing staging command: [{0}]\n\n'.format(' '.join(args)))
    out = io.StringIO()
    err = io.StringIO()
    return_code = execution_utils.Exec(
        args, no_exit=True, out_func=out.write, err_func=err.write)
    message = _STAGING_COMMAND_OUTPUT_TEMPLATE.format(
        out=out.getvalue(), err=err.getvalue())
    message = message.replace('\r\n', '\n')
    log.info(message)
    if return_code:
      raise StagingCommandFailedError(args, return_code, message)
    # Optionally use the custom app yaml if available:
    if explicit_appyaml:
      shutil.copyfile(explicit_appyaml, os.path.join(staging_dir, 'app.yaml'))

    return staging_dir


class NoopCommand(_Command):
  """A command that does nothing.

  Many runtimes do not require a staging step; this isn't a problem.
  """

  def EnsureInstalled(self):
    pass

  def GetPath(self):
    return None

  def GetArgs(self, descriptor, app_dir, staging_dir, explicit_appyaml=None):
    return None

  def Run(self, staging_area, descriptor, app_dir, explicit_appyaml=None):
    """Does nothing."""
    pass

  def __eq__(self, other):
    return isinstance(other, NoopCommand)


class CreateJava17ProjectCommand(_Command):
  """A command that creates a java17 runtime app.yaml."""

  def EnsureInstalled(self):
    pass

  def GetPath(self):
    return

  def GetArgs(self, descriptor, staging_dir, appyaml=None):
    return

  def Run(self, staging_area, descriptor, app_dir, explicit_appyaml=None):
    # Logic is: copy/symlink the project in the staged area, and create a
    # simple file app.yaml for runtime: java17 if it does not exist.
    # If it exists in the standard and documented default location
    # (in project_dir/src/main/appengine/app.yaml), copy it in the staged
    # area.
    appenginewebxml = os.path.join(app_dir, 'src', 'main', 'webapp', 'WEB-INF',
                                   'appengine-web.xml')
    if os.path.exists(appenginewebxml):
      raise self.error()
    if explicit_appyaml:
      shutil.copyfile(explicit_appyaml, os.path.join(staging_area, 'app.yaml'))
    else:
      appyaml = os.path.join(app_dir, 'src', 'main', 'appengine', 'app.yaml')
      if os.path.exists(appyaml):
        # Put the user app.yaml at the root of the staging directory to deploy
        # as required by the Cloud SDK.
        shutil.copy2(appyaml, staging_area)
      else:
        # Create a very simple 1 liner app.yaml for Java17 runtime.
        files.WriteFileContents(
            os.path.join(staging_area, 'app.yaml'),
            'runtime: java17\ninstance_class: F2\n')

    for name in os.listdir(app_dir):
      # Do not deploy locally built artifacts, buildpack will clean this anyway.
      if name == self.ignore:
        continue
      srcname = os.path.join(app_dir, name)
      dstname = os.path.join(staging_area, name)
      try:
        os.symlink(srcname, dstname)
      except (AttributeError, OSError):
        # AttributeError can occur if this is a Windows machine with an older
        # version of Python, in which case os.symlink is not defined. If this is
        # a newer version of Windows, but the user is not allowed to create
        # symlinks, we'll get an OSError saying "symbolic link privilege not
        # held." In both cases, we just fall back to copying the files.
        log.debug('Could not symlink files in staging directory, falling back '
                  'to copying')
        if os.path.isdir(srcname):
          files.CopyTree(srcname, dstname)
        else:
          shutil.copy2(srcname, dstname)

    return staging_area

  def __eq__(self, other):
    return isinstance(other, CreateJava17ProjectCommand)


class CreateJava17MavenProjectCommand(CreateJava17ProjectCommand):
  """A command that creates a java17 runtime app.yaml from a pom.xml file."""

  def __init__(self):
    self.error = MavenPomNotSupported
    self.ignore = 'target'
    super(CreateJava17MavenProjectCommand, self).__init__()

  def __eq__(self, other):
    return isinstance(other, CreateJava17GradleProjectCommand)


class CreateJava17GradleProjectCommand(CreateJava17ProjectCommand):
  """A command that creates a java17 runtime app.yaml from a build.gradle file."""

  def __init__(self):
    self.error = GradleBuildNotSupported
    self.ignore = 'build'
    super(CreateJava17GradleProjectCommand, self).__init__()

  def __eq__(self, other):
    return isinstance(other, CreateJava17GradleProjectCommand)


class CreateJava17YamlCommand(_Command):
  """A command that creates a java17 runtime app.yaml from a jar file."""

  def EnsureInstalled(self):
    pass

  def GetPath(self):
    return None

  def GetArgs(self, descriptor, app_dir, staging_dir, explicit_appyaml=None):
    return None

  def Run(self, staging_area, descriptor, app_dir, explicit_appyaml=None):
    # Logic is simple: copy the jar in the staged area, and create a simple
    # file app.yaml for runtime: java17.
    shutil.copy2(descriptor, staging_area)
    if explicit_appyaml:
      shutil.copyfile(explicit_appyaml, os.path.join(staging_area, 'app.yaml'))
    else:
      files.WriteFileContents(
          os.path.join(staging_area, 'app.yaml'),
          'runtime: java17\ninstance_class: F2\n',
          private=True)
    manifest = jarfile.ReadManifest(descriptor)
    if manifest:
      main_entry = manifest.main_section.get('Main-Class')
      if main_entry is None:
        raise NoMainClassError()
      classpath_entry = manifest.main_section.get('Class-Path')
      if classpath_entry:
        libs = classpath_entry.split()
        for lib in libs:
          dependent_file = os.path.join(app_dir, lib)
          # We copy the dep jar in the correct staging sub directories
          # and only if it exists,
          if os.path.isfile(dependent_file):
            destination = os.path.join(staging_area, lib)
            files.MakeDir(os.path.abspath(os.path.join(destination, os.pardir)))
            try:
              os.symlink(dependent_file, destination)
            except (AttributeError, OSError):
              log.debug(
                  'Could not symlink files in staging directory, falling back '
                  'to copying')
              shutil.copy(dependent_file, destination)
    return staging_area

  def __eq__(self, other):
    return isinstance(other, CreateJava17YamlCommand)


class StageAppWithoutAppYamlCommand(_Command):
  """A command that creates a staged directory with an optional app.yaml."""

  def EnsureInstalled(self):
    pass

  def GetPath(self):
    return None

  def GetArgs(self, descriptor, app_dir, staging_dir, explicit_appyaml=None):
    return None

  def Run(self, staging_area, descriptor, app_dir, explicit_appyaml=None):
    # Copy the application in tmp area, and copy the optional app.yaml in it.
    scratch_area = os.path.join(staging_area, 'scratch')
    if os.path.isdir(app_dir):
      files.CopyTree(app_dir, scratch_area)
    else:
      os.mkdir(scratch_area)
      shutil.copy2(app_dir, scratch_area)
    if explicit_appyaml:
      shutil.copyfile(explicit_appyaml, os.path.join(scratch_area, 'app.yaml'))

    return scratch_area

  def __eq__(self, other):
    return isinstance(other, StageAppWithoutAppYamlCommand)


class _BundledCommand(_Command):
  """Represents a cross-platform command.

  Paths are relative to the Cloud SDK Root directory.

  Attributes:
    _nix_path: str, the path to the executable on Linux and OS X
    _windows_path: str, the path to the executable on Windows
    _component: str or None, the name of the Cloud SDK component which contains
      the executable
    _mapper: fn or None, function that maps a staging invocation to a command.
  """

  def __init__(self, nix_path, windows_path, component=None, mapper=None):
    super(_BundledCommand, self).__init__()
    self._nix_path = nix_path
    self._windows_path = windows_path
    self._component = component
    self._mapper = mapper or None

  @property
  def name(self):
    if platforms.OperatingSystem.Current() is platforms.OperatingSystem.WINDOWS:
      return self._windows_path
    else:
      return self._nix_path

  def GetPath(self):
    """Returns the path to the command.

    Returns:
      str, the path to the command

    Raises:
       NoSdkRootError: if no Cloud SDK root could be found (and therefore the
       command is not installed).
    """
    sdk_root = config.Paths().sdk_root
    if not sdk_root:
      raise NoSdkRootError()
    return os.path.join(sdk_root, self.name)

  def GetArgs(self, descriptor, app_dir, staging_dir, explicit_appyaml=None):
    if self._mapper:
      return self._mapper(self.GetPath(), descriptor, app_dir, staging_dir)
    else:
      return super(_BundledCommand, self).GetArgs(descriptor, app_dir,
                                                  staging_dir)

  def EnsureInstalled(self):
    if self._component is None:
      return
    msg = ('The component [{component}] is required for staging this '
           'application.').format(component=self._component)
    update_manager.UpdateManager.EnsureInstalledAndRestart([self._component],
                                                           msg=msg)


class ExecutableCommand(_Command):
  """Represents a command that the user supplies.

  Attributes:
    _path: str, full path to the executable.
  """

  def __init__(self, path):
    super(ExecutableCommand, self).__init__()
    self._path = path

  @property
  def name(self):
    os.path.basename(self._path)

  def GetPath(self):
    return self._path

  def EnsureInstalled(self):
    pass

  def GetArgs(self, descriptor, app_dir, staging_dir, explicit_appyaml=None):
    if explicit_appyaml:
      return [
          self.GetPath(), descriptor, app_dir, staging_dir, explicit_appyaml
      ]
    else:
      return [self.GetPath(), descriptor, app_dir, staging_dir]

  @classmethod
  def FromInput(cls, executable):
    """Returns the command corresponding to the user input.

    Could be either of:
    - command on the $PATH or %PATH%
    - full path to executable (absolute or relative)

    Args:
      executable: str, the user-specified staging exectuable to use

    Returns:
      _Command corresponding to the executable

    Raises:
      StagingCommandNotFoundError: if the executable couldn't be found
    """
    try:
      path = files.FindExecutableOnPath(executable)
    except ValueError:
      # If this is a path (e.g. with os.path.sep in the string),
      # FindExecutableOnPath throws an exception
      path = None
    if path:
      return cls(path)

    if os.path.exists(executable):
      return cls(executable)

    raise StagingCommandNotFoundError('The provided staging command [{}] could '
                                      'not be found.'.format(executable))


# Path to the go-app-stager binary
_GO_APP_STAGER_DIR = os.path.join('platform', 'google_appengine')

# Path to the jar which contains the staging command
_APPENGINE_TOOLS_JAR = os.path.join('platform', 'google_appengine', 'google',
                                    'appengine', 'tools', 'java', 'lib',
                                    'appengine-tools-api.jar')

_STAGING_REGISTRY = {
    runtime_registry.RegistryEntry(
        re.compile(r'(go|go1\..+)$'), {env.FLEX, env.MANAGED_VMS}):
        _BundledCommand(
            os.path.join(_GO_APP_STAGER_DIR, 'go-app-stager'),
            os.path.join(_GO_APP_STAGER_DIR, 'go-app-stager.exe'),
            component='app-engine-go'),
    runtime_registry.RegistryEntry(
        re.compile(r'(go|go1\..+|%s)$' % env.GO_TI_RUNTIME_EXPR.pattern), {
            env.STANDARD,
        }):
        _BundledCommand(
            os.path.join(_GO_APP_STAGER_DIR, 'go-app-stager'),
            os.path.join(_GO_APP_STAGER_DIR, 'go-app-stager.exe'),
            component='app-engine-go'),
    runtime_registry.RegistryEntry('java-xml', {env.STANDARD}):
        _BundledCommand(
            _APPENGINE_TOOLS_JAR,
            _APPENGINE_TOOLS_JAR,
            component='app-engine-java',
            mapper=_JavaStagingMapper),
    runtime_registry.RegistryEntry('java-jar', {env.STANDARD}):
        CreateJava17YamlCommand(),
    runtime_registry.RegistryEntry('java-maven-project', {env.STANDARD}):
        CreateJava17MavenProjectCommand(),
    runtime_registry.RegistryEntry('java-gradle-project', {env.STANDARD}):
        CreateJava17GradleProjectCommand(),
    runtime_registry.RegistryEntry('generic-copy', {env.FLEX, env.STANDARD}):
        StageAppWithoutAppYamlCommand(),
}

# _STAGING_REGISTRY_BETA extends _STAGING_REGISTRY, overriding entries if the
# same key is used.
_STAGING_REGISTRY_BETA = {}


class Stager(object):

  def __init__(self, registry, staging_area):
    self.registry = registry
    self.staging_area = staging_area

  def Stage(self, descriptor, app_dir, runtime, environment, appyaml=None):
    """Stage the given deployable or do nothing if N/A.

    Args:
      descriptor: str, path to the unstaged <service>.yaml or appengine-web.xml
      app_dir: str, path to the unstaged app directory
      runtime: str, the name of the runtime for the application to stage
      environment: api_lib.app.env.Environment, the environment for the
        application to stage
      appyaml: str or None, the app.yaml location to used for deployment.

    Returns:
      str, the path to the staged directory or None if no corresponding staging
          command was found.

    Raises:
      NoSdkRootError: if no Cloud SDK installation root could be found.
      StagingCommandFailedError: if the staging command process exited non-zero.
    """
    command = self.registry.Get(runtime, environment)
    if not command:
      return None
    command.EnsureInstalled()
    return command.Run(self.staging_area, descriptor, app_dir, appyaml)


def GetRegistry():
  return runtime_registry.Registry(_STAGING_REGISTRY, default=NoopCommand())


def GetBetaRegistry():
  mappings = _STAGING_REGISTRY.copy()
  mappings.update(_STAGING_REGISTRY_BETA)
  return runtime_registry.Registry(mappings, default=NoopCommand())


def GetStager(staging_area):
  """Get the default stager."""
  return Stager(GetRegistry(), staging_area)


def GetBetaStager(staging_area):
  """Get the beta stager, used for `gcloud beta *` commands."""
  return Stager(GetBetaRegistry(), staging_area)


def GetNoopStager(staging_area):
  """Get a stager with an empty registry."""
  return Stager(
      runtime_registry.Registry({}, default=NoopCommand()), staging_area)


def GetOverrideStager(command, staging_area):
  """Get a stager with a registry that always calls the given command."""
  return Stager(
      runtime_registry.Registry(None, override=command, default=NoopCommand()),
      staging_area)
