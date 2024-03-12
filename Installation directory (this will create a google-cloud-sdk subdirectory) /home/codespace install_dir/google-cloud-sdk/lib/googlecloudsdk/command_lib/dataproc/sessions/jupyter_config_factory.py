# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Factory for JupyterConfig message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.apis import arg_utils


class JupyterConfigFactory(object):
  """Factory for JupyterConfig message.

  Factory to add JupyterConfig message arguments to argument parser and create
  JupyterConfig message from parsed arguments.
  """

  def __init__(self, dataproc):
    """Factory for JupyterConfig message.

    Args:
      dataproc: A api_lib.dataproc.Dataproc instance.
    """
    self.dataproc = dataproc

  def GetMessage(self, args):
    """Builds a JupyterConfig message according to user settings.

    Args:
      args: Parsed arguments.

    Returns:
      JupyterConfig: A JupyterConfig message instance.
    """
    jupyter_config = self.dataproc.messages.JupyterConfig()
    if args.kernel:
      jupyter_config.kernel = arg_utils.ChoiceToEnum(
          args.kernel,
          self.dataproc.messages.JupyterConfig.KernelValueValuesEnum,
      )

    return jupyter_config


def AddArguments(parser):
  """Adds arguments related to JupyterConfig message to the given parser."""
  parser.add_argument(
      '--kernel',
      choices=['python', 'scala'],
      help=('Jupyter kernel type. The value could be "python" or "scala".'))
