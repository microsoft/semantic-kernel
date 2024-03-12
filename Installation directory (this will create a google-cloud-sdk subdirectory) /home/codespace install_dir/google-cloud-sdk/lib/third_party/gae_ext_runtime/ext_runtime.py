# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Support for externalized runtimes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os
import subprocess
import sys
import threading

from . import comm
import ruamel.yaml as yaml
from six.moves import input

# Try importing these modules from the cloud SDK first.
try:
  from googlecloudsdk.third_party.appengine.admin.tools.conversion import schema
except ImportError:
  from yaml_conversion import schema

try:
  from googlecloudsdk.third_party.py27 import py27_subprocess as subprocess
except ImportError:
  import subprocess


WRITING_FILE_MESSAGE = 'Writing [{0}] to [{1}].'
FILE_EXISTS_MESSAGE = 'Not writing [{0}], it already exists.'


class Error(Exception):
  """Base class for exceptions in this module."""


class PluginInvocationFailed(Error):
  """Raised when a plugin invocation returns a non-zero result code."""


class InvalidRuntimeDefinition(Error):
  """Raised when an inconsistency is found in the runtime definition."""
  pass


class Params(object):
  """Parameters passed to the the runtime module Fingerprint() methods.

  Attributes:
    appinfo: (apphosting.api.appinfo.AppInfoExternal or None) The parsed
      app.yaml file for the module if it exists.
    custom: (bool) True if the Configurator should generate a custom runtime.
    runtime (str or None) Runtime (alias allowed) that should be enforced.
    deploy: (bool) True if this is happening from deployment.
  """

  def __init__(self, appinfo=None, custom=False, runtime=None, deploy=False):
    self.appinfo = appinfo
    self.custom = custom
    self.runtime = runtime
    self.deploy = deploy

  def ToDict(self):
    """Returns the object converted to a dictionary.

    Returns:
      ({str: object}) A dictionary that can be converted to json using
      json.dump().
    """
    return {'appinfo': self.appinfo and self.appinfo.ToDict(),
            'custom': self.custom,
            'runtime': self.runtime,
            'deploy': self.deploy}


class Configurator(object):
  """Base configurator class.

  Configurators generate config files for specific classes of runtimes.  They
  are returned by the Fingerprint functions in the runtimes sub-package after
  a successful match of the runtime's heuristics.
  """

  def CollectData(self):
    """Collect all information on this application.

    This is called after the runtime type is detected and may gather
    additional information from the source code and from the user.  Whereas
    performing user queries during detection is deprecated, user queries are
    allowed in CollectData().

    The base class version of this does nothing.
    """

  def Prebuild(self):
    """Run additional build behavior before the application is deployed.

    This is called after the runtime type has been detected and after any
    additional data has been collected.

    The base class version of this does nothing.
    """

  def GenerateConfigs(self):
    """Generate all configuration files for the module.

    Generates config files in the current working directory.

    Returns:
      (callable()) Function that will delete all of the generated files.
    """
    raise NotImplementedError()


class ExecutionEnvironment(object):
  """An interface for providing system functionality to a runtime definition.

  Abstract interface containing methods for console IO and system
  introspection.  This exists to allow gcloud to inject special functionality.
  """

  def GetPythonExecutable(self):
    """Returns the full path of the python executable (str)."""
    raise NotImplementedError()

  def CanPrompt(self):
    """Returns true """
    raise NotImplementedError()

  def PromptResponse(self, message):
    raise NotImplementedError()


  def Print(self, message):
    """Print a message to the console.

    Args:
      message: (str)
    """
    raise NotImplementedError()


class DefaultExecutionEnvironment(ExecutionEnvironment):
  """Standard implementation of the ExecutionEnvironment."""

  def GetPythonExecutable(self):
    return sys.executable

  def CanPrompt(self):
    return sys.stdin.isatty()

  def PromptResponse(self, message):
    sys.stdout.write(message)
    sys.stdout.flush()
    return input('> ')

  def Print(self, message):
    print(message)


