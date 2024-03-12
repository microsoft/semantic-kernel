# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Unit tests for gsutil seek_ahead_thread."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import threading

import six
from six.moves import queue as Queue
from six.moves import range

from gslib.name_expansion import SeekAheadNameExpansionIterator
from gslib.seek_ahead_thread import SeekAheadResult
from gslib.seek_ahead_thread import SeekAheadThread
import gslib.tests.testcase as testcase
from gslib.ui_controller import UIController
from gslib.ui_controller import UIThread
from gslib.utils import constants
from gslib.utils import parallelism_framework_util
from gslib.utils import unit_util

_ZERO_TASKS_TO_DO_ARGUMENT = (
    parallelism_framework_util.ZERO_TASKS_TO_DO_ARGUMENT)


class TestSeekAheadThread(testcase.GsUtilUnitTestCase):
  """Unit tests for SeekAheadThread class and surrounding functionality."""

  # After waiting this long, assume the SeekAheadThread is hung.
  thread_wait_time = 5

  def testCancellation(self):
    """Tests cancellation of SeekAheadThread."""

    class TrackingCancellationIterator(object):
      """Yields dummy results and sends cancellation after some # of yields."""

      def __init__(self, num_iterations, num_iterations_before_cancel,
                   cancel_event):
        """Initializes the iterator.

        Args:
          num_iterations: Total number of results to yield.
          num_iterations_before_cancel: Set cancel event before yielding
              on the given iteration.
          cancel_event: threading.Event() to signal SeekAheadThread to stop.
        """
        self.num_iterations_before_cancel = num_iterations_before_cancel
        self.iterated_results = 0
        self.num_iterations = num_iterations
        self.cancel_issued = False
        self.cancel_event = cancel_event

      def __iter__(self):
        while self.iterated_results < self.num_iterations:
          if (not self.cancel_issued and
              self.iterated_results >= self.num_iterations_before_cancel):
            self.cancel_event.set()
            self.cancel_issued = True
          yield SeekAheadResult()
          self.iterated_results += 1

    # We expect to get up to the nearest NUM_OBJECTS_PER_LIST_PAGE results.
    noplp = constants.NUM_OBJECTS_PER_LIST_PAGE
    for num_iterations, num_iterations_before_cancel, expected_iterations in (
        (noplp, 0, 0), (noplp + 1, 1, noplp), (noplp + 1, noplp, noplp),
        (noplp * 2 + 1, noplp + 1, noplp * 2), (2, 1, 2), (noplp, 1, noplp),
        (noplp * 2, noplp + 1, noplp * 2)):

      cancel_event = threading.Event()
      status_queue = Queue.Queue()
      stream = six.StringIO()
      ui_controller = UIController()
      ui_thread = UIThread(status_queue, stream, ui_controller)

      seek_ahead_iterator = TrackingCancellationIterator(
          num_iterations, num_iterations_before_cancel, cancel_event)
      seek_ahead_thread = SeekAheadThread(seek_ahead_iterator, cancel_event,
                                          status_queue)
      seek_ahead_thread.join(self.thread_wait_time)
      status_queue.put(_ZERO_TASKS_TO_DO_ARGUMENT)
      ui_thread.join(self.thread_wait_time)
      if seek_ahead_thread.is_alive():
        seek_ahead_thread.terminate = True
        self.fail(
            'Cancellation issued after %s iterations, but SeekAheadThread '
            'is still alive.' % num_iterations_before_cancel)
      self.assertEqual(
          expected_iterations, seek_ahead_iterator.iterated_results,
          'Cancellation issued after %s iterations, SeekAheadThread iterated '
          '%s results, expected: %s results.' %
          (num_iterations_before_cancel, seek_ahead_iterator.iterated_results,
           expected_iterations))
      message = stream.getvalue()
      if message:
        self.fail('Status queue should be empty but contains message: %s' %
                  message)

  def testEstimateWithoutSize(self):
    """Tests SeekAheadThread providing an object count."""

    class SeekAheadResultIterator(object):

      def __init__(self, num_results):
        self.num_results = num_results
        self.yielded = 0

      def __iter__(self):
        while self.yielded < self.num_results:
          yield SeekAheadResult()
          self.yielded += 1

    cancel_event = threading.Event()
    status_queue = Queue.Queue()
    stream = six.StringIO()
    ui_controller = UIController()
    ui_thread = UIThread(status_queue, stream, ui_controller)
    num_objects = 5
    seek_ahead_iterator = SeekAheadResultIterator(num_objects)
    seek_ahead_thread = SeekAheadThread(seek_ahead_iterator, cancel_event,
                                        status_queue)
    seek_ahead_thread.join(self.thread_wait_time)
    status_queue.put(_ZERO_TASKS_TO_DO_ARGUMENT)
    ui_thread.join(self.thread_wait_time)
    if seek_ahead_thread.is_alive():
      seek_ahead_thread.terminate = True
      self.fail('SeekAheadThread is still alive.')

    message = stream.getvalue()
    if not message:
      self.fail('Status queue empty but SeekAheadThread should have posted '
                'summary message')
    self.assertEqual(
        message, 'Estimated work for this command: objects: %s\n' % num_objects)

  def testEstimateWithSize(self):
    """Tests SeekAheadThread providing an object count and total size."""

    class SeekAheadResultIteratorWithSize(object):
      """Yields dummy result of the given size."""

      def __init__(self, num_objects, size):
        self.num_objects = num_objects
        self.size = size
        self.yielded = 0

      def __iter__(self):
        while self.yielded < self.num_objects:
          yield SeekAheadResult(data_bytes=self.size)
          self.yielded += 1

    cancel_event = threading.Event()
    status_queue = Queue.Queue()
    stream = six.StringIO()
    ui_controller = UIController()
    ui_thread = UIThread(status_queue, stream, ui_controller)

    num_objects = 5
    object_size = 10
    seek_ahead_iterator = SeekAheadResultIteratorWithSize(
        num_objects, object_size)
    seek_ahead_thread = SeekAheadThread(seek_ahead_iterator, cancel_event,
                                        status_queue)
    seek_ahead_thread.join(self.thread_wait_time)
    status_queue.put(_ZERO_TASKS_TO_DO_ARGUMENT)
    ui_thread.join(self.thread_wait_time)

    if seek_ahead_thread.is_alive():
      seek_ahead_thread.terminate = True
      self.fail('SeekAheadThread is still alive.')

    message = stream.getvalue()

    if not message:
      self.fail('Status queue empty but SeekAheadThread should have posted '
                'summary message')

    total_size = num_objects * object_size
    self.assertEqual(
        message,
        'Estimated work for this command: objects: %s, total size: %s\n' %
        (num_objects, unit_util.MakeHumanReadable(total_size)))

  def testWithLocalFiles(self):
    """Tests SeekAheadThread with an actual directory."""
    tmpdir = self.CreateTempDir()
    num_files = 5
    total_size = 0

    # Create 5 files with sizes 0, 1, 2, 3, 4.
    for i in range(num_files):
      self.CreateTempFile(tmpdir=tmpdir,
                          file_name='obj%s' % str(i),
                          contents=b'a' * i)
      total_size += i

    # Recursively "copy" tmpdir.
    seek_ahead_iterator = SeekAheadNameExpansionIterator(
        'cp', 0, None, [tmpdir], True)

    cancel_event = threading.Event()
    status_queue = Queue.Queue()
    stream = six.StringIO()
    ui_controller = UIController()
    ui_thread = UIThread(status_queue, stream, ui_controller)

    seek_ahead_thread = SeekAheadThread(seek_ahead_iterator, cancel_event,
                                        status_queue)
    seek_ahead_thread.join(self.thread_wait_time)
    status_queue.put(_ZERO_TASKS_TO_DO_ARGUMENT)
    ui_thread.join(self.thread_wait_time)

    if seek_ahead_thread.is_alive():
      seek_ahead_thread.terminate = True
      self.fail('SeekAheadThread is still alive.')

    message = stream.getvalue()
    if not message:
      self.fail('Status queue empty but SeekAheadThread should have posted '
                'summary message')

    self.assertEqual(
        message,
        'Estimated work for this command: objects: %s, total size: %s\n' %
        (num_files, unit_util.MakeHumanReadable(total_size)))
