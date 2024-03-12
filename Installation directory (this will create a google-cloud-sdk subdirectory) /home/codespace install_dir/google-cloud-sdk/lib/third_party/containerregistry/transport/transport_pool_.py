# Copyright 2017 Google Inc. All Rights Reserved.
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
"""A threadsafe pool of httplib2.Http handlers."""

from __future__ import absolute_import

from __future__ import print_function

import threading

import httplib2
from six.moves import range  # pylint: disable=redefined-builtin



class Http(httplib2.Http):
  """A threadsafe pool of httplib2.Http transports."""

  def __init__(self, transport_factory, size=2):
    self._condition = threading.Condition(threading.Lock())
    self._transports = [transport_factory() for _ in range(size)]

  def _get_transport(self):
    with self._condition:
      while True:
        if self._transports:
          return self._transports.pop()

        # Nothing is available, wait until it is.
        # This releases the lock until a notification occurs.
        self._condition.wait()

  def _return_transport(self, transport):
    with self._condition:
      self._transports.append(transport)

      # We returned an item, notify a waiting thread.
      self._condition.notify(n=1)

  def request(self, *args, **kwargs):
    """This awaits a transport and delegates the request call.

    Args:
      *args: arguments to request.
      **kwargs: named arguments to request.

    Returns:
      tuple of response and content.
    """
    transport = self._get_transport()
    try:
      return transport.request(*args, **kwargs)
    finally:
      self._return_transport(transport)
