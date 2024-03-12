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

"""Utility functions for gcloud app."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import os
import posixpath
import sys
import time
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import platforms
from googlecloudsdk.third_party.appengine.api import client_deployinfo
import six
from six.moves import urllib


class Error(exceptions.Error):
  """Exceptions for the appcfg module."""


class NoFieldsSpecifiedError(Error):
  """The user specified no fields to a command which requires at least one."""


class NoCloudSDKError(Error):
  """The module was unable to find Cloud SDK."""

  def __init__(self):
    super(NoCloudSDKError, self).__init__(
        'Unable to find a Cloud SDK installation.')


class NoAppengineSDKError(Error):
  """The module was unable to find the appengine SDK."""


class TimeoutError(Error):
  """An exception for when a retry with wait operation times out."""

  def __init__(self):
    super(TimeoutError, self).__init__(
        'Timed out waiting for the operation to complete.')


class RPCError(Error):
  """For when an error occurs when making an RPC call."""

  def __init__(self, url_error, body=''):
    super(RPCError, self).__init__(
        'Server responded with code [{code}]:\n  {reason}.\n  {body}'
        .format(code=url_error.code,
                reason=getattr(url_error, 'reason', '(unknown)'),
                body=body))
    self.url_error = url_error


def GetCloudSDKRoot():
  """Gets the directory of the root of the Cloud SDK, error if it doesn't exist.

  Raises:
    NoCloudSDKError: If there is no SDK root.

  Returns:
    str, The path to the root of the Cloud SDK.
  """
  sdk_root = config.Paths().sdk_root
  if not sdk_root:
    raise NoCloudSDKError()
  log.debug('Found Cloud SDK root: %s', sdk_root)
  return sdk_root


def GetAppEngineSDKRoot():
  """Gets the directory of the GAE SDK directory in the SDK.

  Raises:
    NoCloudSDKError: If there is no SDK root.
    NoAppengineSDKError: If the GAE SDK cannot be found.

  Returns:
    str, The path to the root of the GAE SDK within the Cloud SDK.
  """
  sdk_root = GetCloudSDKRoot()
  gae_sdk_dir = os.path.join(sdk_root, 'platform', 'google_appengine')
  if not os.path.isdir(gae_sdk_dir):
    raise NoAppengineSDKError()
  log.debug('Found App Engine SDK root: %s', gae_sdk_dir)

  return gae_sdk_dir


def GenerateVersionId(datetime_getter=datetime.datetime.now):
  """Generates a version id based off the current time.

  Args:
    datetime_getter: A function that returns a datetime.datetime instance.

  Returns:
    A version string based.
  """
  return datetime_getter().isoformat().lower().replace('-', '').replace(
      ':', '')[:15]


def ConvertToPosixPath(path):
  """Converts a native-OS path to /-separated: os.path.join('a', 'b')->'a/b'."""
  return posixpath.join(*path.split(os.path.sep))


def ConvertToCloudRegion(region):
  """Converts a App Engine region to the format used elsewhere in Cloud."""
  if region in {'europe-west', 'us-central'}:
    return region + '1'
  else:
    return region


def ShouldSkip(skip_files, path):
  """Returns whether the given path should be skipped by the skip_files field.

  A user can specify a `skip_files` field in their .yaml file, which is a list
  of regular expressions matching files that should be skipped. By this point in
  the code, it's been turned into one mega-regex that matches any file to skip.

  Args:
    skip_files: A regular expression object for files/directories to skip.
    path: str, the path to the file/directory which might be skipped (relative
      to the application root)

  Returns:
    bool, whether the file/dir should be skipped.
  """
  # On Windows, os.path.join uses the path separator '\' instead of '/'.
  # However, the skip_files regular expression always uses '/'.
  # To handle this, we'll replace '\' characters with '/' characters.
  path = ConvertToPosixPath(path)
  return skip_files.match(path)


def FileIterator(base, skip_files):
  """Walks a directory tree, returning all the files. Follows symlinks.

  Args:
    base: The base path to search for files under.
    skip_files: A regular expression object for files/directories to skip.

  Yields:
    Paths of files found, relative to base.
  """
  dirs = ['']

  while dirs:
    current_dir = dirs.pop()
    entries = set(os.listdir(os.path.join(base, current_dir)))
    for entry in sorted(entries):
      name = os.path.join(current_dir, entry)
      fullname = os.path.join(base, name)

      if os.path.isfile(fullname):
        if ShouldSkip(skip_files, name):
          log.info('Ignoring file [%s]: File matches ignore regex.', name)
        else:
          yield name
      elif os.path.isdir(fullname):
        if ShouldSkip(skip_files, name):
          log.info('Ignoring directory [%s]: Directory matches ignore regex.',
                   name)
        else:
          dirs.append(name)


def RetryWithBackoff(func, retry_notify_func,
                     initial_delay=1, backoff_factor=2,
                     max_delay=60, max_tries=20, raise_on_timeout=True):
  """Calls a function multiple times, backing off more and more each time.

  Args:
    func: f() -> (bool, value), A function that performs some operation that
      should be retried a number of times upon failure. If the first tuple
      element is True, we'll immediately return (True, value). If False, we'll
      delay a bit and try again, unless we've hit the 'max_tries' limit, in
      which case we'll return (False, value).
    retry_notify_func: f(value, delay) -> None, This function will be called
      immediately before the next retry delay.  'value' is the value returned
      by the last call to 'func'.  'delay' is the retry delay, in seconds
    initial_delay: int, Initial delay after first try, in seconds.
    backoff_factor: int, Delay will be multiplied by this factor after each
      try.
    max_delay: int, Maximum delay, in seconds.
    max_tries: int, Maximum number of tries (the first one counts).
    raise_on_timeout: bool, True to raise an exception if the operation times
      out instead of returning False.

  Returns:
    What the last call to 'func' returned, which is of the form (done, value).
    If 'done' is True, you know 'func' returned True before we ran out of
    retries.  If 'done' is False, you know 'func' kept returning False and we
    ran out of retries.

  Raises:
    TimeoutError: If raise_on_timeout is True and max_tries is exhausted.
  """
  delay = initial_delay
  try_count = max_tries
  value = None

  while True:
    try_count -= 1
    done, value = func()
    if done:
      return True, value
    if try_count <= 0:
      if raise_on_timeout:
        raise TimeoutError()
      return False, value
    retry_notify_func(value, delay)
    time.sleep(delay)
    delay = min(delay * backoff_factor, max_delay)


def RetryNoBackoff(callable_func, retry_notify_func, delay=5, max_tries=200):
  """Calls a function multiple times, with the same delay each time.

  Args:
    callable_func: A function that performs some operation that should be
      retried a number of times upon failure.  Signature: () -> (done, value)
      If 'done' is True, we'll immediately return (True, value)
      If 'done' is False, we'll delay a bit and try again, unless we've
      hit the 'max_tries' limit, in which case we'll return (False, value).
    retry_notify_func: This function will be called immediately before the
      next retry delay.  Signature: (value, delay) -> None
      'value' is the value returned by the last call to 'callable_func'
      'delay' is the retry delay, in seconds
    delay: Delay between tries, in seconds.
    max_tries: Maximum number of tries (the first one counts).

  Returns:
    What the last call to 'callable_func' returned, which is of the form
    (done, value).  If 'done' is True, you know 'callable_func' returned True
    before we ran out of retries.  If 'done' is False, you know 'callable_func'
    kept returning False and we ran out of retries.

  Raises:
    Whatever the function raises--an exception will immediately stop retries.
  """
  # A backoff_factor of 1 means the delay won't grow.
  return RetryWithBackoff(callable_func, retry_notify_func, delay, 1, delay,
                          max_tries)


def GetSourceName():
  """Gets the name of this source version."""
  return 'Google-appcfg-{0}'.format(config.CLOUD_SDK_VERSION)


def GetUserAgent():
  """Determines the value of the 'User-agent' header to use for HTTP requests.

  Returns:
    String containing the 'user-agent' header value.
  """
  product_tokens = []

  # SDK version
  product_tokens.append(config.CLOUDSDK_USER_AGENT)

  # Platform
  product_tokens.append(platforms.Platform.Current().UserAgentFragment())

  # Python version
  python_version = '.'.join(six.text_type(i) for i in sys.version_info)
  product_tokens.append('Python/%s' % python_version)

  return ' '.join(product_tokens)


class ClientDeployLoggingContext(object):
  """Context for sending and recording server rpc requests.

  Attributes:
    rpcserver: The AbstractRpcServer to use for the upload.
    requests: A list of client_deployinfo.Request objects to include
      with the client deploy log.
    time_func: Function to get the current time in milliseconds.
    request_params: A dictionary with params to append to requests
  """

  def __init__(self,
               rpcserver,
               request_params,
               usage_reporting,
               time_func=time.time):
    """Creates a new AppVersionUpload.

    Args:
      rpcserver: The RPC server to use. Should be an instance of HttpRpcServer
        or TestRpcServer.
      request_params: A dictionary with params to append to requests
      usage_reporting: Whether to actually upload data.
      time_func: Function to return the current time in millisecods
        (default time.time).
    """
    self.rpcserver = rpcserver
    self.request_params = request_params
    self.usage_reporting = usage_reporting
    self.time_func = time_func
    self.requests = []

  def Send(self, url, payload='', **kwargs):
    """Sends a request to the server, with common params."""
    start_time_usec = self.GetCurrentTimeUsec()
    request_size_bytes = len(payload)
    try:
      log.debug('Send: {0}, params={1}'.format(url, self.request_params))

      kwargs.update(self.request_params)
      result = self.rpcserver.Send(url, payload=payload, **kwargs)
      self._RegisterReqestForLogging(url, 200, start_time_usec,
                                     request_size_bytes)
      return result
    except RPCError as err:
      self._RegisterReqestForLogging(url, err.url_error.code, start_time_usec,
                                     request_size_bytes)
      raise

  def GetCurrentTimeUsec(self):
    """Returns the current time in microseconds."""
    return int(round(self.time_func() * 1000 * 1000))

  def _RegisterReqestForLogging(self, path, response_code, start_time_usec,
                                request_size_bytes):
    """Registers a request for client deploy logging purposes."""
    end_time_usec = self.GetCurrentTimeUsec()
    self.requests.append(client_deployinfo.Request(
        path=path,
        response_code=response_code,
        start_time_usec=start_time_usec,
        end_time_usec=end_time_usec,
        request_size_bytes=request_size_bytes))

  def LogClientDeploy(self, runtime, start_time_usec, success):
    """Logs a client deployment attempt.

    Args:
      runtime: The runtime for the app being deployed.
      start_time_usec: The start time of the deployment in micro seconds.
      success: True if the deployment succeeded otherwise False.
    """
    if not self.usage_reporting:
      log.info('Skipping usage reporting.')
      return
    end_time_usec = self.GetCurrentTimeUsec()
    try:
      info = client_deployinfo.ClientDeployInfoExternal(
          runtime=runtime,
          start_time_usec=start_time_usec,
          end_time_usec=end_time_usec,
          requests=self.requests,
          success=success,
          sdk_version=config.CLOUD_SDK_VERSION)
      self.Send('/api/logclientdeploy', info.ToYAML())
    except BaseException as e:  # pylint: disable=broad-except
      log.debug('Exception logging deploy info continuing - {0}'.format(e))


class RPCServer(object):
  """This wraps the underlying RPC server so we can make a nice error message.

  This will go away once we switch to just using our own http object.
  """

  def __init__(self, original_server):
    """Construct a new rpc server.

    Args:
      original_server: The server to wrap.
    """
    self._server = original_server

  def Send(self, *args, **kwargs):
    try:
      response = self._server.Send(*args, **kwargs)
      log.debug('Got response: %s', response)
      return response
    except urllib.error.HTTPError as e:
      # This is the message body, if included in e
      if hasattr(e, 'read'):
        body = e.read()
      else:
        body = ''
      exceptions.reraise(RPCError(e, body=body))
