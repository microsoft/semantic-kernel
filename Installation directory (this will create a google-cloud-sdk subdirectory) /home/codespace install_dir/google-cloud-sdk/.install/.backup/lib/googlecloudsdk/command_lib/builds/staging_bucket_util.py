# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

import os

from googlecloudsdk.api_lib.cloudbuild import snapshot
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_transform

_ALLOWED_SOURCE_EXT = ('.zip', '.tgz', '.gz')


def GetDefaultStagingBucket():
  """Returns the default bucket stage files.

  Returns:
    GCS bucket name.
  """
  safe_project = (properties.VALUES.core.project.Get(required=True)
                  .replace(':', '_')
                  .replace('.', '_')
                  # The string 'google' is not allowed in bucket names.
                  .replace('google', 'elgoog'))

  return safe_project + '_cloudbuild'


def GetDefaultRegionalStagingBucket(region):
  """Returns the default regional bucket name.

  Args:
    region: Cloud Build region.

  Returns:
    GCS bucket name.
  """
  safe_project = (
      properties.VALUES.core.project.Get(required=True)
      .replace(':', '_')
      .replace('.', '_')
      # The string 'google' is not allowed in bucket names.
      .replace('google', 'elgoog')
  )

  return safe_project + '_' + region + '_cloudbuild'


def Upload(
    source,
    gcs_source_staging,
    gcs_client,
    ignore_file,
    hide_logs=False,
):
  """Uploads a file to GCS.

  Args:
    source: The location of the source.
    gcs_source_staging: storage.objects Resource, The GCS object to write.
    gcs_client: storage_api.StorageClient, The storage client to use for
      uploading.
    ignore_file: Override .gcloudignore file to specify skip files.
    hide_logs: boolean, not print the status message if the flag is true.

  Returns:
    storage_v1_messages.Object, The written GCS object.
  """
  if source.startswith('gs://'):
    gcs_source = resources.REGISTRY.Parse(source, collection='storage.objects')
    return gcs_client.Rewrite(gcs_source, gcs_source_staging)

  if not os.path.exists(source):
    raise c_exceptions.BadFileException(
        'could not find source [{src}]'.format(src=source)
    )

  if os.path.isdir(source):
    source_snapshot = snapshot.Snapshot(source, ignore_file=ignore_file)
    size_str = resource_transform.TransformSize(
        source_snapshot.uncompressed_size
    )
    if not hide_logs:
      log.status.Print(
          'Creating temporary tarball archive of {num_files} file(s)'
          ' totalling {size} before compression.'.format(
              num_files=len(source_snapshot.files), size=size_str
          )
      )
    return source_snapshot.CopyTarballToGCS(
        gcs_client,
        gcs_source_staging,
        ignore_file=ignore_file,
        hide_logs=hide_logs,
    )
  else:
    # os.path.isfile(source)
    unused_root, ext = os.path.splitext(source)
    if ext not in _ALLOWED_SOURCE_EXT:
      # TODO(b/320560159): Properly include source in error message
      raise c_exceptions.BadFileException(
          'Local file [{src}] is none of ' + ', '.join(_ALLOWED_SOURCE_EXT)
      )
    if not hide_logs:
      log.status.Print(
          'Uploading local file [{src}] to [gs://{bucket}/{object}].'.format(
              src=source,
              bucket=gcs_source_staging.bucket,
              object=gcs_source_staging.object,
          )
      )
    return gcs_client.CopyFileToGCS(source, gcs_source_staging)
