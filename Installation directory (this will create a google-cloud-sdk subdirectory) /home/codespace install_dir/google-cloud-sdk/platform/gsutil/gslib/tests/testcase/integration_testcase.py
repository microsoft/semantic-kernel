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
"""Contains gsutil base integration test case class."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import datetime
import locale
import logging
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time

import boto
from boto import config
from boto.exception import StorageResponseError
from boto.s3.deletemarker import DeleteMarker
from boto.storage_uri import BucketStorageUri
import gslib
from gslib.boto_translation import BotoTranslation
from gslib.cloud_api import PreconditionException
from gslib.cloud_api import Preconditions
from gslib.discard_messages_queue import DiscardMessagesQueue
from gslib.exception import CommandException
from gslib.gcs_json_api import GcsJsonApi
from gslib.kms_api import KmsApi
from gslib.project_id import GOOG_PROJ_ID_HDR
from gslib.project_id import PopulateProjectId
from gslib.tests.testcase import base
import gslib.tests.util as util
from gslib.tests.util import InvokedFromParFile
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import RUN_S3_TESTS
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.tests.util import unittest
from gslib.tests.util import USING_JSON_API
import gslib.third_party.storage_apitools.storage_v1_messages as apitools_messages
from gslib.utils.constants import UTF8
from gslib.utils.encryption_helper import Base64Sha256FromBase64EncryptionKey
from gslib.utils.encryption_helper import CryptoKeyWrapperFromKey
from gslib.utils.hashing_helper import Base64ToHexHash
from gslib.utils.metadata_util import CreateCustomMetadata
from gslib.utils.metadata_util import GetValueFromObjectCustomMetadata
from gslib.utils.posix_util import ATIME_ATTR
from gslib.utils.posix_util import GID_ATTR
from gslib.utils.posix_util import MODE_ATTR
from gslib.utils.posix_util import MTIME_ATTR
from gslib.utils.posix_util import UID_ATTR
from gslib.utils.retry_util import Retry
import six
from six.moves import range

LOGGER = logging.getLogger('integration-test')


# TODO: Replace tests which looks for test_api == ApiSelector.(XML|JSON) with
# these decorators.
def SkipForXML(reason):
  """Skips the test if running S3 tests, or if prefer_api isn't set to json."""
  if not USING_JSON_API or RUN_S3_TESTS:
    return unittest.skip(reason)
  else:
    return lambda func: func


def SkipForJSON(reason):
  if USING_JSON_API:
    return unittest.skip(reason)
  else:
    return lambda func: func


def SkipForGS(reason):
  if not RUN_S3_TESTS:
    return unittest.skip(reason)
  else:
    return lambda func: func


def SkipForS3(reason):
  if RUN_S3_TESTS:
    return unittest.skip(reason)
  else:
    return lambda func: func


# TODO: Right now, most tests use the XML API. Instead, they should respect
# prefer_api in the same way that commands do.
@unittest.skipUnless(util.RUN_INTEGRATION_TESTS,
                     'Not running integration tests.')
