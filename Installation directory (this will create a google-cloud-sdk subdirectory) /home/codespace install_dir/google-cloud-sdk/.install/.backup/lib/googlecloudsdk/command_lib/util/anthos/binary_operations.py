# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Library for defining Binary backed operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import collections
import os

from googlecloudsdk.command_lib.util.anthos import structured_messages as sm
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms

import six

_DEFAULT_FAILURE_ERROR_MESSAGE = (
    'Error executing command [{command}] (with context [{context}]). '
    'Process exited with code {exit_code}')

_DEFAULT_MISSING_EXEC_MESSAGE = 'Executable [{}] not found.'

_STRUCTURED_TEXT_EXPECTED_ERROR = ('Expected structured message, '
                                   'logging as raw text:{}')

_INSTALL_MISSING_EXEC_PROMPT = (
    'This command requires the `{binary}` component to be installed. '
    'Would you like to install the `{binary}` component to continue '
    'command execution?')


def _LogDefaultOperationFailure(result_object):
  log.error(
      _DEFAULT_FAILURE_ERROR_MESSAGE.format(
          command=result_object.executed_command,
          context=result_object.context,
          exit_code=result_object.exit_code))


class BinaryOperationError(core_exceptions.Error):
  """Base class for binary operation errors."""


class BinaryExecutionError(BinaryOperationError):
  """Raised if there is an error executing the executable."""

  def __init__(self, original_error, context):
    super(BinaryExecutionError,
          self).__init__('Error executing binary on [{}]: [{}]'.format(
              context, original_error))


class InvalidOperationForBinary(BinaryOperationError):
  """Raised when an invalid Operation is invoked on a binary."""


class StructuredOutputError(BinaryOperationError):
  """Raised when there is a problem processing as sturctured message."""


class MissingExecutableException(BinaryOperationError):
  """Raised if an executable can not be found on the path."""

  def __init__(self, exec_name, custom_message=None):

    if custom_message:
      error_msg = custom_message
    else:
      error_msg = _DEFAULT_MISSING_EXEC_MESSAGE.format(exec_name)

    super(MissingExecutableException, self).__init__(error_msg)


class ExecutionError(BinaryOperationError):
  """Raised if there is an error executing the executable."""

  def __init__(self, command, error):
    super(ExecutionError,
          self).__init__('Error executing command on [{}]: [{}]'.format(
              command, error))


class InvalidWorkingDirectoryError(BinaryOperationError):
  """Raised when an invalid path is passed for binary working directory."""

  def __init__(self, command, path):
    super(InvalidWorkingDirectoryError, self).__init__(
        'Error executing command on [{}]. Invalid Path [{}]'.format(
            command, path))


class ArgumentError(BinaryOperationError):
  """Raised if there is an error parsing argument to a command."""


def DefaultStdOutHandler(result_holder):
  """Default processing for stdout from subprocess."""

  def HandleStdOut(stdout):
    stdout = stdout.rstrip()
    if stdout:
      result_holder.stdout = stdout

  return HandleStdOut


def DefaultStdErrHandler(result_holder):
  """Default processing for stderr from subprocess."""

  def HandleStdErr(stderr):
    stderr = stderr.rstrip()
    if stderr:
      result_holder.stderr = stderr

  return HandleStdErr


def DefaultFailureHandler(result_holder, show_exec_error=False):
  """Default processing for subprocess failure status."""
  if result_holder.exit_code != 0:
    result_holder.failed = True
  if show_exec_error and result_holder.failed:
    _LogDefaultOperationFailure(result_holder)


def DefaultStreamOutHandler(result_holder, capture_output=False):
  """Default processing for streaming stdout from subprocess."""

  def HandleStdOut(line):
    if line:
      line.rstrip()
      log.Print(line)
    if capture_output:
      if not result_holder.stdout:
        result_holder.stdout = []
      result_holder.stdout.append(line)

  return HandleStdOut


def DefaultStreamErrHandler(result_holder, capture_output=False):
  """Default processing for streaming stderr from subprocess."""

  def HandleStdErr(line):
    if line:
      log.status.Print(line)
    if capture_output:
      if not result_holder.stderr:
        result_holder.stderr = []
      result_holder.stderr.append(line)

  return HandleStdErr


