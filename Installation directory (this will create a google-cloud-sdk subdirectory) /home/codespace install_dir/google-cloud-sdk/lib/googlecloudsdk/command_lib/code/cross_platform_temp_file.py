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
"""Alternate tempfile.NamedTemporaryFile that's easier to use on Windows.

(Windows locks files from simultaneous writes/reads).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import os
import tempfile


class _WindowsNamedTempFile(object):
  """Wrapper around named temporary file for Windows.

  NamedTemporaryFiles cannot be read by other processes on windows because
  only one process can open a file at a time. This file will be unlinked
  at the end of the context.
  """

  def __init__(self, *args, **kwargs):
    self._requested_delete = kwargs.get('delete', True)
    self._args = args
    self._kwargs = kwargs.copy()
    self._kwargs['delete'] = False
    self._f = None

  def __enter__(self):
    self._f = tempfile.NamedTemporaryFile(*self._args, **self._kwargs)
    return self._f

  def __exit__(self, exc_type, exc_value, tb):
    if self._requested_delete and self._f:
      try:
        os.unlink(self._f.name)
      except OSError:
        # File already unlinked. No need to clean up.
        pass


@contextlib.contextmanager
def NamedTempFile(contents, prefix='tmp', suffix='', delete=True):
  """Write a named temporary with given contents.

  Args:
    contents: (str) File contents.
    prefix: (str) File base name prefix.
    suffix: (str) Filename suffix.
    delete: (bool) Delete file on __exit__.

  Yields:
    The temporary file object.
  """
  common_args = dict(mode='w+t', prefix=prefix, suffix=suffix, delete=delete)
  if os.name == 'nt':
    with _WindowsNamedTempFile(**common_args) as f:
      f.write(contents)
      f.close()
      yield f
  else:
    with tempfile.NamedTemporaryFile(**common_args) as f:
      f.write(contents)
      f.flush()
      yield f
