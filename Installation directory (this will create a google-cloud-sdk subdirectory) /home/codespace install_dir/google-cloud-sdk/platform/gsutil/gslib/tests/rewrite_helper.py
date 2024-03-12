# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Helper functions for testing calls to the Rewrite API."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals


class RewriteHaltException(Exception):
  pass


class HaltingRewriteCallbackHandler(object):
  """Test callback handler for intentionally stopping a rewrite operation."""

  def __init__(self, halt_at_byte):
    self._halt_at_byte = halt_at_byte

  # pylint: disable=invalid-name
  def call(self, total_bytes_rewritten, unused_total_size):
    """Forcibly exits if the operation has passed the halting point."""
    if total_bytes_rewritten >= self._halt_at_byte:
      raise RewriteHaltException('Artificially halting rewrite')


class EnsureRewriteResumeCallbackHandler(object):
  """Test callback handler for ensuring a rewrite operation resumed."""

  def __init__(self, required_byte):
    self._required_byte = required_byte

  # pylint: disable=invalid-name
  def call(self, total_bytes_rewritten, unused_total_size):
    """Exits if the total bytes rewritten is less than expected."""
    if total_bytes_rewritten <= self._required_byte:
      raise RewriteHaltException(
          'Rewrite did not resume; %s bytes written, but %s bytes should '
          'have already been written.' %
          (total_bytes_rewritten, self._required_byte))


class EnsureRewriteRestartCallbackHandler(object):
  """Test callback handler for ensuring a rewrite operation restarted."""

  def __init__(self, required_byte):
    self._required_byte = required_byte
    self._got_restart_bytes = False

  # pylint: disable=invalid-name
  def call(self, total_bytes_rewritten, unused_total_size):
    """Exits if the total bytes rewritten is greater than expected."""
    if not self._got_restart_bytes:
      if total_bytes_rewritten <= self._required_byte:
        # Restarted successfully, so future calls are allowed to rewrite the
        # rest of the bytes.
        self._got_restart_bytes = True
      else:
        raise RewriteHaltException(
            'Rewrite did not restart; %s bytes written, but no more than %s '
            'bytes should have already been written.' %
            (total_bytes_rewritten, self._required_byte))
