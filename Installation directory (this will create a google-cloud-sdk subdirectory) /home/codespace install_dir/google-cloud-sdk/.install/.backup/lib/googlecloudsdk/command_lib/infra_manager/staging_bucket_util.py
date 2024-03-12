# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Support library to handle the staging bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


# The object name to use for our staging GCS storage. This is supposed to be
# identifiable as infra-manager generated, which will assist with cleanup.
STAGING_DIR = 'im_source_staging'


# This function is very similar to the one made for Cloud Build.
def GetDefaultStagingBucket():
  """Returns the default bucket stage files.

  Returns:
    A string representing the GCS bucket name.
  """
  safe_project = (
      properties.VALUES.core.project.Get(required=True)
      .replace(':', '_')
      .replace('.', '_')
      # The string 'google' is not allowed in bucket names.
      .replace('google', 'elgoog')
  )

  return safe_project + '_infra_manager_staging'


def DefaultGCSStagingDir(deployment_short_name, location):
  """Get default staging directory.

  Args:
    deployment_short_name: short name of the deployment.
    location: location of the deployment.

  Returns:
    A default staging directory string.
  """

  gcs_source_bucket_name = GetDefaultStagingBucket()
  gcs_source_staging_dir = 'gs://{0}/{1}/{2}/{3}'.format(
      gcs_source_bucket_name, STAGING_DIR, location, deployment_short_name
  )
  return gcs_source_staging_dir


def DeleteStagingGCSFolder(gcs_client, object_uri):
  """Deletes object if the object_uri is a staging path or else skips deletion.

  Args:
    gcs_client: a storage_api.StorageClient instance for interacting with GCS.
    object_uri: a gcs object path in format gs://path/to/gcs/object.

  Raises:
    NotFoundError: If the bucket or folder does not exist.
  """

  staging_dir_prefix = 'gs://{0}/{1}'.format(
      GetDefaultStagingBucket(), STAGING_DIR
  )

  if not object_uri.startswith(staging_dir_prefix):
    return

  gcs_staging_dir_ref = resources.REGISTRY.Parse(
      object_uri, collection='storage.objects'
  )
  bucket_ref = storage_util.BucketReference(gcs_staging_dir_ref.bucket)
  try:
    items = gcs_client.ListBucket(bucket_ref, gcs_staging_dir_ref.object)
    for item in items:
      object_ref = storage_util.ObjectReference.FromName(
          gcs_staging_dir_ref.bucket, item.name
      )
      gcs_client.DeleteObject(object_ref)
  except storage_api.BucketNotFoundError:
    # if staging bucket does not exist, do nothing
    pass