class GsUtilIntegrationTestCase(base.GsUtilTestCase):
  """Base class for gsutil integration tests."""
  GROUP_TEST_ADDRESS = 'gs-discussion@googlegroups.com'
  GROUP_TEST_ID = (
      '00b4903a97d097895ab58ef505d535916a712215b79c3e54932c2eb502ad97f5')
  USER_TEST_ADDRESS = 'gsutiltesting123@gmail.com'
  # This is the legacy CanonicalID for the above email.
  USER_TEST_ID = (
      '00b4903a97f0baa2680740f5adb90b2dcf9c8b878abd84ba1bdba653de949619')
  DOMAIN_TEST = 'google.com'
  # No one can create this bucket without owning the gmail.com domain, and we
  # won't create this bucket, so it shouldn't exist.
  # It would be nice to use google.com here but JSON API disallows
  # 'google' in resource IDs.
  nonexistent_bucket_name = 'nonexistent-bucket-foobar.gmail.com'

  def setUp(self):
    """Creates base configuration for integration tests."""
    super(GsUtilIntegrationTestCase, self).setUp()
    self.bucket_uris = []

    # Set up API version and project ID handler.
    self.api_version = boto.config.get_value('GSUtil', 'default_api_version',
                                             '1')

    # Instantiate a JSON API for use by the current integration test.
    self.json_api = GcsJsonApi(BucketStorageUri, logging.getLogger(),
                               DiscardMessagesQueue(), 'gs')
    self.xml_api = BotoTranslation(BucketStorageUri, logging.getLogger(),
                                   DiscardMessagesQueue, self.default_provider)
    self.kms_api = KmsApi(logging.getLogger())

    self.multiregional_buckets = util.USE_MULTIREGIONAL_BUCKETS

    self._use_gcloud_storage = config.getbool('GSUtil', 'use_gcloud_storage',
                                              False)

    if util.RUN_S3_TESTS:
      self.nonexistent_bucket_name = (
          'nonexistentbucket-asf801rj3r9as90mfnnkjxpo02')

  # Retry with an exponential backoff if a server error is received. This
  # ensures that we try *really* hard to clean up after ourselves.
  # TODO: As long as we're still using boto to do the teardown,
  # we decorate with boto exceptions.  Eventually this should be migrated
  # to CloudApi exceptions.
  @Retry(StorageResponseError, tries=7, timeout_secs=1)
  def tearDown(self):
    super(GsUtilIntegrationTestCase, self).tearDown()

    while self.bucket_uris:
      bucket_uri = self.bucket_uris[-1]
      try:
        bucket_list = self._ListBucket(bucket_uri)
      except StorageResponseError as e:
        # This can happen for tests of rm -r command, which for bucket-only
        # URIs delete the bucket at the end.
        if e.status == 404:
          self.bucket_uris.pop()
          continue
        else:
          raise
      while bucket_list:
        error = None
        for k in bucket_list:
          try:
            if isinstance(k, DeleteMarker):
              bucket_uri.get_bucket().delete_key(k.name,
                                                 version_id=k.version_id)
            else:
              k.delete()
          except StorageResponseError as e:
            # This could happen if objects that have already been deleted are
            # still showing up in the listing due to eventual consistency. In
            # that case, we continue on until we've tried to deleted every
            # object in the listing before raising the error on which to retry.
            if e.status == 404:
              # This could happen if objects that have already been deleted are
              # still showing up in the listing due to eventual consistency. In
              # that case, we continue on until we've tried to deleted every
              # obj in the listing before raising the error on which to retry.
              error = e
            elif e.status == 403 and (e.error_code == 'ObjectUnderActiveHold' or
                                      e.error_code == 'RetentionPolicyNotMet'):
              # Object deletion fails if they are under active Temporary Hold,
              # Event-Based hold or still under retention.
              #
              # We purposefully do not raise error in order to allow teardown
              # to process all the objects in a bucket first. The retry logic on
              # the teardown method will kick in when bucket deletion fails (due
              # to bucket being non-empty) and retry deleting these objects
              # and their associated buckets.
              self._ClearHoldsOnObjectAndWaitForRetentionDuration(
                  bucket_uri, k.name)
            else:
              raise
        if error:
          raise error  # pylint: disable=raising-bad-type
        bucket_list = self._ListBucket(bucket_uri)
      bucket_uri.delete_bucket()
      self.bucket_uris.pop()

  def _ClearHoldsOnObjectAndWaitForRetentionDuration(self, bucket_uri,
                                                     object_name):
    """Removes Holds on test objects and waits till retention duration is over.

    This method makes sure that object is not under active Temporary Hold or
    Release Hold. It also waits (up to 1 minute) till retention duration for the
    object is over. This is necessary for cleanup, otherwise such test objects
    cannot be deleted.

    It's worth noting that tests should do their best to remove holds and wait
    for objects' retention period on their own and this is just a fallback.
    Additionally, Tests should not use retention duration longer than 1 minute,
    preferably only few seconds in order to avoid lengthening test execution
    time unnecessarily.

    Args:
      bucket_uri: bucket's uri.
      object_name: object's name.
    """
    object_metadata = self.json_api.GetObjectMetadata(
        bucket_uri.bucket_name,
        object_name,
        fields=['timeCreated', 'temporaryHold', 'eventBasedHold'])
    object_uri = '{}{}'.format(bucket_uri, object_name)
    if object_metadata.temporaryHold:
      self.RunGsUtil(['retention', 'temp', 'release', object_uri])

    if object_metadata.eventBasedHold:
      self.RunGsUtil(['retention', 'event', 'release', object_uri])

    retention_policy = self.json_api.GetBucket(bucket_uri.bucket_name,
                                               fields=['retentionPolicy'
                                                      ]).retentionPolicy
    retention_period = (retention_policy.retentionPeriod
                        if retention_policy is not None else 0)
    # throwing exceptions for Retention durations larger than 60 seconds.
    if retention_period <= 60:
      time.sleep(retention_period)
    else:
      raise CommandException(('Retention duration is too large for bucket "{}".'
                              ' Use shorter durations for Retention duration in'
                              ' tests').format(bucket_uri))

  def _SetObjectCustomMetadataAttribute(self, provider, bucket_name,
                                        object_name, attr_name, attr_value):
    """Sets a custom metadata attribute for an object.

    Args:
      provider: Provider string for the bucket, ex. 'gs' or 's3.
      bucket_name: The name of the bucket the object is in.
      object_name: The name of the object itself.
      attr_name: The name of the custom metadata attribute to set.
      attr_value: The value of the custom metadata attribute to set.

    Returns:
      None
    """
    obj_metadata = apitools_messages.Object()
    obj_metadata.metadata = CreateCustomMetadata({attr_name: attr_value})
    if provider == 'gs':
      self.json_api.PatchObjectMetadata(bucket_name,
                                        object_name,
                                        obj_metadata,
                                        provider=provider)
    else:
      self.xml_api.PatchObjectMetadata(bucket_name,
                                       object_name,
                                       obj_metadata,
                                       provider=provider)

  def SetPOSIXMetadata(self,
                       provider,
                       bucket_name,
                       object_name,
                       atime=None,
                       mtime=None,
                       uid=None,
                       gid=None,
                       mode=None):
    """Sets POSIX metadata for the object."""
    obj_metadata = apitools_messages.Object()
    obj_metadata.metadata = apitools_messages.Object.MetadataValue(
        additionalProperties=[])
    if atime is not None:
      CreateCustomMetadata(entries={ATIME_ATTR: atime},
                           custom_metadata=obj_metadata.metadata)
    if mode is not None:
      CreateCustomMetadata(entries={MODE_ATTR: mode},
                           custom_metadata=obj_metadata.metadata)
    if mtime is not None:
      CreateCustomMetadata(entries={MTIME_ATTR: mtime},
                           custom_metadata=obj_metadata.metadata)
    if uid is not None:
      CreateCustomMetadata(entries={UID_ATTR: uid},
                           custom_metadata=obj_metadata.metadata)
    if gid is not None:
      CreateCustomMetadata(entries={GID_ATTR: gid},
                           custom_metadata=obj_metadata.metadata)
    if provider == 'gs':
      self.json_api.PatchObjectMetadata(bucket_name,
                                        object_name,
                                        obj_metadata,
                                        provider=provider)
    else:
      self.xml_api.PatchObjectMetadata(bucket_name,
                                       object_name,
                                       obj_metadata,
                                       provider=provider)

  def ClearPOSIXMetadata(self, obj):
    """Uses the setmeta command to clear POSIX attributes from user metadata.

    Args:
      obj: The object to clear POSIX metadata for.
    """
    provider_meta_string = 'goog' if obj.scheme == 'gs' else 'amz'
    self.RunGsUtil([
        'setmeta', '-h',
        'x-%s-meta-%s' % (provider_meta_string, ATIME_ATTR), '-h',
        'x-%s-meta-%s' % (provider_meta_string, MTIME_ATTR), '-h',
        'x-%s-meta-%s' % (provider_meta_string, UID_ATTR), '-h',
        'x-%s-meta-%s' % (provider_meta_string, GID_ATTR), '-h',
        'x-%s-meta-%s' % (provider_meta_string, MODE_ATTR),
        suri(obj)
    ])

  def _ServiceAccountCredentialsPresent(self):
    # TODO: Currently, service accounts cannot be project owners (unless
    # they are exempted for legacy reasons). Unfortunately, setting a canned ACL
    # other than project-private, the ACL that buckets get by default, removes
    # project-editors access from the bucket ACL. So any canned ACL that would
    # actually represent a change the bucket would also orphan the service
    # account's access to the bucket. If service accounts can be owners
    # in the future, remove this function and update all callers.
    return (config.has_option('Credentials', 'gs_service_key_file') or
            config.has_option('GoogleCompute', 'service_account'))

  def _ListBucket(self, bucket_uri):
    if bucket_uri.scheme == 's3':
      # storage_uri will omit delete markers from bucket listings, but
      # these must be deleted before we can remove an S3 bucket.
      return list(v for v in bucket_uri.get_bucket().list_versions())
    return list(bucket_uri.list_bucket(all_versions=True))

  def AssertNObjectsInBucket(self, bucket_uri, num_objects, versioned=False):
    """Checks (with retries) that 'ls bucket_uri/**' returns num_objects.

    This is a common test pattern to deal with eventual listing consistency for
    tests that rely on a set of objects to be listed.

    Args:
      bucket_uri: storage_uri for the bucket.
      num_objects: number of objects expected in the bucket.
      versioned: If True, perform a versioned listing.

    Raises:
      AssertionError if number of objects does not match expected value.

    Returns:
      Listing split across lines.
    """

    def _CheckBucket():
      command = ['ls', '-a'] if versioned else ['ls']
      b_uri = [suri(bucket_uri) + '/**'] if num_objects else [suri(bucket_uri)]
      listing = self.RunGsUtil(command + b_uri, return_stdout=True).split('\n')
      # num_objects + one trailing newline.
      self.assertEqual(len(listing), num_objects + 1)
      return listing

    if self.multiregional_buckets:
      # Use @Retry as hedge against bucket listing eventual consistency.
      @Retry(AssertionError, tries=5, timeout_secs=1)
      def _Check1():
        return _CheckBucket()

      return _Check1()
    else:
      return _CheckBucket()

  def AssertObjectUsesCSEK(self, object_uri_str, encryption_key):
    """Strongly consistent check that the correct CSEK encryption key is used.

    This check forces use of the JSON API, as encryption information is not
    returned in object metadata via the XML API.

    Args:
      object_uri_str: uri for the object.
      encryption_key: expected CSEK key.
    """
    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      stdout = self.RunGsUtil(['stat', object_uri_str],
                              return_stdout=True,
                              force_gsutil=True)
    self.assertIn(
        Base64Sha256FromBase64EncryptionKey(encryption_key).decode('ascii'),
        stdout, 'Object %s did not use expected encryption key with hash %s. '
        'Actual object: %s' %
        (object_uri_str, Base64Sha256FromBase64EncryptionKey(encryption_key),
         stdout))

  def AssertObjectUsesCMEK(self, object_uri_str, encryption_key):
    """Strongly consistent check that the correct KMS encryption key is used.

    This check forces use of the JSON API, as encryption information is not
    returned in object metadata via the XML API.

    Args:
      object_uri_str: uri for the object.
      encryption_key: expected CMEK key.
    """
    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      stdout = self.RunGsUtil(['stat', object_uri_str],
                              return_stdout=True,
                              force_gsutil=True)
    self.assertRegex(stdout, r'KMS key:\s+%s' % encryption_key)

  def AssertObjectUnencrypted(self, object_uri_str):
    """Checks that no CSEK or CMEK attributes appear in `stat` output.

    This check forces use of the JSON API, as encryption information is not
    returned in object metadata via the XML API.

    Args:
      object_uri_str: uri for the object.
    """
    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      stdout = self.RunGsUtil(['stat', object_uri_str],
                              return_stdout=True,
                              force_gsutil=True)
    self.assertNotIn('Encryption key SHA256', stdout)
    self.assertNotIn('KMS key', stdout)

  def CreateBucketWithRetentionPolicy(self,
                                      retention_period_in_seconds,
                                      is_locked=None,
                                      bucket_name=None):
    """Creates a test bucket with Retention Policy.

    The bucket and all of its contents will be deleted after the test.

    Args:
      retention_period_in_seconds: Retention duration in seconds
      is_locked: Indicates whether Retention Policy should be locked
                 on the bucket or not.
      bucket_name: Create the bucket with this name. If not provided, a
                   temporary test bucket name is constructed.

    Returns:
      StorageUri for the created bucket.
    """
    # Creating bucket with Retention Policy.
    retention_policy = (apitools_messages.Bucket.RetentionPolicyValue(
        retentionPeriod=retention_period_in_seconds))
    bucket_uri = self.CreateBucket(bucket_name=bucket_name,
                                   retention_policy=retention_policy,
                                   prefer_json_api=True)

    if is_locked:
      # Locking Retention Policy
      self.RunGsUtil(['retention', 'lock', suri(bucket_uri)], stdin='y')

    # Verifying Retention Policy on the bucket.
    self.VerifyRetentionPolicy(
        bucket_uri,
        expected_retention_period_in_seconds=retention_period_in_seconds,
        expected_is_locked=is_locked)

    return bucket_uri

  def VerifyRetentionPolicy(self,
                            bucket_uri,
                            expected_retention_period_in_seconds=None,
                            expected_is_locked=None):
    """Verifies the Retention Policy on a bucket.

    Args:
      bucket_uri: Specifies the bucket.
      expected_retention_period_in_seconds: Specifies the expected Retention
                                            Period of the Retention Policy on
                                            the bucket. Setting this field to
                                            None, implies that no Retention
                                            Policy should be present.
      expected_is_locked: Indicates whether the Retention Policy should be
                          locked or not.
    """
    actual_retention_policy = self.json_api.GetBucket(
        bucket_uri.bucket_name, fields=['retentionPolicy']).retentionPolicy

    if expected_retention_period_in_seconds is None:
      self.assertEqual(actual_retention_policy, None)
    else:
      self.assertEqual(actual_retention_policy.retentionPeriod,
                       expected_retention_period_in_seconds)
      self.assertEqual(actual_retention_policy.isLocked, expected_is_locked)
      # Verifying the effectiveTime of the Retention Policy:
      #    since this is integration test and we don't have exact time of the
      #    server. We just verify that the effective time is a timestamp within
      #    last minute.
      effective_time_in_seconds = self.DateTimeToSeconds(
          actual_retention_policy.effectiveTime)
      current_time_in_seconds = self.DateTimeToSeconds(datetime.datetime.now())
      self.assertGreater(effective_time_in_seconds,
                         current_time_in_seconds - 60)

  def DateTimeToSeconds(self, datetime_obj):
    return int(time.mktime(datetime_obj.timetuple()))

  def CreateBucket(self,
                   bucket_name=None,
                   test_objects=0,
                   storage_class=None,
                   retention_policy=None,
                   provider=None,
                   prefer_json_api=False,
                   versioning_enabled=False,
                   bucket_policy_only=False,
                   bucket_name_prefix='',
                   bucket_name_suffix='',
                   location=None,
                   public_access_prevention=None):
    """Creates a test bucket.

    The bucket and all of its contents will be deleted after the test.

    Args:
      bucket_name: Create the bucket with this name. If not provided, a
                   temporary test bucket name is constructed.
      test_objects: The number of objects that should be placed in the bucket.
                    Defaults to 0.
      storage_class: Storage class to use. If not provided we us standard.
      retention_policy: Retention policy to be used on the bucket.
      provider: Provider to use - either "gs" (the default) or "s3".
      prefer_json_api: If True, use the JSON creation functions where possible.
      versioning_enabled: If True, set the bucket's versioning attribute to
          True.
      bucket_policy_only: If True, set the bucket's iamConfiguration's
          bucketPolicyOnly attribute to True.
      bucket_name_prefix: Unicode string to be prepended to bucket_name
      bucket_name_suffix: Unicode string to be appended to bucket_name
      location: The location/region in which the bucket should be created.
      public_access_prevention: String value of public access prevention. Valid
          values are "enforced" and "unspecified".

    Returns:
      StorageUri for the created bucket.
    """
    if not provider:
      provider = self.default_provider

    # Location is controlled by the -b test flag.
    if location is None:
      if self.multiregional_buckets or provider == 's3':
        location = None
      else:
        # We default to the "us-central1" location for regional buckets,
        # but allow overriding this value in the Boto config.
        location = boto.config.get('GSUtil',
                                   'test_cmd_regional_bucket_location',
                                   'us-central1')

    bucket_name_prefix = six.ensure_text(bucket_name_prefix)
    bucket_name_suffix = six.ensure_text(bucket_name_suffix)

    if bucket_name:
      bucket_name = ''.join(
          [bucket_name_prefix, bucket_name, bucket_name_suffix])
      bucket_name = util.MakeBucketNameValid(bucket_name)
    else:
      bucket_name = self.MakeTempName('bucket',
                                      prefix=bucket_name_prefix,
                                      suffix=bucket_name_suffix)

    if prefer_json_api and provider == 'gs':
      json_bucket = self.CreateBucketJson(
          bucket_name=bucket_name,
          test_objects=test_objects,
          storage_class=storage_class,
          location=location,
          versioning_enabled=versioning_enabled,
          retention_policy=retention_policy,
          bucket_policy_only=bucket_policy_only,
          public_access_prevention=public_access_prevention)
      bucket_uri = boto.storage_uri('gs://%s' % json_bucket.name.lower(),
                                    suppress_consec_slashes=False)
      return bucket_uri

    bucket_uri = boto.storage_uri('%s://%s' % (provider, bucket_name.lower()),
                                  suppress_consec_slashes=False)

    if provider == 'gs':
      # Apply API version and project ID headers if necessary.
      headers = {
          'x-goog-api-version': self.api_version,
          GOOG_PROJ_ID_HDR: PopulateProjectId()
      }
    else:
      headers = {}
      if not bucket_policy_only:
        # S3 test account settings disable ACLs by default,
        # but they should be re-enabled if requested.
        headers['x-amz-object-ownership'] = 'ObjectWriter'

    @Retry(StorageResponseError, tries=7, timeout_secs=1)
    def _CreateBucketWithExponentialBackoff():
      """Creates a bucket, retrying with exponential backoff on error.

      Parallel tests can easily run into bucket creation quotas.
      Retry with exponential backoff so that we create them as fast as we
      reasonably can.

      Returns:
        StorageUri for the created bucket
      """
      try:
        bucket_uri.create_bucket(storage_class=storage_class,
                                 location=location or '',
                                 headers=headers)
      except StorageResponseError as e:
        # If the service returns a transient error or a connection breaks,
        # it's possible the request succeeded. If that happens, the service
        # will return 409s for all future calls even though our intent
        # succeeded. If the error message says we already own the bucket,
        # assume success to reduce test flakiness. This depends on
        # randomness of test naming buckets to prevent name collisions for
        # test buckets created concurrently in the same project, which is
        # acceptable because this is far less likely than service errors.
        if e.status == 409 and e.body and 'already own' in e.body:
          pass
        else:
          raise

    _CreateBucketWithExponentialBackoff()
    self.bucket_uris.append(bucket_uri)

    if versioning_enabled:
      bucket_uri.configure_versioning(True)

    if provider != 'gs' and not public_access_prevention:
      # S3 test account settings enable public access prevention
      # by default, so we should disable it if requested.
      xml_body = ('<?xml version="1.0" encoding="UTF-8"?>'
                  '<PublicAccessBlockConfiguration>'
                  '<BlockPublicAcls>False</BlockPublicAcls>'
                  '</PublicAccessBlockConfiguration>')
      bucket_uri.set_subresource('publicAccessBlock', xml_body)

    for i in range(test_objects):
      self.CreateObject(bucket_uri=bucket_uri,
                        object_name=self.MakeTempName('obj'),
                        contents='test {:d}'.format(i).encode('ascii'))
    return bucket_uri

  def CreateVersionedBucket(self, bucket_name=None, test_objects=0):
    """Creates a versioned test bucket.

    The bucket and all of its contents will be deleted after the test.

    Args:
      bucket_name: Create the bucket with this name. If not provided, a
                   temporary test bucket name is constructed.
      test_objects: The number of objects that should be placed in the bucket.
                    Defaults to 0.

    Returns:
      StorageUri for the created bucket with versioning enabled.
    """
    # Note that we prefer the JSON API so that we don't require two separate
    # steps to create and then set versioning on the bucket (as versioning
    # propagation on an existing bucket is subject to eventual consistency).
    bucket_uri = self.CreateBucket(bucket_name=bucket_name,
                                   test_objects=test_objects,
                                   prefer_json_api=True,
                                   versioning_enabled=True)
    return bucket_uri

  def CreateObject(self,
                   bucket_uri=None,
                   object_name=None,
                   contents=None,
                   prefer_json_api=False,
                   encryption_key=None,
                   mode=None,
                   mtime=None,
                   uid=None,
                   gid=None,
                   storage_class=None,
                   gs_idempotent_generation=0,
                   kms_key_name=None):
    """Creates a test object.

    Args:
      bucket_uri: The URI of the bucket to place the object in. If not
          specified, a new temporary bucket is created.
      object_name: The name to use for the object. If not specified, a temporary
          test object name is constructed.
      contents: The contents to write to the object. If not specified, the key
          is not written to, which means that it isn't actually created
          yet on the server.
      prefer_json_api: If true, use the JSON creation functions where possible.
      encryption_key: AES256 encryption key to use when creating the object,
          if any.
      mode: The POSIX mode for the object. Must be a base-8 3-digit integer
          represented as a string.
      mtime: The modification time of the file in POSIX time (seconds since
          UTC 1970-01-01). If not specified, this defaults to the current
          system time.
      uid: A POSIX user ID.
      gid: A POSIX group ID.
      storage_class: String representing the storage class to use for the
          object.
      gs_idempotent_generation: For use when overwriting an object for which
          you know the previously uploaded generation. Create GCS object
          idempotently by supplying this generation number as a precondition
          and assuming the current object is correct on precondition failure.
          Defaults to 0 (new object); to disable, set to None.
      kms_key_name: Fully-qualified name of the KMS key that should be used to
          encrypt the object. Note that this is currently only valid for 'gs'
          objects.

    Returns:
      A StorageUri for the created object.
    """
    bucket_uri = bucket_uri or self.CreateBucket()
    # checking for valid types - None or unicode/binary text
    if contents is not None:
      if not isinstance(contents, (six.binary_type, six.text_type)):
        raise TypeError('contents must be either none or bytes, not {}'.format(
            type(contents)))
      contents = six.ensure_binary(contents)
    if (contents and bucket_uri.scheme == 'gs' and
        (prefer_json_api or encryption_key or kms_key_name)):

      object_name = object_name or self.MakeTempName('obj')
      json_object = self.CreateObjectJson(
          contents=contents,
          bucket_name=bucket_uri.bucket_name,
          object_name=object_name,
          encryption_key=encryption_key,
          mtime=mtime,
          storage_class=storage_class,
          gs_idempotent_generation=gs_idempotent_generation,
          kms_key_name=kms_key_name)
      object_uri = bucket_uri.clone_replace_name(object_name)
      # pylint: disable=protected-access
      # Need to update the StorageUri with the correct values while
      # avoiding creating a versioned string.

      md5 = (Base64ToHexHash(json_object.md5Hash),
             json_object.md5Hash.strip('\n"\''))
      object_uri._update_from_values(None,
                                     json_object.generation,
                                     True,
                                     md5=md5)
      # pylint: enable=protected-access
      return object_uri

    bucket_uri = bucket_uri or self.CreateBucket()
    object_name = object_name or self.MakeTempName('obj')
    key_uri = bucket_uri.clone_replace_name(object_name)
    if contents is not None:
      if bucket_uri.scheme == 'gs' and gs_idempotent_generation is not None:
        try:
          key_uri.set_contents_from_string(contents,
                                           headers={
                                               'x-goog-if-generation-match':
                                                   str(gs_idempotent_generation)
                                           })
        except StorageResponseError as e:
          if e.status == 412:
            pass
          else:
            raise
      else:
        key_uri.set_contents_from_string(contents)
    custom_metadata_present = (mode is not None or mtime is not None or
                               uid is not None or gid is not None)
    if custom_metadata_present:
      self.SetPOSIXMetadata(bucket_uri.scheme,
                            bucket_uri.bucket_name,
                            object_name,
                            atime=None,
                            mtime=mtime,
                            uid=uid,
                            gid=gid,
                            mode=mode)
    return key_uri

  def CreateBucketJson(self,
                       bucket_name=None,
                       test_objects=0,
                       storage_class=None,
                       location=None,
                       versioning_enabled=False,
                       retention_policy=None,
                       bucket_policy_only=False,
                       public_access_prevention=None):
    """Creates a test bucket using the JSON API.

    The bucket and all of its contents will be deleted after the test.

    Args:
      bucket_name: Create the bucket with this name. If not provided, a
                   temporary test bucket name is constructed.
      test_objects: The number of objects that should be placed in the bucket.
                    Defaults to 0.
      storage_class: Storage class to use. If not provided we use standard.
      location: Location to use.
      versioning_enabled: If True, set the bucket's versioning attribute to
          True.
      retention_policy: Retention policy to be used on the bucket.
      bucket_policy_only: If True, set the bucket's iamConfiguration's
          bucketPolicyOnly attribute to True.
      public_access_prevention: String value of public access prevention. Valid
          values are "enforced" and "unspecified".

    Returns:
      Apitools Bucket for the created bucket.
    """
    bucket_name = util.MakeBucketNameValid(bucket_name or
                                           self.MakeTempName('bucket'))
    bucket_metadata = apitools_messages.Bucket(name=bucket_name.lower())
    if storage_class:
      bucket_metadata.storageClass = storage_class
    if location:
      bucket_metadata.location = location
    if versioning_enabled:
      bucket_metadata.versioning = (apitools_messages.Bucket.VersioningValue(
          enabled=True))
    if retention_policy:
      bucket_metadata.retentionPolicy = retention_policy
    if bucket_policy_only or public_access_prevention:
      iam_config = apitools_messages.Bucket.IamConfigurationValue()
      if bucket_policy_only:
        iam_config.bucketPolicyOnly = iam_config.BucketPolicyOnlyValue()
        iam_config.bucketPolicyOnly.enabled = True
      if public_access_prevention:
        iam_config.publicAccessPrevention = public_access_prevention
      bucket_metadata.iamConfiguration = iam_config

    # TODO: Add retry and exponential backoff.
    bucket = self.json_api.CreateBucket(bucket_name, metadata=bucket_metadata)
    # Add bucket to list of buckets to be cleaned up.
    # TODO: Clean up JSON buckets using JSON API.
    self.bucket_uris.append(
        boto.storage_uri('gs://%s' % bucket_name,
                         suppress_consec_slashes=False))
    for i in range(test_objects):
      self.CreateObjectJson(bucket_name=bucket_name,
                            object_name=self.MakeTempName('obj'),
                            contents='test {:d}'.format(i).encode('ascii'))
    return bucket

  def CreateObjectJson(self,
                       contents,
                       bucket_name=None,
                       object_name=None,
                       encryption_key=None,
                       mtime=None,
                       storage_class=None,
                       gs_idempotent_generation=None,
                       kms_key_name=None):
    """Creates a test object (GCS provider only) using the JSON API.

    Args:
      contents: The contents to write to the object.
      bucket_name: Name of bucket to place the object in. If not specified,
          a new temporary bucket is created. Assumes the given bucket name is
          valid.
      object_name: The name to use for the object. If not specified, a temporary
          test object name is constructed.
      encryption_key: AES256 encryption key to use when creating the object,
          if any.
      mtime: The modification time of the file in POSIX time (seconds since
          UTC 1970-01-01). If not specified, this defaults to the current
          system time.
      storage_class: String representing the storage class to use for the
          object.
      gs_idempotent_generation: For use when overwriting an object for which
          you know the previously uploaded generation. Create GCS object
          idempotently by supplying this generation number as a precondition
          and assuming the current object is correct on precondition failure.
          Defaults to 0 (new object); to disable, set to None.
      kms_key_name: Fully-qualified name of the KMS key that should be used to
          encrypt the object. Note that this is currently only valid for 'gs'
          objects.

    Returns:
      An apitools Object for the created object.
    """
    bucket_name = bucket_name or self.CreateBucketJson().name
    object_name = object_name or self.MakeTempName('obj')
    preconditions = Preconditions(gen_match=gs_idempotent_generation)
    custom_metadata = apitools_messages.Object.MetadataValue(
        additionalProperties=[])
    if mtime is not None:
      CreateCustomMetadata({MTIME_ATTR: mtime}, custom_metadata)
    object_metadata = apitools_messages.Object(
        name=object_name,
        metadata=custom_metadata,
        bucket=bucket_name,
        contentType='application/octet-stream',
        storageClass=storage_class,
        kmsKeyName=kms_key_name)
    encryption_keywrapper = CryptoKeyWrapperFromKey(encryption_key)
    try:
      return self.json_api.UploadObject(six.BytesIO(contents),
                                        object_metadata,
                                        provider='gs',
                                        encryption_tuple=encryption_keywrapper,
                                        preconditions=preconditions)
    except PreconditionException:
      if gs_idempotent_generation is None:
        raise
      with SetBotoConfigForTest([('GSUtil', 'decryption_key1', encryption_key)
                                ]):
        return self.json_api.GetObjectMetadata(bucket_name, object_name)

  def GetObjectMetadataWithFields(self, bucket_name, object_name, fields):
    """Retrieves and verifies an object's metadata attribute.

    Args:
      bucket_name: The name of the bucket the object is in.
      object_name: The name of the object itself.
      fields: List of attributes strings. Custom attributes begin "metadata/".

    Returns:
      Apitools object.
    """
    gsutil_api = (self.json_api
                  if self.default_provider == 'gs' else self.xml_api)
    return gsutil_api.GetObjectMetadata(bucket_name,
                                        object_name,
                                        provider=self.default_provider,
                                        fields=fields)

  def VerifyObjectCustomAttribute(self,
                                  bucket_name,
                                  object_name,
                                  attr_name,
                                  expected_value,
                                  expected_present=True):
    """Retrieves and verifies an object's custom metadata attribute.

    Args:
      bucket_name: The name of the bucket the object is in.
      object_name: The name of the object itself.
      attr_name: The name of the custom metadata attribute.
      expected_value: The expected retrieved value for the attribute.
      expected_present: True if the attribute must be present in the
          object metadata, False if it must not be present.

    Returns:
      None
    """
    metadata = self.GetObjectMetadataWithFields(
        bucket_name, object_name, fields=['metadata/%s' % attr_name])
    attr_present, value = GetValueFromObjectCustomMetadata(
        metadata, attr_name, default_value=expected_value)
    self.assertEqual(expected_present, attr_present)
    self.assertEqual(expected_value, value)

  def VerifyPublicAccessPreventionValue(self, bucket_uri, value):
    # TODO: Delete this method in favor of VerifyCommandGet
    stdout = self.RunGsUtil(['publicaccessprevention', 'get',
                             suri(bucket_uri)],
                            return_stdout=True)
    public_access_prevention_re = re.compile(r':\s+(?P<pap_val>.+)$')
    public_access_prevention_match = re.search(public_access_prevention_re,
                                               stdout)
    public_access_prevention_val = public_access_prevention_match.group(
        'pap_val')
    self.assertEqual(str(value), public_access_prevention_val)

  def VerifyCommandGet(self, bucket_uri, command, expected):
    """Verifies if <command> get returns the expected value."""
    stdout = self.RunGsUtil([command, 'get', suri(bucket_uri)],
                            return_stdout=True)
    output_regex = re.compile('{}: (?P<actual>.+)$'.format(suri(bucket_uri)))
    output_match = re.search(output_regex, stdout)
    actual = output_match.group('actual')
    self.assertEqual(actual, expected)

  def RunGsUtil(self,
                cmd,
                return_status=False,
                return_stdout=False,
                return_stderr=False,
                expected_status=0,
                stdin=None,
                env_vars=None,
                force_gsutil=False):
    """Runs the gsutil command.

    Args:
      cmd: The command to run, as a list, e.g. ['cp', 'foo', 'bar']
      return_status: If True, the exit status code is returned.
      return_stdout: If True, the standard output of the command is returned.
      return_stderr: If True, the standard error of the command is returned.
      expected_status: The expected return code. If not specified, defaults to
                       0. If the return code is a different value, an exception
                       is raised.
      stdin: A string of data to pipe to the process as standard input.
      env_vars: A dictionary of variables to extend the subprocess's os.environ
                with.
      force_gsutil: If True, will always run the command using gsutil,
        irrespective of the value provided for use_gcloud_storage.

    Returns:
      If multiple return_* values were specified, this method returns a tuple
      containing the desired return values specified by the return_* arguments
      (in the order those parameters are specified in the method definition).
      If only one return_* value was specified, that value is returned directly
      rather than being returned within a 1-tuple.
    """
    full_gsutil_command = util.GetGsutilCommand(cmd, force_gsutil=force_gsutil)
    process = util.GetGsutilSubprocess(full_gsutil_command, env_vars=env_vars)

    c_out = util.CommunicateWithTimeout(process, stdin=stdin)
    stdout = c_out[0].replace(os.linesep, '\n')
    stderr = c_out[1].replace(os.linesep, '\n')
    status = process.returncode

    if expected_status is not None:
      cmd = map(six.ensure_text, cmd)
      self.assertEqual(
          int(status),
          int(expected_status),
          msg='Expected status {}, got {}.\nCommand:\n{}\n\nstderr:\n{}'.format(
              expected_status, status, ' '.join(cmd), stderr))

    toreturn = []
    if return_status:
      toreturn.append(status)
    if return_stdout:
      toreturn.append(stdout)
    if return_stderr:
      toreturn.append(stderr)

    if len(toreturn) == 1:
      return toreturn[0]
    elif toreturn:
      return tuple(toreturn)

  def RunGsUtilTabCompletion(self, cmd, expected_results=None):
    """Runs the gsutil command in tab completion mode.

    Args:
      cmd: The command to run, as a list, e.g. ['cp', 'foo', 'bar']
      expected_results: The expected tab completion results for the given input.
    """
    cmd = [gslib.GSUTIL_PATH] + ['--testexceptiontraces'] + cmd
    if InvokedFromParFile():
      argcomplete_start_idx = 1
    else:
      argcomplete_start_idx = 2
      # Prepend the interpreter path; ensures we use the same interpreter that
      # was used to invoke the integration tests. In practice, this only differs
      # when you're running the tests using a different interpreter than
      # whatever `/usr/bin/env python` resolves to.
      cmd = [str(sys.executable)] + cmd
    cmd_str = ' '.join(cmd)

    @Retry(AssertionError, tries=5, timeout_secs=1)
    def _RunTabCompletion():
      """Runs the tab completion operation with retries."""
      # Set this to True if the argcomplete tests start failing and you want to
      # see any output you can get. I've had to do this so many times that I'm
      # just going to leave this in the code for convenience ¯\_(ツ)_/¯
      #
      # If set, this will print out extra info from the argcomplete subprocess.
      # You'll probably want to find one test that's failing and run it
      # individually, e.g.:
      #   python3 ./gsutil test tabcomplete.TestTabComplete.test_single_object
      # so that only one subprocess is run, thus routing the output to your
      # local terminal rather than swallowing it.
      hacky_debugging = False

      results_string = None
      with tempfile.NamedTemporaryFile(
          delete=False) as tab_complete_result_file:
        if hacky_debugging:
          # These redirectons are valuable for debugging purposes. 1 and 2 are,
          # obviously, stdout and stderr of the subprocess. 9 is the fd for
          # argparse debug stream.
          cmd_str_with_result_redirect = (
              '{cs} 1>{fn} 2>{fn} 8>{fn} 9>{fn}'.format(
                  cs=cmd_str, fn=tab_complete_result_file.name))
        else:
          # argcomplete returns results via the '8' file descriptor, so we
          # redirect to a file so we can capture the completion results.
          cmd_str_with_result_redirect = '{cs} 8>{fn}'.format(
              cs=cmd_str, fn=tab_complete_result_file.name)
        env = os.environ.copy()
        env['_ARGCOMPLETE'] = str(argcomplete_start_idx)
        # Use a sane default for COMP_WORDBREAKS.
        env['_ARGCOMPLETE_COMP_WORDBREAKS'] = '''"'@><=;|&(:'''
        if 'COMP_WORDBREAKS' in env:
          env['_ARGCOMPLETE_COMP_WORDBREAKS'] = env['COMP_WORDBREAKS']
        env['COMP_LINE'] = cmd_str
        env['COMP_POINT'] = str(len(cmd_str))
        subprocess.call(cmd_str_with_result_redirect, env=env, shell=True)
        results_string = tab_complete_result_file.read().decode(
            locale.getpreferredencoding())
      if results_string:
        if hacky_debugging:
          print('---------------------------------------')
          print(results_string)
          print('---------------------------------------')
        results = results_string.split('\013')
      else:
        results = []
      self.assertEqual(results, expected_results)

    # When tests are run in parallel, tab completion could take a long time,
    # so choose a long timeout value.
    with SetBotoConfigForTest([('GSUtil', 'tab_completion_timeout', '120')]):
      _RunTabCompletion()

  @contextlib.contextmanager
  def SetAnonymousBotoCreds(self):
    # Tell gsutil not to override the real error message with a warning about
    # anonymous access if no credentials are provided in the config file.
    boto_config_for_test = [('Tests', 'bypass_anonymous_access_warning', 'True')
                           ]

    # Also, maintain any custom host/port/API configuration, since we'll need
    # to contact the same host when operating in a development environment.
    for creds_config_key in ('gs_host', 'gs_json_host', 'gs_json_host_header',
                             'gs_post', 'gs_json_port'):
      boto_config_for_test.append(('Credentials', creds_config_key,
                                   boto.config.get('Credentials',
                                                   creds_config_key, None)))
    boto_config_for_test.append(
        ('Boto', 'https_validate_certificates',
         boto.config.get('Boto', 'https_validate_certificates', None)))
    for api_config_key in ('json_api_version', 'prefer_api'):
      boto_config_for_test.append(('GSUtil', api_config_key,
                                   boto.config.get('GSUtil', api_config_key,
                                                   None)))

    with SetBotoConfigForTest(boto_config_for_test, use_existing_config=False):
      # Make sure to reset Developer Shell credential port so that the child
      # gsutil process is really anonymous. Also, revent Boto from falling back
      # on credentials from other files like ~/.aws/credentials or environment
      # variables.
      with SetEnvironmentForTest({
          'DEVSHELL_CLIENT_PORT': None,
          'AWS_SECRET_ACCESS_KEY': '_',
          'AWS_ACCESS_KEY_ID': '_',
          # If shim is used, gcloud might attempt to load credentials.
          'CLOUDSDK_AUTH_DISABLE_CREDENTIALS': 'True',
      }):
        yield

  def _VerifyLocalMode(self, path, expected_mode):
    """Verifies the mode of the file specified at path.

    Args:
      path: The path of the file on the local file system.
      expected_mode: The expected mode as a 3-digit base-8 number.

    Returns:
      None
    """
    self.assertEqual(expected_mode, int(oct(os.stat(path).st_mode)[-3:], 8))

  def _VerifyLocalUid(self, path, expected_uid):
    """Verifies the uid of the file specified at path.

    Args:
      path: The path of the file on the local file system.
      expected_uid: The expected uid of the file.

    Returns:
      None
    """
    self.assertEqual(expected_uid, os.stat(path).st_uid)

  def _VerifyLocalGid(self, path, expected_gid):
    """Verifies the gid of the file specified at path.

    Args:
      path: The path of the file on the local file system.
      expected_gid: The expected gid of the file.

    Returns:
      None
    """
    self.assertEqual(expected_gid, os.stat(path).st_gid)

  def VerifyLocalPOSIXPermissions(self, path, gid=None, uid=None, mode=None):
    """Verifies the uid, gid, and mode of the file specified at path.

    Will only check the attribute if the corresponding method parameter is not
    None.

    Args:
      path: The path of the file on the local file system.
      gid: The expected gid of the file.
      uid: The expected uid of the file.
      mode: The expected mode of the file.

    Returns:
      None
    """
    if gid is not None:
      self._VerifyLocalGid(path, gid)
    if uid is not None:
      self._VerifyLocalUid(path, uid)
    if mode is not None:
      self._VerifyLocalMode(path, mode)

  def FlatListDir(self, directory):
    """Perform a flat listing over directory.

    Args:
      directory: The directory to list

    Returns:
      Listings with path separators canonicalized to '/', to make assertions
      easier for Linux vs Windows.
    """
    result = []
    for dirpath, _, filenames in os.walk(directory):
      for f in filenames:
        result.append(os.path.join(dirpath, f))
    return '\n'.join(result).replace('\\', '/')

  def FlatListBucket(self, bucket_url_string):
    """Perform a flat listing over bucket_url_string."""
    return self.RunGsUtil(['ls', suri(bucket_url_string, '**')],
                          return_stdout=True)

  def StorageUriCloneReplaceKey(self, storage_uri, key):
    """Wrapper for StorageUri.clone_replace_key().

    Args:
      storage_uri: URI representing the object to be cloned
      key: key for the new StorageUri to represent
    """
    return storage_uri.clone_replace_key(key)

  def StorageUriCloneReplaceName(self, storage_uri, name):
    """Wrapper for StorageUri.clone_replace_name().

    Args:
      storage_uri: URI representing the object to be cloned
      key: new object name
    """
    return storage_uri.clone_replace_name(name)

  def StorageUriSetContentsFromString(self, storage_uri, contents):
    """Wrapper for StorageUri.set_contents_from_string().

    Args:
      storage_uri: URI representing the object
      contents: String of the new contents of the object
    """
    return storage_uri.set_contents_from_string(contents)