def ReadStructuredOutput(msg_string, as_json=True):
  """Process a line of structured output into an OutputMessgage.

  Args:
    msg_string: string, line JSON/YAML formatted raw output text.
    as_json: boolean, if True set default string representation for parsed
      message to JSON. If False (default) use YAML.

  Returns:
    OutputMessage, parsed Message

  Raises: StructuredOutputError is msg_string can not be parsed as an
    OutputMessage.

  """
  try:
    return sm.OutputMessage.FromString(msg_string.strip(), as_json=as_json)
  except (sm.MessageParsingError, sm.InvalidMessageError) as e:
    raise StructuredOutputError('Error processing message '
                                '[{msg}] as an OutputMessage: '
                                '{error}'.format(msg=msg_string, error=e))


def _LogStructuredStdOut(line):
  """Parse and log stdout text as an OutputMessage.

  Attempts to parse line into an OutputMessage and log any resource output or
  status messages accordingly. If message can not be parsed, raises a
  StructuredOutputError.

  Args:
    line: string, line of output read from stdout.

  Returns:
    Tuple: (str, object): Tuple of parsed OutputMessage body and
       processed resources or None.

  Raises: StructuredOutputError, if line can not be parsed.
  """
  msg = None
  resources = None
  if line:
    msg_rec = line.strip()
    msg = ReadStructuredOutput(msg_rec)
    # if there are resources, log the message body to stderr
    # process message resource_body with any supplied resource_processors
    # then log the processed message resource_body to stdout
    if msg.resource_body:
      log.status.Print(msg.body)
      log.Print(msg.resource_body)
    else:  # Otherwise just log the message body to stdout
      log.Print(msg.body)

  return (msg.body, resources)


def _CaptureStdOut(result_holder,
                   output_message=None,
                   resource_output=None,
                   raw_output=None):
  """Update OperationResult from OutputMessage or plain text."""
  if not result_holder.stdout:
    result_holder.stdout = []

  if output_message:
    result_holder.stdout.append(output_message)
  if resource_output:
    result_holder.stdout.append(resource_output)
  if raw_output:
    result_holder.stdout.append(raw_output)


def DefaultStreamStructuredOutHandler(result_holder,
                                      capture_output=False,
                                      warn_if_not_stuctured=True):
  """Default processing for structured stdout from threaded subprocess."""

  def HandleStdOut(line):
    """Process structured stdout."""
    if line:
      msg_rec = line.strip()
      try:
        msg, resources = _LogStructuredStdOut(msg_rec)
        if capture_output:
          _CaptureStdOut(
              result_holder, output_message=msg, resource_output=resources)
      except StructuredOutputError as sme:
        if warn_if_not_stuctured:
          log.warning(_STRUCTURED_TEXT_EXPECTED_ERROR.format(sme))
        log.out.Print(msg_rec)
        _CaptureStdOut(result_holder, raw_output=msg_rec)

  return HandleStdOut


def ProcessStructuredOut(result_holder):
  """Default processing for structured stdout from a non-threaded subprocess.

  Attempts to parse result_holder.stdstdout into an OutputMessage and return
  a tuple of output messages and resource content.

  Args:
    result_holder:  OperationResult

  Returns:
    ([str], [JSON]), Tuple of output messages and resource content.
  Raises:
    StructuredOutputError if result_holder can not be processed.
  """
  if result_holder.stdout:
    all_msg = (
        result_holder.stdout if yaml.list_like(result_holder.stdout) else
        result_holder.stdout.strip().split('\n'))
    msgs = []
    resources = []
    for msg_rec in all_msg:
      msg = ReadStructuredOutput(msg_rec)
      msgs.append(msg.body)
      if msg.resource_body:
        resources.append(msg.resource_body)

    return msgs, resources
  return None, None


def _CaptureStdErr(result_holder, output_message=None, raw_output=None):
  """Update OperationResult either from OutputMessage or plain text."""
  if not result_holder.stderr:
    result_holder.stderr = []
  if output_message:
    if output_message.body:
      result_holder.stderr.append(output_message.body)
    if output_message.IsError():
      result_holder.stderr.append(output_message.error_details.Format())
  elif raw_output:
    result_holder.stderr.append(raw_output)


