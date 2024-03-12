# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Shared resource flags for datafusion commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core.console import console_io


def ParsePolicyFile(policy_file_path, policy_message_type):
  """Constructs an IAM Policy message from a JSON/YAML formatted file.

  Args:
    policy_file_path: Path to the JSON or YAML IAM policy file.
    policy_message_type: Policy message type to convert JSON or YAML to.
  Returns:
    a protorpc.Message of type policy_message_type filled in from the JSON or
    YAML policy file.
  Raises:
    BadFileException if the JSON or YAML file is malformed.
  """
  policy, unused_mask = iam_util.ParseYamlOrJsonPolicyFile(
      policy_file_path,
      policy_message_type)

  if not policy.etag:
    msg = ('The specified policy does not contain an "etag" field '
           'identifying a specific version to replace. Changing a '
           'policy without an "etag" can overwrite concurrent policy '
           'changes.')
    console_io.PromptContinue(
        message=msg, prompt_string='Replace existing policy', cancel_on_no=True)
  return policy


def DoSetIamPolicy(instance_ref,
                   namespace,
                   new_iam_policy,
                   messages,
                   client):
  """Sets IAM policy for a given instance or a namespace."""
  if namespace:
    policy_request = messages.DatafusionProjectsLocationsInstancesNamespacesSetIamPolicyRequest(
        resource='%s/namespaces/%s' % (instance_ref.RelativeName(), namespace),
        setIamPolicyRequest=messages.SetIamPolicyRequest(
            policy=new_iam_policy))
    return client.projects_locations_instances_namespaces.SetIamPolicy(
        policy_request)
  else:
    policy_request = messages.DatafusionProjectsLocationsInstancesSetIamPolicyRequest(
        resource=instance_ref.RelativeName(),
        setIamPolicyRequest=messages.SetIamPolicyRequest(
            policy=new_iam_policy))
    return client.projects_locations_instances.SetIamPolicy(policy_request)


def AddPolicyFileArg(parser):
  parser.add_argument(
      'policy_file',
      metavar='POLICY_FILE',
      help="""\
        Path to a local JSON or YAML file containing a valid policy.

        The output of the `get-iam-policy` command is a valid file, as is any
        JSON or YAML file conforming to the structure of a
        [Policy](https://cloud.google.com/iam/reference/rest/v1/Policy).
        """)
