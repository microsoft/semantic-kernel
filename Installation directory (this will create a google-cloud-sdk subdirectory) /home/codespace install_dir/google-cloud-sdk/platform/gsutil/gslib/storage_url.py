# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""File and Cloud URL representation classes."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import re
import stat
import sys

from gslib.exception import CommandException
from gslib.exception import InvalidUrlError
from gslib.utils import system_util
from gslib.utils import text_util

# Matches provider strings of the form 'gs://'
PROVIDER_REGEX = re.compile(r'(?P<provider>[^:]*)://$')
# Matches bucket strings of the form 'gs://bucket'
BUCKET_REGEX = re.compile(r'(?P<provider>[^:]*)://(?P<bucket>[^/]*)/{0,1}$')
# Matches object strings of the form 'gs://bucket/obj'
OBJECT_REGEX = re.compile(
    r'(?P<provider>[^:]*)://(?P<bucket>[^/]*)/(?P<object>.*)')
# Matches versioned object strings of the form 'gs://bucket/obj#1234'
GS_GENERATION_REGEX = re.compile(r'(?P<object>.+)#(?P<generation>[0-9]+)$')
# Matches versioned object strings of the form 's3://bucket/obj#NULL'
S3_VERSION_REGEX = re.compile(r'(?P<object>.+)#(?P<version_id>.+)$')
# Matches file strings of the form 'file://dir/filename'
FILE_OBJECT_REGEX = re.compile(r'([^:]*://)(?P<filepath>.*)')
# Regex to determine if a string contains any wildcards.
WILDCARD_REGEX = re.compile(r'[*?\[\]]')

RELATIVE_PATH_SYMBOLS = frozenset(['.', '..'])


class StorageUrl(object):
  """Abstract base class for file and Cloud Storage URLs."""

  def Clone(self):
    raise NotImplementedError('Clone not overridden')

  def IsFileUrl(self):
    raise NotImplementedError('IsFileUrl not overridden')

  def IsCloudUrl(self):
    raise NotImplementedError('IsCloudUrl not overridden')

  def IsStream():
    raise NotImplementedError('IsStream not overridden')

  def IsFifo(self):
    raise NotImplementedError('IsFifo not overridden')

  def CreatePrefixUrl(self, wildcard_suffix=None):
    """Returns a prefix of this URL that can be used for iterating.

    Args:
      wildcard_suffix: If supplied, this wildcard suffix will be appended to the
                       prefix with a trailing slash before being returned.

    Returns:
      A prefix of this URL that can be used for iterating.

    If this URL contains a trailing slash, it will be stripped to create the
    prefix. This helps avoid infinite looping when prefixes are iterated, but
    preserves other slashes so that objects with '/' in the name are handled
    properly.

    For example, when recursively listing a bucket with the following contents:
      gs://bucket// <-- object named slash
      gs://bucket//one-dir-deep
    a top-level expansion with '/' as a delimiter will result in the following
    URL strings:
      'gs://bucket//' : OBJECT
      'gs://bucket//' : PREFIX
    If we right-strip all slashes from the prefix entry and add a wildcard
    suffix, we will get 'gs://bucket/*' which will produce identical results
    (and infinitely recurse).

    Example return values:
      ('gs://bucket/subdir/', '*') becomes 'gs://bucket/subdir/*'
      ('gs://bucket/', '*') becomes 'gs://bucket/*'
      ('gs://bucket/', None) becomes 'gs://bucket'
      ('gs://bucket/subdir//', '*') becomes 'gs://bucket/subdir//*'
      ('gs://bucket/subdir///', '**') becomes 'gs://bucket/subdir///**'
      ('gs://bucket/subdir/', '*') where 'subdir/' is an object becomes
           'gs://bucket/subdir/*', but iterating on this will return 'subdir/'
           as a BucketListingObject, so we will not recurse on it as a subdir
           during listing.
    """
    raise NotImplementedError('CreatePrefixUrl not overridden')

  def _WarnIfUnsupportedDoubleWildcard(self):
    """Warn if ** use may lead to undefined results."""
    # Accepted 'url_string' values with '**', where '^' = start, and '$' = end.
    # - ^**$
    # - ^**/
    # - /**$
    # - /**/
    if not self.object_name:
      return
    delimiter_bounded_url = self.delim + self.object_name + self.delim
    split_url = delimiter_bounded_url.split(
        '{delim}**{delim}'.format(delim=self.delim))
    removed_correct_double_wildcards_url_string = ''.join(split_url)
    if '**' in removed_correct_double_wildcards_url_string:
      # Found a center '**' not in the format '/**/'.
      # Not using logger.warning b/c it's too much overhead to pass the logger
      # object to every StorageUrl.
      sys.stderr.write(
          '** behavior is undefined if directly preceeded or followed by'
          ' with characters other than / in the cloud and {} locally.'.format(
              os.sep))

  @property
  def url_string(self):
    raise NotImplementedError('url_string not overridden')

  @property
  def versionless_url_string(self):
    raise NotImplementedError('versionless_url_string not overridden')

  def __eq__(self, other):
    return isinstance(other, StorageUrl) and self.url_string == other.url_string

  def __hash__(self):
    return hash(self.url_string)


