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
"""Definition for errors in AI Platform."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class ArgumentError(exceptions.Error):
  pass


class InvalidInstancesFileError(exceptions.Error):
  """Indicates that the input file was invalid in some way."""
  pass


class NoFieldsSpecifiedError(exceptions.Error):
  """Error indicating that no updates were requested in a Patch operation."""
  pass


class DockerError(exceptions.Error):
  """Exception that passes info on a failed Docker command."""

  def __init__(self, message, cmd, exit_code):
    super(DockerError, self).__init__(message)
    self.message = message
    self.cmd = cmd
    self.exit_code = exit_code
