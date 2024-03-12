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
"""Utils for GKE Connect generate gateway RBAC policy names."""

from googlecloudsdk.command_lib.container.fleet import invalid_args_error

RBAC_IMPERSONATE_POLICY_NAME = 'gateway-impersonate-{metadata}'
RBAC_PERMISSION_POLICY_NAME = 'gateway-permission-{metadata}'
RBAC_ANTHOS_SUPPORT_POLICY_NAME = 'gateway-anthos-support-permission-{metadata}'
PRINCIPAL_USER_FORMAT = [
    'principal:',
    '',
    'iam.googleapis.com',
    'locations',
    'workforcePools',
    'subject',
]
PRINCIPAL_GROUP_FORMAT = [
    'principalSet:',
    '',
    'iam.googleapis.com',
    'locations',
    'workforcePools',
    'group',
]
UNWANTED_CHARS = [' ', '/', '%']


def RbacPolicyName(policy_name, project_id, membership, identity, is_user):
  """Generate RBAC policy name."""
  formatted_identity = FormatIdentityForResourceNaming(identity, is_user)
  if membership:
    metadata_name = project_id + '_' + formatted_identity + '_' + membership
  else:
    metadata_name = project_id + '_' + formatted_identity

  if policy_name == 'impersonate':
    return RBAC_IMPERSONATE_POLICY_NAME.format(metadata=metadata_name)
  if policy_name == 'permission':
    return RBAC_PERMISSION_POLICY_NAME.format(metadata=metadata_name)
  if policy_name == 'anthos':
    return RBAC_ANTHOS_SUPPORT_POLICY_NAME.format(metadata=metadata_name)


def FormatIdentityForResourceNaming(identity, is_user):
  """Format user by removing disallowed characters for k8s resource naming."""
  # Check if the identity is a user or group.
  if is_user:
    desired_format = PRINCIPAL_USER_FORMAT
    error_message = invalid_args_error.INVALID_ARGS_USER_MESSAGE
  else:
    desired_format = PRINCIPAL_GROUP_FORMAT
    error_message = invalid_args_error.INVALID_ARGS_GROUP_MESSAGE
  parts = identity.split('/')
  if len(parts) >= 9:
    # Check the fields shared by all third-party principals.
    common_parts = parts[:4] + parts[5:8:2]
    if common_parts == desired_format:
      workforce_pool = identity.split('/workforcePools/')[1].split('/')[0]
      principal = identity.split('/{}/'.format(desired_format[-1]))[1]
      # Keep only the prefix if the identity is represented by an email.
      principal = principal.split('@')[0]
      # Include workforce pool and remove unwanted characters from the
      # principal name.
      resource_name = workforce_pool + '_' + principal
    else:
      raise invalid_args_error.InvalidArgsError(error_message)
  else:
    if '@' not in identity:
      raise invalid_args_error.InvalidArgsError(error_message)
    else:
      resource_name = identity.split('@')[0]
  # Get rid of spaces to make RBAC policy management easier (not using
  # quotes around the name) and '/' and '%' due to naming restrictions.
  for ch in UNWANTED_CHARS:
    resource_name = resource_name.replace(ch, '')

  return resource_name
