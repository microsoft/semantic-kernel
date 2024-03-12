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
"""Adapter to use externalized runtimes loaders from gcloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from gae_ext_runtime import ext_runtime

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class NoRuntimeRootError(exceptions.Error):
  """Raised when we can't determine where the runtimes are."""


def _GetRuntimeDefDir():
  runtime_root = properties.VALUES.app.runtime_root.Get()
  if runtime_root:
    return runtime_root

  raise NoRuntimeRootError('Unable to determine the root directory where '
                           'GAE runtimes are stored.  Please define '
                           'the CLOUDSDK_APP_RUNTIME_ROOT environmnent '
                           'variable.')


class GCloudExecutionEnvironment(ext_runtime.ExecutionEnvironment):
  """ExecutionEnvironment implemented using gcloud's core functions."""

  def GetPythonExecutable(self):
    return execution_utils.GetPythonExecutable()

  def CanPrompt(self):
    return console_io.CanPrompt()

  def PromptResponse(self, message):
    return console_io.PromptResponse(message)

  def Print(self, message):
    return log.status.Print(message)


class CoreRuntimeLoader(object):
  """A loader stub for the core runtimes.

  The externalized core runtimes are currently distributed with the cloud sdk.
  This class encapsulates the name of a core runtime to avoid having to load
  it at module load time.  Instead, the wrapped runtime is demand-loaded when
  the Fingerprint() method is called.
  """

  def __init__(self, name, visible_name, allowed_runtime_names):
    self._name = name
    self._rep = None
    self._visible_name = visible_name
    self._allowed_runtime_names = allowed_runtime_names

  # These need to be named this way because they're constants in the
  # non-externalized implementation.
  # pylint:disable=invalid-name
  @property
  def ALLOWED_RUNTIME_NAMES(self):
    return self._allowed_runtime_names

  # pylint:disable=invalid-name
  @property
  def NAME(self):
    return self._visible_name

  def Fingerprint(self, path, params):
    if not self._rep:
      path_to_runtime = os.path.join(_GetRuntimeDefDir(), self._name)
      self._rep = ext_runtime.ExternalizedRuntime.Load(
          path_to_runtime, GCloudExecutionEnvironment())
    return self._rep.Fingerprint(path, params)


_PROMPTS_DISABLED_ERROR_MESSAGE = (
    '("disable_prompts" set to true, run "gcloud config set disable_prompts '
    'False" to fix this)')


def GetNonInteractiveErrorMessage():
  """Returns useful instructions when running non-interactive.

  Certain fingerprinting modules require interactive functionality.  It isn't
  always obvious why gcloud is running in non-interactive mode (e.g. when
  "disable_prompts" is set) so this returns an appropriate addition to the
  error message in these circumstances.

  Returns:
    (str) The appropriate error message snippet.
  """
  if properties.VALUES.core.disable_prompts.GetBool():
    # We add a leading space to the raw message so that it meshes well with
    # its display context.
    return ' ' + _PROMPTS_DISABLED_ERROR_MESSAGE
  else:
    # The other case for non-interactivity (running detached from a terminal)
    # should be obvious.
    return ''


