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

"""Path Utilities for storage commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import platforms


def sanitize_file_resource_for_windows(resource):
  """Returns the resource with invalid characters replaced.

  The invalid characters are only replaced if the resource URL is a FileUrl
  and the platform is Windows. This is required because Cloud URLs may have
  certain characters that are not allowed in file paths on Windows.

  Args:
    resource (Resource): The resource.

  Returns:
    The resource with invalid characters replaced from the path.
  """
  if (
      (not isinstance(resource.storage_url, storage_url.FileUrl))
      or (not platforms.OperatingSystem.IsWindows())
      or (
          not properties.VALUES.storage.convert_incompatible_windows_path_characters.GetBool()
      )
  ):
    return resource

  sanitized_resource = copy.deepcopy(resource)
  sanitized_resource.storage_url.object_name = (
      platforms.MakePathWindowsCompatible(
          sanitized_resource.storage_url.object_name
      )
  )
  return sanitized_resource