class ExternalRuntimeConfigurator(Configurator):
  """Configurator for general externalized runtimes.

  Attributes:
    runtime: (ExternalizedRuntime) The runtime that produced this.
    params: (Params) Runtime parameters.
    data: ({str: object, ...} or None) Optional dictionary of runtime data
      passed back through a runtime_parameters message.
    generated_appinfo: ({str: object, ...} or None) Generated appinfo if any
      is produced by the runtime.
    path: (str) Path to the user's source directory.
  """

  def __init__(self, runtime, params, data, generated_appinfo, path, env):
    """Constructor.

    Args:
      runtime: (ExternalizedRuntime) The runtime that produced this.
      params: (Params) Runtime parameters.
      data: ({str: object, ...} or None) Optional dictionary of runtime data
        passed back through a runtime_parameters message.
      generated_appinfo: ({str: object, ...} or None) Optional dictionary
        representing the contents of app.yaml if the runtime produces this.
      path: (str) Path to the user's source directory.
      env: (ExecutionEnvironment)
    """
    self.runtime = runtime
    self.params = params
    self.data = data
    if generated_appinfo:

      # Add env: flex if we don't have an "env" field.
      self.generated_appinfo = {}
      if not 'env' in generated_appinfo:
        self.generated_appinfo['env'] = 'flex'

      # And then update with the values provided by the runtime def.
      self.generated_appinfo.update(generated_appinfo)
    else:
      self.generated_appinfo = None
    self.path = path
    self.env = env

  def MaybeWriteAppYaml(self):
    """Generates the app.yaml file if it doesn't already exist."""

    if not self.generated_appinfo:
      return

    notify = logging.info if self.params.deploy else self.env.Print
    # TODO(user): The config file need not be named app.yaml.  We need to
    # pass the appinfo file name in through params. and use it here.
    filename = os.path.join(self.path, 'app.yaml')

    # Don't generate app.yaml if we've already got it.  We consider the
    # presence of appinfo to be an indicator of the existence of app.yaml as
    # well as the existence of the file itself because this helps with
    # testability, as well as preventing us from writing the file if another
    # config file is being used.
    if self.params.appinfo or os.path.exists(filename):
      notify(FILE_EXISTS_MESSAGE.format('app.yaml'))
      return

    notify(WRITING_FILE_MESSAGE.format('app.yaml', self.path))
    with open(filename, 'w') as f:
      yaml.safe_dump(self.generated_appinfo, f, default_flow_style=False)

  def SetGeneratedAppInfo(self, generated_appinfo):
    """Sets the generated appinfo."""
    self.generated_appinfo = generated_appinfo

  def CollectData(self):
    self.runtime.CollectData(self)

  def Prebuild(self):
    self.runtime.Prebuild(self)

  def GenerateConfigs(self):
    self.MaybeWriteAppYaml()

    # At this point, if we have don't have appinfo, but we do have generated
    # appinfo, we want to use the generated appinfo and pass it to config
    # generation.
    if not self.params.appinfo and self.generated_appinfo:
      self.params.appinfo = comm.dict_to_object(self.generated_appinfo)
    return self.runtime.GenerateConfigs(self)

  def GenerateConfigData(self):
    self.MaybeWriteAppYaml()

    # At this point, if we have don't have appinfo, but we do have generated
    # appinfo, we want to use the generated appinfo and pass it to config
    # generation.
    if not self.params.appinfo and self.generated_appinfo:
      self.params.appinfo = comm.dict_to_object(self.generated_appinfo)
    return self.runtime.GenerateConfigData(self)


def _NormalizePath(basedir, pathname):
  """Get the absolute path from a unix-style relative path.

  Args:
    basedir: (str) Platform-specific encoding of the base directory.
    pathname: (str) A unix-style (forward slash separated) path relative to
      the runtime definition root directory.

  Returns:
    (str) An absolute path conforming to the conventions of the operating
    system.  Note: in order for this to work, 'pathname' must not contain
    any characters with special meaning in any of the targeted operating
    systems.  Keep those names simple.
  """
  components = pathname.split('/')
  return os.path.join(basedir, *components)


class GeneratedFile(object):
  """Wraps the name and contents of a generated file."""

  def __init__(self, filename, contents):
    """Constructor.

    Args:
      filename: (str) Unix style file path relative to the target source
        directory.
      contents: (str) File contents.
    """
    self.filename = filename
    self.contents = contents

  def WriteTo(self, dest_dir, notify):
    """Write the file to the destination directory.

    Args:
      dest_dir: (str) Destination directory.
      notify: (callable(str)) Function to notify the user.

    Returns:
      (str or None) The full normalized path name of the destination file,
      None if it wasn't generated because it already exists.
    """
    path = _NormalizePath(dest_dir, self.filename)
    if not os.path.exists(path):
      notify(WRITING_FILE_MESSAGE.format(self.filename, dest_dir))
      with open(path, 'w') as f:
        f.write(self.contents)
      return path
    else:
      notify(FILE_EXISTS_MESSAGE.format(self.filename))

    return None


