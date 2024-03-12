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

"""Utilities for computing copy operations from command arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import os
import re


class Path(object):
  """Wrapper to help with dealing with local and GCS paths uniformly."""

  _INVALID_PATH_FORMAT = r'{sep}\.+({sep}|$)'

  def __init__(self, path):
    self.path = path

  @property
  def is_remote(self):
    return self.path.startswith('gs://')

  @property
  def is_dir_like(self):
    if self.is_remote:
      return self.path.endswith('/')
    return self.path.endswith(os.sep)

  def Join(self, part):
    if self.is_remote:
      return Path(self.path.rstrip('/') + '/' + part.lstrip('/'))
    return Path(os.path.join(self.path, part))

  def IsPathSafe(self):
    if self.is_remote:
      sep = '/'
    else:
      # Need \\\\ for the regex to work with nt (Windows) paths as intended.
      sep = os.sep * 2 if os.name == 'nt' else os.sep
    return not bool(re.search(
        Path._INVALID_PATH_FORMAT.format(sep=sep),
        self.path))

  def __str__(self):
    return self.path

  def __repr__(self):
    return self.path
