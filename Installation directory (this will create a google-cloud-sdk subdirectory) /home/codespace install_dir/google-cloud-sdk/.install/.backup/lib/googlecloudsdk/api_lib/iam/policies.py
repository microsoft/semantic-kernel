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
"""Utilities for Policies API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import binascii

from apitools.base.protorpclite import messages as apitools_messages
from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import yaml
import six


def GetClientInstance(release_track, no_http=False):
  if release_track == base.ReleaseTrack.ALPHA:
    return apis.GetClientInstance('iam', 'v2alpha', no_http=no_http)
  elif release_track == base.ReleaseTrack.BETA:
    return apis.GetClientInstance('iam', 'v2beta', no_http=no_http)
  else:
    return apis.GetClientInstance('iam', 'v2', no_http=no_http)


def GetMessagesModule(release_track, client=None):
  client = client or GetClientInstance(release_track)
  return client.MESSAGES_MODULE


def ParseYamlOrJsonPolicyFile(policy_file_path, policy_message_type):
  """Create an IAM V2 Policy protorpc.Message from YAML or JSON formatted file.

  Returns the parsed policy object.
  Args:
    policy_file_path: Path to the YAML or JSON IAM policy file.
    policy_message_type: Policy message type to convert YAML to.

  Returns:
    policy that is a protorpc.Message of type policy_message_type filled in
    from the JSON or YAML policy file
  Raises:
    BadFileException if the YAML or JSON file is malformed.
    IamEtagReadError if the etag is badly formatted.
  """
  policy_to_parse = yaml.load_path(policy_file_path)
  try:
    policy = encoding.PyValueToMessage(policy_message_type, policy_to_parse)
  except (AttributeError, apitools_messages.ValidationError) as e:
    # Raised when the input file is not properly formatted YAML policy file.
    raise gcloud_exceptions.BadFileException(
        'Policy file [{0}] is not a properly formatted YAML or JSON '
        'policy file. {1}'.format(policy_file_path, six.text_type(e)))
  except (apitools_messages.DecodeError, binascii.Error) as e:
    # DecodeError is raised when etag is badly formatted (not proper Base64)
    raise iam_util.IamEtagReadError(
        'The etag of policy file [{0}] is not properly formatted. {1}'.format(
            policy_file_path, six.text_type(e)))
  return policy


def ListDenyPolicies(resource_id, resource_type, release_track):
  """Gets the IAM Deny policies for an organization.

  Args:
    resource_id: id for the resource
    resource_type: what type of a resource the id represents. Either
      organization, project, or folder
    release_track: ALPHA or BETA or GA

  Returns:
    The output from the ListPolicies API call for deny policies for the passed
    resource.
  """

  client = GetClientInstance(release_track)
  messages = GetMessagesModule(release_track)
  policies_to_return = []

  if resource_type in ['organization', 'folder', 'project']:

    attachment_point = 'policies/cloudresourcemanager.googleapis.com%2F{}s%2F{}/denypolicies'.format(
        resource_type, resource_id)

    policies_to_fetch = client.policies.ListPolicies(
        messages.IamPoliciesListPoliciesRequest(
            parent=attachment_point)).policies

    for policy_metadata in policies_to_fetch:
      policy = client.policies.Get(
          messages.IamPoliciesGetRequest(name=policy_metadata.name))
      policies_to_return.append(policy)

    return policies_to_return

  raise gcloud_exceptions.UnknownArgumentException('resource_type',
                                                   resource_type)
