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

"""Base class for Organization commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import organizations
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources


class UnknownOrganizationError(exceptions.BadArgumentException):

  def __init__(self, org_argument, metavar='ORGANIZATION_ID'):
    message = ('Cannot determine Organization ID from [{0}]. '
               'Try `gcloud organizations list` to find your Organization ID.'
               .format(org_argument))
    super(UnknownOrganizationError, self).__init__(metavar, message)


def StripOrgPrefix(org_id):
  prefix = 'organizations/'
  if org_id.startswith(prefix):
    return org_id[len(prefix):]
  else:
    return org_id


def OrganizationsUriFunc(resource):
  """Get the Organization URI for the given resource."""
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName('cloudresourcemanager', 'v1')
  org_id = StripOrgPrefix(resource.name)
  org_ref = registry.Parse(
      None,
      params={
          'organizationsId': org_id,
      },
      collection='cloudresourcemanager.organizations')
  return org_ref.SelfLink()


def GetOrganization(org_argument):
  """Get the Organization object for the provided Organization argument.

  Returns the organization object for a given organization ID or will search
  for and return the organization object associated with the given domain name.

  Args:
    org_argument: The value of the organization argument.

  Returns:
    An object representing an organization, or None if the organization could
    not be determined.
  """
  orgs_client = organizations.Client()
  org_id = StripOrgPrefix(org_argument)

  if org_id.isdigit():
    return orgs_client.Get(org_id)
  else:
    return orgs_client.GetByDomain(org_id)


def GetOrganizationId(org_argument):
  """Get the Organization ID for the provided Organization argument.

  Numeric values will be returned, values like 'organizations/123456789' will
  return '123456789' and a value like 'example.com' will search for the
  organization ID associated with that domain.

  Args:
    org_argument: The value of the organization argument.

  Returns:
    A string containing the numeric organization ID, or None if the
    organization ID could not be determined.
  """
  orgs_client = organizations.Client()
  org_id = StripOrgPrefix(org_argument)
  if org_id.isdigit():
    return org_id
  else:
    org_object = orgs_client.GetByDomain(org_id)
    if org_object:
      return StripOrgPrefix(org_object.name)
    else:
      return None
