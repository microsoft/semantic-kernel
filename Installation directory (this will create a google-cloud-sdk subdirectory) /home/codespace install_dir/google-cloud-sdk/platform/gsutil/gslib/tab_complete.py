# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Shell tab completion."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import itertools
import json
import threading
import time

import boto

from boto.gs.acl import CannedACLStrings
from gslib.storage_url import IsFileUrlString
from gslib.storage_url import StorageUrlFromString
from gslib.storage_url import StripOneSlash
from gslib.utils.boto_util import GetTabCompletionCacheFilename
from gslib.utils.boto_util import GetTabCompletionLogFilename
from gslib.wildcard_iterator import CreateWildcardIterator

TAB_COMPLETE_CACHE_TTL = 15

_TAB_COMPLETE_MAX_RESULTS = 1000

_TIMEOUT_WARNING = """
Tab completion aborted (took >%ss), you may complete the command manually.
The timeout can be adjusted in the gsutil configuration file.
""".rstrip()


class CompleterType(object):
  CLOUD_BUCKET = 'cloud_bucket'
  CLOUD_OBJECT = 'cloud_object'
  CLOUD_OR_LOCAL_OBJECT = 'cloud_or_local_object'
  LOCAL_OBJECT = 'local_object'
  LOCAL_OBJECT_OR_CANNED_ACL = 'local_object_or_canned_acl'
  NO_OP = 'no_op'


class LocalObjectCompleter(object):
  """Completer object for local files."""

  def __init__(self):
    # This is only safe to import if argcomplete is present in the install
    # (which happens for Cloud SDK installs), so import on usage, not on load.
    # pylint: disable=g-import-not-at-top
    from argcomplete.completers import FilesCompleter
    self.files_completer = FilesCompleter()

  def __call__(self, prefix, **kwargs):
    return self.files_completer(prefix, **kwargs)


class LocalObjectOrCannedACLCompleter(object):
  """Completer object for local files and canned ACLs.

  Currently, only Google Cloud Storage canned ACL names are supported.
  """

  def __init__(self):
    self.local_object_completer = LocalObjectCompleter()

  def __call__(self, prefix, **kwargs):
    local_objects = self.local_object_completer(prefix, **kwargs)
    canned_acls = [acl for acl in CannedACLStrings if acl.startswith(prefix)]
    return local_objects + canned_acls


class TabCompletionCache(object):
  """Cache for tab completion results."""

  def __init__(self, prefix, results, timestamp, partial_results):
    self.prefix = prefix
    self.results = results
    self.timestamp = timestamp
    self.partial_results = partial_results

  @staticmethod
  def LoadFromFile(filename):
    """Instantiates the cache from a file.

    Args:
      filename: The file to load.
    Returns:
      TabCompletionCache instance with loaded data or an empty cache
          if the file cannot be loaded
    """
    try:
      with open(filename, 'r') as fp:
        cache_dict = json.loads(fp.read())
        prefix = cache_dict['prefix']
        results = cache_dict['results']
        timestamp = cache_dict['timestamp']
        partial_results = cache_dict['partial-results']
    except Exception:  # pylint: disable=broad-except
      # Guarding against incompatible format changes in the cache file.
      # Erring on the side of not breaking tab-completion in case of cache
      # issues.
      prefix = None
      results = []
      timestamp = 0
      partial_results = False

    return TabCompletionCache(prefix, results, timestamp, partial_results)

  def GetCachedResults(self, prefix):
    """Returns the cached results for prefix or None if not in cache."""
    current_time = time.time()
    if current_time - self.timestamp >= TAB_COMPLETE_CACHE_TTL:
      return None

    results = None

    if prefix == self.prefix:
      results = self.results
    elif (not self.partial_results and prefix.startswith(self.prefix) and
          prefix.count('/') == self.prefix.count('/')):
      results = [x for x in self.results if x.startswith(prefix)]

    if results is not None:
      # Update cache timestamp to make sure the cache entry does not expire if
      # the user is performing multiple completions in a single
      # bucket/subdirectory since we can answer these requests from the cache.
      # e.g. gs://prefix<tab> -> gs://prefix-mid<tab> -> gs://prefix-mid-suffix
      self.timestamp = time.time()
      return results

  def UpdateCache(self, prefix, results, partial_results):
    """Updates the in-memory cache with the results for the given prefix."""
    self.prefix = prefix
    self.results = results
    self.partial_results = partial_results
    self.timestamp = time.time()

  def WriteToFile(self, filename):
    """Writes out the cache to the given file."""
    json_str = json.dumps({
        'prefix': self.prefix,
        'results': self.results,
        'partial-results': self.partial_results,
        'timestamp': self.timestamp,
    })

    try:
      with open(filename, 'w') as fp:
        fp.write(json_str)
    except IOError:
      pass


class CloudListingRequestThread(threading.Thread):
  """Thread that performs a listing request for the given URL string."""

  def __init__(self, wildcard_url_str, gsutil_api):
    """Instantiates Cloud listing request thread.

    Args:
      wildcard_url_str: The URL to list.
      gsutil_api: gsutil Cloud API instance to use.
    """
    super(CloudListingRequestThread, self).__init__()
    self.daemon = True
    self._wildcard_url_str = wildcard_url_str
    self._gsutil_api = gsutil_api
    self.results = None

  def run(self):
    it = CreateWildcardIterator(
        self._wildcard_url_str,
        self._gsutil_api).IterAll(bucket_listing_fields=['name'])
    self.results = [
        str(c) for c in itertools.islice(it, _TAB_COMPLETE_MAX_RESULTS)
    ]


