# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Client for interaction with Dataplex."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import io

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml


def GetClientInstance():
  return apis.GetClientInstance('dataplex', 'v1')


def GetMessageModule():
  return apis.GetMessagesModule('dataplex', 'v1')


def WaitForOperation(
    operation, resource, sleep_ms=5000, pre_start_sleep_ms=1000
):
  """Waits for the given google.longrunning.Operation to complete."""
  operation_ref = resources.REGISTRY.Parse(
      operation.name, collection='dataplex.projects.locations.operations'
  )
  poller = waiter.CloudOperationPoller(
      resource, GetClientInstance().projects_locations_operations
  )
  return waiter.WaitFor(
      poller,
      operation_ref,
      'Waiting for [{0}] to finish'.format(operation_ref.RelativeName()),
      sleep_ms=sleep_ms,
      pre_start_sleep_ms=pre_start_sleep_ms,
  )


def CreateLabels(dataplex_resource, args):
  if getattr(args, 'labels', None):
    return dataplex_resource.LabelsValue(
        additionalProperties=[
            dataplex_resource.LabelsValue.AdditionalProperty(
                key=key, value=value
            )
            for key, value in sorted(args.labels.items())
        ]
    )
  return None


def ReadObject(object_url, storage_client=None):
  """Reads an object's content from GCS.

  Args:
    object_url: Can be a local file path or the URL of the object to be read
      from gcs bucket (must have "gs://" prefix).
    storage_client: Storage api client used to read files from gcs.

  Returns:
    A str for the content of the file.

  Raises:
    ObjectReadError:
      If the read of GCS object is not successful.
  """
  if not object_url.startswith('gs://'):
    return yaml.load_path(object_url)
  client = storage_client or storage_api.StorageClient()
  object_ref = storage_util.ObjectReference.FromUrl(object_url)
  try:
    bytes_io = client.ReadObject(object_ref)
    wrapper = io.TextIOWrapper(bytes_io, encoding='utf-8')
    return yaml.load(wrapper.read())
  except Exception as e:
    raise exceptions.BadFileException(
        'Unable to read file {0} due to incorrect file path or insufficient'
        ' read permissions'.format(object_url)
    ) from e


def SnakeToCamel(arg_str):
  """Converts snake case string to camel case."""
  return ''.join(
      word.capitalize() if ind > 0 else word
      for ind, word in enumerate(arg_str.split('_'))
  )


def SnakeToCamelDict(arg_type):
  """Reccursive method to convert all nested snake case dictionary keys to camel case."""
  if isinstance(arg_type, list):
    return [
        SnakeToCamelDict(list_val)
        if isinstance(list_val, (dict, list))
        else list_val
        for list_val in arg_type
    ]
  return {
      SnakeToCamel(key): (
          SnakeToCamelDict(value) if isinstance(value, (dict, list)) else value
      )
      for key, value in arg_type.items()
  }


def FetchExecutionSpecArgs(args_map_as_list):
  """Returns Dataplex task execution spec args as a map of key,value pairs from an input list of strings of format key=value."""
  execution_args_map = dict()
  for arg_entry in args_map_as_list:
    if '=' not in arg_entry:
      raise argparse.ArgumentTypeError(
          "Execution spec argument '{}' should be of the type argKey=argValue."
          .format(arg_entry)
      )
    arg_entry_split = arg_entry.split('=', 1)
    if (
        len(arg_entry_split) < 2
        or len(arg_entry_split[0].strip()) == 0
        or len(arg_entry_split[1]) == 0
    ):
      raise argparse.ArgumentTypeError(
          "Execution spec argument '{}' should be of the format"
          ' argKey=argValue.'.format(arg_entry)
      )
    execution_args_map[arg_entry_split[0]] = arg_entry_split[1]
  return execution_args_map
