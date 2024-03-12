# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Flags for gcloud ml language commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import files


LANGUAGE_API = 'language'


class Error(exceptions.Error):
  """Exceptions for this module."""


class ContentFileError(Error):
  """Error if content file can't be read and isn't a GCS URL."""


class ContentError(Error):
  """Error if content is not given."""


def UpdateRequestWithInput(unused_ref, args, request):
  """The Python hook for yaml commands to inject content into the request."""
  content = args.content
  content_file = args.content_file
  document = request.document

  if content_file:
    if content:
      raise ValueError('Either a file or content must be provided for '
                       'analysis by the Natural Language API, not both.')
    if os.path.isfile(content_file):
      document.content = files.ReadFileContents(content_file)
    elif storage_util.ObjectReference.IsStorageUrl(content_file):
      document.gcsContentUri = content_file
    else:
      raise ContentFileError(
          'Could not find --content-file [{}]. Content file must be a path '
          'to a local file or a Google Cloud Storage URL (format: '
          '`gs://bucket_name/object_name`)'.format(content_file))
  elif content:
    document.content = content
  else:
    # Either content_file or content are required. If content is an empty
    # string, raise an error.
    raise ContentError('The content provided is empty. Please provide '
                       'language content to analyze.')
  return request