def DefaultStreamStructuredErrHandler(result_holder,
                                      capture_output=False,
                                      warn_if_not_stuctured=True):
  """Default processing for structured stderr from threaded subprocess."""

  def HandleStdErr(line):
    """Handle line as a structured message.

    Attempts to parse line into an OutputMessage and log any errors or warnings
    accordingly. If line cannot be parsed as an OutputMessage, logs it as plain
    text to stderr. If capture_output is True will capture any logged text to
    result_holder.

    Args:
      line: string, line of output read from stderr.
    """
    if line:
      msg_rec = line.strip()
      try:
        msg = ReadStructuredOutput(line)
        if msg.IsError():
          if msg.level == 'info':
            log.info(msg.error_details.Format())
          elif msg.level == 'error':
            log.error(msg.error_details.Format())
          elif msg.level == 'warning':
            log.warning(msg.error_details.Format())
          elif msg.level == 'debug':
            log.debug(msg.error_details.Format())
        else:
          log.status.Print(msg.body)
        if capture_output:
          _CaptureStdErr(result_holder, output_message=msg)
      except StructuredOutputError as sme:
        if warn_if_not_stuctured:
          log.warning(_STRUCTURED_TEXT_EXPECTED_ERROR.format(sme))
        log.status.Print(msg_rec)
        if capture_output:
          _CaptureStdErr(result_holder, raw_output=msg_rec)

  return HandleStdErr


def ProcessStructuredErr(result_holder):
  """Default processing for structured stderr from non-threaded subprocess.

  Attempts to parse result_holder.stderr into an OutputMessage and return any
  status messages or raised errors.

  Args:
    result_holder:  OperationResult

  Returns:
    ([status messages], [errors]), Tuple of status messages and errors.
  Raises:
    StructuredOutputError if result_holder can not be processed.
  """
  if result_holder.stderr:
    all_msg = (
        result_holder.stderr if yaml.list_like(result_holder.stderr) else
        result_holder.stderr.strip().split('\n'))
    messages = []
    errors = []
    for msg_rec in all_msg:
      msg = ReadStructuredOutput(msg_rec)
      if msg.IsError():
        errors.append(msg.error_details.Format())
      else:
        messages.append(msg.body)
    return messages, errors
  return None, None


# Some golang binary commands (e.g. kubectl diff) behave this way
# so this is for those known exceptional cases.
def NonZeroSuccessFailureHandler(result_holder, show_exec_error=False):
  """Processing for subprocess where non-zero exit status is not always failure.

  Uses rule of thumb that defines success as:
  - a process with zero exit status OR
  - a process with non-zero exit status AND some stdout output.

  All others are considered failed.

  Args:
    result_holder: OperationResult, result of command execution
    show_exec_error: bool, if true log the process command and exit status the
      terminal for failed executions.

  Returns:
    None. Sets the failed attribute of the result_holder.
  """
  if result_holder.exit_code != 0 and not result_holder.stdout:
    result_holder.failed = True
  if show_exec_error and result_holder.failed:
    _LogDefaultOperationFailure(result_holder)


def CheckBinaryComponentInstalled(component_name, check_hidden=False):
  platform = platforms.Platform.Current() if config.Paths().sdk_root else None
  try:
    manager = update_manager.UpdateManager(platform_filter=platform, warn=False)
    return component_name in manager.GetCurrentVersionsInformation(
        include_hidden=check_hidden)
  except local_state.Error:
    log.warning('Component check failed. Could not verify SDK install path.')
    return None


def CheckForInstalledBinary(binary_name,
                            check_hidden=False,
                            custom_message=None,
                            install_if_missing=False):
  """Check if binary is installed and return path or raise error.

  Prefer the installed component over any version found on path.

  Args:
    binary_name: str, name of binary to search for.
    check_hidden: bool, whether to check hidden components for the binary.
    custom_message: str, custom message to used by MissingExecutableException if
      thrown.
    install_if_missing: bool, if true will prompt user to install binary if not
      found.

  Returns:
    Path to executable if found on path or installed component.

  Raises:
    MissingExecutableException: if executable can not be found or can not be
     installed as a component.
  """
  is_component = CheckBinaryComponentInstalled(binary_name, check_hidden)

  if is_component:
    return os.path.join(config.Paths().sdk_bin_path, binary_name)

  path_executable = files.FindExecutableOnPath(binary_name)
  if path_executable:
    return path_executable

  if install_if_missing:
    return InstallBinaryNoOverrides(
        binary_name, _INSTALL_MISSING_EXEC_PROMPT.format(binary=binary_name))

  raise MissingExecutableException(binary_name, custom_message)


def InstallBinaryNoOverrides(binary_name, prompt):
  """Helper method for installing binary dependencies within command execs."""
  console_io.PromptContinue(
      message='Pausing command execution:',
      prompt_string=prompt,
      cancel_on_no=True,
      cancel_string='Aborting component install for {} and command execution.'
      .format(binary_name))
  platform = platforms.Platform.Current()
  update_manager_client = update_manager.UpdateManager(platform_filter=platform)
  update_manager_client.Install([binary_name])

  path_executable = files.FindExecutableOnPath(binary_name)
  if path_executable:
    return path_executable

  raise MissingExecutableException(
      binary_name, '{} binary not installed'.format(binary_name))


