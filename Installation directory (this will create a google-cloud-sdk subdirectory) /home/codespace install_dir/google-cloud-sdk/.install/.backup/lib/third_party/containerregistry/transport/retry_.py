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
"""This package facilitates retries for HTTP/REST requests to the registry."""



import logging
import time

from containerregistry.transport import nested

import httplib2
import six.moves.http_client

DEFAULT_SOURCE_TRANSPORT_CALLABLE = httplib2.Http
DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF_FACTOR = 0.5
if six.PY3:
  import builtins  # pylint: disable=g-import-not-at-top,import-error
  BrokenPipeError = builtins.BrokenPipeError
  RETRYABLE_EXCEPTION_TYPES = [
      BrokenPipeError,
      six.moves.http_client.IncompleteRead,
      six.moves.http_client.ResponseNotReady
  ]
else:
  RETRYABLE_EXCEPTION_TYPES = [
      six.moves.http_client.IncompleteRead,
      six.moves.http_client.ResponseNotReady
  ]


def ShouldRetry(err):
  for exception_type in RETRYABLE_EXCEPTION_TYPES:
    if isinstance(err, exception_type):
      return True

  return False


class Factory(object):
  """A factory for creating RetryTransports."""

  def __init__(self):
    self.kwargs = {}
    self.source_transport_callable = DEFAULT_SOURCE_TRANSPORT_CALLABLE

  def WithSourceTransportCallable(self, source_transport_callable):
    self.source_transport_callable = source_transport_callable
    return self

  def WithMaxRetries(self, max_retries):
    self.kwargs['max_retries'] = max_retries
    return self

  def WithBackoffFactor(self, backoff_factor):
    self.kwargs['backoff_factor'] = backoff_factor
    return self

  def WithShouldRetryFunction(self, should_retry_fn):
    self.kwargs['should_retry_fn'] = should_retry_fn
    return self

  def Build(self):
    """Returns a RetryTransport constructed with the given values."""
    return RetryTransport(self.source_transport_callable(), **self.kwargs)


class RetryTransport(nested.NestedTransport):
  """A wrapper for the given transport which automatically retries errors."""

  def __init__(self,
               source_transport,
               max_retries = DEFAULT_MAX_RETRIES,
               backoff_factor = DEFAULT_BACKOFF_FACTOR,
               should_retry_fn = ShouldRetry):
    super(RetryTransport, self).__init__(source_transport)
    self._max_retries = max_retries
    self._backoff_factor = backoff_factor
    self._should_retry = should_retry_fn

  def request(self, *args, **kwargs):
    """Does the request, exponentially backing off and retrying as appropriate.

    Backoff is backoff_factor * (2 ^ (retry #)) seconds.
    Args:
      *args: The sequence of positional arguments to forward to the source
        transport.
      **kwargs: The keyword arguments to forward to the source transport.

    Returns:
      The response of the HTTP request, and its contents.
    """
    retries = 0
    while True:
      try:
        return self.source_transport.request(*args, **kwargs)
      except Exception as err:  # pylint: disable=broad-except
        if retries >= self._max_retries or not self._should_retry(err):
          raise

        logging.error('Retrying after exception %s.', err)
        retries += 1
        time.sleep(self._backoff_factor * (2**retries))
        continue
