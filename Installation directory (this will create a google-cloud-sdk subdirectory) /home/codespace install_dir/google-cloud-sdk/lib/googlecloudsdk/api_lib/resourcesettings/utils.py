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
"""Utilities for manipulating organization policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resourcesettings import service as settings_service

ORGANIZATION = 'organization'
FOLDER = 'folder'
PROJECT = 'project'


def ComputeResourceType(args):
  """Returns the resource type from the user-specified arguments.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  if args.organization:
    resource_type = ORGANIZATION
  elif args.folder:
    resource_type = FOLDER
  else:
    resource_type = PROJECT

  return resource_type


def GetPatchRequestFromArgs(args, name, local_value, etag):
  """Returns the GoogleCloudResourcesettingsV1Setting from the user-specified arguments.

  Args:
    resource_type: A String object that contains the resource type
    name: The resource name of the setting and has the following syntax:
      [organizations|folders|projects]/{resource_id}/settings/{setting_name}.
    local_value: The configured value of the setting at the given parent
      resource
    etag: A fingerprint used for optimistic concurrency.
  """

  resource_type = ComputeResourceType(args)

  return GetPatchRequestFromResourceType(resource_type, name, local_value, etag)


def GetPatchRequestFromResourceType(resource_type, name, local_value, etag):
  """Returns the GoogleCloudResourcesettingsV1Setting from the user-specified arguments.

  Args:
    resource_type: A String object that contains the resource type
    name: The resource name of the setting and has the following syntax:
      [organizations|folders|projects]/{resource_id}/settings/{setting_name}.
    local_value: The configured value of the setting at the given parent
      resource
    etag: A fingerprint used for optimistic concurrency.
  """

  setting = settings_service.ResourceSettingsMessages(
  ).GoogleCloudResourcesettingsV1Setting(
      name=name, localValue=local_value, etag=etag)

  if resource_type == ORGANIZATION:
    request = settings_service.ResourceSettingsMessages(
    ).ResourcesettingsOrganizationsSettingsPatchRequest(
        name=name, googleCloudResourcesettingsV1Setting=setting)
  elif resource_type == FOLDER:
    request = settings_service.ResourceSettingsMessages(
    ).ResourcesettingsFoldersSettingsPatchRequest(
        name=name, googleCloudResourcesettingsV1Setting=setting)
  else:
    request = settings_service.ResourceSettingsMessages(
    ).ResourcesettingsProjectsSettingsPatchRequest(
        name=name, googleCloudResourcesettingsV1Setting=setting)

  return request


def GetRequestFromArgs(args, setting_name, is_effective):
  """Returns the get_request from the user-specified arguments.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
    setting_name: setting name such as `settings/iam-projectCreatorRoles`
    is_effective: indicate if it is requesting for an effective setting
  """

  resource_type = ComputeResourceType(args)

  return GetRequestFromResourceType(resource_type, setting_name, is_effective)


def GetRequestFromResourceType(resource_type, setting_name, is_effective):
  """Returns the get_request from the user-specified arguments.

  Args:
    resource_type: A String object that contains the resource type
    setting_name: setting name such as `settings/iam-projectCreatorRoles`
    is_effective: indicate if it is requesting for an effective setting
  """

  messages = settings_service.ResourceSettingsMessages()

  if resource_type == ORGANIZATION:
    view = messages.ResourcesettingsOrganizationsSettingsGetRequest.ViewValueValuesEnum.SETTING_VIEW_EFFECTIVE_VALUE if is_effective else messages.ResourcesettingsOrganizationsSettingsGetRequest.ViewValueValuesEnum.SETTING_VIEW_LOCAL_VALUE
    get_request = messages.ResourcesettingsOrganizationsSettingsGetRequest(
        name=setting_name, view=view)
  elif resource_type == FOLDER:
    view = messages.ResourcesettingsFoldersSettingsGetRequest.ViewValueValuesEnum.SETTING_VIEW_EFFECTIVE_VALUE if is_effective else messages.ResourcesettingsFoldersSettingsGetRequest.ViewValueValuesEnum.SETTING_VIEW_LOCAL_VALUE
    get_request = messages.ResourcesettingsFoldersSettingsGetRequest(
        name=setting_name, view=view)
  else:
    view = messages.ResourcesettingsProjectsSettingsGetRequest.ViewValueValuesEnum.SETTING_VIEW_EFFECTIVE_VALUE if is_effective else messages.ResourcesettingsProjectsSettingsGetRequest.ViewValueValuesEnum.SETTING_VIEW_LOCAL_VALUE
    get_request = messages.ResourcesettingsProjectsSettingsGetRequest(
        name=setting_name, view=view)

  return get_request


def GetListRequestFromArgs(args, parent_resource, show_value):
  """Returns the get_request from the user-specified arguments.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
    parent_resource: resource location such as `organizations/123`
    show_value: if true, show all setting values set on the resource; if false,
      show all available settings.
  """

  messages = settings_service.ResourceSettingsMessages()

  if args.organization:
    view = messages.ResourcesettingsOrganizationsSettingsListRequest.ViewValueValuesEnum.SETTING_VIEW_LOCAL_VALUE if show_value else messages.ResourcesettingsOrganizationsSettingsListRequest.ViewValueValuesEnum.SETTING_VIEW_BASIC
    get_request = messages.ResourcesettingsOrganizationsSettingsListRequest(
        parent=parent_resource, view=view)
  elif args.folder:
    view = messages.ResourcesettingsFoldersSettingsListRequest.ViewValueValuesEnum.SETTING_VIEW_LOCAL_VALUE if show_value else messages.ResourcesettingsFoldersSettingsListRequest.ViewValueValuesEnum.SETTING_VIEW_BASIC
    get_request = messages.ResourcesettingsFoldersSettingsListRequest(
        parent=parent_resource, view=view)
  else:
    view = messages.ResourcesettingsProjectsSettingsListRequest.ViewValueValuesEnum.SETTING_VIEW_LOCAL_VALUE if show_value else messages.ResourcesettingsProjectsSettingsListRequest.ViewValueValuesEnum.SETTING_VIEW_BASIC
    get_request = messages.ResourcesettingsProjectsSettingsListRequest(
        parent=parent_resource, view=view)

  return get_request


def GetServiceFromArgs(args):
  """Returns the service from the user-specified arguments.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """

  resource_type = ComputeResourceType(args)

  return GetServiceFromResourceType(resource_type)


def GetServiceFromResourceType(resource_type):
  """Returns the service from the resource type input.

  Args:
    resource_type: A String object that contains the resource type
  """

  if resource_type == ORGANIZATION:
    service = settings_service.OrganizationsSettingsService()
  elif resource_type == FOLDER:
    service = settings_service.FoldersSettingsService()
  else:
    service = settings_service.ProjectsSettingsService()

  return service


def GetValueServiceFromArgs(args):
  """Returns the value-service from the user-specified arguments.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """

  resource_type = ComputeResourceType(args)

  return GetValueServiceFromResourceType(resource_type)


def GetValueServiceFromResourceType(resource_type):
  """Returns the value-service from the resource type input.

  Args:
    resource_type: A String object that contains the resource type
  """

  if resource_type == ORGANIZATION:
    value_service = settings_service.OrganizationsSettingsValueService()
  elif resource_type == FOLDER:
    value_service = settings_service.FoldersSettingsValueService()
  else:
    value_service = settings_service.ProjectsSettingsValueService()

  return value_service
