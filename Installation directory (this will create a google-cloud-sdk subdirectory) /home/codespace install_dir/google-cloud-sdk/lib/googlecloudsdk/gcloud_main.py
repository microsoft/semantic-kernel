#!/usr/bin/env python
# -*- coding: utf-8 -*- #
#
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
"""gcloud command line tool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

START_TIME = time.time()

# pylint:disable=g-bad-import-order
# pylint:disable=g-import-not-at-top, We want to get the start time first.
import atexit
import errno
import os
import sys

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import cli
from googlecloudsdk.command_lib import crash_handling
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds_context_managers
from googlecloudsdk.core.credentials import devshell as c_devshell
from googlecloudsdk.core.survey import survey_check
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import keyboard_interrupt
from googlecloudsdk.core.util import platforms
import surface

# Disable stack traces when the command is interrupted.
keyboard_interrupt.InstallHandler()

if not config.Paths().sdk_root:
  # Don't do update checks if there is no install root.
  properties.VALUES.component_manager.disable_update_check.Set(True)


def UpdateCheck(command_path, **unused_kwargs):
  try:
    update_manager.UpdateManager.PerformUpdateCheck(command_path=command_path)
  # pylint:disable=broad-except, We never want this to escape, ever. Only
  # messages printed should reach the user.
  except Exception:
    log.debug('Failed to perform update check.', exc_info=True)


def _ShouldCheckSurveyPrompt(command_path):
  """Decides if survey prompt should be checked."""
  if properties.VALUES.survey.disable_prompts.GetBool():
    return False
  # dev shell environment uses temporary folder for user config. That means
  # survey prompt cache gets cleaned each time user starts a new session,
  # which results in too frequent prompting.
  if c_devshell.IsDevshellEnvironment():
    return False

  exempt_commands = [
      'gcloud.components.post-process',
  ]
  for exempt_command in exempt_commands:
    if command_path.startswith(exempt_command):
      return False

  return True


def SurveyPromptCheck(command_path, **unused_kwargs):
  """Checks for in-tool survey prompt."""
  if not _ShouldCheckSurveyPrompt(command_path):
    return
  try:
    survey_check.SurveyPrompter().Prompt()
  # pylint:disable=broad-except, We never want this to escape, ever. Only
  # messages printed should reach the user.
  except Exception:
    log.debug('Failed to check survey prompt.', exc_info=True)
  # pylint:enable=broad-except


def CreateCLI(surfaces, translator=None):
  """Generates the gcloud CLI from 'surface' folder with extra surfaces.

  Args:
    surfaces: list(tuple(dot_path, dir_path)), extra commands or subsurfaces to
      add, where dot_path is calliope command path and dir_path path to command
      group or command.
    translator: yaml_command_translator.Translator, an alternative translator.

  Returns:
    calliope cli object.
  """

  def VersionFunc():
    generated_cli.Execute(['version'])

  def HandleKnownErrorFunc():
    crash_handling.ReportError(is_crash=False)

  pkg_root = os.path.dirname(os.path.dirname(surface.__file__))
  loader = cli.CLILoader(
      name='gcloud',
      command_root_directory=os.path.join(pkg_root, 'surface'),
      allow_non_existing_modules=True,
      version_func=VersionFunc,
      known_error_handler=HandleKnownErrorFunc,
      yaml_command_translator=(translator or
                               yaml_command_translator.Translator()),
  )
  loader.AddReleaseTrack(
      base.ReleaseTrack.ALPHA,
      os.path.join(pkg_root, 'surface', 'alpha'),
      component='alpha')
  loader.AddReleaseTrack(
      base.ReleaseTrack.BETA,
      os.path.join(pkg_root, 'surface', 'beta'),
      component='beta')

  for dot_path, dir_path in surfaces:
    loader.AddModule(dot_path, dir_path, component=None)

  # TODO(b/128465608): Remove cloned ml-engine commands and PreRunHook after a
  # suitable deprecation period.
  # Clone 'ai-platform' surface into 'ml-engine' for backward compatibility.
  loader.AddModule('ml_engine', os.path.join(pkg_root, 'surface',
                                             'ai_platform'))
  loader.RegisterPreRunHook(
      _IssueAIPlatformAliasWarning, include_commands=r'gcloud\..*ml-engine\..*')

  # Clone 'container/hub' surface into 'container/fleet'
  # for backward compatibility.
  loader.AddModule(
      'container.hub',
      os.path.join(pkg_root, 'surface', 'container', 'fleet'))

  # Make 'bigtable.tables' an alias for 'bigtable.instances.tables' to be
  # consistent with other bigtable commands while avoiding a breaking change.
  loader.AddModule(
      'bigtable.tables',
      os.path.join(pkg_root, 'surface', 'bigtable', 'instances', 'tables'),
  )

  # Check for updates on shutdown but not for any of the updater commands.
  # Skip update checks for 'gcloud version' command as it does that manually.
  exclude_commands = r'gcloud\.components\..*|gcloud\.version'
  loader.RegisterPostRunHook(UpdateCheck, exclude_commands=exclude_commands)
  loader.RegisterPostRunHook(SurveyPromptCheck)
  generated_cli = loader.Generate()
  return generated_cli


def _IssueAIPlatformAliasWarning(command_path=None):
  del command_path  # Unused in _IssueTestWarning
  log.warning(
      'The `gcloud ml-engine` commands have been renamed and will soon be '
      'removed. Please use `gcloud ai-platform` instead.')


@crash_handling.CrashManager
def main(gcloud_cli=None, credential_providers=None):
  atexit.register(metrics.Shutdown)
  if not platforms.PythonVersion().IsCompatible():
    sys.exit(1)
  metrics.Started(START_TIME)
  metrics.Executions(
      'gcloud',
      local_state.InstallationState.VersionForInstalledComponent('core'))
  if gcloud_cli is None:
    gcloud_cli = CreateCLI([])

  with creds_context_managers.CredentialProvidersManager(credential_providers):
    try:
      gcloud_cli.Execute()
      # Flush stdout so that if we've received a SIGPIPE we handle the broken
      # pipe within this try block, instead of potentially during interpreter
      # shutdown.
      sys.stdout.flush()
    except IOError as err:
      # We want to ignore EPIPE IOErrors (as of Python 3.3 these can be caught
      # specifically with BrokenPipeError, but we do it this way for Python 2
      # compatibility).
      #
      # By default, Python ignores SIGPIPE (see
      # http://utcc.utoronto.ca/~cks/space/blog/python/SignalExceptionSurprise
      # ).
      # This means that attempting to write any output to a closed pipe (e.g.
      # in the case of output piped to `head` or `grep -q`) will result in an
      # IOError, which gets reported as a gcloud crash. We don't want this
      # behavior, so we ignore EPIPE (it's not a real error; it's a normal
      # thing to occur).
      #
      # Before, we restored the SIGPIPE signal handler, but that caused issues
      # with scripts/programs that wrapped gcloud.
      if err.errno == errno.EPIPE:
        # At this point we've caught the broken pipe, but since Python flushes
        # standard streams on exit, it's still possible for a broken pipe
        # error to happen during interpreter shutdown. The interpreter will
        # catch this but in Python 3 it still prints a warning to stderr
        # saying that the exception was ignored
        # (see https://bugs.python.org/issue11380):
        #
        # Exception ignored in: <_io.TextIOWrapper name='<stdout>' mode='w'
        # encoding='UTF-8'>
        # BrokenPipeError: [Errno 32] Broken pipe
        #
        # To prevent this from happening, we redirect any remaining output to
        # devnull as recommended here:
        # https://docs.python.org/3/library/signal.html#note-on-sigpipe.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
      else:
        raise


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    keyboard_interrupt.HandleInterrupt()
