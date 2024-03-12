# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Shared utility structures and methods for rsync functionality."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals


class DiffAction(object):
  """Enum class representing possible actions to take for an rsync diff."""
  COPY = 'copy'
  REMOVE = 'remove'
  MTIME_SRC_TO_DST = 'mtime_src_to_dst'
  POSIX_SRC_TO_DST = 'posix_src_to_dst'


class RsyncDiffToApply(object):
  """Class that encapsulates info needed to apply diff for one object."""

  def __init__(self, src_url_str, dst_url_str, src_posix_attrs, diff_action,
               copy_size):
    """Constructor.

    Args:
      src_url_str: (str or None) The source URL string, or None if diff_action
          is REMOVE.
      dst_url_str: (str) The destination URL string.
      src_posix_attrs: (posix_util.POSIXAttributes) The source POSIXAttributes.
      diff_action: (DiffAction) DiffAction to be applied.
      copy_size: (int or None) The amount of bytes to copy, or None if
          diff_action is REMOVE.
    """
    self.src_url_str = src_url_str
    self.dst_url_str = dst_url_str
    self.src_posix_attrs = src_posix_attrs
    self.diff_action = diff_action
    self.copy_size = copy_size
