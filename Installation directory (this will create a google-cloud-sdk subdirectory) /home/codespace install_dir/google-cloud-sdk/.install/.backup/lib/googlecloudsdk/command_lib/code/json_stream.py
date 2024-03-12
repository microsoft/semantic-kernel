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
"""Read JSON objects from a stream."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import json

import six


def ReadJsonStream(file_obj):
  """Read the events from the skaffold event stream.

  Args:
    file_obj: A File object.

  Yields:
    Event dicts from the JSON payloads.
  """
  for line in _ReadStreamingLines(file_obj):
    if not line:
      continue
    yield json.loads(six.ensure_str(line))


if six.PY3:

  def _ReadStreamingLines(file_obj):
    with contextlib.suppress(ConnectionResetError):
      for line in file_obj:
        yield line

elif six.PY2:

  def _ReadStreamingLines(file_obj):
    """Python 2 compatibility with py3's streaming behavior.

    If file_obj is an HTTPResponse, iterating over lines blocks until a buffer
    is full.

    Args:
      file_obj: A file-like object, including HTTPResponse.

    Yields:
      Lines, like iter(file_obj) but without buffering stalls.
    """
    while True:
      line = b''
      while True:
        byte = file_obj.read(1)
        if not byte:
          return
        if byte == b'\n':
          break
        line += byte
      yield line