class PluginResult(object):

  def __init__(self):
    self.exit_code = -1
    self.runtime_data = None
    self.generated_appinfo = None
    self.docker_context = None
    self.files = []


class _Collector(object):
  """Manages a PluginResult in a thread-safe context."""

  def __init__(self):
    self.result = PluginResult()
    self.lock = threading.Lock()


_LOG_FUNCS = {
    'info': logging.info,
    'error': logging.error,
    'warn': logging.warn,
    'debug': logging.debug
}

# A section consisting only of scripts.
_EXEC_SECTION = schema.Message(
    python=schema.Value(converter=str))

_RUNTIME_SCHEMA = schema.Message(
    name=schema.Value(converter=str),
    description=schema.Value(converter=str),
    author=schema.Value(converter=str),
    api_version=schema.Value(converter=str),
    generate_configs=schema.Message(
        python=schema.Value(converter=str),
        files_to_copy=schema.RepeatedField(element=schema.Value(converter=str)),
        ),
    detect=_EXEC_SECTION,
    collect_data=_EXEC_SECTION,
    prebuild=_EXEC_SECTION,
    postbuild=_EXEC_SECTION)

_MISSING_FIELD_ERROR = 'Missing [{0}] field in [{1}] message'
_NO_DEFAULT_ERROR = ('User input requested: [{0}] while running '
                     'non-interactive with no default specified.')


