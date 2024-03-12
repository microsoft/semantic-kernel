# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Context manager to help with Control-C handling during critical commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import signal

from googlecloudsdk.api_lib.firebase.test import exit_code
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log


class CancellableTestSection(object):
  """Cancel a test matrix if CTRL-C is typed during a section of code.

  While within this context manager, the CTRL-C signal is caught and a test
  matrix is cancelled. This should only be used with a section of code where
  the test matrix is running.
  """

  def __init__(self, matrix_monitor):
    self._old_sigint_handler = None
    self._old_sigterm_handler = None
    self._matrix_monitor = matrix_monitor

  def __enter__(self):
    self._old_sigint_handler = signal.getsignal(signal.SIGINT)
    self._old_sigterm_handler = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGINT, self._Handler)
    signal.signal(signal.SIGTERM, self._Handler)
    return self

  def __exit__(self, typ, value, traceback):
    signal.signal(signal.SIGINT, self._old_sigint_handler)
    signal.signal(signal.SIGTERM, self._old_sigterm_handler)
    return False

  def _Handler(self, unused_signal, unused_frame):
    log.status.write('\n\nCancelling test [{id}]...\n\n'
                     .format(id=self._matrix_monitor.matrix_id))
    self._matrix_monitor.CancelTestMatrix()
    log.status.write('\nTest matrix has been cancelled.\n')
    raise exceptions.ExitCodeNoError(exit_code=exit_code.MATRIX_CANCELLED)
