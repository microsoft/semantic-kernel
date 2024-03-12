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
"""Parser for tfvar files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.infra_manager import errors
from googlecloudsdk.core.util import files
import hcl2
import six


def ParseTFvarFile(filename):
  """Parses a `tfvar` file and returns a dictionary of configuration values.

  Args:
    filename: The path to the `tfvar` file.

  Returns:
    A dictionary of configuration values.
  """
  try:
    f = files.ReadFileContents(filename)
    config = hcl2.loads(f)

    return config
  except Exception as e:
    raise errors.InvalidDataError(
        "Error encountered while parsing " + filename + ": " + six.text_type(e)
    )
