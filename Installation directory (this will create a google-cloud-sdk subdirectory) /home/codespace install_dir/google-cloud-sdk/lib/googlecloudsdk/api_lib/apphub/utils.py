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
"""Util for Apphub Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources

VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha',
    base.ReleaseTrack.GA: 'v1',
}


# The messages module can also be accessed from client.MESSAGES_MODULE
def GetMessagesModule(release_track=base.ReleaseTrack.ALPHA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetMessagesModule('apphub', api_version)


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance('apphub', api_version)


def AddToUpdateMask(update_mask, field_name):
  if update_mask:
    update_mask += ','
  return update_mask + field_name


def GetOperationResource(operation, release_track=base.ReleaseTrack.ALPHA):
  """Converts an Operation to a Resource that can be used with `waiter.WaitFor`."""
  api_version = VERSION_MAP.get(release_track)
  return resources.Registry().ParseRelativeName(
      operation.name,
      'apphub.projects.locations.operations',
      api_version=api_version,
  )


def WaitForOperation(poller, operation, message, max_wait_sec):
  return waiter.WaitFor(
      poller,
      GetOperationResource(operation),
      message,
      max_wait_ms=max_wait_sec * 1000,
  )


def PopulateAttributes(args, release_track=base.ReleaseTrack.ALPHA):
  """Populate attirbutes from args."""

  attributes = GetMessagesModule(release_track).Attributes()
  if args.environment_type:
    attributes.environment = GetMessagesModule(release_track).Environment(
        type=GetMessagesModule(release_track).Environment.TypeValueValuesEnum(
            args.environment_type
        )
    )

  if args.criticality_type:
    attributes.criticality = GetMessagesModule(release_track).Criticality(
        type=GetMessagesModule(release_track).Criticality.TypeValueValuesEnum(
            args.criticality_type
        )
    )

  for b_owner in args.business_owners or []:
    business_owner = GetMessagesModule(release_track).ContactInfo()
    business_owner.email = b_owner.get('email', None)
    if b_owner.get('display-name', None):
      business_owner.displayName = b_owner.get('display-name', None)
    if release_track == base.ReleaseTrack.ALPHA:
      if b_owner.get('channel-uri', None):
        business_owner.channel = GetMessagesModule(release_track).Channel(
            uri=b_owner.get('channel-uri')
        )
    attributes.businessOwners.append(business_owner)

  for d_owner in args.developer_owners or []:
    developer_owner = GetMessagesModule(release_track).ContactInfo()
    developer_owner.email = d_owner.get('email', None)
    if d_owner.get('display-name', None):
      developer_owner.displayName = d_owner.get('display-name', None)
    if release_track == base.ReleaseTrack.ALPHA:
      if d_owner.get('channel-uri', None):
        developer_owner.channel = GetMessagesModule(release_track).Channel(
            uri=d_owner.get('channel-uri')
        )
    attributes.developerOwners.append(developer_owner)

  for o_owner in args.operator_owners or []:
    operator_owner = GetMessagesModule(release_track).ContactInfo()
    operator_owner.email = o_owner.get('email', None)
    if o_owner.get('display-name'):
      operator_owner.displayName = o_owner.get('display-name')
    if release_track == base.ReleaseTrack.ALPHA:
      if o_owner.get('channel-uri'):
        operator_owner.channel = GetMessagesModule(release_track).Channel(
            uri=o_owner.get('channel-uri')
        )
    attributes.operatorOwners.append(operator_owner)

  return attributes


def MakeGetUriFunc(collection, release_track=base.ReleaseTrack.ALPHA):
  """Returns a function which turns a resource into a uri."""

  def _GetUri(resource):
    api_version = VERSION_MAP.get(release_track)
    result = resources.Registry().ParseRelativeName(
        resource.name, collection=collection, api_version=api_version
    )
    return result.SelfLink()

  return _GetUri


def GetServiceProjectRef(args):
  """Returns a service project reference."""
  service_project_ref = args.CONCEPTS.service_project.Parse()
  if not service_project_ref.Name():
    raise exceptions.InvalidArgumentException(
        'service project', 'service project id must be non-empty.'
    )
  return service_project_ref


def GetOperationRef(args):
  """Returns a operation reference."""
  operation_ref = args.CONCEPTS.operation.Parse()
  if not operation_ref.Name():
    raise exceptions.InvalidArgumentException(
        'operation', 'operation id must be non-empty.'
    )
  return operation_ref


def GetDiscoveredWorkloadRef(args):
  """Returns a discovered workload reference."""
  discovered_workload_ref = args.CONCEPTS.discovered_workload.Parse()
  if not discovered_workload_ref.Name():
    raise exceptions.InvalidArgumentException(
        'discovered workload', 'discovered workload id must be non-empty.'
    )
  return discovered_workload_ref


def GetDiscoveredServiceRef(args):
  """Returns a discovered service reference."""
  discovered_service_ref = args.CONCEPTS.discovered_service.Parse()
  if not discovered_service_ref.Name():
    raise exceptions.InvalidArgumentException(
        'discovered service', 'discovered service id must be non-empty.'
    )
  return discovered_service_ref


def GetApplicationRef(args):
  """Returns a application reference."""
  app_ref = args.CONCEPTS.application.Parse()
  if not app_ref.Name():
    raise exceptions.InvalidArgumentException(
        'application', 'application id must be non-empty.'
    )
  return app_ref


def GetApplicationWorkloadRef(args):
  """Returns a application workload reference."""
  workload_ref = args.CONCEPTS.workload.Parse()
  if not workload_ref.Name():
    raise exceptions.InvalidArgumentException(
        'workload', 'workload id must be non-empty.'
    )
  return workload_ref


def GetApplicationServiceRef(args):
  """Returns a application service reference."""
  service_ref = args.CONCEPTS.service.Parse()
  if not service_ref.Name():
    raise exceptions.InvalidArgumentException(
        'service', 'service id must be non-empty.'
    )
  return service_ref
