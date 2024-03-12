# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Retry decorators for calls raising exceptions.

This module is used mostly to decorate all integration points where the code
makes calls to remote services. Searching through the code base for @retry
should find all such places. For this reason even places where retry is not
needed right now use a @retry.no_retries decorator.
"""

import logging
import random
import sys
import time
import traceback

from google.cloud.ml.util import _exceptions

from six import reraise


class FuzzedExponentialIntervals(object):
  """Iterable for intervals that are exponentially spaced, with fuzzing.

  On iteration, yields retry interval lengths, in seconds. Every iteration over
  this iterable will yield differently fuzzed interval lengths, as long as fuzz
  is nonzero.

  Args:
    initial_delay_secs: The delay before the first retry, in seconds.
    num_retries: The total number of times to retry.
    factor: The exponential factor to use on subsequent retries.
      Default is 2 (doubling).
    fuzz: A value between 0 and 1, indicating the fraction of fuzz. For a
      given delay d, the fuzzed delay is randomly chosen between
      [(1 - fuzz) * d, d].
    max_delay_sec: Maximum delay (in seconds). After this limit is reached,
      further tries use max_delay_sec instead of exponentially increasing
      the time. Defaults to 5 minutes.
  """

  def __init__(self,
               initial_delay_secs,
               num_retries,
               factor=2,
               fuzz=0.5,
               max_delay_secs=30):
    self._initial_delay_secs = initial_delay_secs
    self._num_retries = num_retries
    self._factor = factor
    if not 0 <= fuzz <= 1:
      raise ValueError('Fuzz parameter expected to be in [0, 1] range.')
    self._fuzz = fuzz
    self._max_delay_secs = max_delay_secs

  def __iter__(self):
    current_delay_secs = min(self._max_delay_secs, self._initial_delay_secs)
    for _ in range(self._num_retries):
      fuzz_multiplier = 1 - self._fuzz + random.random() * self._fuzz
      yield current_delay_secs * fuzz_multiplier
      current_delay_secs = min(self._max_delay_secs,
                               current_delay_secs * self._factor)


def retry_on_server_errors_filter(exception):
  """Filter allowing retries on server errors and non-HttpErrors."""
  if isinstance(exception, _exceptions._RequestException):  # pylint: disable=protected-access
    if exception.status >= 500:
      return True
    else:
      return False
  else:
    # We may get here for non HttpErrors such as socket timeouts, SSL
    # exceptions, etc.
    return True


class Clock(object):
  """A simple clock implementing sleep()."""

  def sleep(self, value):
    time.sleep(value)


def no_retries(fun):
  """A retry decorator for places where we do not want retries."""
  return with_exponential_backoff(retry_filter=lambda _: False, clock=None)(fun)


def with_exponential_backoff(num_retries=10,
                             initial_delay_secs=1,
                             logger=logging.warning,
                             retry_filter=retry_on_server_errors_filter,
                             clock=Clock(),
                             fuzz=True):
  """Decorator with arguments that control the retry logic.

  Args:
    num_retries: The total number of times to retry.
    initial_delay_secs: The delay before the first retry, in seconds.
    logger: A callable used to report en exception. Must have the same signature
      as functions in the standard logging module. The default is
      logging.warning.
    retry_filter: A callable getting the exception raised and returning True
      if the retry should happen. For instance we do not want to retry on
      404 Http errors most of the time. The default value will return true
      for server errors (HTTP status code >= 500) and non Http errors.
    clock: A clock object implementing a sleep method. The default clock will
      use time.sleep().
    fuzz: True if the delay should be fuzzed (default). During testing False
      can be used so that the delays are not randomized.

  Returns:
    As per Python decorators with arguments pattern returns a decorator
    for the function which in turn will return the wrapped (decorated) function.

  The decorator is intended to be used on callables that make HTTP or RPC
  requests that can temporarily timeout or have transient errors. For instance
  the make_http_request() call below will be retried 16 times with exponential
  backoff and fuzzing of the delay interval (default settings).

  from cloudml.util import retry
  # ...
  @retry.with_exponential_backoff()
  make_http_request(args)
  """

  def real_decorator(fun):
    """The real decorator whose purpose is to return the wrapped function."""

    retry_intervals = iter(
        FuzzedExponentialIntervals(
            initial_delay_secs, num_retries, fuzz=0.5 if fuzz else 0))

    def wrapper(*args, **kwargs):
      while True:
        try:
          return fun(*args, **kwargs)
        except Exception as exn:  # pylint: disable=broad-except
          if not retry_filter(exn):
            raise
          # Get the traceback object for the current exception. The
          # sys.exc_info() function returns a tuple with three elements:
          # exception type, exception value, and exception traceback.
          exn_traceback = sys.exc_info()[2]
          try:
            try:
              sleep_interval = next(retry_intervals)
            except StopIteration:
              # Re-raise the original exception since we finished the retries.
              reraise(type(exn), exn, exn_traceback)

            logger(
                'Retry with exponential backoff: waiting for %s seconds before '
                'retrying %s because we caught exception: %s '
                'Traceback for above exception (most recent call last):\n%s',
                sleep_interval,
                getattr(fun, '__name__', str(fun)),
                ''.join(traceback.format_exception_only(exn.__class__, exn)),
                ''.join(traceback.format_tb(exn_traceback)))
            clock.sleep(sleep_interval)
          finally:
            # Traceback objects in locals can cause reference cycles that will
            # prevent garbage collection. Clear it now since we do not need
            # it anymore.
            if sys.version_info < (3, 0):  # only for py 2
              sys.exc_clear()
            exn_traceback = None

    return wrapper

  return real_decorator