class BinaryBackedOperation(six.with_metaclass(abc.ABCMeta, object)):
  """Class for declarative operations implemented as external binaries."""

  class OperationResult(object):
    """Generic Holder for Operation return values and errors."""

    def __init__(self,
                 command_str,
                 output=None,
                 errors=None,
                 status=0,
                 failed=False,
                 execution_context=None):
      self.executed_command = command_str
      self.stdout = output
      self.stderr = errors
      self.exit_code = status
      self.context = execution_context
      self.failed = failed

    def __str__(self):
      output = collections.OrderedDict()
      output['executed_command'] = self.executed_command
      output['stdout'] = self.stdout
      output['stderr'] = self.stderr
      output['exit_code'] = self.exit_code
      output['failed'] = self.failed
      output['execution_context'] = self.context
      return yaml.dump(output)

    def __eq__(self, other):
      if isinstance(other, BinaryBackedOperation.OperationResult):
        return (self.executed_command == other.executed_command and
                self.stdout == other.stdout and self.stderr == other.stderr and
                self.exit_code == other.exit_code and
                self.failed == other.failed and self.context == other.context)
      return False

    def __repr__(self):
      return self.__str__()

  def __init__(self,
               binary,
               binary_version=None,
               check_hidden=False,
               std_out_func=None,
               std_err_func=None,
               failure_func=None,
               default_args=None,
               custom_errors=None,
               install_if_missing=False):
    """Creates the Binary Operation.

    Args:
      binary: executable, the name of binary containing the underlying
        operations that this class will invoke.
      binary_version: string, version of the wrapped binary.
      check_hidden: bool, whether to look for the binary in hidden components.
      std_out_func: callable(OperationResult, **kwargs), returns a function to
        call to process stdout from executable and build OperationResult
      std_err_func: callable(OperationResult, **kwargs), returns a function to
        call to process stderr from executable and build OperationResult
      failure_func: callable(OperationResult), function to call to determine if
        the operation result is a failure. Useful for cases where underlying
        binary can exit with non-zero error code yet still succeed.
      default_args: dict{str:str}, mapping of parameter names to values
        containing default/static values that should always be passed to the
        command.
      custom_errors: dict(str:str}, map of custom exception messages to be used
        for known errors.
      install_if_missing: bool, if True prompt for install on missing component.
    """
    self._executable = CheckForInstalledBinary(
        binary_name=binary,
        check_hidden=check_hidden,
        install_if_missing=install_if_missing,
        custom_message=custom_errors['MISSING_EXEC'] if custom_errors else None)
    self._binary = binary
    self._version = binary_version
    self._default_args = default_args
    self.std_out_handler = std_out_func or DefaultStdOutHandler
    self.std_err_handler = std_err_func or DefaultStdErrHandler
    self.set_failure_status = failure_func or DefaultFailureHandler

  @property
  def binary_name(self):
    return self._binary

  @property
  def executable(self):
    return self._executable

  @property
  def defaults(self):
    return self._default_args

  def _Execute(self, cmd, stdin=None, env=None, **kwargs):
    """Execute binary and return operation result.

     Will parse args from kwargs into a list of args to pass to underlying
     binary and then attempt to execute it. Will use configured stdout, stderr
     and failure handlers for this operation if configured or module defaults.

    Args:
      cmd: [str], command to be executed with args
      stdin: str, data to send to binary on stdin
      env: {str, str}, environment vars to send to binary.
      **kwargs: mapping of additional arguments to pass to the underlying
        executor.

    Returns:
      OperationResult: execution result for this invocation of the binary.

    Raises:
      ArgumentError, if there is an error parsing the supplied arguments.
      BinaryOperationError, if there is an error executing the binary.
    """
    op_context = {
        'env': env,
        'stdin': stdin,
        'exec_dir': kwargs.get('execution_dir')
    }
    result_holder = self.OperationResult(
        command_str=cmd, execution_context=op_context)

    std_out_handler = self.std_out_handler(result_holder)
    std_err_handler = self.std_err_handler(result_holder)
    short_cmd_name = os.path.basename(cmd[0])  # useful for error messages

    try:
      working_dir = kwargs.get('execution_dir')
      if working_dir and not os.path.isdir(working_dir):
        raise InvalidWorkingDirectoryError(short_cmd_name, working_dir)

      exit_code = execution_utils.Exec(
          args=cmd,
          no_exit=True,
          out_func=std_out_handler,
          err_func=std_err_handler,
          in_str=stdin,
          cwd=working_dir,
          env=env)
    except (execution_utils.PermissionError,
            execution_utils.InvalidCommandError) as e:
      raise ExecutionError(short_cmd_name, e)
    result_holder.exit_code = exit_code
    self.set_failure_status(result_holder, kwargs.get('show_exec_error', False))
    return result_holder

  @abc.abstractmethod
  def _ParseArgsForCommand(self, **kwargs):
    """Parse and validate kwargs into command argument list.

    Will process any default_args first before processing kwargs, overriding as
    needed. Will also perform any validation on passed arguments. If calling a
    named sub-command on the underlying binary (vs. just executing the root
    binary), the sub-command should be the 1st argument returned in the list.

    Args:
      **kwargs: keyword arguments for the underlying command.

    Returns:
     list of arguments to pass to execution of underlying command.

    Raises:
      ArgumentError: if there is an error parsing or validating arguments.
    """
    pass

  def __call__(self, **kwargs):
    cmd = [self.executable]
    cmd.extend(self._ParseArgsForCommand(**kwargs))
    return self._Execute(cmd, **kwargs)


