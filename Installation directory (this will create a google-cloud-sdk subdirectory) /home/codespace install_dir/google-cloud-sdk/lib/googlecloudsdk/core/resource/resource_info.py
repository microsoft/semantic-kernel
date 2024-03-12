# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Format and filter resource info module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_transform


class ResourceInfo(object):
  """Format and filter resource info.

  (DEPRECATED) attributes are used by core.resource.resource_registry which
  is being phased out.

  Attributes:
    bypass_cache: True if cache_command output should be used instead of cache.
    cache_command: The gcloud command string that updates the URI cache.
    list_command: The gcloud command string that lists URIs one per line.
    list_format: The default list format string for resource_printer.Print().
    defaults: The resource projection transform defaults.
    transforms: Memoized combined transform symbols dict set by GetTransforms().
    async_collection: (DEPRECATED) The operations collection when --async is
      set.
    collection: (DEPRECATED) Memoized collection name set by Get().

  Special format values:
    None: Ignore this format.
    'default': calliope.base.DEFAULT_FORMAT.
    'error': Resource print using this format is an error.
    'none': Do not print anything.
  """

  def __init__(self,
               bypass_cache=False,
               cache_command=None,
               list_command=None,
               list_format=None,
               defaults=None,
               transforms=None,
               async_collection=None):
    self.bypass_cache = bypass_cache
    self.cache_command = cache_command
    self.list_command = list_command
    self.list_format = list_format
    self.defaults = defaults
    self.transforms = transforms
    self._transforms = None  # memoized by GetTransforms().

    # Remaining attributes are only used by core.resource.resource_registry.
    self.collection = None  # memoized by resource_registry.Get().
    self.async_collection = async_collection

  def GetTransforms(self):
    """Returns the combined transform symbols dict.

    Returns:
      The builtin transforms combined with the collection specific transforms
      if any.
    """
    if self._transforms:
      # Return the memoized transforms.
      return self._transforms

    all_transforms = []

    # The builtin transforms are always available.
    all_transforms.append(resource_transform.GetTransforms())

    # Check if there are any collection specific transforms.
    if self.collection:
      transforms = resource_transform.GetTransforms(self.collection)
      if transforms:
        all_transforms.append(transforms)

    # Check is there are explicit ResourceInfo transforms.
    if self.transforms:
      all_transforms.append(self.transforms)

    # Combine the transform dicts in order.
    if len(all_transforms) == 1:
      self._transforms = all_transforms[0]
    else:
      self._transforms = {}
      for transforms in all_transforms:
        self._transforms.update(transforms)

    return self._transforms
