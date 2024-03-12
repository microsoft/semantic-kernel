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
"""Base class to inherit kuberun command classes from."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import os

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import auth
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberuncli
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import transport
from googlecloudsdk.core.console import console_io


class KubeRunCommand(base.BinaryBackedCommand):
  """Base class for kuberun commands.

    By default, following the principles of go/gcloud-go-binary-commands,
    - stderr is used to stream user messages, status and errors.
    - stdout is captured and processed via SuccessResult() or FailureResult().
    Note: We deviate slightly in the way we process failure results. Instead of
    returning structured output via stdout on failures, per go/gcloud-for-crfa,
    we simply return the error message to show the user.

    All child classes must implement Command(), and define a 'flags' attribute.
    Classes formatting command output (e.g. via JSON) should override
    SuccessResult(), which will be called when the binary exits successfully.
  """

  @classmethod
  def Args(cls, parser):
    if not hasattr(cls, 'flags'):
      raise AttributeError('type {} has not defined the flags attribute'.format(
          cls.__name__))
    flags.RegisterFlags(parser, cls.flags)

  def BuildKubeRunArgs(self, args):
    """Converts args to argument list for the given kuberun command.

    Args:
      args: the arguments passed to gcloud

    Returns:
      a list representing the arguments to be passed to the kuberun binary
    """
    command_args = []
    for f in self.flags:
      command_args.extend(f.FormatFlags(args))
    return command_args

  @abc.abstractmethod
  def Command(self):
    """Returns the supported kuberun command including all command groups."""
    pass

  def FailureResult(self, out):
    """Processes the result of a failed kuberun command execution.

    Args:
      out: str, the output of the kuberun command

    Raises:
      An exception using 'out' as the message or a default message if empty
    """
    raise exceptions.Error(out if out else 'Command execution failed')

  def SuccessResult(self, out, args):
    """Processes the result of a successful kuberun command execution.

    Child classes typically override this method to parse and return a
    structured result (e.g. JSON). The returned data object will be passed
    through cloudsdk filtering/sorting (if applicable) and rendered in the
    default or user-specified output format.

    Args:
      out: str, the output of the kuberun command
      args: the arguments passed to the gcloud command

    Returns:
      A resource object dispatched by display.Displayer().
    """
    return out

  @property
  def command_executor(self):
    return kuberuncli.KubeRunStreamingCli(std_out_func=_CaptureStreamOutHandler)

  def Run(self, args):
    enable_experimental = (
        properties.VALUES.kuberun.enable_experimental_commands.GetBool())
    if not enable_experimental:
      # This prompt is here because our commands are not yet public and marking
      # them as hidden doesn't proclude a customer from using the command if
      # they know about it.
      console_io.PromptContinue(
          message='This command is currently under construction and not supported.',
          throw_if_unattended=True,
          cancel_on_no=True,
          default=False)

    project = properties.VALUES.core.project.Get()
    command = self.Command()
    command.extend(self.BuildKubeRunArgs(args))

    devkit_dir = ''  # '' to force Go binary to use the fdk-dir for gcloud_lite
    if config.Paths().sdk_root:
      devkit_dir = os.path.join(config.Paths().sdk_root, 'lib', 'kuberun',
                                'kuberun_devkits')
    env_vars = {
        'CLOUDSDK_AUTH_TOKEN':
            auth.GetAuthToken(account=properties.VALUES.core.account.Get()),
        'CLOUDSDK_PROJECT':
            project,
        'CLOUDSDK_USER_AGENT':  # Cloud SDK prefix + user agent string
            '{} {}'.format(config.CLOUDSDK_USER_AGENT,
                           transport.MakeUserAgentString()),
        'KUBERUN_DEVKIT_DIRECTORY':
            devkit_dir,
    }

    region = properties.VALUES.compute.region.Get(
        required=False, validate=False)
    if region:
      env_vars['CLOUDSDK_COMPUTE_REGION'] = region

    zone = properties.VALUES.compute.zone.Get(required=False, validate=False)
    if zone:
      env_vars['CLOUDSDK_COMPUTE_ZONE'] = zone

    response = self.command_executor(
        command=command,
        env=kuberuncli.GetEnvArgsForCommand(extra_vars=env_vars),
        show_exec_error=args.show_exec_error)
    log.debug('Response: %s' % response.stdout)
    log.debug('ErrResponse: %s' % response.stderr)

    if response.failed:
      return self.FailureResult(response.stdout)

    return self.SuccessResult(response.stdout, args)


def _CaptureStreamOutHandler(result_holder, **kwargs):
  """Captures streaming stdout from subprocess for processing in result handlers."""
  del kwargs  # we want to capture stdout regardless of other options

  def HandleStdOut(line):
    if line:
      line.rstrip()
      if not result_holder.stdout:
        result_holder.stdout = line
      else:
        result_holder.stdout += '\n' + line

  return HandleStdOut
