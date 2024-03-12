# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Integration tests for retention command."""

from __future__ import absolute_import

import datetime
import re

import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.util import ObjectToURI as suri

_SECONDS_IN_DAY = 24 * 60 * 60
_DAYS_IN_MONTH = 31
_SECONDS_IN_MONTH = _DAYS_IN_MONTH * _SECONDS_IN_DAY
_DAYS_IN_YEAR = 365.25
_SECONDS_IN_YEAR = int(_DAYS_IN_YEAR * _SECONDS_IN_DAY)


class TestRetention(testcase.GsUtilIntegrationTestCase):
  """Integration tests for retention command."""

  @SkipForS3('Retention is not supported for s3 objects.')
  @SkipForXML('Retention is not supported for XML API.')
  def test_set_retention_seconds(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(['retention', 'set', '60s', suri(bucket_uri)])
    self.VerifyRetentionPolicy(bucket_uri,
                               expected_retention_period_in_seconds=60)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_set_retention_days(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(['retention', 'set', '1d', suri(bucket_uri)])
    self.VerifyRetentionPolicy(
        bucket_uri, expected_retention_period_in_seconds=_SECONDS_IN_DAY)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_set_retention_months(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(['retention', 'set', '1m', suri(bucket_uri)])
    self.VerifyRetentionPolicy(
        bucket_uri, expected_retention_period_in_seconds=_SECONDS_IN_MONTH)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_set_retention_years(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(['retention', 'set', '1y', suri(bucket_uri)])
    self.VerifyRetentionPolicy(
        bucket_uri, expected_retention_period_in_seconds=_SECONDS_IN_YEAR)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_set_retention_multiple_sequential(self):
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()

    self.RunGsUtil(
        ['retention', 'set', '1y',
         suri(bucket1_uri),
         suri(bucket2_uri)])

    self.VerifyRetentionPolicy(
        bucket1_uri, expected_retention_period_in_seconds=_SECONDS_IN_YEAR)
    self.VerifyRetentionPolicy(
        bucket2_uri, expected_retention_period_in_seconds=_SECONDS_IN_YEAR)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_set_retention_multiple_parallel(self):
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()

    self.RunGsUtil(
        ['-m', 'retention', 'set', '1y',
         suri(bucket1_uri),
         suri(bucket2_uri)])

    self.VerifyRetentionPolicy(
        bucket1_uri, expected_retention_period_in_seconds=_SECONDS_IN_YEAR)
    self.VerifyRetentionPolicy(
        bucket2_uri, expected_retention_period_in_seconds=_SECONDS_IN_YEAR)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_increase_retention_unlocked(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY)
    self.RunGsUtil(['retention', 'set', '1m', suri(bucket_uri)])
    self.VerifyRetentionPolicy(
        bucket_uri, expected_retention_period_in_seconds=_SECONDS_IN_MONTH)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_decrease_retention_unlocked(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_MONTH)
    self.RunGsUtil(
        ['retention', 'set', '{}s'.format(_SECONDS_IN_DAY),
         suri(bucket_uri)])
    self.VerifyRetentionPolicy(
        bucket_uri, expected_retention_period_in_seconds=_SECONDS_IN_DAY)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_clear_unlocked_retention(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY)
    self.RunGsUtil(['retention', 'clear', suri(bucket_uri)])
    self.VerifyRetentionPolicy(bucket_uri,
                               expected_retention_period_in_seconds=None)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_set_retention_unlocked_invalid_arg(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(
        ['retention', 'set', '1a', suri(bucket_uri)],
        expected_status=1,
        return_stderr=True)
    self.assertRegex(stderr, r'Incorrect retention period specified')

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_lock_retention_userConfirms(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY)
    self.RunGsUtil(['retention', 'lock', suri(bucket_uri)], stdin='y')
    self.VerifyRetentionPolicy(
        bucket_uri,
        expected_retention_period_in_seconds=_SECONDS_IN_DAY,
        expected_is_locked=True)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_lock_retention_userDoesNotConfirm(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY)
    stderr = self.RunGsUtil(
        ['retention', 'lock', suri(bucket_uri)], stdin='n', return_stderr=True)
    self.assertRegex(stderr,
                             'Abort [Ll]ocking [Rr]etention [Pp]olicy on')
    self.VerifyRetentionPolicy(
        bucket_uri, expected_retention_period_in_seconds=_SECONDS_IN_DAY)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_lock_with_no_retention_policy_invalid(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(
        ['retention', 'lock', suri(bucket_uri)],
        stdin='y',
        expected_status=1,
        return_stderr=True)
    self.assertRegex(
        stderr, 'does not have a(n Unlocked)? [Rr]etention [Pp]olicy')
    self.VerifyRetentionPolicy(bucket_uri,
                               expected_retention_period_in_seconds=None)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_lock_retention_with_invalid_arg(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(
        ['retention', 'lock', '-a', suri(bucket_uri)],
        stdin='y',
        expected_status=1,
        return_stderr=True)
    self.assertRegex(stderr, r'Incorrect option\(s\) specified')

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_lock_retention_already_locked(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY, is_locked=True)
    stderr = self.RunGsUtil(
        ['retention', 'lock', suri(bucket_uri)], stdin='y', return_stderr=True)
    self.assertRegex(stderr,
                             r'Retention [Pp]olicy on .* is already locked')

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_increase_retention_locked(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY, is_locked=True)
    self.RunGsUtil([
        'retention', 'set', '{}s'.format(_SECONDS_IN_DAY + 1),
        suri(bucket_uri)
    ])
    self.VerifyRetentionPolicy(
        bucket_uri,
        expected_retention_period_in_seconds=_SECONDS_IN_DAY + 1,
        expected_is_locked=True)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_decrease_retention_locked(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY, is_locked=True)
    stderr = self.RunGsUtil([
        'retention', 'set', '{}s'.format(_SECONDS_IN_DAY - 1),
        suri(bucket_uri)
    ],
                            expected_status=1,
                            return_stderr=True)
    self.assertRegex(
        stderr, 'Cannot reduce retention duration of a '
        'locked Retention Policy for bucket')

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_clear_locked_retention(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY, is_locked=True)
    stderr = self.RunGsUtil(
        ['retention', 'clear', suri(bucket_uri)],
        expected_status=1,
        return_stderr=True)
    self.assertRegex(
        stderr,
        r'Bucket .* has a locked Retention Policy which cannot be removed')

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_get_retention_locked(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY, is_locked=True)
    stdout = self.RunGsUtil(
        ['-DD', 'retention', 'get', suri(bucket_uri)], return_stdout=True)
    if self._use_gcloud_storage:
      self.assertRegex(stdout, r'isLocked\: true')
      self.assertRegex(stdout, r'retentionPeriod\: \'86400\'')
      self.assertRegex(stdout, r'effectiveTime\: \'.*\'')
    else:
      self.assertRegex(stdout, r'Retention Policy \(LOCKED\):')
      self.assertRegex(stdout, r'Duration: 1 Day\(s\)')
      self.assertRegex(stdout, r'Effective Time: .* GMT')
    actual_retention_policy = self.json_api.GetBucket(
        bucket_uri.bucket_name, fields=['retentionPolicy']).retentionPolicy

    if self._use_gcloud_storage:
      expected_effective_time = datetime.datetime.fromisoformat(
          re.search(r'effectiveTime\: \'(.*)\'', stdout).group(1))
      actual_effective_time = actual_retention_policy.effectiveTime
    else:
      expected_effective_time = self._ConvertTimeStringToSeconds(
          re.search(r'(?<=Time: )[\w,: ]+', stdout).group())
      actual_effective_time = self.DateTimeToSeconds(
          actual_retention_policy.effectiveTime.replace(tzinfo=None))
    self.assertEqual(actual_effective_time, expected_effective_time)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_get_retention_unlocked(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY)
    stdout = self.RunGsUtil(
        ['retention', 'get', suri(bucket_uri)], return_stdout=True)
    if self._use_gcloud_storage:
      # Sometimes the field is absent if isLocked is false.
      self.assertNotRegexpMatches(stdout, r'isLocked \: true')
      self.assertRegex(stdout, r'retentionPeriod\: \'86400\'')
      self.assertRegex(stdout, r'effectiveTime\: \'.*\'')
    else:
      self.assertRegex(stdout, r'Retention Policy \(UNLOCKED\):')
      self.assertRegex(stdout, r'Duration: 1 Day\(s\)')
      self.assertRegex(stdout, r'Effective Time: .* GMT')
    actual_retention_policy = self.json_api.GetBucket(
        bucket_uri.bucket_name, fields=['retentionPolicy']).retentionPolicy

    if self._use_gcloud_storage:
      expected_effective_time = datetime.datetime.fromisoformat(
          re.search(r'effectiveTime\: \'(.*)\'', stdout).group(1))
      actual_effective_time = actual_retention_policy.effectiveTime
    else:
      expected_effective_time = self._ConvertTimeStringToSeconds(
          re.search(r'(?<=Time: )[\w,: ]+', stdout).group())
      actual_effective_time = self.DateTimeToSeconds(
          actual_retention_policy.effectiveTime.replace(tzinfo=None))

    self.assertEqual(actual_effective_time, expected_effective_time)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_get_no_retention(self):
    bucket_uri = self.CreateBucket()
    stdout = self.RunGsUtil(
        ['retention', 'get', suri(bucket_uri)], return_stdout=True)
    if self._use_gcloud_storage:
      self.assertRegex(stdout, 'null')
    else:
      self.assertRegex(stdout, 'has no Retention Policy')

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_get_invalid_args(self):
    bucket_uri = self.CreateBucketWithRetentionPolicy(
        retention_period_in_seconds=_SECONDS_IN_DAY)
    stderr = self.RunGsUtil(
        ['retention', 'get', '-a', suri(bucket_uri)],
        expected_status=1,
        return_stderr=True)
    self.assertRegex(stderr, r'Incorrect option\(s\) specified.')

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_set_temporary_hold_invalid_arg(self):
    object_uri = self.CreateObject()
    stderr = self.RunGsUtil(['retention', 'temp', 'held',
                             suri(object_uri)],
                            expected_status=1,
                            return_stderr=True)
    self.assertRegex(
        stderr, r'Invalid subcommand ".*" for the "retention temp" command')

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_temporary_hold_bucket_with_no_retention(self):
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             temporary_hold=None)
    self.RunGsUtil(['retention', 'temp', 'set', suri(object_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             temporary_hold=True)
    self.RunGsUtil(['retention', 'temp', 'release', suri(object_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             temporary_hold=False)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_temporary_hold_bucket_with_retention(self):
    retention_period = 1
    bucket_uri = self.CreateBucketWithRetentionPolicy(retention_period)
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             temporary_hold=None,
                                             retention_period=retention_period)
    self.RunGsUtil(['retention', 'temp', 'set', suri(object_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             temporary_hold=True,
                                             retention_period=retention_period)
    self.RunGsUtil(['retention', 'temp', 'release', suri(object_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             temporary_hold=False,
                                             retention_period=retention_period)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_temporary_hold_multiple_sequential(self):
    bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    object2_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    self.RunGsUtil(
        ['retention', 'temp', 'set',
         suri(object1_uri),
         suri(object2_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object1_uri,
                                             temporary_hold=True)
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object2_uri,
                                             temporary_hold=True)
    self.RunGsUtil(
        ['retention', 'temp', 'release',
         suri(object1_uri),
         suri(object2_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object1_uri,
                                             temporary_hold=False)
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object2_uri,
                                             temporary_hold=False)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_temporary_hold_multiple_parallel(self):
    bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    object2_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    self.RunGsUtil([
        '-m', 'retention', 'temp', 'set',
        suri(object1_uri),
        suri(object2_uri)
    ])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object1_uri,
                                             temporary_hold=True)
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object2_uri,
                                             temporary_hold=True)
    self.RunGsUtil([
        '-m', 'retention', 'temp', 'release',
        suri(object1_uri),
        suri(object2_uri)
    ])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object1_uri,
                                             temporary_hold=False)
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object2_uri,
                                             temporary_hold=False)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_set_event_based_hold_invalid_arg(self):
    object_uri = self.CreateObject()
    stderr = self.RunGsUtil(['retention', 'event', 'rel',
                             suri(object_uri)],
                            expected_status=1,
                            return_stderr=True)
    self.assertRegex(
        stderr, r'Invalid subcommand ".*" for the "retention event" command')

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_event_based_hold_bucket_with_no_retention(self):
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             event_based_hold=None)
    self.RunGsUtil(['retention', 'event', 'set', suri(object_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             event_based_hold=True)
    self.RunGsUtil(['retention', 'event', 'release', suri(object_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             event_based_hold=False)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_event_based_hold_bucket_with_retention(self):
    retention_period = 1
    bucket_uri = self.CreateBucketWithRetentionPolicy(retention_period)
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             event_based_hold=None,
                                             retention_period=retention_period)
    self.RunGsUtil(['retention', 'event', 'set', suri(object_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             event_based_hold=True,
                                             retention_period=None)
    self.RunGsUtil(['retention', 'event', 'release', suri(object_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object_uri,
                                             event_based_hold=False,
                                             retention_period=retention_period)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_event_based_hold_multiple_sequential(self):
    bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    object2_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    self.RunGsUtil(
        ['retention', 'event', 'set',
         suri(object1_uri),
         suri(object2_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object1_uri,
                                             event_based_hold=True)
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object2_uri,
                                             event_based_hold=True)
    self.RunGsUtil(
        ['retention', 'event', 'release',
         suri(object1_uri),
         suri(object2_uri)])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object1_uri,
                                             event_based_hold=False)
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object2_uri,
                                             event_based_hold=False)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_event_based_hold_multiple_parallel(self):
    bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    object2_uri = self.CreateObject(bucket_uri=bucket_uri, contents='content')
    self.RunGsUtil([
        '-m', 'retention', 'event', 'set',
        suri(object1_uri),
        suri(object2_uri)
    ])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object1_uri,
                                             event_based_hold=True)
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object2_uri,
                                             event_based_hold=True)
    self.RunGsUtil([
        '-m', 'retention', 'event', 'release',
        suri(object1_uri),
        suri(object2_uri)
    ])
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object1_uri,
                                             event_based_hold=False)
    self._VerifyObjectHoldAndRetentionStatus(bucket_uri,
                                             object2_uri,
                                             event_based_hold=False)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_default_event_based_hold(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(['retention', 'event-default', 'set', suri(bucket_uri)])
    self._VerifyDefaultEventBasedHold(bucket_uri,
                                      expected_default_event_based_hold=True)
    self.RunGsUtil(['retention', 'event-default', 'release', suri(bucket_uri)])
    self._VerifyDefaultEventBasedHold(bucket_uri,
                                      expected_default_event_based_hold=False)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_default_event_based_hold_multiple_sequential(self):
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()
    self.RunGsUtil([
        'retention', 'event-default', 'set',
        suri(bucket1_uri),
        suri(bucket2_uri)
    ])
    self._VerifyDefaultEventBasedHold(bucket1_uri,
                                      expected_default_event_based_hold=True)
    self._VerifyDefaultEventBasedHold(bucket2_uri,
                                      expected_default_event_based_hold=True)

  @SkipForS3('Retention is not supported for s3 objects')
  @SkipForXML('Retention is not supported for XML API')
  def test_default_event_based_hold_multiple_parallel(self):
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()
    self.RunGsUtil([
        'retention', 'event-default', 'set',
        suri(bucket1_uri),
        suri(bucket2_uri)
    ])
    self._VerifyDefaultEventBasedHold(bucket1_uri,
                                      expected_default_event_based_hold=True)
    self._VerifyDefaultEventBasedHold(bucket2_uri,
                                      expected_default_event_based_hold=True)

  def _VerifyObjectHoldAndRetentionStatus(self,
                                          bucket_uri,
                                          object_uri,
                                          temporary_hold=None,
                                          event_based_hold=None,
                                          retention_period=None):
    object_metadata = self.json_api.GetObjectMetadata(
        bucket_uri.bucket_name,
        object_uri.object_name,
        fields=[
            'timeCreated', 'temporaryHold', 'eventBasedHold',
            'retentionExpirationTime'
        ])
    if temporary_hold is None:
      self.assertEqual(object_metadata.temporaryHold, None)
    else:
      self.assertEqual(object_metadata.temporaryHold, temporary_hold)

    if event_based_hold is None:
      self.assertEqual(object_metadata.eventBasedHold, None)
    else:
      self.assertEqual(object_metadata.eventBasedHold, event_based_hold)

    if retention_period is None:
      self.assertEqual(object_metadata.retentionExpirationTime, None)
    elif event_based_hold is False:
      retention_policy = self.json_api.GetBucket(bucket_uri.bucket_name,
                                                 fields=['retentionPolicy'
                                                        ]).retentionPolicy
      time_delta = datetime.timedelta(0, retention_policy.retentionPeriod)
      expected_expiration_time = object_metadata.timeCreated + time_delta
      if event_based_hold is None:
        self.assertEqual(object_metadata.retentionExpirationTime,
                         expected_expiration_time)
      else:
        # since we don't expose the release time of event-based hold we can
        # only verify that expected_expiration_time is greater than
        #     object-creation-time + retention period
        # that is because
        #     eventBased-hold's release time > object-creation-time
        self.assertGreater(object_metadata.retentionExpirationTime,
                           expected_expiration_time)

  def _VerifyDefaultEventBasedHold(self,
                                   bucket_uri,
                                   expected_default_event_based_hold=None):
    actual_default_event_based_hold = self.json_api.GetBucket(
        bucket_uri.bucket_name,
        fields=['defaultEventBasedHold']).defaultEventBasedHold

    if expected_default_event_based_hold is None:
      self.assertEqual(actual_default_event_based_hold, None)
    else:
      self.assertEqual(actual_default_event_based_hold,
                       expected_default_event_based_hold)

  def _ConvertTimeStringToSeconds(self, time_string):
    """Converts time in following format to its equivalent timestamp in seconds.

      Format: '%a, %d %b %Y %H:%M:%S GMT'
        i.e.: 'Fri, 18 Aug 2017 23:31:39 GMT'

    Args:
      time_string: time in string format.

    Returns:
      returns equivalent timestamp in seconds of given time.
    """
    converted_time = datetime.datetime.strptime(time_string,
                                                '%a, %d %b %Y %H:%M:%S GMT')
    return self.DateTimeToSeconds(converted_time)
