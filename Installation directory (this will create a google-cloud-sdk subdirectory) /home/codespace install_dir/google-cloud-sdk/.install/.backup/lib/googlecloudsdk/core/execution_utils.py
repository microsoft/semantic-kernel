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

"""Functions to help with shelling out to other commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import contextlib
import errno
import os
import re
import signal
import subprocess
import sys
import threading
import time


from googlecloudsdk.core import argv_utils
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import parallel
from googlecloudsdk.core.util import platforms

import six
from six.moves import map


class OutputStreamProcessingException(exceptions.Error):
  """Error class for errors raised during output stream processing."""


class PermissionError(exceptions.Error):
  """User does not have execute permissions."""

  def __init__(self, error):
    super(PermissionError, self).__init__(
        '{err}\nPlease verify that you have execute permission for all '
        'files in your CLOUD SDK bin folder'.format(err=error))


class InvalidCommandError(exceptions.Error):
  """Command entered cannot be found."""

  def __init__(self, cmd):
    super(InvalidCommandError, self).__init__(
        '{cmd}: command not found'.format(cmd=cmd))

try:
  # pylint:disable=invalid-name
  TIMEOUT_EXPIRED_ERR = subprocess.TimeoutExpired

# subprocess.TimeoutExpired and subprocess.Popen.wait are only available in
# py3.3, use our own TimeoutExpired and SubprocessTimeoutWrapper classes in
# earlier versions. Callers that need to wait for subprocesses should catch
# TIMEOUT_EXPIRED_ERR instead of the underlying version-specific errors.
except AttributeError:

  class TimeoutExpired(exceptions.Error):
    """Simulate subprocess.TimeoutExpired on old (<3.3) versions of Python."""

  # pylint:disable=invalid-name
  TIMEOUT_EXPIRED_ERR = TimeoutExpired

  class SubprocessTimeoutWrapper:
    """Forwarding wrapper for subprocess.Popen, adds timeout arg to wait.

    subprocess.Popen.wait doesn't provide a timeout in versions < 3.3. This
    class wraps subprocess.Popen, adds a backported wait that includes the
    timeout arg, and forwards other calls to the underlying subprocess.Popen.

    Callers generally shouldn't use this class directly: Subprocess will
    return either a subprocess.Popen or SubprocessTimeoutWrapper as
    appropriate based on the available version of subprocesses.

    See
    https://docs.python.org/3/library/subprocess.html#subprocess.Popen.wait.
    """

    def __init__(self, proc):
      self.proc = proc

    # pylint:disable=invalid-name
    def wait(self, timeout=None):
      """Busy-wait for wrapped process to have a return code.

      Args:
        timeout: int, Seconds to wait before raising TimeoutExpired.

      Returns:
        int, The subprocess return code.

      Raises:
        TimeoutExpired: if subprocess doesn't finish before the given timeout.
      """
      if timeout is None:
        return self.proc.wait()

      now = time.time()
      later = now + timeout
      delay = 0.01  # 10ms
      ret = self.proc.poll()
      while ret is None:
        if time.time() > later:
          raise TimeoutExpired()
        time.sleep(delay)
        ret = self.proc.poll()
      return ret

    def __getattr__(self, name):
      return getattr(self.proc, name)


# Doesn't work in par or stub files.
def GetPythonExecutable():
  """Gets the path to the Python interpreter that should be used."""
  cloudsdk_python = encoding.GetEncodedValue(os.environ, 'CLOUDSDK_PYTHON')
  if cloudsdk_python:
    return cloudsdk_python
  python_bin = sys.executable
  if not python_bin:
    raise ValueError('Could not find Python executable.')
  return python_bin


# From https://en.wikipedia.org/wiki/Unix_shell#Bourne_shell_compatible
# Many scripts that we execute via execution_utils are bash scripts, and we need
# a compatible shell to run them.
# zsh, was initially on this list, but it doesn't work 100% without running it
# in `emulate sh` mode.
_BORNE_COMPATIBLE_SHELLS = [
    'ash',
    'bash',
    'busybox'
    'dash',
    'ksh',
    'mksh',
    'pdksh',
    'sh',
]


def _GetShellExecutable():
  """Gets the path to the Shell that should be used.

  First tries the current environment $SHELL, if set, then `bash` and `sh`. The
  first of these that is found is used.

  The shell must be Borne-compatible, as the commands that we execute with it
  are often bash/sh scripts.

  Returns:
    str, the path to the shell

  Raises:
    ValueError: if no Borne compatible shell is found
  """
  shells = ['/bin/bash', '/bin/sh']

  user_shell = encoding.GetEncodedValue(os.environ, 'SHELL')
  if user_shell and os.path.basename(user_shell) in _BORNE_COMPATIBLE_SHELLS:
    shells.insert(0, user_shell)

  for shell in shells:
    if os.path.isfile(shell):
      return shell

  raise ValueError("You must set your 'SHELL' environment variable to a "
                   "valid Borne-compatible shell executable to use this tool.")


def _GetToolArgs(interpreter, interpreter_args, executable_path, *args):
  tool_args = []
  if interpreter:
    tool_args.append(interpreter)
  if interpreter_args:
    tool_args.extend(interpreter_args)
  tool_args.append(executable_path)
  tool_args.extend(list(args))
  return tool_args


def GetToolEnv(env=None):
  """Generate the environment that should be used for the subprocess.

  Args:
    env: {str, str}, An existing environment to augment.  If None, the current
      environment will be cloned and used as the base for the subprocess.

  Returns:
    The modified env.
  """
  if env is None:
    env = dict(os.environ)
  env = encoding.EncodeEnv(env)
  encoding.SetEncodedValue(env, 'CLOUDSDK_WRAPPER', '1')

  # Flags can set properties which override the properties file and the existing
  # env vars.  We need to propagate them to children processes through the
  # environment so that those commands will use the same settings.
  for s in properties.VALUES:
    for p in s:
      if p.is_feature_flag:
        continue
      encoding.SetEncodedValue(
          env, p.EnvironmentName(), p.Get(required=False, validate=False))

  # Configuration needs to be handled separately because it's not a real
  # property (although it behaves like one).
  encoding.SetEncodedValue(
      env, config.CLOUDSDK_ACTIVE_CONFIG_NAME,
      named_configs.ConfigurationStore.ActiveConfig().name)

  return env


# Doesn't work in par or stub files.
def ArgsForPythonTool(executable_path, *args, **kwargs):
  """Constructs an argument list for calling the Python interpreter.

  Args:
    executable_path: str, The full path to the Python main file.
    *args: args for the command
    **kwargs: python: str, path to Python executable to use (defaults to
      automatically detected)

  Returns:
    An argument list to execute the Python interpreter

  Raises:
    TypeError: if an unexpected keyword argument is passed
  """
  unexpected_arguments = set(kwargs) - set(['python'])
  if unexpected_arguments:
    raise TypeError(("ArgsForPythonTool() got unexpected keyword arguments "
                     "'[{0}]'").format(', '.join(unexpected_arguments)))
  python_executable = kwargs.get('python') or GetPythonExecutable()
  python_args_str = encoding.GetEncodedValue(
      os.environ, 'CLOUDSDK_PYTHON_ARGS', '')
  python_args = python_args_str.split()
  return _GetToolArgs(
      python_executable, python_args, executable_path, *args)


def ArgsForCMDTool(executable_path, *args):
  """Constructs an argument list for calling the cmd interpreter.

  Args:
    executable_path: str, The full path to the cmd script.
    *args: args for the command

  Returns:
    An argument list to execute the cmd interpreter
  """
  return _GetToolArgs('cmd', ['/c'], executable_path, *args)


def ArgsForExecutableTool(executable_path, *args):
  """Constructs an argument list for an executable.

   Can be used for calling a native binary or shell executable.

  Args:
    executable_path: str, The full path to the binary.
    *args: args for the command

  Returns:
    An argument list to execute the native binary
  """
  return _GetToolArgs(None, None, executable_path, *args)


# Works in regular installs as well as hermetic par and stub files. Doesn't work
# in classic par and stub files.
def ArgsForGcloud():
  """Constructs an argument list to run gcloud."""
  if not sys.executable:
    # In hermetic par/stub files sys.executable is None. In regular installs,
    # and in classic par/stub files it is a non-empty string.
    return _GetToolArgs(None, None, argv_utils.GetDecodedArgv()[0])
  return ArgsForPythonTool(config.GcloudPath())


class _ProcessHolder(object):
  """Process holder that can handle signals raised during processing."""

  def __init__(self):
    self.process = None
    self.signum = None

  def Handler(self, signum, unused_frame):
    """Handle the intercepted signal."""
    self.signum = signum
    if self.process:
      log.debug('Subprocess [{pid}] got [{signum}]'.format(
          signum=signum,
          pid=self.process.pid
      ))
      # We could have jumped to the signal handler between cleaning up our
      # finished child process in communicate() and removing the signal handler.
      # Check to see if our process is still running before we attempt to send
      # it a signal. If poll() returns None, even if the process dies right
      # between that and the terminate() call, the terminate() call will still
      # complete without an error (it just might send a signal to a zombie
      # process).
      if self.process.poll() is None:
        self.process.terminate()
      # The return code will be checked later in the normal processing flow.


@contextlib.contextmanager
def ReplaceEnv(**env_vars):
  """Temporarily set process environment variables."""
  old_environ = dict(os.environ)
  os.environ.update(env_vars)
  try:
    yield
  finally:
    os.environ.clear()
    os.environ.update(old_environ)


@contextlib.contextmanager
def _ReplaceSignal(signo, handler):
  old_handler = signal.signal(signo, handler)
  try:
    yield
  finally:
    signal.signal(signo, old_handler)


def _Exec(args,
          process_holder,
          env=None,
          out_func=None,
          err_func=None,
          in_str=None,
          **extra_popen_kwargs):
  """See Exec docstring."""
  if out_func:
    extra_popen_kwargs['stdout'] = subprocess.PIPE
  if err_func:
    extra_popen_kwargs['stderr'] = subprocess.PIPE
  if in_str:
    extra_popen_kwargs['stdin'] = subprocess.PIPE
  try:
    if args and isinstance(args, list):
      # On Python 2.x on Windows, the first arg can't be unicode. We encode
      # encode it anyway because there is really nothing else we can do if
      # that happens.
      # https://bugs.python.org/issue19264
      args = [encoding.Encode(a) for a in args]
    p = subprocess.Popen(args, env=GetToolEnv(env=env), **extra_popen_kwargs)
  except OSError as err:
    if err.errno == errno.EACCES:
      raise PermissionError(err.strerror)
    elif err.errno == errno.ENOENT:
      raise InvalidCommandError(args[0])
    raise
  process_holder.process = p

  if process_holder.signum is not None:
    # This covers the small possibility that process_holder handled a
    # signal when the process was starting but not yet set to
    # process_holder.process.
    if p.poll() is None:
      p.terminate()

  if isinstance(in_str, six.text_type):
    in_str = in_str.encode('utf-8')
  stdout, stderr = list(map(encoding.Decode, p.communicate(input=in_str)))

  if out_func:
    out_func(stdout)
  if err_func:
    err_func(stderr)
  return p.returncode


def Exec(args,
         env=None,
         no_exit=False,
         out_func=None,
         err_func=None,
         in_str=None,
         **extra_popen_kwargs):
  """Emulates the os.exec* set of commands, but uses subprocess.

  This executes the given command, waits for it to finish, and then exits this
  process with the exit code of the child process.

  Args:
    args: [str], The arguments to execute.  The first argument is the command.
    env: {str: str}, An optional environment for the child process.
    no_exit: bool, True to just return the exit code of the child instead of
      exiting.
    out_func: str->None, a function to call with the stdout of the executed
      process. This can be e.g. log.file_only_logger.debug or log.out.write.
    err_func: str->None, a function to call with the stderr of the executed
      process. This can be e.g. log.file_only_logger.debug or log.err.write.
    in_str: bytes or str, input to send to the subprocess' stdin.
    **extra_popen_kwargs: Any additional kwargs will be passed through directly
      to subprocess.Popen

  Returns:
    int, The exit code of the child if no_exit is True, else this method does
    not return.

  Raises:
    PermissionError: if user does not have execute permission for cloud sdk bin
    files.
    InvalidCommandError: if the command entered cannot be found.
  """
  log.debug('Executing command: %s', args)
  # We use subprocess instead of execv because windows does not support process
  # replacement.  The result of execv on windows is that a new processes is
  # started and the original is killed.  When running in a shell, the prompt
  # returns as soon as the parent is killed even though the child is still
  # running.  subprocess waits for the new process to finish before returning.
  process_holder = _ProcessHolder()

  # pylint:disable=protected-access
  # Python 3 has a cleaner way to check if on main thread, but must support PY2.
  if isinstance(threading.current_thread(), threading._MainThread):
    # pylint:enable=protected-access
    # Signal replacement is not allowed by Python on non-main threads.
    # https://bugs.python.org/issue38904
    with _ReplaceSignal(signal.SIGTERM, process_holder.Handler):
      with _ReplaceSignal(signal.SIGINT, process_holder.Handler):
        ret_val = _Exec(args, process_holder, env, out_func, err_func, in_str,
                        **extra_popen_kwargs)
  else:
    ret_val = _Exec(args, process_holder, env, out_func, err_func, in_str,
                    **extra_popen_kwargs)

  if no_exit and process_holder.signum is None:
    return ret_val
  sys.exit(ret_val)


def Subprocess(args, env=None, **extra_popen_kwargs):
  """Run subprocess.Popen with optional timeout and custom env.

  Returns a running subprocess. Depending on the available version of the
  subprocess library, this will return either a subprocess.Popen or a
  SubprocessTimeoutWrapper (which forwards calls to a subprocess.Popen).
  Callers should catch TIMEOUT_EXPIRED_ERR instead of
  subprocess.TimeoutExpired to be compatible with both classes.

  Args:
    args: [str], The arguments to execute.  The first argument is the command.
    env: {str: str}, An optional environment for the child process.
    **extra_popen_kwargs: Any additional kwargs will be passed through directly
      to subprocess.Popen

  Returns:
    subprocess.Popen or SubprocessTimeoutWrapper, The running subprocess.

  Raises:
    PermissionError: if user does not have execute permission for cloud sdk bin
    files.
    InvalidCommandError: if the command entered cannot be found.
  """
  # Handle unicode-encoded args, see _Exec.
  try:
    if args and isinstance(args, list):
      args = [encoding.Encode(a) for a in args]
    p = subprocess.Popen(args, env=GetToolEnv(env=env), **extra_popen_kwargs)
  except OSError as err:
    if err.errno == errno.EACCES:
      raise PermissionError(err.strerror)
    elif err.errno == errno.ENOENT:
      raise InvalidCommandError(args[0])
    raise
  process_holder = _ProcessHolder()
  process_holder.process = p
  if process_holder.signum is not None:
    if p.poll() is None:
      p.terminate()

  try:
    return SubprocessTimeoutWrapper(p)
  except NameError:
    return p


def _ProcessStreamHandler(proc, err=False, handler=log.Print):
  """Process output stream from a running subprocess in realtime."""
  stream = proc.stderr if err else proc.stdout
  stream_reader = stream.readline
  while True:
    line = stream_reader() or b''
    if not line and proc.poll() is not None:
      try:
        stream.close()
      except OSError:
        pass  # This is thread cleanup so we should just
        # exit so runner can Join()
      break
    line_str = line.decode('utf-8')
    line_str = line_str.rstrip('\r\n')
    if line_str:
      handler(line_str)


def _StreamSubprocessOutput(proc,
                            raw=False,
                            stdout_handler=log.Print,
                            stderr_handler=log.status.Print,
                            capture=False):
  """Log stdout and stderr output from running sub-process."""
  stdout = []
  stderr = []
  with ReplaceEnv(PYTHONUNBUFFERED='1'):
    while True:
      out_line = proc.stdout.readline() or b''
      err_line = proc.stderr.readline() or b''
      if not (err_line or out_line) and proc.poll() is not None:
        break
      if out_line:
        if capture:
          stdout.append(out_line)
        out_str = out_line.decode('utf-8')
        out_str = out_str.rstrip('\r\n') if not raw else out_str
        stdout_handler(out_str)

      if err_line:
        if capture:
          stderr.append(err_line)
        err_str = err_line.decode('utf-8')
        err_str = err_str.rstrip('\r\n') if not raw else err_str
        stderr_handler(err_str)
  return proc.returncode, stdout, stderr


def _KillProcIfRunning(proc):
  """Kill process and close open streams."""
  if proc:
    code = None
    if hasattr(proc, 'returncode'):
      code = proc.returncode
    elif hasattr(proc, 'exitcode'):
      code = proc.exitcode
    if code is None or proc.poll() is None:
      proc.terminate()
    try:
      if proc.stdin and not proc.stdin.closed:
        proc.stdin.close()
      if proc.stdout and not proc.stdout.closed:
        proc.stdout.close()
      if proc.stderr and not proc.stderr.closed:
        proc.stderr.close()
    except OSError:
      pass  # Clean Up


def ExecWithStreamingOutput(args,
                            env=None,
                            no_exit=False,
                            out_func=None,
                            err_func=None,
                            in_str=None,
                            **extra_popen_kwargs):
  """Emulates the os.exec* set of commands, but uses subprocess.

  This executes the given command, waits for it to finish, and then exits this
  process with the exit code of the child process. Allows realtime processing of
  stderr and stdout from subprocess using threads.

  Args:
    args: [str], The arguments to execute.  The first argument is the command.
    env: {str: str}, An optional environment for the child process.
    no_exit: bool, True to just return the exit code of the child instead of
      exiting.
    out_func: str->None, a function to call with each line of the stdout of the
      executed process. This can be e.g. log.file_only_logger.debug or
      log.out.write.
    err_func: str->None, a function to call with each line of the stderr of
      the executed process. This can be e.g. log.file_only_logger.debug or
      log.err.write.
    in_str: bytes or str, input to send to the subprocess' stdin.
    **extra_popen_kwargs: Any additional kwargs will be passed through directly
      to subprocess.Popen

  Returns:
    int, The exit code of the child if no_exit is True, else this method does
    not return.

  Raises:
    PermissionError: if user does not have execute permission for cloud sdk bin
    files.
    InvalidCommandError: if the command entered cannot be found.
  """
  log.debug('Executing command: %s', args)
  # We use subprocess instead of execv because windows does not support process
  # replacement.  The result of execv on windows is that a new processes is
  # started and the original is killed.  When running in a shell, the prompt
  # returns as soon as the parent is killed even though the child is still
  # running.  subprocess waits for the new process to finish before returning.
  env = GetToolEnv(env=env)
  process_holder = _ProcessHolder()
  with _ReplaceSignal(signal.SIGTERM, process_holder.Handler):
    with _ReplaceSignal(signal.SIGINT, process_holder.Handler):
      out_handler_func = out_func or log.Print
      err_handler_func = err_func or log.status.Print
      if in_str:
        extra_popen_kwargs['stdin'] = subprocess.PIPE
      try:
        if args and isinstance(args, list):
          # On Python 2.x on Windows, the first arg can't be unicode. We encode
          # encode it anyway because there is really nothing else we can do if
          # that happens.
          # https://bugs.python.org/issue19264
          args = [encoding.Encode(a) for a in args]
        p = subprocess.Popen(args, env=env, stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE, **extra_popen_kwargs)
        process_holder.process = p
        if in_str:
          in_str = six.text_type(in_str).encode('utf-8')
          try:
            p.stdin.write(in_str)
            p.stdin.close()
          except OSError as exc:
            if (exc.errno == errno.EPIPE or
                exc.errno == errno.EINVAL):
              pass  # Obey same conventions as subprocess.communicate()
            else:
              _KillProcIfRunning(p)
              raise OutputStreamProcessingException(exc)

        try:
          with parallel.GetPool(2) as pool:
            std_out_future = pool.ApplyAsync(_ProcessStreamHandler,
                                             (p, False, out_handler_func))
            std_err_future = pool.ApplyAsync(_ProcessStreamHandler,
                                             (p, True, err_handler_func))
            std_out_future.Get()
            std_err_future.Get()
        except Exception as e:
          _KillProcIfRunning(p)
          raise OutputStreamProcessingException(e)

      except OSError as err:
        if err.errno == errno.EACCES:
          raise PermissionError(err.strerror)
        elif err.errno == errno.ENOENT:
          raise InvalidCommandError(args[0])
        raise

      if process_holder.signum is not None:
        # This covers the small possibility that process_holder handled a
        # signal when the process was starting but not yet set to
        # process_holder.process.
        _KillProcIfRunning(p)

      ret_val = p.returncode

  if no_exit and process_holder.signum is None:
    return ret_val
  sys.exit(ret_val)


def ExecWithStreamingOutputNonThreaded(args,
                                       env=None,
                                       no_exit=False,
                                       out_func=None,
                                       err_func=None,
                                       in_str=None,
                                       raw_output=False,
                                       **extra_popen_kwargs):
  """Emulates the os.exec* set of commands, but uses subprocess.

  This executes the given command, waits for it to finish, and then exits this
  process with the exit code of the child process. Allows realtime processing of
  stderr and stdout from subprocess without threads.

  Args:
    args: [str], The arguments to execute.  The first argument is the command.
    env: {str: str}, An optional environment for the child process.
    no_exit: bool, True to just return the exit code of the child instead of
      exiting.
    out_func: str->None, a function to call with each line of the stdout of the
      executed process. This can be e.g. log.file_only_logger.debug or
      log.out.write.
    err_func: str->None, a function to call with each line of the stderr of
      the executed process. This can be e.g. log.file_only_logger.debug or
      log.err.write.
    in_str: bytes or str, input to send to the subprocess' stdin.
    raw_output: bool, stream raw lines of output perserving line
      endings/formatting.
    **extra_popen_kwargs: Any additional kwargs will be passed through directly
      to subprocess.Popen

  Returns:
    int, The exit code of the child if no_exit is True, else this method does
    not return.

  Raises:
    PermissionError: if user does not have execute permission for cloud sdk bin
    files.
    InvalidCommandError: if the command entered cannot be found.
  """
  log.debug('Executing command: %s', args)
  # We use subprocess instead of execv because windows does not support process
  # replacement.  The result of execv on windows is that a new processes is
  # started and the original is killed.  When running in a shell, the prompt
  # returns as soon as the parent is killed even though the child is still
  # running.  subprocess waits for the new process to finish before returning.
  env = GetToolEnv(env=env)
  process_holder = _ProcessHolder()
  with _ReplaceSignal(signal.SIGTERM, process_holder.Handler):
    with _ReplaceSignal(signal.SIGINT, process_holder.Handler):
      out_handler_func = out_func or log.Print
      err_handler_func = err_func or log.status.Print
      if in_str:
        extra_popen_kwargs['stdin'] = subprocess.PIPE
      try:
        if args and isinstance(args, list):
          # On Python 2.x on Windows, the first arg can't be unicode. We encode
          # encode it anyway because there is really nothing else we can do if
          # that happens.
          # https://bugs.python.org/issue19264
          args = [encoding.Encode(a) for a in args]
        p = subprocess.Popen(args, env=env, stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE, **extra_popen_kwargs)

        if in_str:
          in_str = six.text_type(in_str).encode('utf-8')
          try:
            p.stdin.write(in_str)
            p.stdin.close()
          except OSError as exc:
            if (exc.errno == errno.EPIPE or
                exc.errno == errno.EINVAL):
              pass  # Obey same conventions as subprocess.communicate()
            else:
              _KillProcIfRunning(p)
              raise OutputStreamProcessingException(exc)

        try:
          _StreamSubprocessOutput(p, stdout_handler=out_handler_func,
                                  stderr_handler=err_handler_func,
                                  raw=raw_output)
        except Exception as e:
          _KillProcIfRunning(p)
          raise OutputStreamProcessingException(e)
      except OSError as err:
        if err.errno == errno.EACCES:
          raise PermissionError(err.strerror)
        elif err.errno == errno.ENOENT:
          raise InvalidCommandError(args[0])
        raise
      process_holder.process = p

      if process_holder.signum is not None:
        # This covers the small possibility that process_holder handled a
        # signal when the process was starting but not yet set to
        # process_holder.process.
        _KillProcIfRunning(p)

      ret_val = p.returncode

  if no_exit and process_holder.signum is None:
    return ret_val
  sys.exit(ret_val)


def UninterruptibleSection(stream, message=None):
  """Run a section of code with CTRL-C disabled.

  When in this context manager, the ctrl-c signal is caught and a message is
  printed saying that the action cannot be cancelled.

  Args:
    stream: the stream to write to if SIGINT is received
    message: str, optional: the message to write

  Returns:
    Context manager that is uninterruptible during its lifetime.
  """
  message = '\n\n{message}\n\n'.format(
      message=(message or 'This operation cannot be cancelled.'))
  def _Handler(unused_signal, unused_frame):
    stream.write(message)
  return CtrlCSection(_Handler)


def RaisesKeyboardInterrupt():
  """Run a section of code where CTRL-C raises KeyboardInterrupt."""
  def _Handler(signal, frame):  # pylint: disable=redefined-outer-name
    del signal, frame  # Unused in _Handler
    raise KeyboardInterrupt
  return CtrlCSection(_Handler)


def CtrlCSection(handler):
  """Run a section of code with CTRL-C redirected handler.

  Args:
    handler: func(), handler to call if SIGINT is received. In every case
      original Ctrl-C handler is not invoked.

  Returns:
    Context manager that redirects ctrl-c handler during its lifetime.
  """
  return _ReplaceSignal(signal.SIGINT, handler)


def KillSubprocess(p):
  """Kills a subprocess using an OS specific method when python can't do it.

  This also kills all processes rooted in this process.

  Args:
    p: the Popen or multiprocessing.Process object to kill

  Raises:
    RuntimeError: if it fails to kill the process
  """

  # This allows us to kill a Popen object or a multiprocessing.Process object
  code = None
  if hasattr(p, 'returncode'):
    code = p.returncode
  elif hasattr(p, 'exitcode'):
    code = p.exitcode

  if code is not None:
    # already dead
    return

  if platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS:
    # Consume stdout so it doesn't show in the shell
    taskkill_process = subprocess.Popen(
        ['taskkill', '/F', '/T', '/PID', six.text_type(p.pid)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    (stdout, stderr) = taskkill_process.communicate()
    if taskkill_process.returncode != 0 and _IsTaskKillError(stderr):
      # Sometimes taskkill does things in the wrong order and the processes
      # disappear before it gets a chance to kill it.  This is exposed as an
      # error even though it's the outcome we want.
      raise RuntimeError(
          'Failed to call taskkill on pid {0}\nstdout: {1}\nstderr: {2}'
          .format(p.pid, stdout, stderr))

  else:
    # Create a mapping of ppid to pid for all processes, then kill all
    # subprocesses from the main process down

    # set env LANG for subprocess.Popen to be 'en_US.UTF-8'
    new_env = encoding.EncodeEnv(dict(os.environ))
    new_env['LANG'] = 'en_US.UTF-8'
    get_pids_process = subprocess.Popen(['ps', '-e',
                                         '-o', 'ppid=', '-o', 'pid='],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        env=new_env)
    (stdout, stderr) = get_pids_process.communicate()
    stdout = stdout.decode('utf-8')
    if get_pids_process.returncode != 0:
      raise RuntimeError('Failed to get subprocesses of process: {0}'
                         .format(p.pid))

    # Create the process map
    pid_map = {}
    for line in stdout.strip().split('\n'):
      (ppid, pid) = re.match(r'\s*(\d+)\s+(\d+)', line).groups()
      ppid = int(ppid)
      pid = int(pid)
      children = pid_map.get(ppid)
      if not children:
        pid_map[ppid] = [pid]
      else:
        children.append(pid)

    # Expand all descendants of the main process
    all_pids = [p.pid]
    to_process = [p.pid]
    while to_process:
      current = to_process.pop()
      children = pid_map.get(current)
      if children:
        to_process.extend(children)
        all_pids.extend(children)

    # Kill all the subprocesses we found
    for pid in all_pids:
      _KillPID(pid)

    # put this in if you need extra info from the process itself
    # print p.communicate()


def _IsTaskKillError(stderr):
  """Returns whether the stderr output of taskkill indicates it failed.

  Args:
    stderr: the string error output of the taskkill command

  Returns:
    True iff the stderr is considered to represent an actual error.
  """
  # The taskkill "reason" string indicates why it fails. We consider the
  # following reasons to be acceptable. Reason strings differ among different
  # versions of taskkill. If you know a string is specific to a version, feel
  # free to document that here.
  non_error_reasons = (
      # The process might be in the midst of exiting.
      'Access is denied.',
      'The operation attempted is not supported.',
      'There is no running instance of the task.',
      'There is no running instance of the task to terminate.')
  non_error_patterns = (
      re.compile(r'The process "\d+" not found\.'),)
  for reason in non_error_reasons:
    if reason in stderr:
      return False
  for pattern in non_error_patterns:
    if pattern.search(stderr):
      return False

  return True


def _KillPID(pid):
  """Kills the given process with SIGTERM, then with SIGKILL if it doesn't stop.

  Args:
    pid: The process id of the process to check.
  """
  try:
    # Try sigterm first.
    os.kill(pid, signal.SIGTERM)

    # If still running, wait a few seconds to see if it dies.
    deadline = time.time() + 3
    while time.time() < deadline:
      if not _IsStillRunning(pid):
        return
      time.sleep(0.1)

    # No luck, just force kill it.
    os.kill(pid, signal.SIGKILL)
  except OSError as error:
    if 'No such process' not in error.strerror:
      exceptions.reraise(sys.exc_info()[1])


def _IsStillRunning(pid):
  """Determines if the given pid is still running.

  Args:
    pid: The process id of the process to check.

  Returns:
    bool, True if it is still running.
  """
  try:
    (actual_pid, code) = os.waitpid(pid, os.WNOHANG)
    if (actual_pid, code) == (0, 0):
      return True
  except OSError as error:
    if 'No child processes' not in error.strerror:
      exceptions.reraise(sys.exc_info()[1])
  return False