class ExternalizedRuntime(object):
  """Encapsulates an externalized runtime."""

  def __init__(self, path, config, env):
    """
    Args:
      path: (str) Path to the root of the runtime definition.
      config: ({str: object, ...}) The runtime definition configuration (from
        runtime.yaml).
      env: (ExecutionEnvironment)
    """

    self.root = path
    self.env = env
    try:
      # Do validation up front, after this we can assume all of the types are
      # correct.
      self.config = _RUNTIME_SCHEMA.ConvertValue(config)
    except ValueError as ex:
      raise InvalidRuntimeDefinition(
          'Invalid runtime definition: {0}'.format(ex.message))

  @property
  def name(self):
    return self.config.get('name', 'unnamed')

  @staticmethod
  def Load(path, env):
    """Loads the externalized runtime from the specified path.

    Args:
      path: (str) root directory of the runtime definition.  Should
        contain a "runtime.yaml" file.

    Returns:
      (ExternalizedRuntime)
    """
    with open(os.path.join(path, 'runtime.yaml')) as f:
      return ExternalizedRuntime(path, yaml.load(f), env)

  def _ProcessPluginStderr(self, section_name, stderr):
    """Process the standard error stream of a plugin.

    Standard error output is just written to the log at "warning" priority and
    otherwise ignored.

    Args:
      section_name: (str) Section name, to be attached to log messages.
      stderr: (file) Process standard error stream.
    """
    while True:
      line = stderr.readline()
      if not line:
        break
      logging.warn('%s: %s' % (section_name, line.rstrip()))

  def _ProcessMessage(self, plugin_stdin, message, result, params,
                      runtime_data):
    """Process a message received from the plugin.

    Args:
      plugin_stdin: (file) The standard input stream of the plugin process.
      message: ({str: object, ...}) The message (this maps directly to the
        message's json object).
      result: (PluginResult) A result object in which to store data collected
        from some types of message.
      params: (Params) Parameters passed in through the
        fingerprinter.
      runtime_data: (object or None) Arbitrary runtime data obtained from the
        "detect" plugin.  This will be None if we are processing a message for
        the detect plugin itself or if no runtime data was provided.
    """

    def SendResponse(response):
      json.dump(response, plugin_stdin)
      plugin_stdin.write('\n')
      plugin_stdin.flush()

    msg_type = message.get('type')
    if msg_type is None:
      logging.error('Missing type in message: %0.80s' % str(message))
    elif msg_type in _LOG_FUNCS:
      _LOG_FUNCS[msg_type](message.get('message'))
    elif msg_type == 'runtime_parameters':
      try:
        result.runtime_data = message['runtime_data']
      except KeyError:
        logging.error(_MISSING_FIELD_ERROR.format('runtime_data', msg_type))
      result.generated_appinfo = message.get('appinfo')
    elif msg_type == 'gen_file':
      try:
        # TODO(user): deal with 'encoding'
        filename = message['filename']
        contents = message['contents']
        result.files.append(GeneratedFile(filename, contents))
      except KeyError as ex:
        logging.error(_MISSING_FIELD_ERROR.format(ex, msg_type))
    elif msg_type == 'get_config':
      response = {'type': 'get_config_response',
                  'params': params.ToDict(),
                  'runtime_data': runtime_data}
      SendResponse(response)
    elif msg_type == 'query_user':
      try:
        prompt = message['prompt']
      except KeyError as ex:
        logging.error(_MISSING_FIELD_ERROR.format('prompt', msg_type))
        return
      default = message.get('default')

      if self.env.CanPrompt():
        if default:
          message = '{0} [{1}]: '.format(prompt, default)
        else:
          message = prompt + ':'
        result = self.env.PromptResponse(message)
      else:
        # TODO(user): Support the "id" field once there is a way to pass
        # these through.
        if default is not None:
          result = default
        else:
          result = ''
          logging.error(_NO_DEFAULT_ERROR.format(prompt))

      SendResponse({'type': 'query_user_response', 'result': result})
    elif msg_type == 'set_docker_context':
      try:
        result.docker_context = message['path']
      except KeyError:
        logging.error(_MISSING_FIELD_ERROR.format('path', msg_type))
        return
    # TODO(user): implement remaining message types.
    else:
      logging.error('Unknown message type %s' % msg_type)

  def _ProcessPluginPipes(self, section_name, proc, result, params,
                          runtime_data):
    """Process the standard output and input streams of a plugin."""
    while True:
      line = proc.stdout.readline()
      if not line:
        break

      # Parse and process the message.
      try:
        message = json.loads(line)
        self._ProcessMessage(proc.stdin, message, result, params, runtime_data)
      except ValueError:
        # Unstructured lines get logged as "info".
        logging.info('%s: %s' % (section_name, line.rstrip()))

  def RunPlugin(self, section_name, plugin_spec, params, args=None,
                valid_exit_codes=(0,),
                runtime_data=None):
    """Run a plugin.

    Args:
      section_name: (str) Name of the config section that the plugin spec is
        from.
      plugin_spec: ({str: str, ...}) A dictionary mapping plugin locales to
        script names
      params: (Params or None) Parameters for the plugin.
      args: ([str, ...] or None) Command line arguments for the plugin.
      valid_exit_codes: (int, ...) Exit codes that will be accepted without
        raising an exception.
      runtime_data: ({str: object, ...}) A dictionary of runtime data passed
        back from detect.

    Returns:
      (PluginResult) A bundle of the exit code and data produced by the plugin.

    Raises:
      PluginInvocationFailed: The plugin terminated with a non-zero exit code.
    """
    # TODO(user): Support other script types.
    if 'python' in plugin_spec:
      normalized_path = _NormalizePath(self.root, plugin_spec['python'])

      # We're sharing 'result' with the output collection thread, we can get
      # away with this without locking because we pass it into the thread at
      # creation and do not use it again until after we've joined the thread.
      result = PluginResult()
      p = subprocess.Popen([self.env.GetPythonExecutable(), normalized_path] +
                           (args if args else []),
                           stdout=subprocess.PIPE,
                           stdin=subprocess.PIPE,
                           stderr=subprocess.PIPE)
      stderr_thread = threading.Thread(target=self._ProcessPluginStderr,
                                       args=(section_name, p.stderr,))
      stderr_thread.start()
      stdout_thread = threading.Thread(target=self._ProcessPluginPipes,
                                       args=(section_name, p, result,
                                             params, runtime_data))
      stdout_thread.start()

      stderr_thread.join()
      stdout_thread.join()
      exit_code = p.wait()
      result.exit_code = exit_code
      if exit_code not in valid_exit_codes:
        raise PluginInvocationFailed('Failed during execution of plugin %s '
                                     'for section %s of runtime %s. rc = %s' %
                                     (normalized_path, section_name,
                                      self.config.get('name', 'unknown'),
                                      exit_code))
      return result
    else:
      logging.error('No usable plugin type found for %s' % section_name)

  def Detect(self, path, params):
    """Determine if 'path' contains an instance of the runtime type.

    Checks to see if the 'path' directory looks like an instance of the
    runtime type.

    Args:
      path: (str) The path name.
      params: (Params) Parameters used by the framework.

    Returns:
      (Configurator) An object containing parameters inferred from source
        inspection.
    """
    detect = self.config.get('detect')
    if detect:
      result = self.RunPlugin('detect', detect, params, [path], (0, 1))
      if result.exit_code:
        return None
      else:
        return ExternalRuntimeConfigurator(self, params, result.runtime_data,
                                           result.generated_appinfo,
                                           path,
                                           self.env)

    else:
      return None

  def CollectData(self, configurator):
    """Do data collection on a detected runtime.

    Args:
      configurator: (ExternalRuntimeConfigurator) The configurator retuned by
        Detect().

    Raises:
      InvalidRuntimeDefinition: For a variety of problems with the runtime
        definition.
    """
    collect_data = self.config.get('collectData')
    if collect_data:
      result = self.RunPlugin('collect_data', collect_data,
                              configurator.params,
                              runtime_data=configurator.data)
      if result.generated_appinfo:
        configurator.SetGeneratedAppInfo(result.generated_appinfo)

  def Prebuild(self, configurator):
    """Perform any additional build behavior before the application is deployed.

    Args:
      configurator: (ExternalRuntimeConfigurator) The configurator returned by
      Detect().
    """
    prebuild = self.config.get('prebuild')
    if prebuild:
      result = self.RunPlugin('prebuild', prebuild, configurator.params,
          args=[configurator.path], runtime_data=configurator.data)

      if result.docker_context:
        configurator.path = result.docker_context

  # The legacy runtimes use "Fingerprint" for this function, the externalized
  # runtime code uses "Detect" to mirror the name in runtime.yaml, so alias it.
  # b/25117700
  Fingerprint = Detect

  def GetAllConfigFiles(self, configurator):
    """Generate list of GeneratedFile objects.

    Args:
      configurator: Configurator, the runtime configurator

    Returns:
      [GeneratedFile] a list of GeneratedFile objects.

    Raises:
      InvalidRuntimeDefinition: For a variety of problems with the runtime
        definition.
    """

    generate_configs = self.config.get('generateConfigs')
    if generate_configs:
      files_to_copy = generate_configs.get('filesToCopy')
      if files_to_copy:
        all_config_files = []

        # Make sure there's nothing else.
        if len(generate_configs) != 1:
          raise InvalidRuntimeDefinition('If "files_to_copy" is specified, '
                                         'it must be the only field in '
                                         'generate_configs.')
        for filename in files_to_copy:
          full_name = _NormalizePath(self.root, filename)
          if not os.path.isfile(full_name):
            raise InvalidRuntimeDefinition('File [%s] specified in '
                                           'files_to_copy, but is not in '
                                           'the runtime definition.' %
                                           filename)
          with open(full_name, 'r') as file_to_read:
            file_contents = file_to_read.read()
          all_config_files.append(GeneratedFile(filename, file_contents))
        return all_config_files
      else:
        result = self.RunPlugin('generate_configs', generate_configs,
                                configurator.params,
                                runtime_data=configurator.data)
        return result.files

  def GenerateConfigData(self, configurator):
    """Do config generation on the runtime, return file objects.

    Args:
      configurator: (ExternalRuntimeConfigurator) The configurator retuned by
        Detect().

    Returns:
      [GeneratedFile] list of generated file objects.
    """
    # Log or print status messages depending on whether we're in gen-config or
    # deploy.
    notify = logging.info if configurator.params.deploy else self.env.Print
    all_config_files = self.GetAllConfigFiles(configurator)
    if all_config_files is None:
      return []
    for config_file in all_config_files:
      if config_file.filename == 'app.yaml':
        config_file.WriteTo(configurator.path, notify)
    config_files = []
    for config_file in all_config_files:
      if not os.path.exists(_NormalizePath(configurator.path,
                                           config_file.filename)):
        config_files.append(config_file)
    return config_files

  def GenerateConfigs(self, configurator):
    """Do config generation on the runtime.

    This should generally be called from the configurator's GenerateConfigs()
    method.

    Args:
      configurator: (ExternalRuntimeConfigurator) The configurator retuned by
        Detect().

    Returns:
      (bool) True if files were generated, False if not
    """
    # Log or print status messages depending on whether we're in gen-config or
    # deploy.
    notify = logging.info if configurator.params.deploy else self.env.Print
    all_config_files = self.GetAllConfigFiles(configurator)
    if all_config_files is None:
      return
    created = False
    for gen_file in all_config_files:
      if gen_file.WriteTo(configurator.path, notify) is not None:
        created = True
    if not created:
      notify('All config files already exist, not generating anything.')
    return created

