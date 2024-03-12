# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Customized versions of runners in subprocess.

Some of this is just for python 2 support and can be simplified.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import os.path
import subprocess
import threading
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.code import json_stream
from googlecloudsdk.core import config
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files as file_utils
import six


def _FindOrInstallComponent(component_name):
  """Finds the path to a component or install it.

  Args:
    component_name: Name of the component.

  Returns:
    Path to the component. Returns None if the component can't be found.
  """
  if (config.Paths().sdk_root and
      update_manager.UpdateManager.EnsureInstalledAndRestart([component_name])):
    return os.path.join(config.Paths().sdk_root, 'bin', component_name)

  return None


def GetGcloudPreferredExecutable(exe):
  """Finds the path to an executable, preferring the gcloud packaged version.

  Args:
    exe: Name of the executable.

  Returns:
    Path to the executable.
  Raises:
    EnvironmentError: The executable can't be found.
  """
  path = _FindOrInstallComponent(exe) or file_utils.FindExecutableOnPath(exe)
  if not path:
    raise EnvironmentError('Unable to locate %s.' % exe)
  return path


class _TimeoutThread(object):
  """A context manager based on threading.Timer.

  Pass a function to call after the given time has passed. If you exit before
  the timer fires, nothing happens. If you exit after we've had to call the
  timer function, we raise TimeoutError at exit time.
  """

  def __init__(self,
               func,
               timeout_sec,
               error_format='Task ran for more than {timeout_sec} seconds'):
    self.func = func
    self.timeout_sec = timeout_sec
    self.error_format = error_format
    self.timer = None

  def __enter__(self):
    self.Reset()
    return self

  def Reset(self):
    if self.timer is not None:
      self.timer.cancel()
    self.timer = threading.Timer(self.timeout_sec, self.func)
    self.timer.start()

  def __exit__(self, exc_type, exc_value, traceback):
    timed_out = self.timer.finished.is_set()
    self.timer.cancel()

    if timed_out:
      raise utils.TimeoutError(
          self.error_format.format(timeout_sec=self.timeout_sec))


def Run(cmd, timeout_sec, show_output=True, inpt=None):
  """Run command and optionally send the output to /dev/null or nul."""
  with file_utils.FileWriter(os.devnull) as devnull:
    stdout = devnull
    stderr = devnull
    stdin = None
    if show_output:
      stdout = None
      stderr = None
    if inpt:
      stdin = subprocess.PIPE
    # [py3 port] Should be able to use subprocess.run (etc) with 'timeout' param
    # here and below. We're only using the Popen API in order to have a process
    # to give to _TimeoutThread.
    p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, stdin=stdin)
    with _TimeoutThread(p.kill, timeout_sec):
      if inpt:
        p.communicate(six.ensure_binary(inpt))
      else:
        p.wait()
    if p.returncode != 0:
      raise subprocess.CalledProcessError(p.returncode, cmd)


def _GetStdout(cmd, timeout_sec, show_stderr=True):
  p = subprocess.Popen(
      cmd,
      stdout=subprocess.PIPE,
      stderr=None if show_stderr else subprocess.PIPE)
  with _TimeoutThread(p.kill, timeout_sec):
    stdout, _ = p.communicate()
  if p.returncode != 0:
    raise subprocess.CalledProcessError(p.returncode, cmd)
  return six.ensure_text(stdout)


def GetOutputLines(cmd, timeout_sec, show_stderr=True, strip_output=False):
  """Run command and get its stdout as a list of lines.

  Args:
    cmd: List of executable and arg strings.
    timeout_sec: Command will be killed if it exceeds this.
    show_stderr: False to suppress stderr from the command.
    strip_output: Strip head/tail whitespace before splitting into lines.

  Returns:
    List of lines (without newlines).
  """
  stdout = _GetStdout(cmd, timeout_sec, show_stderr=show_stderr)
  if strip_output:
    stdout = stdout.strip()
  lines = stdout.splitlines()
  return lines


def GetOutputJson(cmd, timeout_sec, show_stderr=True):
  """Run command and get its JSON stdout as a parsed dict.

  Args:
    cmd: List of executable and arg strings.
    timeout_sec: Command will be killed if it exceeds this.
    show_stderr: False to suppress stderr from the command.

  Returns:
    Parsed JSON.
  """
  stdout = _GetStdout(cmd, timeout_sec, show_stderr=show_stderr)
  return json.loads(stdout.strip())


def StreamOutputJson(cmd, event_timeout_sec, show_stderr=True):
  """Run command and get its output streamed as an iterable of dicts.

  Args:
    cmd: List of executable and arg strings.
    event_timeout_sec: Command will be killed if we don't get a JSON line for
      this long. (This is not the same as timeout_sec above).
    show_stderr: False to suppress stderr from the command.

  Yields:
    Parsed JSON.

  Raises:
    CalledProcessError: cmd returned with a non-zero exit code.
    TimeoutError: cmd has timed out.
  """
  p = subprocess.Popen(
      cmd,
      stdout=subprocess.PIPE,
      stderr=None if show_stderr else subprocess.PIPE)
  with _TimeoutThread(
      p.kill,
      event_timeout_sec,
      error_format='No subprocess output for {timeout_sec} seconds') as timer:
    for obj in json_stream.ReadJsonStream(p.stdout):
      timer.Reset()
      yield obj
    p.wait()
  if p.returncode != 0:
    raise subprocess.CalledProcessError(p.returncode, cmd)
