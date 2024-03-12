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
"""Utilities for interacting with folders in gcloud storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum


class ManagedFolderSetting(enum.Enum):
  """Indicates how to deal with managed folders."""

  # Used for resource-specific commands that should not have output influenced
  # by managed folders at all. Example usage: the `objects list` command.
  DO_NOT_LIST = 'do_not_list'

  # Indicates that managed folders should be included as prefixes.
  LIST_AS_PREFIXES = 'list_as_prefixes'

  # When expanding a recursive wildcard, yields managed folders with object
  # resources sorted by name: managed folders will precede any objects that are
  # prefixed by the folder name. When expanding a non-recursive wildcard,
  # attempts to convert prefixes to managed folders using a GET call.
  LIST_WITH_OBJECTS = 'list_with_objects'

  # Yields managed folder resources without object/prefix resources.
  LIST_WITHOUT_OBJECTS = 'list_without_objects'


def _contains(potential_container_url, potential_containee_url):
  """Checks containment based on string representations."""
  potential_container_string = potential_container_url.versionless_url_string
  potential_containee_string = potential_containee_url.versionless_url_string

  # Simple substring matching does not handle the ordering between
  # gs://bucket/object and gs://bucket/object2 correctly: they should not
  # be treated as if they stand in a containment relationship.
  delimiter = potential_container_url.delimiter
  prefix = potential_container_string.rstrip(delimiter) + delimiter
  return potential_containee_string.startswith(prefix)


def reverse_containment_order(ordered_iterator, get_url_function=None):
  """Reorders resources so containees are yielded before containers.

  For example, an iterator with the following:
  [
      gs://bucket/prefix/,
      gs://bucket/prefix/object,
      gs://bucket/prefix/object2,
      gs://bucket/prefix2/,
      gs://bucket/prefix2/object,
  ]

  Will become:
  [
      gs://bucket/prefix/object,
      gs://bucket/prefix/object2,
      gs://bucket/prefix/,
      gs://bucket/prefix2/object,
      gs://bucket/prefix2/,
  ]

  Args:
    ordered_iterator (Iterable[object]): Yields objects containing resources
      s.t. container resources are yielded before and contiguous with all of
      their containee resources. Bucket/folder/object resources ordered
      alphabetically by storage URL safisfy this constraint.
    get_url_function (None|object -> storage_url.StorageUrl): Maps objects
      yielded by `iterator` to storage URLs. Defaults to assuming yielded
      objects are URLs. Similar to the `key` attribute on the built-in
      list.sort() method.

  Yields:
    Resources s.t. containees are yielded before their containers, and
      contiguous with other containees.
  """
  if not get_url_function:
    get_url_function = lambda url: url

  # This function is mostly used to ensure managed folder deletion tasks are
  # yielded after tasks for the resources they contain. The nesting depth for
  # managed folders is limited, so the size of the stack is also limited.
  stack = []
  for resource_container in ordered_iterator:
    while True:
      if not stack or _contains(
          get_url_function(stack[-1]),
          get_url_function(resource_container),
      ):
        stack.append(resource_container)
        break
      else:
        yield stack.pop()
  while stack:
    yield stack.pop()
