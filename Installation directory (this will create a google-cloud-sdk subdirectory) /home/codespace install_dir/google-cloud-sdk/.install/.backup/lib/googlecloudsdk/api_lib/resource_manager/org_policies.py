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
"""Org Policies utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite.messages import DecodeError
from apitools.base.py import encoding
from googlecloudsdk.api_lib.resource_manager import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
import six

CONSTRAINTS_PREFIX = 'constraints/'
ORG_POLICIES_API_VERSION = 'v1'


def OrgPoliciesClient():
  return apis.GetClientInstance('cloudresourcemanager',
                                ORG_POLICIES_API_VERSION)


def OrgPoliciesMessages():
  return apis.GetMessagesModule('cloudresourcemanager',
                                ORG_POLICIES_API_VERSION)


def GetFileAsMessage(path, message):
  """Reads a YAML or JSON object of type message from local path.

  Args:
    path: A local path to an object specification in YAML or JSON format.
    message: The message type to be parsed from the file.

  Returns:
    Object of type message, if successful.
  Raises:
    files.Error, exceptions.ResourceManagerInputFileError
  """
  in_text = files.ReadFileContents(path)
  if not in_text:
    raise exceptions.ResourceManagerInputFileError(
        'Empty policy file [{0}]'.format(path))

  # Parse it, first trying YAML then JSON.
  try:
    result = encoding.PyValueToMessage(message, yaml.load(in_text))
  except (ValueError, AttributeError, yaml.YAMLParseError):
    try:
      result = encoding.JsonToMessage(message, in_text)
    except (ValueError, DecodeError) as e:
      # ValueError is raised when JSON is badly formatted
      # DecodeError is raised when a tag is badly formatted (not Base64)
      raise exceptions.ResourceManagerInputFileError(
          'Policy file [{0}] is not properly formatted YAML or JSON '
          'due to [{1}]'.format(path, six.text_type(e)))
  return result


def FormatConstraint(constraint_id):
  if constraint_id.startswith(CONSTRAINTS_PREFIX):
    return constraint_id
  else:
    return CONSTRAINTS_PREFIX + constraint_id
