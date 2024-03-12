# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Implementation of retrying logic."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import functools
import itertools
import math
import random
import sys
import time

from googlecloudsdk.core import exceptions

try:
  # Python 3.3 and above.
  collections_abc = collections.abc
except AttributeError:
  collections_abc = collections


_DEFAULT_JITTER_MS = 1000


class RetryerState(object):
  """Object that holds the state of the retryer."""

  def __init__(self, retrial, time_passed_ms, time_to_wait_ms):
    """Initializer for RetryerState.

    Args:
      retrial: int, the retry attempt we are currently at.
      time_passed_ms: int, number of ms that passed since we started retryer.
      time_to_wait_ms: int, number of ms to wait for the until next trial.
          If this number is -1, it means the iterable item that specifies the
          next sleep value has raised StopIteration.
    """
    self.retrial = retrial
    self.time_passed_ms = time_passed_ms
    self.time_to_wait_ms = time_to_wait_ms


class RetryException(Exception):
  """Raised to stop retrials on failure."""

  def __init__(self, message, last_result, state):
    self.message = message
    self.last_result = last_result
    self.state = state
    super(RetryException, self).__init__(message)

  def __str__(self):
    return ('last_result={last_result}, last_retrial={last_retrial}, '
            'time_passed_ms={time_passed_ms},'
            'time_to_wait={time_to_wait_ms}'.format(
                last_result=self.last_result,
                last_retrial=self.state.retrial,
                time_passed_ms=self.state.time_passed_ms,
                time_to_wait_ms=self.state.time_to_wait_ms))


class WaitException(RetryException):
  """Raised when timeout was reached."""


class MaxRetrialsException(RetryException):
  """Raised when too many retrials reached."""


class Retryer(object):
  """Retries a function based on specified retry strategy."""

  def __init__(self, max_retrials=None, max_wait_ms=None,
               exponential_sleep_multiplier=None, jitter_ms=_DEFAULT_JITTER_MS,
               status_update_func=None, wait_ceiling_ms=None):
    """Initializer for Retryer.

    Args:
      max_retrials: int, max number of retrials before raising RetryException.
      max_wait_ms: int, number of ms to wait before raising
      exponential_sleep_multiplier: float, The exponential factor to use on
          subsequent retries.
      jitter_ms: int, random [0, jitter_ms] additional value to wait.
      status_update_func: func(result, state) called right after each trial.
      wait_ceiling_ms: int, maximum wait time between retries, regardless of
          modifiers added like exponential multiplier or jitter.
    """

    self._max_retrials = max_retrials
    self._max_wait_ms = max_wait_ms
    self._exponential_sleep_multiplier = exponential_sleep_multiplier
    self._jitter_ms = jitter_ms
    self._status_update_func = status_update_func
    self._wait_ceiling_ms = wait_ceiling_ms

  def _RaiseIfStop(self, result, state):
    if self._max_retrials is not None and self._max_retrials <= state.retrial:
      raise MaxRetrialsException('Reached', result, state)
    if self._max_wait_ms is not None:
      if state.time_passed_ms + state.time_to_wait_ms > self._max_wait_ms:
        raise WaitException('Timeout', result, state)

  def _GetTimeToWait(self, last_retrial, sleep_ms):
    """Get time to wait after applying modifyers.

    Apply the exponential sleep multiplyer, jitter and ceiling limiting to the
    base sleep time.

    Args:
      last_retrial: int, which retry attempt we just tried. First try this is 0.
      sleep_ms: int, how long to wait between the current trials.

    Returns:
      int, ms to wait before trying next attempt with all waiting logic applied.
    """
    wait_time_ms = sleep_ms
    if wait_time_ms:
      if self._exponential_sleep_multiplier:
        # For exponential backoff, the amount to sleep is given by:
        #   wait_time_ms * (self._exponential_sleep_multiplier ** last_retrial)
        # If a small wait ceiling is provided, the number of retrials will
        # increase pretty quickly, and thus this quantity will eventually get
        # way too large, to the point of overflowing when converting to a float.
        # Thus, we cap it at a "reasonable" value of 100 years just to avoid
        # computing it if the number would be greater than that.
        hundred_years_ms = 100*365*86400*1000
        if self._exponential_sleep_multiplier > 1.0 and last_retrial > math.log(
            hundred_years_ms / wait_time_ms,
            self._exponential_sleep_multiplier):
          wait_time_ms = hundred_years_ms
        else:
          wait_time_ms *= self._exponential_sleep_multiplier ** last_retrial
      if self._jitter_ms:
        wait_time_ms += random.random() * self._jitter_ms
      if self._wait_ceiling_ms:
        wait_time_ms = min(wait_time_ms, self._wait_ceiling_ms)
      return wait_time_ms
    return 0

  def RetryOnException(self, func, args=None, kwargs=None,
                       should_retry_if=None, sleep_ms=None):
    """Retries the function if an exception occurs.

    Args:
      func: The function to call and retry.
      args: a sequence of positional arguments to be passed to func.
      kwargs: a dictionary of positional arguments to be passed to func.
      should_retry_if: func(exc_type, exc_value, exc_traceback, state) that
          returns True or False.
      sleep_ms: int or iterable for how long to wait between trials.

    Returns:
      Whatever the function returns.

    Raises:
      RetryException, WaitException: if function is retries too many times,
        or time limit is reached.
    """

    args = args if args is not None else ()
    kwargs = kwargs if kwargs is not None else {}

    def TryFunc():
      try:
        return func(*args, **kwargs), None
      except:  # pylint: disable=bare-except
        return None, sys.exc_info()

    if should_retry_if is None:
      should_retry = lambda x, s: x[1] is not None
    else:
      def ShouldRetryFunc(try_func_result, state):
        exc_info = try_func_result[1]
        if exc_info is None:
          # No exception, no reason to retry.
          return False
        return should_retry_if(exc_info[0], exc_info[1], exc_info[2], state)
      should_retry = ShouldRetryFunc

    result, exc_info = self.RetryOnResult(
        TryFunc, should_retry_if=should_retry, sleep_ms=sleep_ms)
    if exc_info:
      # Exception that was not retried was raised. Re-raise.
      exceptions.reraise(exc_info[1], tb=exc_info[2])
    return result

  def RetryOnResult(self, func, args=None, kwargs=None,
                    should_retry_if=None, sleep_ms=None):
    """Retries the function if the given condition is satisfied.

    Args:
      func: The function to call and retry.
      args: a sequence of arguments to be passed to func.
      kwargs: a dictionary of positional arguments to be passed to func.
      should_retry_if: result to retry on or func(result, RetryerState) that
          returns True or False if we should retry or not.
      sleep_ms: int or iterable, for how long to wait between trials.

    Returns:
      Whatever the function returns.

    Raises:
      MaxRetrialsException: function retried too many times.
      WaitException: time limit is reached.
    """
    args = args if args is not None else ()
    kwargs = kwargs if kwargs is not None else {}

    start_time_ms = _GetCurrentTimeMs()
    retrial = 0
    if callable(should_retry_if):
      should_retry = should_retry_if
    else:
      should_retry = lambda x, s: x == should_retry_if

    if isinstance(sleep_ms, collections_abc.Iterable):
      sleep_gen = iter(sleep_ms)
    else:
      sleep_gen = itertools.repeat(sleep_ms)

    while True:
      result = func(*args, **kwargs)
      time_passed_ms = _GetCurrentTimeMs() - start_time_ms
      try:
        sleep_from_gen = next(sleep_gen)
      except StopIteration:
        time_to_wait_ms = -1
      else:
        time_to_wait_ms = self._GetTimeToWait(retrial, sleep_from_gen)
      state = RetryerState(retrial, time_passed_ms, time_to_wait_ms)

      if not should_retry(result, state):
        return result

      if time_to_wait_ms == -1:
        raise MaxRetrialsException('Sleep iteration stop', result, state)
      if self._status_update_func:
        self._status_update_func(result, state)
      self._RaiseIfStop(result, state)
      _SleepMs(time_to_wait_ms)
      retrial += 1


