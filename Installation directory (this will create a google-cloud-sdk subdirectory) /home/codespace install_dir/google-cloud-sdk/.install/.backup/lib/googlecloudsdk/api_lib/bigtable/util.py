# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""A library that is used to support our commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def GetAdminClient():
  """Shortcut to get the latest Bigtable Admin client."""
  return apis.GetClientInstance('bigtableadmin', 'v2')


def GetAdminMessages():
  """Shortcut to get the latest Bigtable Admin messages."""
  return apis.GetMessagesModule('bigtableadmin', 'v2')


def ProjectUrl():
  return '/'.join(['projects', properties.VALUES.core.project.Get()])


def LocationUrl(location):
  return '/'.join([ProjectUrl(), 'locations', location])


def _Await(result_service, operation_ref, message):
  client = GetAdminClient()
  poller = waiter.CloudOperationPoller(result_service, client.operations)
  return waiter.WaitFor(poller, operation_ref, message)


def AwaitCluster(operation_ref, message):
  """Waits for cluster long running operation to complete."""
  client = GetAdminClient()
  return _Await(client.projects_instances_clusters, operation_ref, message)


def AwaitInstance(operation_ref, message):
  """Waits for instance long running operation to complete."""
  client = GetAdminClient()
  return _Await(client.projects_instances, operation_ref, message)


def AwaitAppProfile(operation_ref, message):
  """Waits for app profile long running operation to complete."""
  client = GetAdminClient()
  return _Await(client.projects_instances_appProfiles, operation_ref, message)


def AwaitTable(operation_ref, message):
  """Waits for table long running operation to complete."""
  client = GetAdminClient()
  return _Await(client.projects_instances_tables, operation_ref, message)


def AwaitBackup(operation_ref, message):
  """Waits for backup long running operation to complete."""
  client = GetAdminClient()
  return _Await(
      client.projects_instances_clusters_backups, operation_ref, message
  )


def GetAppProfileRef(instance, app_profile):
  """Get a resource reference to an app profile."""
  return resources.REGISTRY.Parse(
      app_profile,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance,
      },
      collection='bigtableadmin.projects.instances.appProfiles',
  )


def GetClusterRef(instance, cluster):
  """Get a resource reference to a cluster."""
  return resources.REGISTRY.Parse(
      cluster,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance,
      },
      collection='bigtableadmin.projects.instances.clusters',
  )


def GetOperationRef(operation):
  """Get a resource reference to a long running operation."""
  return resources.REGISTRY.ParseRelativeName(
      operation.name, 'bigtableadmin.operations'
  )


def GetInstanceRef(instance):
  """Get a resource reference to an instance."""
  return resources.REGISTRY.Parse(
      instance,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection='bigtableadmin.projects.instances',
  )


def GetTableRef(instance, table):
  """Get a resource reference to a table."""
  return resources.REGISTRY.Parse(
      table,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance,
      },
      collection='bigtableadmin.projects.instances.tables',
  )


WARNING_TYPE_PREFIX = 'CLOUD_BIGTABLE_APP_PROFILE_WARNING'


def FormatErrorMessages(exception):
  """Format app profile error message from API and raise new exception.

  The error messages returned from the backend API are not formatted well when
  using the default format. This raises a new generic exception with a well
  formatted error message built from the original response.

  Args:
    exception: HttpError raised by API.

  Raises:
    exceptions.HttpException: Reformatted error raised by API.
  """
  response = json.loads(exception.content)
  if (
      response.get('error') is None
      or response.get('error').get('details') is None
  ):
    raise exception
  errors = ['Errors:']
  warnings = ['Warnings (use --force to ignore):']
  for detail in response['error']['details']:
    violations = detail.get('violations', [])
    for violation in violations:
      if violation.get('type').startswith(WARNING_TYPE_PREFIX):
        warnings.append(violation.get('description'))
      else:
        errors.append(violation.get('description'))

  error_msg = ''
  if len(warnings) > 1:
    error_msg += '\n\t'.join(warnings)
  if len(errors) > 1:
    error_msg += '\n\t'.join(errors)

  if not error_msg:
    raise exception
  raise exceptions.HttpException(
      exception, '{}\n{}'.format(response['error']['message'], error_msg)
  )
