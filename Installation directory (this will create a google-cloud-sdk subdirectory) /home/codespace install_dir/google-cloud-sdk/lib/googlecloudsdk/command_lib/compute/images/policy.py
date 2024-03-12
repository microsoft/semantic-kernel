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
"""Utilities necessary to augment images statuses with org policy.

AugmentImagesStatus function in this module call OrgPolicy and augment images
status if the policy requires it.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.resource_manager import org_policies
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


def AugmentImagesStatus(resource_registry, project_id, images):
  """Sets images status to 'BLOCKED_BY_POLICY' as specified by OrgPolicy.

  Get OrgPolicy for the project and set images status to BLOCKED_BY_POLICY
  if the policy exists and blocks the image. If no policy exists, all images are
  allowed.

  NOTE: This function sends requests to OrgPolicy API.

  Args:
    resource_registry: resources.Registry, Resource registry
    project_id: str, Project in which image will be used
    images: Iterable[Dict], The images (in dict form) to set the status on

  Yields:
    Images (in dict form) with status set to BLOCKED_BY_POLICY as specified by
    OrgPolicy.

  Raises:
    exceptions.GetPolicyError if OrgPolicy call failed or returned malformed
    data.
  """

  # Iterate through generator and convert to list up-front: we'll need to copy
  # it
  # Copy all images since we'll be mutating them
  images = copy.deepcopy(list(images))

  # If the OrgPolicy call fails, it populates errors_collected rather than
  # raising an exception. Checking the OrgPolicy client-side is non-critical,
  # so we don't want a failure here to block output. Instead, we yield all
  # images to the user and then raise exception (if errors are present).
  # This way we both return data and errors.
  errors_collected = []
  policy = _GetPolicyNoThrow(project_id, errors_collected)

  if policy is not None:
    # Else GetEffectiveOrgPolicy call failed. We don't report any image as
    # BLOCKED_BY_POLICY in such case.
    for image in images:
      if image['status'] != 'READY':
        yield image
      elif _IsAllowed(resource_registry,
                      resource_registry.Parse(image['selfLink']).project,
                      policy, errors_collected):
        yield image
      else:
        image['status'] = 'BLOCKED_BY_POLICY'
        yield image
  else:
    for image in images:
      yield image

  # At this point all images were returned, but we may have some errors
  # collected which should be forwarded to the user as well. OrgPolicy call is
  # considered non-critical for the command. If API call failed or returned
  # malformed data, list command will continue to work (without information from
  # OrgPolicy). Error will be visible only if --verbosity=info or greater
  for error in errors_collected or []:
    log.info(error)


def _GetPolicy(project_id):
  """Get effective org policy of given project."""
  messages = org_policies.OrgPoliciesMessages()
  request = messages.CloudresourcemanagerProjectsGetEffectiveOrgPolicyRequest(
      projectsId=project_id,
      getEffectiveOrgPolicyRequest=messages.GetEffectiveOrgPolicyRequest(
          constraint=org_policies.FormatConstraint(
              'compute.trustedImageProjects')))
  client = org_policies.OrgPoliciesClient()
  response = client.projects.GetEffectiveOrgPolicy(request)
  # There are several possible policy types; the only policy type that applies
  # to 'compute.trustedImageProjects' is listPolicy, so we can assume that's
  # what the caller is interested in.
  return response.listPolicy


def _GetPolicyNoThrow(project_id, errors_to_propagate):
  """Call GetPolicy and handle possible errors from backend."""
  try:
    return _GetPolicy(project_id)
  except apitools_exceptions.HttpError as e:
    # We were unable to get OrgPolicy. This is an attempt to degrade gcloud
    # functionality gracefully. We turn stack unwind into object and store it
    # in output parameter for later processing (displaying).
    errors_to_propagate.append(e)

    return None


def _IsAllowed(resource_registry, project_id, policy, errors_to_propagate):
  """Decides if project is allowed within policy."""
  # Computational complexity is O(len(allowed_values) + len(denied_values))

  if policy.allValues is policy.AllValuesValueValuesEnum.ALLOW:
    return True
  elif policy.allValues is policy.AllValuesValueValuesEnum.DENY:
    return False

  is_allowed = False
  # policy.allowedValues is a repeated field, it is never None
  if not policy.allowedValues:
    is_allowed = True

  try:
    for project_record in policy.allowedValues:
      resource_registry.ParseRelativeName(project_record, 'compute.projects')
  except resources.InvalidResourceException as e:
    # If policy is malformed we want to consider all projects as allowed
    # (graceful degradation). Error will be reported to the user separately
    errors_to_propagate.append(e)
    is_allowed = True
  else:
    if (resource_registry.Parse(
        project_id,
        collection='compute.projects').RelativeName() in policy.allowedValues):
      is_allowed = True

  is_denied = False
  try:
    for project_record in policy.deniedValues:
      resource_registry.ParseRelativeName(project_record, 'compute.projects')
  except resources.InvalidResourceException as e:
    is_denied = False
    errors_to_propagate.append(e)
  else:
    if (resource_registry.Parse(
        project_id,
        collection='compute.projects').RelativeName() in policy.deniedValues):
      is_denied = True

  return is_allowed and not is_denied
