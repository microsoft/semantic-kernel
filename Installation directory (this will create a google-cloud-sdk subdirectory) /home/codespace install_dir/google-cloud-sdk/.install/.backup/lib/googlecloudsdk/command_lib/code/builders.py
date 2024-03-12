# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Classes related to build settings."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from googlecloudsdk.command_lib.code import dataobject

from googlecloudsdk.core import exceptions


class InvalidLocationError(exceptions.Error):
  """File is in an invalid location."""


class DockerfileBuilder(dataobject.DataObject):
  """Data for a request to build with an existing Dockerfile."""

  # The 'dockerfile' attribute may be relative to the Settings.context dir or
  # it may be an absolute path. Note that Settings.context is determined later
  # than this instance is made, so it has to be passed into the methods below.
  NAMES = ('dockerfile',)

  def DockerfileAbsPath(self, context):
    return os.path.abspath(os.path.join(context, self.dockerfile))

  def DockerfileRelPath(self, context):
    return os.path.relpath(self.DockerfileAbsPath(context), context)

  def Validate(self, context):
    complete_path = self.DockerfileAbsPath(context)
    if os.path.commonprefix([context, complete_path]) != context:
      raise InvalidLocationError(
          'Invalid Dockerfile path. Dockerfile must be located in the build '
          'context directory.\n'
          'Dockerfile: {0}\n'
          'Build Context Directory: {1}'.format(complete_path, context))
    if not os.path.exists(complete_path):
      raise InvalidLocationError(complete_path + ' does not exist.')


class BuildpackBuilder(dataobject.DataObject):
  """Settings for building with a buildpack.

    Attributes:
      builder: Name of the builder.
      trust: True if the lifecycle should trust this builder.
      devmode: Build with devmode.
  """

  NAMES = ('builder', 'trust', 'devmode')
