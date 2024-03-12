# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Helpers for dealing with storage buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log


def _BucketAllowsPublicObjectReads(bucket):
  return any([acl.entity.lower() == 'allusers' and acl.role.lower() == 'reader'
              for acl in bucket.defaultObjectAcl])


def ValidateBucketForCertificateAuthority(bucket_name):
  """Validates that a user-specified bucket can be used with a Private CA.

  Args:
    bucket_name: The name of the GCS bucket to validate.

  Returns:
    A BucketReference wrapping the given bucket name.

  Raises:
    InvalidArgumentException: when the given bucket can't be used with a CA.
  """
  messages = storage_util.GetMessages()
  client = storage_api.StorageClient(messages=messages)

  try:
    bucket = client.GetBucket(
        bucket_name,
        messages.StorageBucketsGetRequest.ProjectionValueValuesEnum.full)

    if not _BucketAllowsPublicObjectReads(bucket):
      # Show a warning but don't fail, since this could be intentional.
      log.warning(
          'The specified bucket does not publicly expose new objects by '
          'default, so some clients may not be able to access the CA '
          'certificate or CRLs. For more details, see '
          'https://cloud.google.com/storage/docs/access-control/making-data-public'
      )

    return storage_util.BucketReference(bucket_name)
  except storage_api.BucketNotFoundError:
    raise exceptions.InvalidArgumentException(
        'gcs-bucket', 'The given bucket does not exist.')
