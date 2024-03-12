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
"""Useful commands for interacting with the Cloud Identity Groups API."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.util import apis

API_NAME = 'cloudidentity'


def GetClient(version):
  """Import and return the appropriate Cloud Identity Groups client.

  Args:
    version: str, the version of the API desired

  Returns:
    Cloud Identity Groups client for the appropriate release track
  """
  return apis.GetClientInstance(API_NAME, version)


def GetMessages(version):
  """Import and return the appropriate Cloud Identity Groups messages module.

  Args:
    version: str, the version of the API desired

  Returns:
    Cloud Identity Groups messages for the appropriate release track
  """
  return apis.GetMessagesModule(API_NAME, version)


def GetGroup(version, group):
  """Get a Cloud Identity Group.

  Args:
    version: Release track information.
    group: Name of group as returned by LookupGroupName()
      (i.e. 'groups/{group_id}').
  Returns:
    Group resource object.
  """
  client = GetClient(version)
  messages = GetMessages(version)
  return client.groups.Get(
      messages.CloudidentityGroupsGetRequest(name=group))


def LookupGroupName(version, email):
  """Lookup Group Name for a specified group key id.

  Args:
    version: Release track information
    email: str, group email

  Returns:
    LookupGroupNameResponse: Response message for LookupGroupName operation
    which is containing a resource name of the group in the format:
    'name: groups/{group_id}'
  """

  client = GetClient(version)
  messages = GetMessages(version)

  encoding.AddCustomJsonFieldMapping(
      messages.CloudidentityGroupsLookupRequest,
      'groupKey_id', 'groupKey.id')
  return client.groups.Lookup(
      messages.CloudidentityGroupsLookupRequest(groupKey_id=email))


def LookupMembershipName(version, group_id, member_email):
  """Lookup membership name for a specific pair of member key id and group email.

  Args:
    version: Release track information
    group_id: str, group id (e.g. groups/03qco8b4452k99t)
    member_email: str, member email
  Returns:
    LookupMembershipNameResponse: Response message for LookupMembershipName
    operation which is containing a resource name of the membership in the
    format:
    'name: members/{member_id}'
  """

  client = GetClient(version)
  messages = GetMessages(version)

  encoding.AddCustomJsonFieldMapping(
      messages.CloudidentityGroupsMembershipsLookupRequest,
      'memberKey_id', 'memberKey.id')
  return client.groups_memberships.Lookup(
      messages.CloudidentityGroupsMembershipsLookupRequest(
          memberKey_id=member_email, parent=group_id))
