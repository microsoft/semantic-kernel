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

"""Utilities for gcloud ml vision commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import files

VISION_API = 'vision'
VISION_API_VERSION = 'v1'
IMAGE_URI_FORMAT = r'^(https{,1}?|gs)://'
FILE_URI_FORMAT = r'gs://([^/]+)/(.+)'
FILE_PREFIX = r'gs://([^/]+)(/.*)*'


class Error(exceptions.Error):
  """Error for gcloud ml vision commands."""


class ImagePathError(Error):
  """Error if an image path is improperly formatted."""


class GcsSourceError(Error):
  """Error if a gcsSource path is improperly formatted."""


class GcsDestinationError(Error):
  """Error if a gcsDestination path is improperly formatted."""


def GetImageFromPath(path):
  """Builds an Image message from a path.

  Args:
    path: the path arg given to the command.

  Raises:
    ImagePathError: if the image path does not exist and does not seem to be
        a remote URI.

  Returns:
    vision_v1_messages.Image: an image message containing information for the
        API on the image to analyze.
  """
  messages = apis.GetMessagesModule(VISION_API, VISION_API_VERSION)
  image = messages.Image()

  if os.path.isfile(path):
    image.content = files.ReadBinaryFileContents(path)
  elif re.match(IMAGE_URI_FORMAT, path):
    image.source = messages.ImageSource(imageUri=path)
  else:
    raise ImagePathError(
        'The image path does not exist locally or is not properly formatted. '
        'A URI for a remote image must be a Google Cloud Storage image URI, '
        'which must be in the form `gs://bucket_name/object_name`, or a '
        'publicly accessible image HTTP/HTTPS URL. Please double-check your '
        'input and try again.')
  return image


def GetGcsSourceFromPath(input_file):
  """Validate a Google Cloud Storage location to read the PDF/TIFF file from.

  Args:
    input_file: the input file path arg given to the command.

  Raises:
    GcsSourceError: if the file is not a Google Cloud Storage object.

  Returns:
    vision_v1_messages.GcsSource: Google Cloud Storage URI for the input file.
    This must only be a Google Cloud Storage object.
    Wildcards are not currently supported.
  """
  messages = apis.GetMessagesModule(VISION_API, VISION_API_VERSION)
  gcs_source = messages.GcsSource()

  if re.match(FILE_URI_FORMAT, input_file):
    gcs_source.uri = input_file
  else:
    raise GcsSourceError(
        'The URI for the input file must be a Google Cloud Storage object, '
        'which must be in the form `gs://bucket_name/object_name.'
        'Please double-check your input and try again.')
  return gcs_source


def GetGcsDestinationFromPath(path):
  """Validate a Google Cloud Storage location to write the output to.

  Args:
    path: the path arg given to the command.

  Raises:
    GcsDestinationError: if the file is not a Google Cloud Storage object.

  Returns:
    vision_v1_messages.GcsDestination:Google Cloud Storage URI prefix
    where the results will be stored.
    This must only be a Google Cloud Storage object.
    Wildcards are not currently supported.
  """
  messages = apis.GetMessagesModule(VISION_API, VISION_API_VERSION)
  gcs_destination = messages.GcsDestination()

  if re.match(FILE_PREFIX, path):
    gcs_destination.uri = path
  else:
    raise GcsDestinationError(
        'The URI for the input file must be a Google Cloud Storage object, '
        'which must be in the File prefix format `gs://bucket_name/here/file_name_prefix.'
        'or directory prefix format `gs://bucket_name/some/location/. '
        'Please double-check your input and try again.')
  return gcs_destination

