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
"""V1-specific utilities for function source code."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import exceptions as http_exceptions
from googlecloudsdk.api_lib.functions import cmek_util
from googlecloudsdk.api_lib.functions.v1 import util as api_util
from googlecloudsdk.command_lib.functions import source_util
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files as file_utils


def _AddDefaultBranch(source_archive_url):
  cloud_repo_pattern = (
      r'^https://source\.developers\.google\.com'
      r'/projects/[^/]+'
      r'/repos/[^/]+$'
  )
  if re.match(cloud_repo_pattern, source_archive_url):
    return source_archive_url + '/moveable-aliases/master'
  return source_archive_url


def _GetUploadUrl(messages, service, function_ref, kms_key=None):
  """Retrieves the upload url to upload source code."""
  generate_upload_url_request = None
  if kms_key:
    generate_upload_url_request = messages.GenerateUploadUrlRequest(
        kmsKeyName=kms_key
    )
  request = (
      messages.CloudfunctionsProjectsLocationsFunctionsGenerateUploadUrlRequest
  )(
      parent='projects/{}/locations/{}'.format(
          function_ref.projectsId, function_ref.locationsId
      ),
      generateUploadUrlRequest=generate_upload_url_request,
  )
  try:
    response = service.GenerateUploadUrl(request)
    return response.uploadUrl
  except http_exceptions.HttpError as e:
    cmek_util.ProcessException(e, kms_key)
    raise e


def SetFunctionSourceProps(
    function,
    function_ref,
    source_arg,
    stage_bucket,
    ignore_file=None,
    kms_key=None,
):
  """Add sources to function.

  Args:
    function: The function to add a source to.
    function_ref: The reference to the function.
    source_arg: Location of source code to deploy.
    stage_bucket: The name of the Google Cloud Storage bucket where source code
      will be stored.
    ignore_file: custom ignore_file name. Override .gcloudignore file to
      customize files to be skipped.
    kms_key: KMS key configured for the function.

  Returns:
    A list of fields on the function that have been changed.
  Raises:
    FunctionsError: If the kms_key doesn't exist or GCF P4SA lacks permissions.
  """
  function.sourceArchiveUrl = None
  function.sourceRepository = None
  function.sourceUploadUrl = None

  messages = api_util.GetApiMessagesModule()

  if source_arg is None:
    source_arg = '.'
  source_arg = source_arg or '.'
  if source_arg.startswith('gs://'):
    if not source_arg.endswith('.zip'):
      # Users may have .zip archives with unusual names, and we don't want to
      # prevent those from being deployed; the deployment should go through so
      # just warn here.
      log.warning(
          '[{}] does not end with extension `.zip`. '
          'The `--source` argument must designate the zipped source archive '
          'when providing a Google Cloud Storage URI.'.format(source_arg)
      )
    function.sourceArchiveUrl = source_arg
    return ['sourceArchiveUrl']
  elif source_arg.startswith('https://'):
    function.sourceRepository = messages.SourceRepository(
        url=_AddDefaultBranch(source_arg)
    )
    return ['sourceRepository']
  with file_utils.TemporaryDirectory() as tmp_dir:
    zip_file = source_util.CreateSourcesZipFile(
        tmp_dir,
        source_arg,
        ignore_file,
        enforce_size_limit=True,
    )
    service = api_util.GetApiClientInstance().projects_locations_functions

    if stage_bucket:
      dest_object = source_util.UploadToStageBucket(
          zip_file, function_ref, stage_bucket
      )
      function.sourceArchiveUrl = dest_object.ToUrl()
      return ['sourceArchiveUrl']

    upload_url = _GetUploadUrl(messages, service, function_ref, kms_key)
    source_util.UploadToGeneratedUrl(
        zip_file,
        upload_url,
        extra_headers={
            # Magic header that needs to be specified per:
            # https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions/generateUploadUrl
            'x-goog-content-length-range': '0,104857600',
        },
    )
    function.sourceUploadUrl = upload_url
    return ['sourceUploadUrl']
