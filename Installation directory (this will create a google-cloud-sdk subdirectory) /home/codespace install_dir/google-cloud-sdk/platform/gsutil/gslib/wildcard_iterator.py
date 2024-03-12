# -*- coding: utf-8 -*-
# Copyright 2010 Google Inc. All Rights Reserved.
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
"""Wildcard iterator class and supporting functions."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import fnmatch
import glob
import logging
import os
import re
import textwrap

import six

from gslib.bucket_listing_ref import BucketListingBucket
from gslib.bucket_listing_ref import BucketListingObject
from gslib.bucket_listing_ref import BucketListingPrefix
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import CloudApi
from gslib.cloud_api import NotFoundException
from gslib.exception import CommandException
from gslib.storage_url import ContainsWildcard
from gslib.storage_url import GenerationFromUrlAndString
from gslib.storage_url import StorageUrlFromString
from gslib.storage_url import StripOneSlash
from gslib.storage_url import WILDCARD_REGEX
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils.constants import UTF8
from gslib.utils.text_util import FixWindowsEncodingIfNeeded
from gslib.utils.text_util import PrintableStr

if six.PY3:
  # StandardError was removed, so use the base exception type instead
  StandardError = Exception

FLAT_LIST_REGEX = re.compile(r'(?P<before>.*?)\*\*(?P<after>.*)')

_UNICODE_EXCEPTION_TEXT = (
    'Invalid Unicode path encountered (%s). gsutil cannot proceed '
    'with such files present. Please remove or rename this file and '
    'try again. NOTE: the path printed above replaces the '
    'problematic characters with a hex-encoded printable '
    'representation. For more details (including how to convert to a '
    'gsutil-compatible encoding) see `gsutil help encoding`.')


class WildcardIterator(object):
  """Class for iterating over Google Cloud Storage strings containing wildcards.

  The base class is abstract; you should instantiate using the
  wildcard_iterator() static factory method, which chooses the right
  implementation depending on the base string.
  """

  # TODO: Standardize on __str__ and __repr__ here and elsewhere.  Define both
  # and make one return the other.
  def __repr__(self):
    """Returns string representation of WildcardIterator."""
    return 'WildcardIterator(%s)' % self.wildcard_url.url_string


class CloudWildcardIterator(WildcardIterator):
  """WildcardIterator subclass for buckets, bucket subdirs and objects.

  Iterates over BucketListingRef matching the Url string wildcard. It's
  much more efficient to first get metadata that's available in the Bucket
  (for example to get the name and size of each object), because that
  information is available in the object list results.
  """

  def __init__(self,
               wildcard_url,
               gsutil_api,
               all_versions=False,
               project_id=None,
               logger=None):
    """Instantiates an iterator that matches the wildcard URL.

    Args:
      wildcard_url: CloudUrl that contains the wildcard to iterate.
      gsutil_api: Cloud storage interface.  Passed in for thread safety, also
                  settable for testing/mocking.
      all_versions: If true, the iterator yields all versions of objects
                    matching the wildcard.  If false, yields just the live
                    object version.
      project_id: Project ID to use for bucket listings.
      logger: logging.Logger used for outputting debug messages during
              iteration. If None, the root logger will be used.
    """
    self.wildcard_url = wildcard_url
    self.all_versions = all_versions
    self.gsutil_api = gsutil_api
    self.project_id = project_id
    self.logger = logger or logging.getLogger()

  def __iter__(self,
               bucket_listing_fields=None,
               expand_top_level_buckets=False):
    """Iterator that gets called when iterating over the cloud wildcard.

    In the case where no wildcard is present, returns a single matching object,
    single matching prefix, or one of each if both exist.

    Args:
      bucket_listing_fields: Iterable fields to include in bucket listings.
                             Ex. ['name', 'acl'].  Iterator is
                             responsible for converting these to list-style
                             format ['items/name', 'items/acl'] as well as
                             adding any fields necessary for listing such as
                             prefixes.  API implementation is responsible for
                             adding pagination fields.  If this is None,
                             all fields are returned.
      expand_top_level_buckets: If true, yield no BUCKET references.  Instead,
                                expand buckets into top-level objects and
                                prefixes.

    Yields:
      BucketListingRef of type BUCKET, OBJECT or PREFIX.
    """
    single_version_request = self.wildcard_url.HasGeneration()

    # For wildcard expansion purposes, we need at a minimum the name of
    # each object and prefix.  If we're not using the default of requesting
    # all fields, make sure at least these are requested.  The Cloud API
    # tolerates specifying the same field twice.
    get_fields = None
    if bucket_listing_fields:
      get_fields = set()
      for field in bucket_listing_fields:
        get_fields.add(field)
      bucket_listing_fields = self._GetToListFields(
          get_fields=bucket_listing_fields)
      bucket_listing_fields.update(['items/name', 'prefixes'])
      get_fields.update(['name'])
      # If we're making versioned requests, ensure generation and
      # metageneration are also included.
      if single_version_request or self.all_versions:
        bucket_listing_fields.update(
            ['items/generation', 'items/metageneration'])
        get_fields.update(['generation', 'metageneration'])

    # Handle bucket wildcarding, if any, in _ExpandBucketWildcards. Then
    # iterate over the expanded bucket strings and handle any object
    # wildcarding.
    for bucket_listing_ref in self._ExpandBucketWildcards(bucket_fields=['id']):
      bucket_url_string = bucket_listing_ref.url_string
      if self.wildcard_url.IsBucket():
        # IsBucket() guarantees there are no prefix or object wildcards, and
        # thus this is a top-level listing of buckets.
        if expand_top_level_buckets:
          url = StorageUrlFromString(bucket_url_string)
          for obj_or_prefix in self.gsutil_api.ListObjects(
              url.bucket_name,
              delimiter='/',
              all_versions=self.all_versions,
              provider=self.wildcard_url.scheme,
              fields=bucket_listing_fields):
            if obj_or_prefix.datatype == CloudApi.CsObjectOrPrefixType.OBJECT:
              yield self._GetObjectRef(bucket_url_string,
                                       obj_or_prefix.data,
                                       with_version=self.all_versions)
            else:  # CloudApi.CsObjectOrPrefixType.PREFIX:
              yield self._GetPrefixRef(bucket_url_string, obj_or_prefix.data)
        else:
          yield bucket_listing_ref
      else:
        # By default, assume a non-wildcarded URL is an object, not a prefix.
        # This prevents unnecessary listings (which are slower, more expensive,
        # and also subject to eventual consistency).
        if (not ContainsWildcard(self.wildcard_url.url_string) and
            self.wildcard_url.IsObject() and not self.all_versions):
          try:
            get_object = self.gsutil_api.GetObjectMetadata(
                self.wildcard_url.bucket_name,
                self.wildcard_url.object_name,
                generation=self.wildcard_url.generation,
                provider=self.wildcard_url.scheme,
                fields=get_fields)
            yield self._GetObjectRef(self.wildcard_url.bucket_url_string,
                                     get_object,
                                     with_version=(self.all_versions or
                                                   single_version_request))
            return
          except (NotFoundException, AccessDeniedException):
            # It's possible this is a prefix - try to list instead.
            pass

        # Expand iteratively by building prefix/delimiter bucket listing
        # request, filtering the results per the current level's wildcard
        # (if present), and continuing with the next component of the
        # wildcard. See _BuildBucketFilterStrings() documentation for details.
        if single_version_request:
          url_string = '%s%s#%s' % (bucket_url_string,
                                    self.wildcard_url.object_name,
                                    self.wildcard_url.generation)
        else:
          # Rstrip any prefixes to correspond with rstripped prefix wildcard
          # from _BuildBucketFilterStrings().
          url_string = '%s%s' % (
              bucket_url_string, StripOneSlash(self.wildcard_url.object_name) or
              '/')  # Cover root object named '/' case.
        urls_needing_expansion = [url_string]
        while urls_needing_expansion:
          url = StorageUrlFromString(urls_needing_expansion.pop(0))
          (prefix, delimiter, prefix_wildcard,
           suffix_wildcard) = (self._BuildBucketFilterStrings(url.object_name))
          regex_patterns = self._GetRegexPatterns(prefix_wildcard)

          # If we have a suffix wildcard, we only care about listing prefixes.
          listing_fields = (set(['prefixes'])
                            if suffix_wildcard else bucket_listing_fields)

          # List bucket for objects matching prefix up to delimiter.
          for obj_or_prefix in self.gsutil_api.ListObjects(
              url.bucket_name,
              prefix=prefix,
              delimiter=delimiter,
              all_versions=self.all_versions or single_version_request,
              provider=self.wildcard_url.scheme,
              fields=listing_fields):
            for pattern in regex_patterns:
              if obj_or_prefix.datatype == CloudApi.CsObjectOrPrefixType.OBJECT:
                gcs_object = obj_or_prefix.data
                if pattern.match(gcs_object.name):
                  if not suffix_wildcard or (StripOneSlash(gcs_object.name)
                                             == suffix_wildcard):
                    if not single_version_request or (
                        self._SingleVersionMatches(gcs_object.generation)):
                      yield self._GetObjectRef(
                          bucket_url_string,
                          gcs_object,
                          with_version=(self.all_versions or
                                        single_version_request))
                  break
              else:  # CloudApi.CsObjectOrPrefixType.PREFIX
                prefix = obj_or_prefix.data

                if ContainsWildcard(prefix):
                  # TODO: Disambiguate user-supplied strings from iterated
                  # prefix and object names so that we can better reason
                  # about wildcards and handle this case without raising
                  # an error.
                  raise CommandException(
                      'Cloud folder %s%s contains a wildcard; gsutil does '
                      'not currently support objects with wildcards in their '
                      'name.' % (bucket_url_string, prefix))

                # If the prefix ends with a slash, remove it.  Note that we only
                # remove one slash so that we can successfully enumerate dirs
                # containing multiple slashes.
                rstripped_prefix = StripOneSlash(prefix)
                if pattern.match(rstripped_prefix):
                  if suffix_wildcard and rstripped_prefix != suffix_wildcard:
                    # There's more wildcard left to expand.
                    url_append_string = '%s%s' % (bucket_url_string,
                                                  rstripped_prefix + '/' +
                                                  suffix_wildcard)
                    urls_needing_expansion.append(url_append_string)
                  else:
                    # No wildcard to expand, just yield the prefix.
                    yield self._GetPrefixRef(bucket_url_string, prefix)
                  break

  def _GetRegexPatterns(self, wildcard_pattern):
    """Returns list of regex patterns derived from the wildcard patterns.

    Args:
      wildcard_pattern (str): A wilcard_pattern to filter the resources.

    Returns:
      List of compiled regex patterns.

    This translates the wildcard_pattern and also creates some additional
    patterns so that we can treat ** in a/b/c/**/d.txt as zero or more folders.
    This means, a/b/c/d.txt will also be returned along with a/b/c/e/f/d.txt.
    """
    # Case 1: The original pattern should always be present.
    wildcard_patterns = [wildcard_pattern]
    if '/**/' in wildcard_pattern:
      # Case 2: Will fetch object gs://bucket/dir1/a.txt if pattern is
      # gs://bucket/dir1/**/a.txt
      updated_pattern = wildcard_pattern.replace('/**/', '/')
      wildcard_patterns.append(updated_pattern)
    else:
      updated_pattern = wildcard_pattern

    for pattern in (wildcard_pattern, updated_pattern):
      if pattern.startswith('**/'):
        # Case 3 (using wildcard_pattern): Will fetch object gs://bucket/a.txt
        # if pattern is gs://bucket/**/a.txt. Note that '/**/' will match
        # '/a.txt' not 'a.txt'.
        # Case 4:(using updated_pattern) Will fetch gs://bucket/dir1/dir2/a.txt
        # if the pattern is gs://bucket/**/dir1/**/a.txt
        wildcard_patterns.append(pattern[3:])
    return [re.compile(fnmatch.translate(p)) for p in wildcard_patterns]

  def _BuildBucketFilterStrings(self, wildcard):
    """Builds strings needed for querying a bucket and filtering results.

    This implements wildcard object name matching.

    Args:
      wildcard: The wildcard string to match to objects.

    Returns:
      (prefix, delimiter, prefix_wildcard, suffix_wildcard)
      where:
        prefix is the prefix to be sent in bucket GET request.
        delimiter is the delimiter to be sent in bucket GET request.
        prefix_wildcard is the wildcard to be used to filter bucket GET results.
        suffix_wildcard is wildcard to be appended to filtered bucket GET
          results for next wildcard expansion iteration.
      For example, given the wildcard gs://bucket/abc/d*e/f*.txt we
      would build prefix= abc/d, delimiter=/, prefix_wildcard=d*e, and
      suffix_wildcard=f*.txt. Using this prefix and delimiter for a bucket
      listing request will then produce a listing result set that can be
      filtered using this prefix_wildcard; and we'd use this suffix_wildcard
      to feed into the next call(s) to _BuildBucketFilterStrings(), for the
      next iteration of listing/filtering.

    Raises:
      AssertionError if wildcard doesn't contain any wildcard chars.
    """
    # Generate a request prefix if the object name part of the wildcard starts
    # with a non-wildcard string (e.g., that's true for 'gs://bucket/abc*xyz').
    match = WILDCARD_REGEX.search(wildcard)
    if not match:
      # Input "wildcard" has no wildcard chars, so just return tuple that will
      # cause a bucket listing to match the given input wildcard. Example: if
      # previous iteration yielded gs://bucket/dir/ with suffix_wildcard abc,
      # the next iteration will call _BuildBucketFilterStrings() with
      # gs://bucket/dir/abc, and we will return prefix ='dir/abc',
      # delimiter='/', prefix_wildcard='dir/abc', and suffix_wildcard=''.
      prefix = wildcard
      delimiter = '/'
      prefix_wildcard = wildcard
      suffix_wildcard = ''
    else:
      if match.start() > 0:
        # Wildcard does not occur at beginning of object name, so construct a
        # prefix string to send to server.
        prefix = wildcard[:match.start()]
        wildcard_part = wildcard[match.start():]
      else:
        prefix = None
        wildcard_part = wildcard
      end = wildcard_part.find('/')
      if end != -1:
        wildcard_part = wildcard_part[:end + 1]

      prefix_wildcard = (prefix or '') + wildcard_part
      if not prefix_wildcard.endswith('**/'):
        # Remove trailing '/' so we will match gs://bucket/abc* as well as
        # gs://bucket/abc*/ with the same wildcard regex. Don't do this for
        # double wildcards because those won't pass a delimiter to the API.
        prefix_wildcard = StripOneSlash(prefix_wildcard)

      suffix_wildcard = wildcard[match.end():]
      end = suffix_wildcard.find('/')
      if end == -1:
        suffix_wildcard = ''
      else:
        suffix_wildcard = suffix_wildcard[end + 1:]
      # To implement recursive (**) wildcarding, if prefix_wildcard
      # suffix_wildcard starts with '**' don't send a delimiter, and combine
      # suffix_wildcard at end of prefix_wildcard.
      if prefix_wildcard.find('**') != -1:
        delimiter = None
        prefix_wildcard += suffix_wildcard
        suffix_wildcard = ''
      else:
        delimiter = '/'
    # The following debug output is useful for tracing how the algorithm
    # walks through a multi-part wildcard like gs://bucket/abc/d*e/f*.txt
    self.logger.debug(
        'wildcard=%s, prefix=%s, delimiter=%s, '
        'prefix_wildcard=%s, suffix_wildcard=%s\n', PrintableStr(wildcard),
        PrintableStr(prefix), PrintableStr(delimiter),
        PrintableStr(prefix_wildcard), PrintableStr(suffix_wildcard))
    return (prefix, delimiter, prefix_wildcard, suffix_wildcard)

  def _SingleVersionMatches(self, listed_generation):
    decoded_generation = GenerationFromUrlAndString(self.wildcard_url,
                                                    listed_generation)
    return str(self.wildcard_url.generation) == str(decoded_generation)

  def _ExpandBucketWildcards(self, bucket_fields=None):
    """Expands bucket and provider wildcards.

    Builds a list of bucket url strings that can be iterated on.

    Args:
      bucket_fields: If present, populate only these metadata fields for
                     buckets.  Example value: ['acl', 'defaultObjectAcl']

    Yields:
      BucketListingRefereneces of type BUCKET.
    """
    bucket_url = StorageUrlFromString(self.wildcard_url.bucket_url_string)
    if (bucket_fields and set(bucket_fields) == set(['id']) and
        not ContainsWildcard(self.wildcard_url.bucket_name)):
      # If we just want the name of a non-wildcarded bucket URL,
      # don't make an RPC.
      yield BucketListingBucket(bucket_url)
    elif (self.wildcard_url.IsBucket() and
          not ContainsWildcard(self.wildcard_url.bucket_name)):
      # If we have a non-wildcarded bucket URL, get just that bucket.
      yield BucketListingBucket(bucket_url,
                                root_object=self.gsutil_api.GetBucket(
                                    self.wildcard_url.bucket_name,
                                    provider=self.wildcard_url.scheme,
                                    fields=bucket_fields))
    else:
      regex = fnmatch.translate(self.wildcard_url.bucket_name)
      prog = re.compile(regex)

      fields = self._GetToListFields(bucket_fields)
      if fields:
        fields.add('items/id')
      for bucket in self.gsutil_api.ListBuckets(
          fields=fields,
          project_id=self.project_id,
          provider=self.wildcard_url.scheme):
        if prog.match(bucket.id):
          url = StorageUrlFromString('%s://%s/' %
                                     (self.wildcard_url.scheme, bucket.id))
          yield BucketListingBucket(url, root_object=bucket)

  def _GetToListFields(self, get_fields=None):
    """Prepends 'items/' to the input fields and converts it to a set.

    This way field sets requested for GetBucket can be used in ListBucket calls.
    Note that the input set must contain only bucket or object fields; listing
    fields such as prefixes or nextPageToken should be added after calling
    this function.

    Args:
      get_fields: Iterable fields usable in GetBucket/GetObject calls.

    Returns:
      Set of fields usable in ListBuckets/ListObjects calls.
    """
    if get_fields:
      list_fields = set()
      for field in get_fields:
        list_fields.add('items/' + field)
      return list_fields

  def _GetObjectRef(self, bucket_url_string, gcs_object, with_version=False):
    """Creates a BucketListingRef of type OBJECT from the arguments.

    Args:
      bucket_url_string: Wildcardless string describing the containing bucket.
      gcs_object: gsutil_api root Object for populating the BucketListingRef.
      with_version: If true, return a reference with a versioned string.

    Returns:
      BucketListingRef of type OBJECT.
    """
    # Generation can be None in test mocks, so just return the
    # live object for simplicity.
    if with_version and gcs_object.generation is not None:
      generation_str = GenerationFromUrlAndString(self.wildcard_url,
                                                  gcs_object.generation)
      object_string = '%s%s#%s' % (bucket_url_string, gcs_object.name,
                                   generation_str)
    else:
      object_string = '%s%s' % (bucket_url_string, gcs_object.name)
    object_url = StorageUrlFromString(object_string)
    return BucketListingObject(object_url, root_object=gcs_object)

  def _GetPrefixRef(self, bucket_url_string, prefix):
    """Creates a BucketListingRef of type PREFIX from the arguments.

    Args:
      bucket_url_string: Wildcardless string describing the containing bucket.
      prefix: gsutil_api Prefix for populating the BucketListingRef

    Returns:
      BucketListingRef of type PREFIX.
    """
    prefix_url = StorageUrlFromString('%s%s' % (bucket_url_string, prefix))
    return BucketListingPrefix(prefix_url, root_object=prefix)

  def IterBuckets(self, bucket_fields=None):
    """Iterates over the wildcard, returning refs for each expanded bucket.

    This ignores the object part of the URL entirely and expands only the
    the bucket portion.  It will yield BucketListingRefs of type BUCKET only.

    Args:
      bucket_fields: Iterable fields to include in bucket listings.
                     Ex. ['defaultObjectAcl', 'logging'].  This function is
                     responsible for converting these to listing-style
                     format ['items/defaultObjectAcl', 'items/logging'], as
                     well as adding any fields necessary for listing such as
                     'items/id'.  API implemenation is responsible for
                     adding pagination fields.  If this is None, all fields are
                     returned.

    Yields:
      BucketListingRef of type BUCKET, or empty iterator if no matches.
    """
    for blr in self._ExpandBucketWildcards(bucket_fields=bucket_fields):
      yield blr

  def IterAll(self, bucket_listing_fields=None, expand_top_level_buckets=False):
    """Iterates over the wildcard, yielding bucket, prefix or object refs.

    Args:
      bucket_listing_fields: If present, populate only these metadata
                             fields for listed objects.
      expand_top_level_buckets: If true and the wildcard expands only to
                                Bucket(s), yields the expansion of each bucket
                                into a top-level listing of prefixes and objects
                                in that bucket instead of a BucketListingRef
                                to that bucket.

    Yields:
      BucketListingRef, or empty iterator if no matches.
    """
    for blr in self.__iter__(bucket_listing_fields=bucket_listing_fields,
                             expand_top_level_buckets=expand_top_level_buckets):
      yield blr

  def IterObjects(self, bucket_listing_fields=None):
    """Iterates over the wildcard, yielding only object BucketListingRefs.

    Args:
      bucket_listing_fields: If present, populate only these metadata
                             fields for listed objects.

    Yields:
      BucketListingRefs of type OBJECT or empty iterator if no matches.
    """
    for blr in self.__iter__(bucket_listing_fields=bucket_listing_fields,
                             expand_top_level_buckets=True):
      if blr.IsObject():
        yield blr


def _GetFileObject(filepath):
  """Returns an apitools Object class with supported file attributes.

  To provide size estimates for local to cloud file copies, we need to retrieve
  expose the local file's size.

  Args:
    filepath: Path to the file.

  Returns:
    apitools Object that with file name and size attributes filled-in.
  """
  # TODO: If we are preserving POSIX attributes, we could instead call
  # os.stat() here.
  return apitools_messages.Object(size=os.path.getsize(filepath))


class FileWildcardIterator(WildcardIterator):
  """WildcardIterator subclass for files and directories.

  If you use recursive wildcards ('**') only a single such wildcard is
  supported. For example you could use the wildcard '**/*.txt' to list all .txt
  files in any subdirectory of the current directory, but you couldn't use a
  wildcard like '**/abc/**/*.txt' (which would, if supported, let you find .txt
  files in any subdirectory named 'abc').
  """

  def __init__(self,
               wildcard_url,
               exclude_tuple=None,
               ignore_symlinks=False,
               logger=None):
    """Instantiates an iterator over BucketListingRefs matching wildcard URL.

    Args:
      wildcard_url: FileUrl that contains the wildcard to iterate.
      exclude_tuple: (base_url, exclude_pattern), where base_url is
                     top-level URL to list; exclude_pattern is a regex
                     of paths to ignore during iteration.
      ignore_symlinks: If True, ignore symlinks during iteration.
      logger: logging.Logger used for outputting debug messages during
              iteration. If None, the root logger will be used.
    """
    self.wildcard_url = wildcard_url
    self.exclude_tuple = exclude_tuple
    self.ignore_symlinks = ignore_symlinks
    self.logger = logger or logging.getLogger()

  def __iter__(self, bucket_listing_fields=None):
    """Iterator that gets called when iterating over the file wildcard.

    In the case where no wildcard is present, returns a single matching file
    or directory.

    Args:
      bucket_listing_fields: Iterable fields to include in listings.
          Ex. ['size']. Currently only 'size' is supported.
          If present, will populate yielded BucketListingObject.root_object
          with the file name and size.

    Raises:
      WildcardException: if invalid wildcard found.

    Yields:
      BucketListingRef of type OBJECT (for files) or PREFIX (for directories)
    """
    include_size = (bucket_listing_fields and
                    'size' in set(bucket_listing_fields))

    wildcard = self.wildcard_url.object_name
    match = FLAT_LIST_REGEX.match(wildcard)
    if match:
      # Recursive wildcarding request ('.../**/...').
      # Example input: wildcard = '/tmp/tmp2pQJAX/**/*'
      base_dir = match.group('before')[:-1]
      remaining_wildcard = match.group('after')
      # At this point for the above example base_dir = '/tmp/tmp2pQJAX' and
      # remaining_wildcard = '/*'
      if remaining_wildcard.startswith('*'):
        raise WildcardException('Invalid wildcard with more than 2 consecutive '
                                '*s (%s)' % wildcard)
      # If there was no remaining wildcard past the recursive wildcard,
      # treat it as if it were a '*'. For example, file://tmp/** is equivalent
      # to file://tmp/**/*
      if not remaining_wildcard:
        remaining_wildcard = '*'
      # Skip slash(es).
      remaining_wildcard = remaining_wildcard.lstrip(os.sep)
      filepaths = self._IterDir(base_dir, remaining_wildcard)
    else:
      # Not a recursive wildcarding request.
      filepaths = glob.iglob(wildcard)
    for filepath in filepaths:
      expanded_url = StorageUrlFromString(filepath)
      try:
        if self.ignore_symlinks and os.path.islink(filepath):
          if self.logger:
            self.logger.info('Skipping symbolic link %s...', filepath)
          continue
        if os.path.isdir(filepath):
          yield BucketListingPrefix(expanded_url)
        else:
          blr_object = _GetFileObject(filepath) if include_size else None
          yield BucketListingObject(expanded_url, root_object=blr_object)
      except UnicodeEncodeError:
        raise CommandException('\n'.join(
            textwrap.wrap(_UNICODE_EXCEPTION_TEXT % repr(filepath))))

  def _IterDir(self, directory, wildcard):
    """An iterator over the specified dir and wildcard.

    Args:
      directory (unicode): The path of the directory to iterate over.
      wildcard (str): The wildcard characters used for filename pattern
          matching.

    Yields:
      (str) A string containing the path to a file somewhere under the directory
      hierarchy of `directory`.

    Raises:
      ComandException: If this method encounters a file path that it cannot
      decode as UTF-8.
    """
    if os.path.splitdrive(directory)[0] == directory:
      # For Windows-style paths that consist of a drive letter followed by a
      # colon, os.path.join behaves in an odd manner. It intentionally will not
      # join ['c:' and 'foo'] as 'c:\\foo', but rather as 'c:foo'. The latter
      # format is not handled correctly by gsutil, so we check if the path
      # specifies the root of a volume, and if so, append a backslash so that
      # the resulting joined path looks like 'c:\\foo'.
      directory += '\\'

    # UTF8-encode directory before passing it to os.walk() so if there are
    # non-valid UTF8 chars in the file name (e.g., that can happen if the file
    # originated on Windows) os.walk() will not attempt to decode and then die
    # with a "codec can't decode byte" error, and instead we can catch the error
    # at yield time and print a more informative error message.
    for dirpath, dirnames, filenames in os.walk(six.ensure_text(directory),
                                                topdown=True):
      filtered_dirnames = []

      for dirname in dirnames:
        full_dir_path = os.path.join(dirpath, dirname)
        # Removes directories in place to prevent them and their children from
        # being iterated. See https://docs.python.org/3/library/os.html#os.walk
        if not self._ExcludeDir(full_dir_path):
          filtered_dirnames.append(dirname)
        else:
          # If a symlink is excluded above we don't want to print 2 messages.
          continue
        # This only prints a log message as os.walk() will not, by default,
        # walk down into symbolic links that resolve to directories.
        if self.logger and os.path.islink(full_dir_path):
          self.logger.info('Skipping symlink directory "%s"', full_dir_path)

      dirnames[:] = filtered_dirnames

      for f in fnmatch.filter(filenames, wildcard):
        try:
          yield os.path.join(dirpath, FixWindowsEncodingIfNeeded(f))
        except UnicodeDecodeError:
          # Note: We considered several ways to deal with this, but each had
          # problems:
          # 1. Raise an exception and try to catch in a higher layer (the
          #    gsutil cp command), so we can properly support the gsutil cp -c
          #    option. That doesn't work because raising an exception during
          #    iteration terminates the generator.
          # 2. Accumulate a list of bad filenames and skip processing each
          #    during iteration, then raise at the end, with exception text
          #    printing the bad paths. That doesn't work because iteration is
          #    wrapped in PluralityCheckableIterator, so it's possible there
          #    are not-yet-performed copy operations at the time we reach the
          #    end of the iteration and raise the exception - which would cause
          #    us to skip copying validly named files. Moreover, the gsutil
          #    cp command loops over argv, so if you run the command gsutil cp
          #    -rc dir1 dir2 gs://bucket, an invalid unicode name inside dir1
          #    would cause dir2 never to be visited.
          # 3. Print the invalid pathname and skip it during iteration. That
          #    would work but would mean gsutil cp could exit with status 0
          #    even though some files weren't copied.
          # 4. Change the WildcardIterator to include an error status along with
          #    the result. That would solve the problem but would be a
          #    substantial change (WildcardIterator is used in many parts of
          #    gsutil), and we didn't feel that magnitude of change was
          #    warranted by this relatively uncommon corner case.
          # Instead we chose to abort when one such file is encountered, and
          # require the user to remove or rename the files and try again.
          raise CommandException('\n'.join(
              textwrap.wrap(_UNICODE_EXCEPTION_TEXT %
                            repr(os.path.join(dirpath, f)))))

  def _ExcludeDir(self, dir):
    """Check a directory to see if it should be excluded from os.walk.

    Args:
      dir: String representing the directory to check.

    Returns:
      True if the directory should be excluded.
    """
    if self.exclude_tuple is None:
      return False
    (base_url, exclude_dirs, exclude_pattern) = self.exclude_tuple
    if not exclude_dirs:
      return False
    str_to_check = StorageUrlFromString(
        dir).url_string[len(base_url.url_string):]
    if str_to_check.startswith(self.wildcard_url.delim):
      str_to_check = str_to_check[1:]
    if exclude_pattern.match(str_to_check):
      if self.logger:
        self.logger.info('Skipping excluded directory %s...', dir)
      return True

  # pylint: disable=unused-argument
  def IterObjects(self, bucket_listing_fields=None):
    """Iterates over the wildcard, yielding only object (file) refs.

    Args:
      bucket_listing_fields: Iterable fields to include in listings.
          Ex. ['size']. Currently only 'size' is supported.
          If present, will populate yielded BucketListingObject.root_object
          with the file name and size.

    Yields:
      BucketListingRefs of type OBJECT or empty iterator if no matches.
    """
    for bucket_listing_ref in self.IterAll(
        bucket_listing_fields=bucket_listing_fields):
      if bucket_listing_ref.IsObject():
        yield bucket_listing_ref

  # pylint: disable=unused-argument
  def IterAll(self, bucket_listing_fields=None, expand_top_level_buckets=False):
    """Iterates over the wildcard, yielding BucketListingRefs.

    Args:
      bucket_listing_fields: Iterable fields to include in listings.
          Ex. ['size']. Currently only 'size' is supported.
          If present, will populate yielded BucketListingObject.root_object
          with the file name and size.
      expand_top_level_buckets: Ignored; filesystems don't have buckets.

    Yields:
      BucketListingRefs of type OBJECT (file) or PREFIX (directory),
      or empty iterator if no matches.
    """
    for bucket_listing_ref in self.__iter__(
        bucket_listing_fields=bucket_listing_fields):
      yield bucket_listing_ref

  def IterBuckets(self, unused_bucket_fields=None):
    """Placeholder to allow polymorphic use of WildcardIterator.

    Args:
      unused_bucket_fields: Ignored; filesystems don't have buckets.

    Raises:
      WildcardException: in all cases.
    """
    raise WildcardException(
        'Iterating over Buckets not possible for file wildcards')


class WildcardException(StandardError):
  """Exception raised for invalid wildcard URLs."""

  def __init__(self, reason):
    StandardError.__init__(self)
    self.reason = reason

  def __repr__(self):
    return 'WildcardException: %s' % self.reason

  def __str__(self):
    return 'WildcardException: %s' % self.reason


def CreateWildcardIterator(url_str,
                           gsutil_api,
                           all_versions=False,
                           project_id=None,
                           exclude_tuple=None,
                           ignore_symlinks=False,
                           logger=None):
  """Instantiate a WildcardIterator for the given URL string.

  Args:
    url_str: URL string naming wildcard object(s) to iterate.
    gsutil_api: Cloud storage interface.  Passed in for thread safety, also
                settable for testing/mocking.
    all_versions: If true, the iterator yields all versions of objects
                  matching the wildcard.  If false, yields just the live
                  object version.
    project_id: Project id to use for bucket listings.
    exclude_tuple: (base_url, exclude_pattern), where base_url is
                   top-level URL to list; exclude_pattern is a regex
                   of paths to ignore during iteration.
    ignore_symlinks: For FileUrls, ignore symlinks during iteration if true.
    logger: logging.Logger used for outputting debug messages during iteration.
            If None, the root logger will be used.

  Returns:
    A WildcardIterator that handles the requested iteration.
  """

  url = StorageUrlFromString(url_str)
  logger = logger or logging.getLogger()
  if url.IsFileUrl():
    return FileWildcardIterator(url,
                                exclude_tuple=exclude_tuple,
                                ignore_symlinks=ignore_symlinks,
                                logger=logger)
  else:  # Cloud URL
    return CloudWildcardIterator(url,
                                 gsutil_api,
                                 all_versions=all_versions,
                                 project_id=project_id)