class _FileUrl(StorageUrl):
  """File URL class providing parsing and convenience methods.

    This class assists with usage and manipulation of an
    (optionally wildcarded) file URL string.  Depending on the string
    contents, this class represents one or more directories or files.

    For File URLs, scheme is always file, bucket_name is always blank,
    and object_name contains the file/directory path.
  """

  def __init__(self, url_string, is_stream=False, is_fifo=False):
    self.scheme = 'file'
    self.delim = os.sep
    self.bucket_name = ''
    # If given a URI that starts with "<scheme>://", the object name should not
    # include that prefix.
    match = FILE_OBJECT_REGEX.match(url_string)
    if match and match.lastindex == 2:
      self.object_name = match.group(2)
    else:
      self.object_name = url_string
    # On Windows, the pathname component separator is "\" instead of "/". If we
    # find an occurrence of "/", replace it with "\" so that other logic can
    # rely on being able to split pathname components on `os.sep`.
    if system_util.IS_WINDOWS:
      self.object_name = self.object_name.replace('/', '\\')
    self.generation = None
    self.is_stream = is_stream
    self.is_fifo = is_fifo

    self._WarnIfUnsupportedDoubleWildcard()

  def Clone(self):
    return _FileUrl(self.url_string)

  def IsFileUrl(self):
    return True

  def IsCloudUrl(self):
    return False

  def IsStream(self):
    return self.is_stream

  def IsFifo(self):
    return self.is_fifo

  def IsDirectory(self):
    return (not self.IsStream() and not self.IsFifo() and
            os.path.isdir(self.object_name))

  def CreatePrefixUrl(self, wildcard_suffix=None):
    return self.url_string

  @property
  def url_string(self):
    return '%s://%s' % (self.scheme, self.object_name)

  @property
  def versionless_url_string(self):
    return self.url_string

  def __str__(self):
    return self.url_string


