# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Classes for cloud/file references yielded by gsutil iterators."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals


class BucketListingRef(object):
  """Base class for a reference to one fully expanded iterator result.

  This allows polymorphic iteration over wildcard-iterated URLs.  The
  reference contains a fully expanded URL string containing no wildcards and
  referring to exactly one entity (if a wildcard is contained, it is assumed
  this is part of the raw string and should never be treated as a wildcard).

  Each reference represents a Bucket, Object, or Prefix.  For filesystem URLs,
  Objects represent files and Prefixes represent directories.

  The root_object member contains the underlying object as it was retrieved.
  It is populated by the calling iterator, which may only request certain
  fields to reduce the number of server requests.

  For filesystem URLs, root_object is not populated.
  """

  class _BucketListingRefType(object):
    """Enum class for describing BucketListingRefs."""
    BUCKET = 'bucket'  # Cloud bucket
    OBJECT = 'object'  # Cloud object or filesystem file
    PREFIX = 'prefix'  # Cloud bucket subdir or filesystem directory

  @property
  def url_string(self):
    return self._url_string

  @property
  def type_name(self):
    return self._ref_type

  def IsBucket(self):
    return self._ref_type == self._BucketListingRefType.BUCKET

  def IsObject(self):
    return self._ref_type == self._BucketListingRefType.OBJECT

  def IsPrefix(self):
    return self._ref_type == self._BucketListingRefType.PREFIX

  def __str__(self):
    return self._url_string


class BucketListingBucket(BucketListingRef):
  """BucketListingRef subclass for buckets."""

  def __init__(self, storage_url, root_object=None):
    """Creates a BucketListingRef of type bucket.

    Args:
      storage_url: StorageUrl containing a bucket.
      root_object: Underlying object metadata, if available.
    """
    super(BucketListingBucket, self).__init__()
    self._ref_type = self._BucketListingRefType.BUCKET
    self._url_string = storage_url.url_string
    self.storage_url = storage_url
    self.root_object = root_object


class BucketListingPrefix(BucketListingRef):
  """BucketListingRef subclass for prefixes."""

  def __init__(self, storage_url, root_object=None):
    """Creates a BucketListingRef of type prefix.

    Args:
      storage_url: StorageUrl containing a prefix.
      root_object: Underlying object metadata, if available.
    """
    super(BucketListingPrefix, self).__init__()
    self._ref_type = self._BucketListingRefType.PREFIX
    self._url_string = storage_url.url_string
    self.storage_url = storage_url
    self.root_object = root_object


class BucketListingObject(BucketListingRef):
  """BucketListingRef subclass for objects."""

  def __init__(self, storage_url, root_object=None):
    """Creates a BucketListingRef of type object.

    Args:
      storage_url: StorageUrl containing an object.
      root_object: Underlying object metadata, if available.
    """
    super(BucketListingObject, self).__init__()
    self._ref_type = self._BucketListingRefType.OBJECT
    self._url_string = storage_url.url_string
    self.storage_url = storage_url
    self.root_object = root_object
