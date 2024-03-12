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

"""Common helper methods for Life Sciences commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import tempfile

from apitools.base.protorpclite.messages import DecodeError
from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import extra_types
from apitools.base.py import transfer

from googlecloudsdk.api_lib.lifesciences import exceptions as lifesciences_exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import files
import six

GCS_PREFIX = 'gs://'


def PrettyPrint(resource, print_format='json'):
  """Prints the given resource."""
  resource_printer.Print(
      resources=[resource],
      print_format=print_format,
      out=log.out)


def GetLifeSciencesClient(version='v2beta'):
  return core_apis.GetClientInstance('lifesciences', version)


def GetLifeSciencesMessages(version='v2beta'):
  return core_apis.GetMessagesModule('lifesciences', version)


def GetProjectId():
  return properties.VALUES.core.project.Get(required=True)


def IsGcsPath(path):
  return path.startswith(GCS_PREFIX)


def GetFileAsMessage(path, message, client):
  """Reads a YAML or JSON object of type message from path (local or GCS).

  Args:
    path: A local or GCS path to an object specification in YAML or JSON format.
    message: The message type to be parsed from the file.
    client: The storage_v1 client to use.

  Returns:
    Object of type message, if successful.
  Raises:
    files.Error, lifesciences_exceptions.LifeSciencesInputFileError
  """
  if IsGcsPath(path):
    # Download remote file to a local temp file
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()

    bucket, obj = _SplitBucketAndObject(path)
    storage_messages = core_apis.GetMessagesModule('storage', 'v1')
    get_request = storage_messages.StorageObjectsGetRequest(
        bucket=bucket, object=obj)
    try:
      download = transfer.Download.FromFile(tf.name, overwrite=True)
      client.objects.Get(get_request, download=download)
      del download  # Explicitly close the stream so the results are there
    except apitools_exceptions.HttpError as e:
      raise lifesciences_exceptions.LifeSciencesInputFileError(
          'Unable to read remote file [{0}] due to [{1}]'.format(
              path, six.text_type(e)))
    path = tf.name

  # Read the file.
  in_text = files.ReadFileContents(path)
  if not in_text:
    raise lifesciences_exceptions.LifeSciencesInputFileError(
        'Empty file [{0}]'.format(path))

  # Parse it, first trying YAML then JSON.
  try:
    result = encoding.PyValueToMessage(message, yaml.load(in_text))
  except (ValueError, AttributeError, yaml.YAMLParseError):
    try:
      result = encoding.JsonToMessage(message, in_text)
    except (ValueError, DecodeError) as e:
      # ValueError is raised when JSON is badly formatted
      # DecodeError is raised when a tag is badly formatted (not Base64)
      raise lifesciences_exceptions.LifeSciencesInputFileError(
          'Pipeline file [{0}] is not properly formatted YAML or JSON '
          'due to [{1}]'.format(path, six.text_type(e)))
  return result


def ArgDictToAdditionalPropertiesList(argdict, message):
  result = []
  if argdict is None:
    return result
  # For consistent results (especially for deterministic testing), make
  # the return list ordered by key
  for k, v in sorted(six.iteritems(argdict)):
    result.append(message(key=k, value=v))
  return result


def _SplitBucketAndObject(gcs_path):
  """Split a GCS path into bucket & object tokens, or raise BadFileException."""
  tokens = gcs_path[len(GCS_PREFIX):].strip('/').split('/', 1)
  if len(tokens) != 2:
    raise calliope_exceptions.BadFileException(
        '[{0}] is not a valid Google Cloud Storage path'.format(gcs_path))
  return tokens