class _CloudUrl(StorageUrl):
  """Cloud URL class providing parsing and convenience methods.

    This class assists with usage and manipulation of an
    (optionally wildcarded) cloud URL string.  Depending on the string
    contents, this class represents a provider, bucket(s), or object(s).

    This class operates only on strings.  No cloud storage API calls are
    made from this class.
  """

  def __init__(self, url_string):
    self.scheme = None
    self.delim = '/'
    self.bucket_name = None
    self.object_name = None
    self.generation = None
    provider_match = PROVIDER_REGEX.match(url_string)
    bucket_match = BUCKET_REGEX.match(url_string)
    if provider_match:
      self.scheme = provider_match.group('provider')
    elif bucket_match:
      self.scheme = bucket_match.group('provider')
      self.bucket_name = bucket_match.group('bucket')
    else:
      object_match = OBJECT_REGEX.match(url_string)
      if object_match:
        self.scheme = object_match.group('provider')
        self.bucket_name = object_match.group('bucket')
        self.object_name = object_match.group('object')
        if self.object_name == '.' or self.object_name == '..':
          raise InvalidUrlError('%s is an invalid root-level object name' %
                                self.object_name)
        if self.scheme == 'gs':
          generation_match = GS_GENERATION_REGEX.match(self.object_name)
          if generation_match:
            self.object_name = generation_match.group('object')
            self.generation = generation_match.group('generation')
        elif self.scheme == 's3':
          version_match = S3_VERSION_REGEX.match(self.object_name)
          if version_match:
            self.object_name = version_match.group('object')
            self.generation = version_match.group('version_id')
      else:
        raise InvalidUrlError(
            'CloudUrl: URL string %s did not match URL regex' % url_string)

    if url_string[(len(self.scheme) + len('://')):].startswith(self.delim):
      raise InvalidUrlError(
          'Cloud URL scheme should be followed by colon and two slashes: "://".'
          ' Found: "{}"'.format(url_string))

    self._WarnIfUnsupportedDoubleWildcard()

  def Clone(self):
    return _CloudUrl(self.url_string)

  def IsFileUrl(self):
    return False

  def IsCloudUrl(self):
    return True

  def IsStream(self):
    raise NotImplementedError('IsStream not supported on CloudUrl')

  def IsFifo(self):
    raise NotImplementedError('IsFifo not supported on CloudUrl')

  def IsBucket(self):
    return bool(self.bucket_name and not self.object_name)

  def IsObject(self):
    return bool(self.bucket_name and self.object_name)

  def HasGeneration(self):
    return bool(self.generation)

  def IsProvider(self):
    return bool(self.scheme and not self.bucket_name)

  def CreatePrefixUrl(self, wildcard_suffix=None):
    prefix = StripOneSlash(self.versionless_url_string)
    if wildcard_suffix:
      prefix = '%s/%s' % (prefix, wildcard_suffix)
    return prefix

  @property
  def bucket_url_string(self):
    return '%s://%s/' % (self.scheme, self.bucket_name)

  @property
  def url_string(self):
    url_str = self.versionless_url_string
    if self.HasGeneration():
      url_str += '#%s' % self.generation
    return url_str

  @property
  def versionless_url_string(self):
    if self.IsProvider():
      return '%s://' % self.scheme
    elif self.IsBucket():
      return self.bucket_url_string
    return '%s://%s/%s' % (self.scheme, self.bucket_name, self.object_name)

  def __str__(self):
    return self.url_string


def GetSchemeFromUrlString(url_str):
  """Returns scheme component of a URL string."""

  end_scheme_idx = url_str.find('://')
  if end_scheme_idx == -1:
    # File is the default scheme.
    return 'file'
  else:
    return url_str[0:end_scheme_idx].lower()


def IsKnownUrlScheme(scheme_str):
  return scheme_str in ('file', 's3', 'gs')


def _GetPathFromUrlString(url_str):
  """Returns path component of a URL string."""

  end_scheme_idx = url_str.find('://')
  if end_scheme_idx == -1:
    return url_str
  else:
    return url_str[end_scheme_idx + 3:]


def ContainsWildcard(url_string):
  """Checks whether url_string contains a wildcard.

  Args:
    url_string: URL string to check.

  Returns:
    bool indicator.
  """
  return bool(WILDCARD_REGEX.search(url_string))


def GenerationFromUrlAndString(url, generation):
  """Decodes a generation from a StorageURL and a generation string.

  This is used to represent gs and s3 versioning.

  Args:
    url: StorageUrl representing the object.
    generation: Long or string representing the object's generation or
                version.

  Returns:
    Valid generation string for use in URLs.
  """
  if url.scheme == 's3' and generation:
    return text_util.DecodeLongAsString(generation)
  return generation


def HaveFileUrls(args_to_check):
  """Checks whether args_to_check contain any file URLs.

  Args:
    args_to_check: Command-line argument subset to check.

  Returns:
    True if args_to_check contains any file URLs.
  """
  for url_str in args_to_check:
    storage_url = StorageUrlFromString(url_str)
    if storage_url.IsFileUrl():
      return True
  return False