class StreamingBinaryBackedOperation(
    six.with_metaclass(abc.ABCMeta, BinaryBackedOperation)):
  """Extend Binary Operations for binaries which require streaming output."""

  def __init__(self,
               binary,
               binary_version=None,
               check_hidden=False,
               std_out_func=None,
               std_err_func=None,
               failure_func=None,
               default_args=None,
               custom_errors=None,
               capture_output=False,
               structured_output=False,
               install_if_missing=False):
    super(StreamingBinaryBackedOperation,
          self).__init__(binary, binary_version, check_hidden, std_out_func,
                         std_err_func, failure_func, default_args,
                         custom_errors, install_if_missing)
    self.capture_output = capture_output
    if structured_output:
      default_out_handler = DefaultStreamStructuredOutHandler
      default_err_handler = DefaultStreamStructuredErrHandler
    else:
      default_out_handler = DefaultStreamOutHandler
      default_err_handler = DefaultStreamErrHandler
    self.std_out_handler = std_out_func or default_out_handler
    self.std_err_handler = std_err_func or default_err_handler
    self.structured_output = structured_output

  def _Execute(self, cmd, stdin=None, env=None, **kwargs):
    """Execute binary and return operation result.

     Will parse args from kwargs into a list of args to pass to underlying
     binary and then attempt to execute it. Will use configured stdout, stderr
     and failure handlers for this operation if configured or module defaults.

    Args:
      cmd: [str], command to be executed with args
      stdin: str, data to send to binary on stdin
      env: {str, str}, environment vars to send to binary.
      **kwargs: mapping of additional arguments to pass to the underlying
        executor.

    Returns:
      OperationResult: execution result for this invocation of the binary.

    Raises:
      ArgumentError, if there is an error parsing the supplied arguments.
      BinaryOperationError, if there is an error executing the binary.
    """
    op_context = {
        'env': env,
        'stdin': stdin,
        'exec_dir': kwargs.get('execution_dir')
    }
    result_holder = self.OperationResult(
        command_str=cmd, execution_context=op_context)

    std_out_handler = self.std_out_handler(
        result_holder=result_holder, capture_output=self.capture_output)
    std_err_handler = self.std_err_handler(
        result_holder=result_holder, capture_output=self.capture_output)
    short_cmd_name = os.path.basename(cmd[0])  # useful for error messages

    try:
      working_dir = kwargs.get('execution_dir')
      if working_dir and not os.path.isdir(working_dir):
        raise InvalidWorkingDirectoryError(short_cmd_name, working_dir)
      exit_code = execution_utils.ExecWithStreamingOutput(
          args=cmd,
          no_exit=True,
          out_func=std_out_handler,
          err_func=std_err_handler,
          in_str=stdin,
          cwd=working_dir,
          env=env)
    except (execution_utils.PermissionError,
            execution_utils.InvalidCommandError) as e:
      raise ExecutionError(short_cmd_name, e)
    result_holder.exit_code = exit_code
    self.set_failure_status(result_holder, kwargs.get('show_exec_error', False))
    return result_holder
