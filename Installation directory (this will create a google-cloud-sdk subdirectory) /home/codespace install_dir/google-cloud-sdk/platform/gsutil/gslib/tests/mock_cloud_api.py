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
"""Implements a simple mock gsutil Cloud API for unit testing.

gsutil 4 was primarily unit-tested using boto/gsutil 3's mock storage_uri class,
since it was possible that changing out the underlying mocks would have had
subtly different behavior and increased the risk of breaking back-compat.

Most unit and integration tests in gsutil 4 still set up the test objects with
storage_uris and boto, and the unit tests interact with test objects via
storage uris and boto.

This testing approach ties our tests heavily to boto; extending the
boto mocks is difficult because it requires checking into boto. This also
makes the unit test coverage boto-specific in several cases.

MockCloudApi was initially written to cover some parallel composite upload
cases that the boto mocks couldn't handle. It is not yet a full implementation.
Eventually, we can move to full a mock Cloud API implementation. However, we
need to ensure we don't lose boto coverage from mock storage_uri.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import six
from gslib.cloud_api import ServiceException
from gslib.discard_messages_queue import DiscardMessagesQueue
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils.translation_helper import CreateBucketNotFoundException
from gslib.utils.translation_helper import CreateObjectNotFoundException

if six.PY3:
  long = int


class MockObject(object):
  """Defines a mock cloud storage provider object."""

  def __init__(self, root_object, contents=''):
    self.root_object = root_object
    self.contents = contents

  def __str__(self):
    return '%s/%s#%s' % (self.root_object.bucket, self.root_object.name,
                         self.root_object.generation)

  def __repr__(self):
    return str(self)


class MockBucket(object):
  """Defines a mock cloud storage provider bucket."""

  def __init__(self, bucket_name, versioned=False):
    self.root_object = apitools_messages.Bucket(
        name=bucket_name,
        versioning=apitools_messages.Bucket.VersioningValue(enabled=versioned))
    # Dict of object_name: (dict of 'live': MockObject
    #                               'versioned': ordered list of MockObject).
    self.objects = {}

  def CreateObject(self, object_name, contents=''):
    return self.CreateObjectWithMetadata(
        MockObject(apitools_messages.Object(name=object_name,
                                            contents=contents)))

  def CreateObjectWithMetadata(self, apitools_object, contents=''):
    """Creates an object in the bucket according to the input metadata.

    This will create a new object version (ignoring the generation specified
    in the input object).

    Args:
      apitools_object: apitools Object.
      contents: optional object contents.

    Returns:
      apitools Object representing created object.
    """
    # This modifies the apitools_object with a generation number.
    object_name = apitools_object.name
    if (self.root_object.versioning and self.root_object.versioning.enabled and
        apitools_object.name in self.objects):
      if 'live' in self.objects[object_name]:
        # Versioning enabled and object exists, create an object with a
        # generation 1 higher.
        apitools_object.generation = (
            self.objects[object_name]['live'].root_object.generation + 1)
        # Move the live object to versioned.
        if 'versioned' not in self.objects[object_name]:
          self.objects[object_name]['versioned'] = []
        self.objects[object_name]['versioned'].append(
            self.objects[object_name]['live'])
      elif ('versioned' in self.objects[object_name] and
            self.objects[object_name]['versioned']):
        # Versioning enabled but only archived objects exist, pick a generation
        # higher than the highest versioned object (which will be at the end).
        apitools_object.generation = (
            self.objects[object_name]['versioned'][-1].root_object.generation +
            1)
    else:
      # Versioning disabled or no objects exist yet with this name.
      apitools_object.generation = 1
      self.objects[object_name] = {}
    new_object = MockObject(apitools_object, contents=contents)
    self.objects[object_name]['live'] = new_object
    return new_object


class MockCloudApi(object):
  """Simple mock service for buckets/objects that implements Cloud API.

  Also includes some setup functions for tests.
  """

  def __init__(self, provider='gs'):
    self.buckets = {}
    self.provider = provider
    self.status_queue = DiscardMessagesQueue()

  def MockCreateBucket(self, bucket_name):
    """Creates a simple bucket without exercising the API directly."""
    if bucket_name in self.buckets:
      raise ServiceException('Bucket %s already exists.' % bucket_name,
                             status=409)
    self.buckets[bucket_name] = MockBucket(bucket_name)

  def MockCreateVersionedBucket(self, bucket_name):
    """Creates a simple bucket without exercising the API directly."""
    if bucket_name in self.buckets:
      raise ServiceException('Bucket %s already exists.' % bucket_name,
                             status=409)
    self.buckets[bucket_name] = MockBucket(bucket_name, versioned=True)

  def MockCreateObject(self, bucket_name, object_name, contents=''):
    """Creates an object without exercising the API directly."""
    if bucket_name not in self.buckets:
      self.MockCreateBucket(bucket_name)
    self.buckets[bucket_name].CreateObject(object_name, contents=contents)

  def MockCreateObjectWithMetadata(self, apitools_object, contents=''):
    """Creates an object without exercising the API directly."""
    assert apitools_object.bucket, 'No bucket specified for mock object'
    assert apitools_object.name, 'No object name specified for mock object'
    if apitools_object.bucket not in self.buckets:
      self.MockCreateBucket(apitools_object.bucket)
    return self.buckets[apitools_object.bucket].CreateObjectWithMetadata(
        apitools_object, contents=contents).root_object

  # pylint: disable=unused-argument
  def GetObjectMetadata(self,
                        bucket_name,
                        object_name,
                        generation=None,
                        provider=None,
                        fields=None):
    """See CloudApi class for function doc strings."""
    if generation:
      generation = long(generation)
    if bucket_name in self.buckets:
      bucket = self.buckets[bucket_name]
      if object_name in bucket.objects and bucket.objects[object_name]:
        if generation:
          if 'versioned' in bucket.objects[object_name]:
            for obj in bucket.objects[object_name]['versioned']:
              if obj.root_object.generation == generation:
                return obj.root_object
          if 'live' in bucket.objects[object_name]:
            if (bucket.objects[object_name]['live'].root_object.generation ==
                generation):
              return bucket.objects[object_name]['live'].root_object
        else:
          # Return live object.
          if 'live' in bucket.objects[object_name]:
            return bucket.objects[object_name]['live'].root_object
      raise CreateObjectNotFoundException(404, self.provider, bucket_name,
                                          object_name)
    raise CreateBucketNotFoundException(404, self.provider, bucket_name)