def HaveProviderUrls(args_to_check):
  """Checks whether args_to_check contains any provider URLs (like 'gs://').

  Args:
    args_to_check: Command-line argument subset to check.

  Returns:
    True if args_to_check contains any provider URLs.
  """
  for url_str in args_to_check:
    storage_url = StorageUrlFromString(url_str)
    if storage_url.IsCloudUrl() and storage_url.IsProvider():
      return True
  return False


def IsCloudSubdirPlaceholder(url, blr=None):
  """Determines if a StorageUrl is a cloud subdir placeholder.

  This function is needed because GUI tools (like the GCS cloud console) allow
  users to create empty "folders" by creating a placeholder object; and parts
  of gsutil need to treat those placeholder objects specially. For example,
  gsutil rsync needs to avoid downloading those objects because they can cause
  conflicts (see comments in rsync command for details).

  We currently detect two cases:
    - Cloud objects whose name ends with '_$folder$'
    - Cloud objects whose name ends with '/'

  Args:
    url: (gslib.storage_url.StorageUrl) The URL to be checked.
    blr: (gslib.BucketListingRef or None) The blr to check, or None if not
        available. If `blr` is None, size won't be checked.

  Returns:
    (bool) True if the URL is a cloud subdir placeholder, otherwise False.
  """
  if not url.IsCloudUrl():
    return False
  url_str = url.url_string
  if url_str.endswith('_$folder$'):
    return True
  if blr and blr.IsObject():
    size = blr.root_object.size
  else:
    size = 0
  return size == 0 and url_str.endswith('/')


def IsFileUrlString(url_str):
  """Returns whether a string is a file URL."""

  return GetSchemeFromUrlString(url_str) == 'file'


def StorageUrlFromString(url_str):
  """Static factory function for creating a StorageUrl from a string."""

  scheme = GetSchemeFromUrlString(url_str)

  if not IsKnownUrlScheme(scheme):
    raise InvalidUrlError('Unrecognized scheme "%s"' % scheme)
  if scheme == 'file':
    path = _GetPathFromUrlString(url_str)
    is_stream = (path == '-')
    is_fifo = False
    try:
      is_fifo = stat.S_ISFIFO(os.stat(path).st_mode)
    except OSError:
      pass
    return _FileUrl(url_str, is_stream=is_stream, is_fifo=is_fifo)
  return _CloudUrl(url_str)


def StripOneSlash(url_str):
  if url_str and url_str.endswith('/'):
    return url_str[:-1]
  return url_str


def UrlsAreForSingleProvider(url_args):
  """Tests whether the URLs are all for a single provider.

  Args:
    url_args: (Iterable[str]) Collection of strings to check.

  Returns:
    True if all URLs are for single provider; False if `url_args` was empty (as
    this would not result in a single unique provider) or URLs targeted multiple
    unique providers.
  """
  provider = None
  url = None
  for url_str in url_args:
    url = StorageUrlFromString(url_str)
    if not provider:
      provider = url.scheme
    elif url.scheme != provider:
      return False
  return provider is not None


def UrlsAreMixOfBucketsAndObjects(urls):
  """Tests whether the URLs are a mix of buckets and objects.

  Args:
    url_args: (Iterable[gslib.storage_url.StorageUrl]) Collection of URLs to
    check.

  Returns:
    True if URLs are a mix of buckets and objects. False if URLs are all buckets
    or all objects. None if invalid Cloud URLs are included.
  """
  if all(url.IsCloudUrl() for url in urls):
    are_buckets = list(map(lambda x: x.IsBucket(), urls))
    return any(are_buckets) and not all(are_buckets)


def RaiseErrorIfUrlsAreMixOfBucketsAndObjects(urls, recursion_requested):
  """Raises error if mix of buckets and objects adjusted for recursion."""
  if UrlsAreMixOfBucketsAndObjects(urls) and not recursion_requested:
    raise CommandException('Cannot operate on a mix of buckets and objects.')