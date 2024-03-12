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

"""Cloud SDK default keyboard interrupt handler."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import signal
import sys

from googlecloudsdk.core import log


def HandleInterrupt(signal_number=None, frame=None):
  """Handles keyboard interrupts (aka SIGINT, ^C).

  Disables the stack trace when a command is killed by keyboard interrupt.

  Args:
    signal_number: The interrupt signal number.
    frame: The signal stack frame context.
  """
  del signal_number, frame  # currently unused
  message = '\n\nCommand killed by keyboard interrupt\n'
  try:
    log.err.Print(message)
  except NameError:
    sys.stderr.write(message)
  # Kill ourselves with SIGINT so our parent can detect that we exited because
  # of a signal. SIG_DFL disables further KeyboardInterrupt exceptions.
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  os.kill(os.getpid(), signal.SIGINT)
  # Just in case the kill failed ...
  sys.exit(1)


def InstallHandler():
  """Installs the default Cloud SDK keyboard interrupt handler."""
  try:
    signal.signal(signal.SIGINT, HandleInterrupt)
  except ValueError:
    # Signal cannot be sent from non-main threads. Integration testing will
    # run parallel threads for performance reasons, occasionally hitting this
    # exception. Should not be reached in production.
    pass