def RetryOnException(f=None, max_retrials=None, max_wait_ms=None,
                     sleep_ms=None, exponential_sleep_multiplier=None,
                     jitter_ms=_DEFAULT_JITTER_MS,
                     status_update_func=None,
                     should_retry_if=None):
  """A decorator to retry on exceptions.

  Args:
    f: a function to run possibly multiple times
    max_retrials: int, max number of retrials before raising RetryException.
    max_wait_ms: int, number of ms to wait before raising
    sleep_ms: int or iterable, for how long to wait between trials.
    exponential_sleep_multiplier: float, The exponential factor to use on
        subsequent retries.
    jitter_ms: int, random [0, jitter_ms] additional value to wait.
    status_update_func: func(result, state) called right after each trail.
    should_retry_if: func(exc_type, exc_value, exc_traceback, state) that
        returns True or False.

  Returns:
    A version of f that is executed potentially multiple times and that
    yields the first returned value or the last exception raised.
  """

  if f is None:
    # Returns a decorator---based on retry Retry with max_retrials,
    # max_wait_ms, sleep_ms, etc. fixed.
    return functools.partial(
        RetryOnException,
        exponential_sleep_multiplier=exponential_sleep_multiplier,
        jitter_ms=jitter_ms,
        max_retrials=max_retrials,
        max_wait_ms=max_wait_ms,
        should_retry_if=should_retry_if,
        sleep_ms=sleep_ms,
        status_update_func=status_update_func)

  @functools.wraps(f)
  def DecoratedFunction(*args, **kwargs):
    retryer = Retryer(
        max_retrials=max_retrials,
        max_wait_ms=max_wait_ms,
        exponential_sleep_multiplier=exponential_sleep_multiplier,
        jitter_ms=jitter_ms,
        status_update_func=status_update_func)
    try:
      return retryer.RetryOnException(f, args=args, kwargs=kwargs,
                                      should_retry_if=should_retry_if,
                                      sleep_ms=sleep_ms)
    except MaxRetrialsException as mre:
      to_reraise = mre.last_result[1]
      exceptions.reraise(to_reraise[1], tb=to_reraise[2])

  return DecoratedFunction


def _GetCurrentTimeMs():
  return int(time.time() * 1000)


def _SleepMs(time_to_wait_ms):
  time.sleep(time_to_wait_ms / 1000.0)

