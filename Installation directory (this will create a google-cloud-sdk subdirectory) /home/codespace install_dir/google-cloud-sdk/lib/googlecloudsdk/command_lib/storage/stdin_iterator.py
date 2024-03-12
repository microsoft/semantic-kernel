# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Holds iterator for reading from stdin."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.command_lib.storage import errors
import six


class StdinIterator(six.Iterator):
  """An iterator that returns lines from stdin."""

  def __iter__(self):
    return self

  def __next__(self):
    line = sys.stdin.readline()
    if not line:
      raise StopIteration
    return line.rstrip()


def get_urls_iterable(
    normal_urls_argument, should_read_paths_from_stdin, allow_empty=False
):
  """Helps command decide between normal URL args and a StdinIterator."""
  if not (normal_urls_argument or should_read_paths_from_stdin or allow_empty):
    raise errors.InvalidUrlError(
        'Must have URL arguments if not reading paths from stdin.'
    )
  if normal_urls_argument and should_read_paths_from_stdin:
    raise errors.InvalidUrlError(
        'Cannot have both read from stdin flag and normal URL arguments.'
    )
  if should_read_paths_from_stdin:
    return StdinIterator()
  return normal_urls_argument