class TimeoutError(Exception):
  pass


class CloudObjectCompleter(object):
  """Completer object for Cloud URLs."""

  def __init__(self, gsutil_api, bucket_only=False):
    """Instantiates completer for Cloud URLs.

    Args:
      gsutil_api: gsutil Cloud API instance to use.
      bucket_only: Whether the completer should only match buckets.
    """
    self._gsutil_api = gsutil_api
    self._bucket_only = bucket_only

  def _PerformCloudListing(self, wildcard_url, timeout):
    """Perform a remote listing request for the given wildcard URL.

    Args:
      wildcard_url: The wildcard URL to list.
      timeout: Time limit for the request.
    Returns:
      Cloud resources matching the given wildcard URL.
    Raises:
      TimeoutError: If the listing does not finish within the timeout.
    """
    request_thread = CloudListingRequestThread(wildcard_url, self._gsutil_api)
    request_thread.start()
    request_thread.join(timeout)

    if request_thread.is_alive():
      # This is only safe to import if argcomplete is present in the install
      # (which happens for Cloud SDK installs), so import on usage, not on load.
      # pylint: disable=g-import-not-at-top
      import argcomplete
      argcomplete.warn(_TIMEOUT_WARNING % timeout)
      raise TimeoutError()

    results = request_thread.results

    return results

  def __call__(self, prefix, **kwargs):
    if not prefix:
      prefix = 'gs://'
    elif IsFileUrlString(prefix):
      return []

    wildcard_url = prefix + '*'
    url = StorageUrlFromString(wildcard_url)
    if self._bucket_only and not url.IsBucket():
      return []

    timeout = boto.config.getint('GSUtil', 'tab_completion_timeout', 5)
    if timeout == 0:
      return []

    start_time = time.time()

    cache = TabCompletionCache.LoadFromFile(GetTabCompletionCacheFilename())
    cached_results = cache.GetCachedResults(prefix)

    timing_log_entry_type = ''
    if cached_results is not None:
      results = cached_results
      timing_log_entry_type = ' (from cache)'
    else:
      try:
        results = self._PerformCloudListing(wildcard_url, timeout)
        if self._bucket_only and len(results) == 1:
          results = [StripOneSlash(results[0])]
        partial_results = (len(results) == _TAB_COMPLETE_MAX_RESULTS)
        cache.UpdateCache(prefix, results, partial_results)
      except TimeoutError:
        timing_log_entry_type = ' (request timeout)'
        results = []

    cache.WriteToFile(GetTabCompletionCacheFilename())

    end_time = time.time()
    num_results = len(results)
    elapsed_seconds = end_time - start_time
    _WriteTimingLog(
        '%s results%s in %.2fs, %.2f results/second for prefix: %s\n' %
        (num_results, timing_log_entry_type, elapsed_seconds,
         num_results / elapsed_seconds, prefix))

    return results


class CloudOrLocalObjectCompleter(object):
  """Completer object for Cloud URLs or local files.

  Invokes the Cloud object completer if the input looks like a Cloud URL and
  falls back to local file completer otherwise.
  """

  def __init__(self, gsutil_api):
    self.cloud_object_completer = CloudObjectCompleter(gsutil_api)
    self.local_object_completer = LocalObjectCompleter()

  def __call__(self, prefix, **kwargs):
    if IsFileUrlString(prefix):
      completer = self.local_object_completer
    else:
      completer = self.cloud_object_completer
    return completer(prefix, **kwargs)


class NoOpCompleter(object):
  """Completer that always returns 0 results."""

  def __call__(self, unused_prefix, **unused_kwargs):
    return []


def MakeCompleter(completer_type, gsutil_api):
  """Create a completer instance of the given type.

  Args:
    completer_type: The type of completer to create.
    gsutil_api: gsutil Cloud API instance to use.
  Returns:
    A completer instance.
  Raises:
    RuntimeError: if completer type is not supported.
  """
  if completer_type == CompleterType.CLOUD_OR_LOCAL_OBJECT:
    return CloudOrLocalObjectCompleter(gsutil_api)
  elif completer_type == CompleterType.LOCAL_OBJECT:
    return LocalObjectCompleter()
  elif completer_type == CompleterType.LOCAL_OBJECT_OR_CANNED_ACL:
    return LocalObjectOrCannedACLCompleter()
  elif completer_type == CompleterType.CLOUD_BUCKET:
    return CloudObjectCompleter(gsutil_api, bucket_only=True)
  elif completer_type == CompleterType.CLOUD_OBJECT:
    return CloudObjectCompleter(gsutil_api)
  elif completer_type == CompleterType.NO_OP:
    return NoOpCompleter()
  else:
    raise RuntimeError('Unknown completer "%s"' % completer_type)


def _WriteTimingLog(message):
  """Write an entry to the tab completion timing log, if it's enabled."""
  if boto.config.getbool('GSUtil', 'tab_completion_time_logs', False):
    with open(GetTabCompletionLogFilename(), 'ab') as fp:
      fp.write(message)
