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
"""Cross-version utility classes and functions for gcloud functions commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import re
from typing import Any

from googlecloudsdk.api_lib.functions.v1 import util as api_util_v1
from googlecloudsdk.api_lib.functions.v2 import client as client_v2
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.functions import flags
import six


class FunctionResourceCommand(six.with_metaclass(abc.ABCMeta, base.Command)):
  """Mix-in for single function resource commands that work with both v1 or v2.

  Which version of the command to run is determined by the following precedence:
  1. Explicit setting via the --gen2/--no-gen2 flags or functions/gen2 property.
  2. The generation of the function if it exists.
  2. The v1 API by default in GA, the v2 API in Beta/Alpha.

  Subclasses should add the function resource arg and --gen2 flag.
  """

  def __init__(self, *args, **kwargs):
    super(FunctionResourceCommand, self).__init__(*args, **kwargs)
    self._v2_function = None

  @abc.abstractmethod
  def _RunV1(self, args: parser_extensions.Namespace) -> Any:
    """Runs the command against the v1 API."""

  @abc.abstractmethod
  def _RunV2(self, args: parser_extensions.Namespace) -> Any:
    """Runs the command against the v2 API."""

  @api_util_v1.CatchHTTPErrorRaiseHTTPException
  def Run(self, args: parser_extensions.Namespace) -> Any:
    """Runs the command.

    Args:
      args: The arguments this command was invoked with.

    Returns:
      The result of the command.

    Raises:
      HttpException: If an HttpError occurs.
    """
    if flags.ShouldUseGen2():
      return self._RunV2(args)

    if flags.ShouldUseGen1():
      return self._RunV1(args)

    client = client_v2.FunctionsClient(self.ReleaseTrack())
    self._v2_function = client.GetFunction(
        args.CONCEPTS.name.Parse().RelativeName()
    )

    if self._v2_function:
      if str(self._v2_function.environment) == 'GEN_2':
        return self._RunV2(args)
      else:
        return self._RunV1(args)

    # TODO(b/286788716): Call v2 by default for functions not found in GA track
    if self.ReleaseTrack() == base.ReleaseTrack.GA:
      return self._RunV1(args)

    return self._RunV2(args)


def FormatTimestamp(timestamp):
  """Formats a timestamp which will be presented to a user.

  Args:
    timestamp: Raw timestamp string in RFC3339 UTC "Zulu" format.

  Returns:
    Formatted timestamp string.
  """
  return re.sub(r'(\.\d{3})\d*Z$', r'\1', timestamp.replace('T', ' '))
