# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""GCloud Command/Group/Flag Deprecation Utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base

_WARNING_MSG = 'This command is deprecated and will be removed in version {0}.'

_REMOVED_MSG = 'This command has been removed as of version {0}.'

_COMMAND_ALT_MSG = ' Use `{0}` instead.'


def DeprecateCommandAtVersion(remove_version,
                              remove=False,
                              alt_command=None):  # pylint: disable=common_typos_disable
  """Decorator that marks a GCloud command as deprecated.

  Args:
      remove_version: string, The GCloud sdk version where this command will be
      marked as removed.

      remove: boolean, True if the command should be removed in underlying
      base.Deprecate decorator, False if it should only print a warning

      alt_command: string, optional alternative command to use in place of
      deprecated command

  Raises:
      ValueError: If remove version is missing

  Returns:
    A modified version of the provided class.
  """
  if not remove_version:
    raise ValueError('Valid remove version is required')

  # Warning and Error messages for Calliope
  warn = _WARNING_MSG.format(remove_version)
  error = _REMOVED_MSG.format(remove_version)

  if alt_command:
    warn += _COMMAND_ALT_MSG.format(alt_command)
    error += _COMMAND_ALT_MSG.format(alt_command)

  return base.Deprecate(is_removed=remove, warning=warn, error=error)
